"""
Response generation module for the support ticket workflow.

This module provides response generation functionality for support tickets,
including AI-based generation via AIService and fallback template-based
responses when AI is unavailable.
"""

import logging
from typing import Any, Dict, List, Optional

from app.core.config import settings
from app.schemas import ExtractedField, ResponseDraft

logger = logging.getLogger(__name__)


# Template-based fallback responses by category
RESPONSE_TEMPLATES = {
    "technical": {
        "greeting": "Hello{customer_name},",
        "acknowledgment": "Thank you for reaching out about the technical issue you're experiencing.",
        "explanation": "Our technical team has been notified and is investigating the problem.",
        "action_items": [
            "Please try clearing your browser cache and cookies",
            "Ensure you're using the latest version of the application",
            "If the issue persists, please provide any error messages you see",
        ],
        "timeline": "We aim to respond within {response_time}.",
        "closing": "Best regards,\n{support_signature}",
    },
    "billing": {
        "greeting": "Dear{customer_name},",
        "acknowledgment": "Thank you for contacting us about your billing inquiry.",
        "explanation": "Our billing team will review your request and get back to you shortly.",
        "action_items": [
            "Please have your order ID ready for verification",
            "Check your account settings for recent transactions",
        ],
        "timeline": "We typically resolve billing inquiries within {response_time}.",
        "closing": "Sincerely,\n{billing_signature}",
    },
    "account": {
        "greeting": "Hi{customer_name},",
        "acknowledgment": "Thank you for reaching out about your account.",
        "explanation": "Our account management team is here to help you with your request.",
        "action_items": [
            "Please verify your email address associated with the account",
            "For security purposes, do not share your password",
        ],
        "timeline": "We'll respond to your request within {response_time}.",
        "closing": "Best regards,\n{support_signature}",
    },
    "feature_request": {
        "greeting": "Hello{customer_name},",
        "acknowledgment": "Thank you for taking the time to share your feature request with us.",
        "explanation": "We value your feedback and will consider it for future product development.",
        "action_items": [
            "Your request has been logged in our feature tracking system",
            "We'll notify you if this feature gets implemented",
        ],
        "timeline": "Product updates are typically shared in our monthly newsletter.",
        "closing": "Thank you for helping us improve!\n{product_signature}",
    },
    "bug_report": {
        "greeting": "Hi{customer_name},",
        "acknowledgment": "Thank you for reporting this issue. We appreciate your help in improving our product.",
        "explanation": "Our engineering team has been notified and will investigate the bug.",
        "action_items": [
            "If possible, please provide steps to reproduce the issue",
            "Include any screenshots or error messages if available",
        ],
        "timeline": "Bug reports are typically addressed within {response_time}.",
        "closing": "Best regards,\n{engineering_signature}",
    },
    "general": {
        "greeting": "Hello{customer_name},",
        "acknowledgment": "Thank you for contacting our support team.",
        "explanation": "We're here to help and will address your inquiry as soon as possible.",
        "action_items": [
            "Please provide any additional details that might help us assist you better",
        ],
        "timeline": "We aim to respond within {response_time}.",
        "closing": "Best regards,\n{support_signature}",
    },
}

# Response time by severity
RESPONSE_TIMES = {
    "critical": "1 hour",
    "high": "4 hours",
    "medium": "24 hours",
    "low": "72 hours",
}

# Signatures by team
TEAM_SIGNATURES = {
    "technical_support": "Technical Support Team",
    "billing_team": "Billing & Payments Team",
    "account_management": "Account Management Team",
    "product_team": "Product Team",
    "escalation_team": "Senior Support Team",
    "general_support": "Customer Support Team",
}


