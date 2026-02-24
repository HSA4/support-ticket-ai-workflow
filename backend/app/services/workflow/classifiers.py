"""
Ticket classification module for the support ticket workflow.

This module provides classification functionality for support tickets,
including LLM-based classification via AIService and fallback rule-based
classification using keyword matching from configuration.
"""

import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml

from app.core.config import settings
from app.schemas import ClassificationResult

logger = logging.getLogger(__name__)

# Path to categories configuration file
CATEGORIES_CONFIG_PATH = Path(__file__).parent.parent.parent.parent / "config" / "categories.yaml"
SEVERITIES_CONFIG_PATH = Path(__file__).parent.parent.parent.parent / "config" / "severities.yaml"

# Default category keywords for fallback classification
CATEGORY_KEYWORDS: Dict[str, List[str]] = {
    "technical": ["error", "bug", "crash", "not working", "failed", "broken", "issue", "problem"],
    "billing": ["charge", "refund", "invoice", "payment", "subscription", "overcharged", "bill", "cost"],
    "account": ["login", "password", "account", "access", "locked", "credentials", "sign in", "signin", "signup"],
    "feature_request": ["wish", "request", "feature", "enhancement", "suggest", "idea", "would like", "need"],
    "bug_report": ["bug", "defect", "broken", "incorrect", "unexpected", "wrong", "does not work"],
    "general": ["question", "help", "how to", "information", "inquiry", "wondering"],
}

# Severity indicators for fallback classification
SEVERITY_INDICATORS: Dict[str, List[str]] = {
    "critical": ["urgent", "asap", "critical", "down", "emergency", "production", "immediately", "serious"],
    "high": ["important", "serious", "affecting", "quickly", "soon", "priority"],
    "medium": ["issue", "problem", "help", "when possible"],
    "low": ["minor", "small", "suggestion", "curious", "wondering", "sometime"],
}

# Valid categories and severities
VALID_CATEGORIES = ["technical", "billing", "account", "feature_request", "bug_report", "general"]
VALID_SEVERITIES = ["critical", "high", "medium", "low"]


def _load_yaml_config(file_path: Path) -> Optional[Dict[str, Any]]:
    """Load configuration from YAML file."""
    try:
        if file_path.exists():
            with open(file_path, "r") as f:
                return yaml.safe_load(f)
    except Exception as e:
        logger.warning(f"Failed to load config from {file_path}: {e}")
    return None


def _extract_keywords_from_config(config: Optional[Dict[str, Any]]) -> Dict[str, List[str]]:
    """Extract keywords from loaded configuration."""
    keywords = {}
    if config and "categories" in config:
        for category in config["categories"]:
            cat_id = category.get("id", "")
            cat_keywords = category.get("keywords", [])
            if cat_id and cat_keywords:
                keywords[cat_id] = cat_keywords
    return keywords


def _extract_severity_indicators_from_config(config: Optional[Dict[str, Any]]) -> Dict[str, List[str]]:
    """Extract severity indicators from loaded configuration."""
    indicators = {}
    if config and "severities" in config:
        for severity in config["severities"]:
            sev_id = severity.get("id", "")
            sev_indicators = severity.get("indicators", [])
            if sev_id:
                indicators[sev_id] = sev_indicators
    return indicators


