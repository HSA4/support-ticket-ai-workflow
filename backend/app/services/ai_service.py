"""
AI Service for OpenAI integration.

This module provides the AIService class that handles all LLM-based operations
for the support ticket workflow, including classification, extraction, response
generation, and routing decisions.
"""

import asyncio
import json
import logging
import re
from typing import Any, Dict, List, Optional

from openai import AsyncOpenAI, APIError, RateLimitError, APITimeoutError, APIConnectionError
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
    before_sleep_log,
)

from app.core.config import settings
from app.schemas.workflow import (
    ClassificationResult,
    ExtractionResult,
    ExtractedField,
    ResponseDraft,
    RoutingDecision,
)

logger = logging.getLogger(__name__)


# Constants for available options
AVAILABLE_CATEGORIES = [
    "technical",
    "billing",
    "account",
    "feature_request",
    "bug_report",
    "general",
]

AVAILABLE_TEAMS = [
    "technical_support",
    "billing_team",
    "account_management",
    "product_team",
    "escalation_team",
]

SEVERITY_LEVELS = ["critical", "high", "medium", "low"]


class AIServiceError(Exception):
    """Exception raised when AI service operations fail."""

    pass


class AIParseError(AIServiceError):
    """Exception raised when parsing AI response fails."""

    pass