class ResponseGenerator:
    """
    Response generator for support tickets.

    This class provides methods to generate response drafts for support
    tickets using either AI-based generation or template-based fallback.

    Attributes:
        ai_service: Optional AIService instance for AI-based generation
        enable_ai: Whether AI-based generation is enabled
        templates: Dictionary of response templates by category
    """

    def __init__(
        self,
        ai_service: Optional[Any] = None,
        enable_ai: Optional[bool] = None,
    ):
        """
        Initialize the response generator.

        Args:
            ai_service: Optional AIService instance for AI-based generation
            enable_ai: Override for AI generation enable flag
        """
        self.ai_service = ai_service
        self.enable_ai = enable_ai if enable_ai is not None else settings.ENABLE_RESPONSE_GENERATION
        self.templates = RESPONSE_TEMPLATES.copy()

    async def generate(
        self,
        subject: str,
        body: str,
        category: str,
        severity: str,
        extracted_fields: Optional[List[ExtractedField]] = None,
        customer_name: Optional[str] = None,
        tone: str = "friendly",
        use_ai: Optional[bool] = None,
    ) -> ResponseDraft:
        """
        Generate a response draft for a support ticket.

        Attempts AI-based generation first if enabled, falls back to
        template-based generation if AI fails or is disabled.

        Args:
            subject: Ticket subject line
            body: Ticket body content
            category: Ticket category
            severity: Ticket severity level
            extracted_fields: List of extracted fields for personalization
            customer_name: Customer name for personalization
            tone: Desired response tone (formal, friendly, technical)
            use_ai: Override for whether to use AI generation

        Returns:
            ResponseDraft with generated response content
        """
        should_use_ai = use_ai if use_ai is not None else self.enable_ai
        extracted_dict = self._fields_to_dict(extracted_fields or [])

        # Try AI generation first
        if should_use_ai and self.ai_service:
            try:
                ai_result = await self._generate_with_ai(
                    subject=subject,
                    body=body,
                    category=category,
                    severity=severity,
                    extracted_fields=extracted_dict,
                    customer_name=customer_name,
                    tone=tone,
                )
                if ai_result:
                    return ai_result
            except Exception as e:
                logger.warning(f"AI response generation failed: {e}, falling back to template")

        # Fallback to template-based generation
        return self._generate_with_template(
            category=category,
            severity=severity,
            customer_name=customer_name,
            tone=tone,
        )

    async def _generate_with_ai(
        self,
        subject: str,
        body: str,
        category: str,
        severity: str,
        extracted_fields: Dict[str, Any],
        customer_name: Optional[str],
        tone: str,
    ) -> Optional[ResponseDraft]:
        """
        Generate response using AI service.

        Args:
            subject: Ticket subject line
            body: Ticket body content
            category: Ticket category
            severity: Ticket severity level
            extracted_fields: Dictionary of extracted fields
            customer_name: Customer name for personalization
            tone: Desired response tone

        Returns:
            ResponseDraft from AI generation, or None if failed
        """
        if not self.ai_service:
            return None

        try:
            result = await self.ai_service.generate_response(
                subject=subject,
                body=body,
                category=category,
                severity=severity,
                extracted_fields=extracted_fields,
                customer_name=customer_name,
                tone=tone,
            )

            # Build response from AI result
            return ResponseDraft(
                content=result.get("full_response", ""),
                tone=tone,
                template_used=None,
                suggested_actions=result.get("action_items", []),
                requires_escalation=result.get("requires_escalation", False),
                greeting=result.get("greeting"),
                acknowledgment=result.get("acknowledgment"),
                explanation=result.get("explanation"),
                action_items=result.get("action_items", []),
                timeline=result.get("timeline"),
                closing=result.get("closing"),
            )
        except Exception as e:
            logger.error(f"AI response generation error: {e}")
            raise

    def _generate_with_template(
        self,
        category: str,
        severity: str,
        customer_name: Optional[str],
        tone: str,
    ) -> ResponseDraft:
        """
        Generate response using templates.

        Args:
            category: Ticket category
            severity: Ticket severity level
            customer_name: Customer name for personalization
            tone: Desired response tone

        Returns:
            ResponseDraft from template
        """
        template = self.templates.get(category, self.templates["general"])
        response_time = RESPONSE_TIMES.get(severity, "24 hours")

        # Format customer name
        name_suffix = f" {customer_name}" if customer_name else ""
        signature = TEAM_SIGNATURES.get("general_support", "Customer Support Team")

        # Build response sections
        greeting = template["greeting"].format(customer_name=name_suffix)
        acknowledgment = template["acknowledgment"]
        explanation = template["explanation"]
        action_items = template["action_items"].copy()
        timeline = template["timeline"].format(response_time=response_time)
        closing = template["closing"].format(
            support_signature=signature,
            billing_signature=signature,
            engineering_signature=signature,
            product_signature=signature,
        )

        # Determine if escalation is needed based on severity
        requires_escalation = severity in ["critical", "high"]

        # Build full response content
        content = self._build_full_response(
            greeting=greeting,
            acknowledgment=acknowledgment,
            explanation=explanation,
            action_items=action_items,
            timeline=timeline,
            closing=closing,
            tone=tone,
        )

        return ResponseDraft(
            content=content,
            tone=tone,
            template_used=f"{category}_template",
            suggested_actions=action_items,
            requires_escalation=requires_escalation,
            greeting=greeting,
            acknowledgment=acknowledgment,
            explanation=explanation,
            action_items=action_items,
            timeline=timeline,
            closing=closing,
        )

    def _build_full_response(
        self,
        greeting: str,
        acknowledgment: str,
        explanation: str,
        action_items: List[str],
        timeline: str,
        closing: str,
        tone: str,
    ) -> str:
        """
        Build the full response content from sections.

        Args:
            greeting: Greeting section
            acknowledgment: Acknowledgment section
            explanation: Explanation section
            action_items: List of action items
            timeline: Timeline section
            closing: Closing section
            tone: Response tone

        Returns:
            Full formatted response string
        """
        sections = [greeting, "", acknowledgment, ""]

        if explanation:
            sections.append(explanation)
            sections.append("")

        if action_items:
            sections.append("Here are some steps you can take:")
            for i, item in enumerate(action_items, 1):
                sections.append(f"  {i}. {item}")
            sections.append("")

        sections.append(timeline)
        sections.append("")
        sections.append(closing)

        return "\n".join(sections)

    def _fields_to_dict(self, fields: List[ExtractedField]) -> Dict[str, Any]:
        """
        Convert extracted fields list to dictionary.

        Args:
            fields: List of extracted fields

        Returns:
            Dictionary mapping field names to values
        """
        result = {}
        for field in fields:
            # For duplicate field names, keep the highest confidence
            if field.name not in result:
                result[field.name] = field.value
        return result

    def add_custom_template(
        self,
        category: str,
        template: Dict[str, Any],
    ) -> None:
        """
        Add a custom template for a category.

        Args:
            category: Category name
            template: Template dictionary with required keys
        """
        self.templates[category] = template

    def get_template(self, category: str) -> Optional[Dict[str, Any]]:
        """
        Get the template for a category.

        Args:
            category: Category name

        Returns:
            Template dictionary or None if not found
        """
        return self.templates.get(category)


async def generate_response(
    subject: str,
    body: str,
    category: str,
    severity: str,
    extracted_fields: Optional[List[ExtractedField]] = None,
    customer_name: Optional[str] = None,
    tone: str = "friendly",
    ai_service: Optional[Any] = None,
    use_ai: bool = True,
) -> ResponseDraft:
    """
    Convenience function to generate a response.

    Args:
        subject: Ticket subject line
        body: Ticket body content
        category: Ticket category
        severity: Ticket severity level
        extracted_fields: List of extracted fields
        customer_name: Customer name for personalization
        tone: Desired response tone
        ai_service: Optional AIService instance
        use_ai: Whether to use AI generation

    Returns:
        ResponseDraft
    """
    generator = ResponseGenerator(ai_service=ai_service)
    return await generator.generate(
        subject=subject,
        body=body,
        category=category,
        severity=severity,
        extracted_fields=extracted_fields,
        customer_name=customer_name,
        tone=tone,
        use_ai=use_ai,
    )