class TicketClassifier:
    """
    Ticket classifier supporting both AI-based and rule-based classification.

    This class provides methods to classify support tickets into categories
    and severity levels using either LLM-based classification via AIService
    or fallback rule-based classification using keyword matching.

    Attributes:
        ai_service: Optional AIService instance for LLM-based classification
        category_keywords: Dictionary mapping categories to their keywords
        severity_indicators: Dictionary mapping severities to their indicators
        enable_ai: Whether AI-based classification is enabled
        confidence_threshold: Minimum confidence threshold for AI results
    """

    def __init__(
        self,
        ai_service: Optional[Any] = None,
        enable_ai: Optional[bool] = None,
        confidence_threshold: Optional[float] = None,
    ):
        """
        Initialize the ticket classifier.

        Args:
            ai_service: Optional AIService instance for LLM-based classification
            enable_ai: Override for AI classification enable flag
            confidence_threshold: Override for confidence threshold
        """
        self.ai_service = ai_service
        self.enable_ai = enable_ai if enable_ai is not None else settings.ENABLE_AI_CLASSIFICATION
        self.confidence_threshold = confidence_threshold or settings.AI_CONFIDENCE_THRESHOLD

        # Load keywords from config files, fallback to defaults
        self._load_keywords()

    def _load_keywords(self) -> None:
        """Load category keywords and severity indicators from config files."""
        global CATEGORY_KEYWORDS, SEVERITY_INDICATORS

        # Load categories config
        categories_config = _load_yaml_config(CATEGORIES_CONFIG_PATH)
        config_keywords = _extract_keywords_from_config(categories_config)
        if config_keywords:
            # Merge with defaults, config takes precedence
            self.category_keywords = {**CATEGORY_KEYWORDS, **config_keywords}
        else:
            self.category_keywords = CATEGORY_KEYWORDS.copy()

        # Load severities config
        severities_config = _load_yaml_config(SEVERITIES_CONFIG_PATH)
        config_indicators = _extract_severity_indicators_from_config(severities_config)
        if config_indicators:
            self.severity_indicators = {**SEVERITY_INDICATORS, **config_indicators}
        else:
            self.severity_indicators = SEVERITY_INDICATORS.copy()

        logger.debug(
            f"Loaded {len(self.category_keywords)} category keyword sets "
            f"and {len(self.severity_indicators)} severity indicator sets"
        )

    async def classify(
        self,
        subject: str,
        body: str,
        use_ai: Optional[bool] = None,
    ) -> ClassificationResult:
        """
        Classify a support ticket.

        Attempts AI-based classification first if enabled, falls back to
        rule-based classification if AI fails or is disabled.

        Args:
            subject: Ticket subject line
            body: Ticket body content
            use_ai: Override for whether to use AI classification

        Returns:
            ClassificationResult with category, severity, and confidence scores
        """
        should_use_ai = use_ai if use_ai is not None else self.enable_ai

        if should_use_ai and self.ai_service:
            try:
                result = await self._classify_with_ai(subject, body)
                if result.category_confidence >= self.confidence_threshold:
                    return result
                logger.info(
                    f"AI classification confidence {result.category_confidence} "
                    f"below threshold {self.confidence_threshold}, using fallback"
                )
            except Exception as e:
                logger.warning(f"AI classification failed: {e}, falling back to rule-based")

        # Fallback to rule-based classification
        return self._classify_with_rules(subject, body)

    async def _classify_with_ai(self, subject: str, body: str) -> ClassificationResult:
        """
        Classify ticket using AI service.

        Args:
            subject: Ticket subject line
            body: Ticket body content

        Returns:
            ClassificationResult from AI classification

        Raises:
            Exception: If AI service call fails
        """
        if not self.ai_service:
            raise ValueError("AI service not available")

        return await self.ai_service.classify_ticket(subject, body)

    def _classify_with_rules(self, subject: str, body: str) -> ClassificationResult:
        """
        Classify ticket using rule-based keyword matching.

        Args:
            subject: Ticket subject line
            body: Ticket body content

        Returns:
            ClassificationResult from rule-based classification
        """
        combined_text = f"{subject} {body}".lower()

        # Classify category
        category, category_confidence, keywords_matched = self._match_category(combined_text)

        # Classify severity
        severity, severity_confidence, urgency_indicators = self._match_severity(combined_text)

        # Find secondary categories
        secondary_categories = self._find_secondary_categories(combined_text, category)

        # Generate reasoning
        reasoning = self._generate_reasoning(category, severity, keywords_matched, urgency_indicators)

        return ClassificationResult(
            category=category,
            category_confidence=category_confidence,
            severity=severity,
            severity_confidence=severity_confidence,
            secondary_categories=secondary_categories,
            reasoning=reasoning,
            keywords_matched=keywords_matched,
            urgency_indicators=urgency_indicators,
        )

    def _match_category(self, text: str) -> Tuple[str, float, List[str]]:
        """
        Match text against category keywords.

        Args:
            text: Combined subject and body text (lowercase)

        Returns:
            Tuple of (category, confidence, matched_keywords)
        """
        scores: Dict[str, Tuple[float, List[str]]] = {}

        for category, keywords in self.category_keywords.items():
            matches = []
            for keyword in keywords:
                # Use word boundary matching for more accuracy
                pattern = r"\b" + re.escape(keyword.lower()) + r"\b"
                if re.search(pattern, text):
                    matches.append(keyword)

            if matches:
                # Calculate confidence based on match ratio
                match_ratio = len(matches) / len(keywords)
                # Boost confidence for multiple matches
                confidence = min(0.95, 0.5 + (match_ratio * 0.45) + (len(matches) * 0.05))
                scores[category] = (confidence, matches)

        if scores:
            # Return category with highest confidence
            best_category = max(scores.keys(), key=lambda k: scores[k][0])
            confidence, keywords = scores[best_category]
            return best_category, confidence, keywords

        # Default to general if no matches
        return "general", 0.3, []

    def _match_severity(self, text: str) -> Tuple[str, float, List[str]]:
        """
        Match text against severity indicators.

        Args:
            text: Combined subject and body text (lowercase)

        Returns:
            Tuple of (severity, confidence, matched_indicators)
        """
        scores: Dict[str, Tuple[float, List[str]]] = {}

        for severity, indicators in self.severity_indicators.items():
            matches = []
            for indicator in indicators:
                pattern = r"\b" + re.escape(indicator.lower()) + r"\b"
                if re.search(pattern, text):
                    matches.append(indicator)

            if matches:
                match_ratio = len(matches) / len(indicators) if indicators else 0
                confidence = min(0.9, 0.4 + (match_ratio * 0.5))
                scores[severity] = (confidence, matches)

        if scores:
            # Return severity with highest confidence, preferring higher severity
            sorted_severities = sorted(
                scores.keys(),
                key=lambda k: (scores[k][0], VALID_SEVERITIES.index(k) if k in VALID_SEVERITIES else 99),
                reverse=True,
            )
            best_severity = sorted_severities[0]
            confidence, indicators = scores[best_severity]
            return best_severity, confidence, indicators

        # Default to medium severity
        return "medium", 0.5, []

    def _find_secondary_categories(self, text: str, primary_category: str) -> List[str]:
        """
        Find secondary categories that also match the text.

        Args:
            text: Combined subject and body text (lowercase)
            primary_category: The primary matched category

        Returns:
            List of secondary category names
        """
        secondary = []

        for category, keywords in self.category_keywords.items():
            if category == primary_category:
                continue

            match_count = sum(1 for kw in keywords if re.search(r"\b" + re.escape(kw.lower()) + r"\b", text))
            if match_count >= 2:  # Require at least 2 keyword matches for secondary
                secondary.append(category)

        return secondary[:2]  # Limit to 2 secondary categories

    def _generate_reasoning(
        self,
        category: str,
        severity: str,
        keywords_matched: List[str],
        urgency_indicators: List[str],
    ) -> str:
        """
        Generate human-readable reasoning for the classification.

        Args:
            category: Classified category
            severity: Classified severity
            keywords_matched: List of matched keywords
            urgency_indicators: List of matched urgency indicators

        Returns:
            Reasoning string
        """
        parts = []

        if keywords_matched:
            keyword_str = ", ".join(keywords_matched[:3])
            parts.append(f"Matched keywords: {keyword_str}")

        if urgency_indicators:
            urgency_str = ", ".join(urgency_indicators[:2])
            parts.append(f"Urgency indicators: {urgency_str}")

        parts.append(f"Classified as {category} with {severity} severity")

        return ". ".join(parts) + "."

    def get_category_keywords(self) -> Dict[str, List[str]]:
        """
        Get the current category keywords dictionary.

        Returns:
            Dictionary mapping category names to keyword lists
        """
        return self.category_keywords.copy()

    def get_severity_indicators(self) -> Dict[str, List[str]]:
        """
        Get the current severity indicators dictionary.

        Returns:
            Dictionary mapping severity levels to indicator lists
        """
        return self.severity_indicators.copy()

    def validate_category(self, category: str) -> bool:
        """
        Validate that a category is valid.

        Args:
            category: Category to validate

        Returns:
            True if category is valid, False otherwise
        """
        return category in VALID_CATEGORIES

    def validate_severity(self, severity: str) -> bool:
        """
        Validate that a severity is valid.

        Args:
            severity: Severity to validate

        Returns:
            True if severity is valid, False otherwise
        """
        return severity in VALID_SEVERITIES