class AIService:
    """
    AI Service for handling OpenAI API interactions.

    This service provides methods for classification, field extraction,
    response generation, and routing decisions using the OpenAI API.

    Attributes:
        client: AsyncOpenAI client instance
        model: Default model to use for completions
        max_tokens: Maximum tokens for responses
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the AI service.

        Args:
            api_key: OpenAI API key (defaults to settings.OPENAI_API_KEY)
        """
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.client = AsyncOpenAI(api_key=self.api_key)
        self.model = settings.DEFAULT_MODEL
        self.max_tokens = settings.MAX_TOKENS
        self._token_usage: Dict[str, int] = {"prompt": 0, "completion": 0, "total": 0}

    @retry(
        retry=retry_if_exception_type((RateLimitError, APITimeoutError, APIConnectionError)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True,
    )
    async def _call_openai(
        self,
        messages: List[Dict[str, str]],
        response_format: Optional[Dict[str, str]] = None,
        temperature: float = 0.3,
    ) -> Dict[str, Any]:
        """
        Make a call to the OpenAI API with retry logic and exponential backoff.

        Args:
            messages: List of message dictionaries for the chat completion
            response_format: Optional response format specification
            temperature: Sampling temperature (0.0-2.0)

        Returns:
            Parsed JSON response from the API

        Raises:
            AIServiceError: If the API call fails after retries
        """
        try:
            kwargs = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": self.max_tokens,
            }

            if response_format:
                kwargs["response_format"] = response_format

            response = await self.client.chat.completions.create(**kwargs)

            # Track token usage
            if response.usage:
                self._token_usage["prompt"] += response.usage.prompt_tokens
                self._token_usage["completion"] += response.usage.completion_tokens
                self._token_usage["total"] += response.usage.total_tokens

            # Parse the response content
            content = response.choices[0].message.content
            if not content:
                raise AIServiceError("Empty response from OpenAI")

            # Try to parse as JSON
            try:
                return self._parse_json_response(content)
            except AIParseError as e:
                logger.warning(f"Failed to parse OpenAI response as JSON: {e}")
                raise AIServiceError(f"Invalid JSON response: {content[:200]}")

        except RateLimitError as e:
            logger.warning(f"OpenAI rate limit hit: {e}")
            raise
        except APITimeoutError as e:
            logger.warning(f"OpenAI API timeout: {e}")
            raise
        except APIConnectionError as e:
            logger.warning(f"OpenAI connection error: {e}")
            raise
        except APIError as e:
            logger.error(f"OpenAI API error: {e}")
            raise AIServiceError(f"OpenAI API error: {e}")
        except Exception as e:
            logger.error(f"Unexpected error calling OpenAI: {e}")
            raise AIServiceError(f"Unexpected error: {e}")

    def _parse_json_response(self, content: str) -> Dict[str, Any]:
        """
        Parse JSON from LLM response content.

        Handles various formats including:
        - Raw JSON
        - JSON wrapped in markdown code blocks
        - JSON with extra text before/after

        Args:
            content: The raw response content from the LLM

        Returns:
            Dict[str, Any]: Parsed JSON dictionary

        Raises:
            AIParseError: If JSON cannot be parsed
        """
        content = content.strip()

        # Try to extract JSON from markdown code blocks
        json_block_pattern = r"```(?:json)?\s*([\s\S]*?)\s*```"
        match = re.search(json_block_pattern, content)
        if match:
            content = match.group(1).strip()

        # Try to find JSON object in the content
        json_object_pattern = r"\{[\s\S]*\}"
        match = re.search(json_object_pattern, content)
        if match:
            content = match.group(0)

        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.debug(f"Content was: {content}")
            raise AIParseError(f"Failed to parse JSON response: {e}")

    async def classify_ticket(
        self,
        subject: str,
        body: str,
        categories: Optional[List[str]] = None,
    ) -> ClassificationResult:
        """
        Classify a support ticket into a category and severity.

        Args:
            subject: Ticket subject line
            body: Ticket body content
            categories: Available categories for classification (defaults to standard categories)

        Returns:
            ClassificationResult: Classification with category, severity, and confidence scores
        """
        categories = categories or AVAILABLE_CATEGORIES

        if not settings.ENABLE_AI_CLASSIFICATION:
            return self._fallback_classification(subject, body)

        try:
            from app.prompts.classification import CLASSIFICATION_PROMPT
            from jinja2 import Template

            prompt = Template(CLASSIFICATION_PROMPT).render(
                subject=subject,
                body=body[:3000],  # Truncate to avoid token limits
                categories=", ".join(categories),
            )

            messages = [
                {
                    "role": "system",
                    "content": "You are a precise support ticket classifier. Always respond with valid JSON.",
                },
                {"role": "user", "content": prompt},
            ]

            data = await self._call_openai(
                messages=messages,
                response_format={"type": "json_object"},
                temperature=0.2,
            )

            # Validate and normalize category
            category = data.get("category", "general").lower()
            if category not in AVAILABLE_CATEGORIES:
                category = "general"

            # Validate and normalize severity
            severity = data.get("severity", "medium").lower()
            if severity not in SEVERITY_LEVELS:
                severity = "medium"

            # Validate confidence scores
            category_confidence = float(data.get("category_confidence", 0.5))
            severity_confidence = float(data.get("severity_confidence", 0.5))
            category_confidence = max(0.0, min(1.0, category_confidence))
            severity_confidence = max(0.0, min(1.0, severity_confidence))

            # Validate secondary categories
            secondary_categories = []
            for cat in data.get("secondary_categories", []):
                if isinstance(cat, str) and cat.lower() in AVAILABLE_CATEGORIES:
                    secondary_categories.append(cat.lower())

            return ClassificationResult(
                category=category,
                category_confidence=category_confidence,
                severity=severity,
                severity_confidence=severity_confidence,
                secondary_categories=secondary_categories,
                reasoning=data.get("reasoning"),
                keywords_matched=data.get("keywords_matched", []),
                urgency_indicators=data.get("urgency_indicators", []),
            )

        except (AIParseError, AIServiceError, RateLimitError, APITimeoutError, APIConnectionError) as e:
            logger.warning(f"AI classification failed, using fallback: {e}")
            return self._fallback_classification(subject, body)
        except Exception as e:
            logger.error(f"Unexpected error in classification: {e}")
            return self._fallback_classification(subject, body)

    def _fallback_classification(
        self,
        subject: str,
        body: str,
    ) -> ClassificationResult:
        """
        Fallback rule-based classification using keyword matching.

        Args:
            subject: Ticket subject line
            body: Ticket body content

        Returns:
            ClassificationResult: Classification based on keyword matching
        """
        text = f"{subject} {body}".lower()

        # Category keywords mapping
        category_keywords = {
            "technical": ["error", "bug", "crash", "not working", "failed", "broken", "issue"],
            "billing": ["charge", "refund", "invoice", "payment", "subscription", "overcharged", "bill"],
            "account": ["login", "password", "account", "access", "locked", "credentials", "signin"],
            "feature_request": ["wish", "request", "feature", "enhancement", "suggest", "idea", "would like"],
            "bug_report": ["bug", "defect", "incorrect", "unexpected", "wrong"],
            "general": ["question", "help", "how to", "information", "inquiry"],
        }

        # Severity indicators
        severity_indicators = {
            "critical": ["urgent", "asap", "critical", "down", "emergency", "production", "immediately"],
            "high": ["important", "serious", "affecting", "soon", "quickly"],
            "medium": ["moderate", "somewhat", "issue"],
            "low": ["minor", "small", "whenever", "no rush"],
        }

        # Find matching category
        best_category = "general"
        best_score = 0
        keywords_matched = []

        for category, keywords in category_keywords.items():
            score = sum(1 for kw in keywords if kw in text)
            if score > best_score:
                best_score = score
                best_category = category
                keywords_matched = [kw for kw in keywords if kw in text]

        # Find matching severity
        best_severity = "medium"
        urgency_indicators = []

        for severity, indicators in severity_indicators.items():
            if any(ind in text for ind in indicators):
                best_severity = severity
                urgency_indicators = [ind for ind in indicators if ind in text]
                break

        # Calculate confidence based on keyword matches
        category_confidence = min(0.9, 0.5 + (best_score * 0.1))
        severity_confidence = 0.7 if urgency_indicators else 0.5

        return ClassificationResult(
            category=best_category,
            category_confidence=category_confidence,
            severity=best_severity,
            severity_confidence=severity_confidence,
            secondary_categories=[],
            reasoning=f"Rule-based classification based on keywords: {keywords_matched}",
            keywords_matched=keywords_matched,
            urgency_indicators=urgency_indicators,
        )

    async def extract_fields(
        self,
        subject: str,
        body: str,
        category: str,
    ) -> ExtractionResult:
        """
        Extract structured fields from a support ticket.

        Args:
            subject: Ticket subject line
            body: Ticket body content
            category: Ticket category for context

        Returns:
            ExtractionResult: Extracted fields with confidence scores and source spans
        """
        if not settings.ENABLE_AI_EXTRACTION:
            return self._fallback_extraction(subject, body)

        try:
            from app.prompts.extraction import EXTRACTION_PROMPT
            from jinja2 import Template

            prompt = Template(EXTRACTION_PROMPT).render(
                subject=subject,
                body=body[:3000],  # Truncate to avoid token limits
                category=category,
            )

            messages = [
                {
                    "role": "system",
                    "content": "You are a precise data extractor. Always respond with valid JSON.",
                },
                {"role": "user", "content": prompt},
            ]

            data = await self._call_openai(
                messages=messages,
                response_format={"type": "json_object"},
                temperature=0.1,
            )

            fields = []
            for field_data in data.get("fields", []):
                if not isinstance(field_data, dict):
                    continue

                name = field_data.get("name")
                value = field_data.get("value")
                if name is None or value is None:
                    continue

                confidence = float(field_data.get("confidence", 0.5))
                confidence = max(0.0, min(1.0, confidence))

                fields.append(
                    ExtractedField(
                        name=name,
                        value=value,
                        confidence=confidence,
                        source_span=field_data.get("source_text"),
                    )
                )

            return ExtractionResult(
                fields=fields,
                missing_required=data.get("missing_critical", []),
                validation_errors=data.get("validation_errors", []),
            )

        except (AIParseError, AIServiceError, RateLimitError, APITimeoutError, APIConnectionError) as e:
            logger.warning(f"AI extraction failed, using fallback: {e}")
            return self._fallback_extraction(subject, body)
        except Exception as e:
            logger.error(f"Unexpected error in extraction: {e}")
            return self._fallback_extraction(subject, body)

    def _fallback_extraction(
        self,
        subject: str,
        body: str,
    ) -> ExtractionResult:
        """
        Fallback regex-based field extraction.

        Args:
            subject: Ticket subject line
            body: Ticket body content

        Returns:
            ExtractionResult: Extracted fields using regex patterns
        """
        text = f"{subject} {body}"
        fields = []

        # Order ID patterns
        order_patterns = [
            r"(ORD-\d{6,})",
            r"(#\d{5,})",
            r"order[:\s]+(\d+)",
        ]
        for pattern in order_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                fields.append(
                    ExtractedField(
                        name="order_id",
                        value=match.group(1),
                        confidence=0.9,
                        source_span=match.group(0),
                    )
                )
                break

        # Email pattern
        email_pattern = r"([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})"
        email_matches = re.findall(email_pattern, text)
        for email in email_matches:
            fields.append(
                ExtractedField(
                    name="account_email",
                    value=email,
                    confidence=0.95,
                    source_span=email,
                )
            )

        # Phone number pattern (various formats)
        phone_patterns = [
            r"(\+?\d{1,3}[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4})",
            r"(\+?\d{10,15})",
        ]
        for pattern in phone_patterns:
            match = re.search(pattern, text)
            if match:
                fields.append(
                    ExtractedField(
                        name="phone_number",
                        value=match.group(1),
                        confidence=0.8,
                        source_span=match.group(0),
                    )
                )
                break

        # Error code patterns
        error_patterns = [
            r"(ERR-\d+)",
            r"(0x[0-9A-Fa-f]+)",
            r"error[:\s]+(\d+)",
        ]
        for pattern in error_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                fields.append(
                    ExtractedField(
                        name="error_code",
                        value=match.group(1),
                        confidence=0.85,
                        source_span=match.group(0),
                    )
                )
                break

        # Priority keywords
        priority_keywords = ["urgent", "asap", "critical", "emergency", "immediately", "important"]
        found_keywords = [kw for kw in priority_keywords if kw.lower() in text.lower()]
        if found_keywords:
            fields.append(
                ExtractedField(
                    name="priority_keywords",
                    value=found_keywords,
                    confidence=0.9,
                    source_span=", ".join(found_keywords),
                )
            )

        return ExtractionResult(
            fields=fields,
            missing_required=[],
            validation_errors=[],
        )

    async def generate_response(
        self,
        subject: str,
        body: str,
        category: str,
        severity: str,
        extracted_fields: Dict[str, Any],
        customer_name: Optional[str] = None,
        tone: str = "friendly",
    ) -> ResponseDraft:
        """
        Generate a response draft for a support ticket.

        Args:
            subject: Ticket subject line
            body: Ticket body content
            category: Ticket category
            severity: Ticket severity level
            extracted_fields: Extracted fields for personalization
            customer_name: Customer name for personalization
            tone: Desired response tone

        Returns:
            ResponseDraft: Generated response draft
        """
        context = {
            "subject": subject,
            "body": body,
            "category": category,
            "severity": severity,
            "extracted_fields": extracted_fields,
            "customer_name": customer_name,
            "tone": tone,
        }

        if not settings.ENABLE_RESPONSE_GENERATION:
            return self._fallback_response(context)

        try:
            from app.prompts.response import RESPONSE_GENERATION_PROMPT
            from jinja2 import Template

            prompt = Template(RESPONSE_GENERATION_PROMPT).render(
                subject=subject,
                body=body[:2000],
                category=category,
                severity=severity,
                extracted_fields=json.dumps(extracted_fields, default=str),
                customer_name=customer_name or "Customer",
                tone=tone,
            )

            messages = [
                {
                    "role": "system",
                    "content": "You are a helpful customer support agent. Write professional, empathetic responses. Always respond with valid JSON.",
                },
                {"role": "user", "content": prompt},
            ]

            data = await self._call_openai(
                messages=messages,
                response_format={"type": "json_object"},
                temperature=0.7,
            )

            # Build full response if not provided
            full_response = data.get("full_response", "")
            if not full_response:
                parts = [
                    data.get("greeting", "Dear Customer,"),
                    data.get("acknowledgment", ""),
                    data.get("explanation", ""),
                ]
                if data.get("action_items"):
                    parts.append("\nNext steps:")
                    for item in data["action_items"]:
                        parts.append(f"- {item}")
                parts.append(data.get("timeline", ""))
                parts.append(data.get("closing", "Best regards,\nSupport Team"))
                full_response = "\n\n".join(p for p in parts if p)

            return ResponseDraft(
                content=full_response,
                tone=tone,
                template_used=None,
                suggested_actions=data.get("action_items", []),
                requires_escalation=bool(data.get("requires_escalation", False)),
                greeting=data.get("greeting"),
                acknowledgment=data.get("acknowledgment"),
                explanation=data.get("explanation"),
                action_items=data.get("action_items", []),
                timeline=data.get("timeline"),
                closing=data.get("closing"),
            )

        except (AIParseError, AIServiceError, RateLimitError, APITimeoutError, APIConnectionError) as e:
            logger.warning(f"AI response generation failed, using fallback: {e}")
            return self._fallback_response(context)
        except Exception as e:
            logger.error(f"Unexpected error in response generation: {e}")
            return self._fallback_response(context)

    def _fallback_response(
        self,
        context: Dict[str, Any],
    ) -> ResponseDraft:
        """
        Fallback template-based response generation.

        Args:
            context: Dictionary with ticket context

        Returns:
            ResponseDraft: Template-based response
        """
        category = context.get("category", "general")
        severity = context.get("severity", "medium")
        customer_name = context.get("customer_name", "Customer")
        tone = context.get("tone", "friendly")

        # Template responses by category
        templates = {
            "technical": {
                "greeting": f"Dear {customer_name},",
                "acknowledgment": "Thank you for reporting this technical issue. We understand how frustrating technical problems can be.",
                "action_items": [
                    "Our technical team is investigating the issue",
                    "We will provide an update within 24 hours",
                ],
                "timeline": "Expected resolution: 1-2 business days",
                "closing": "Best regards,\nTechnical Support Team",
            },
            "billing": {
                "greeting": f"Dear {customer_name},",
                "acknowledgment": "Thank you for contacting us about your billing inquiry. We take all billing matters seriously.",
                "action_items": [
                    "Our billing team is reviewing your account",
                    "We will respond with a detailed explanation",
                ],
                "timeline": "Expected response: 24-48 hours",
                "closing": "Best regards,\nBilling Support Team",
            },
            "account": {
                "greeting": f"Dear {customer_name},",
                "acknowledgment": "We understand you're experiencing account-related issues. Account security is our top priority.",
                "action_items": [
                    "Please verify your identity by responding to this email",
                    "Our team will assist with account recovery",
                ],
                "timeline": "Expected resolution: 24 hours",
                "closing": "Best regards,\nAccount Management Team",
            },
            "feature_request": {
                "greeting": f"Dear {customer_name},",
                "acknowledgment": "Thank you for sharing your feature suggestion with us. Customer feedback is invaluable to our product development.",
                "action_items": [
                    "Your request has been logged and forwarded to our product team",
                    "We will keep you updated on its status",
                ],
                "timeline": "We review feature requests monthly",
                "closing": "Best regards,\nProduct Team",
            },
            "bug_report": {
                "greeting": f"Dear {customer_name},",
                "acknowledgment": "Thank you for taking the time to report this bug. Your feedback helps us improve our product.",
                "action_items": [
                    "Our development team is investigating",
                    "We may follow up for additional details",
                ],
                "timeline": "Bug fixes are prioritized based on severity",
                "closing": "Best regards,\nDevelopment Team",
            },
            "general": {
                "greeting": f"Dear {customer_name},",
                "acknowledgment": "Thank you for reaching out to our support team. We're here to help.",
                "action_items": [
                    "We are reviewing your inquiry",
                    "A team member will respond shortly",
                ],
                "timeline": "Expected response: 24 hours",
                "closing": "Best regards,\nSupport Team",
            },
        }

        template = templates.get(category, templates["general"])

        # Adjust for severity
        if severity == "critical":
            template["timeline"] = "We are treating this as a priority and will respond within 1 hour."
            template["action_items"].insert(0, "This issue has been escalated to our senior team")
        elif severity == "high":
            template["timeline"] = "Expected response: 4 hours"

        # Build response content
        parts = [
            template["greeting"],
            template["acknowledgment"],
            "\nNext steps:",
        ]
        for item in template["action_items"]:
            parts.append(f"- {item}")
        parts.append(template["timeline"])
        parts.append(template["closing"])

        full_response = "\n\n".join(parts)

        return ResponseDraft(
            content=full_response,
            tone=tone,
            template_used=f"{category}_template",
            suggested_actions=template["action_items"],
            requires_escalation=(severity == "critical"),
            greeting=template["greeting"],
            acknowledgment=template["acknowledgment"],
            action_items=template["action_items"],
            timeline=template["timeline"],
            closing=template["closing"],
        )

    async def determine_routing(
        self,
        subject: str,
        body: str,
        category: str,
        severity: str,
        extracted_fields: Dict[str, Any],
        teams: Optional[List[str]] = None,
    ) -> RoutingDecision:
        """
        Determine the best team to handle a support ticket.

        Args:
            subject: Ticket subject line
            body: Ticket body content
            category: Ticket category
            severity: Ticket severity level
            extracted_fields: Extracted fields for context
            teams: Available teams for routing (defaults to standard teams)

        Returns:
            RoutingDecision: Routing decision with team, priority, and reasoning
        """
        teams = teams or AVAILABLE_TEAMS
        context = {
            "subject": subject,
            "body": body,
            "category": category,
            "severity": severity,
            "extracted_fields": extracted_fields,
        }

        try:
            from app.prompts.routing import ROUTING_PROMPT
            from jinja2 import Template

            prompt = Template(ROUTING_PROMPT).render(
                subject=subject,
                body=body[:2000],
                category=category,
                severity=severity,
                extracted_fields=json.dumps(extracted_fields, default=str),
                teams=", ".join(teams),
            )

            messages = [
                {
                    "role": "system",
                    "content": "You are a routing expert. Analyze tickets and determine the best team. Always respond with valid JSON.",
                },
                {"role": "user", "content": prompt},
            ]

            data = await self._call_openai(
                messages=messages,
                response_format={"type": "json_object"},
                temperature=0.2,
            )

            # Validate and normalize team
            team = data.get("team", "technical_support").lower()
            if team not in AVAILABLE_TEAMS:
                team = "technical_support"

            # Validate priority
            priority = data.get("priority", "normal").lower()
            valid_priorities = ["urgent", "high", "normal", "low"]
            if priority not in valid_priorities:
                priority = "normal"

            # Process alternative teams
            alternative_teams = []
            for alt in data.get("alternative_teams", []):
                if isinstance(alt, dict):
                    alt_team = alt.get("team", "")
                    if alt_team in AVAILABLE_TEAMS:
                        alternative_teams.append(alt_team)
                elif isinstance(alt, str) and alt in AVAILABLE_TEAMS:
                    alternative_teams.append(alt)

            # Process escalation path
            escalation_path = data.get("escalation_path", [])
            if not isinstance(escalation_path, list):
                escalation_path = []

            return RoutingDecision(
                team=team,
                priority=priority,
                reasoning=data.get("reasoning", f"Routed based on {category} category"),
                alternative_teams=alternative_teams,
                escalation_path=escalation_path if escalation_path else None,
                confidence=0.9,
            )

        except (AIParseError, AIServiceError, RateLimitError, APITimeoutError, APIConnectionError) as e:
            logger.warning(f"AI routing failed, using fallback: {e}")
            return self._fallback_routing(context)
        except Exception as e:
            logger.error(f"Unexpected error in routing: {e}")
            return self._fallback_routing(context)

    def _fallback_routing(
        self,
        context: Dict[str, Any],
    ) -> RoutingDecision:
        """
        Fallback rule-based routing decision.

        Args:
            context: Dictionary with ticket context

        Returns:
            RoutingDecision: Rule-based routing decision
        """
        category = context.get("category", "general")
        severity = context.get("severity", "medium")

        # Category to team mapping
        category_team_map = {
            "technical": "technical_support",
            "billing": "billing_team",
            "account": "account_management",
            "feature_request": "product_team",
            "bug_report": "technical_support",
            "general": "technical_support",
        }

        # Severity to priority mapping
        severity_priority_map = {
            "critical": "urgent",
            "high": "high",
            "medium": "normal",
            "low": "low",
        }

        team = category_team_map.get(category, "technical_support")
        priority = severity_priority_map.get(severity, "normal")

        # Critical severity always goes to escalation team
        if severity == "critical":
            team = "escalation_team"

        # Build reasoning
        reasoning = f"Routed to {team} based on {category} category"
        if severity == "critical":
            reasoning += " and critical severity escalation"

        # Alternative teams based on category
        alternative_teams = []
        if category in ["technical", "bug_report"]:
            alternative_teams = ["account_management"]
        elif category == "account":
            alternative_teams = ["technical_support"]

        # Escalation paths
        escalation_paths = {
            "technical_support": ["senior_technical", "engineering_team"],
            "billing_team": ["billing_manager", "finance_team"],
            "account_management": ["account_manager", "security_team"],
            "product_team": ["product_manager"],
            "escalation_team": ["senior_management"],
        }

        return RoutingDecision(
            team=team,
            priority=priority,
            reasoning=reasoning,
            alternative_teams=alternative_teams,
            escalation_path=escalation_paths.get(team),
            confidence=0.85,
        )

    @property
    def token_usage(self) -> Dict[str, int]:
        """Get current token usage statistics."""
        return self._token_usage.copy()

    def reset_token_usage(self) -> None:
        """Reset token usage counters."""
        self._token_usage = {"prompt": 0, "completion": 0, "total": 0}

    async def health_check(self) -> bool:
        """
        Check if the AI service is healthy and can make API calls.

        Returns:
            True if healthy, False otherwise
        """
        try:
            # Make a minimal API call to check connectivity
            response = await asyncio.wait_for(
                self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": "ping"}],
                    max_tokens=5,
                ),
                timeout=5.0,
            )
            return bool(response.choices)
        except Exception as e:
            logger.warning(f"AI service health check failed: {e}")
            return False

    async def close(self) -> None:
        """Close the OpenAI client connection."""
        # AsyncOpenAI client doesn't require explicit close
        pass
