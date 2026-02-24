"""
Field extraction module for the support ticket workflow.

This module provides extraction functionality for support tickets,
including regex-based patterns for structured data and AI-assisted
extraction for context-dependent fields.
"""

import logging
import re
from typing import Any, Dict, List, Optional, Tuple

from app.core.config import settings
from app.schemas import ExtractedField, ExtractionResult

logger = logging.getLogger(__name__)

# Regex patterns for field extraction
EXTRACTION_PATTERNS = {
    # Order IDs: ORD-XXXXX, #XXXXX, ORDER-XXXXX
    "order_id": [
        r"\b(?:ORD|ORDER)[-]?(\d{5,10})\b",
        r"#(\d{5,10})\b",
        r"\b(?:order|invoice|transaction)\s*(?:id|number|#)?\s*[:\s]?\s*([A-Z0-9]{5,15})\b",
    ],
    # Email addresses (RFC 5322 simplified)
    "account_email": [
        r"\b([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})\b",
    ],
    # Phone numbers (various formats)
    "phone_number": [
        r"\b(?:\+?1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})\b",  # US format
        r"\b\+?(\d{1,3})[-.\s]?(\d{2,4})[-.\s]?(\d{3,4})[-.\s]?(\d{3,4})\b",  # International
        r"\b(?:tel|phone|cell|mobile)[:\s]*([+\d][\d\s\-\(\)]{7,20})\b",  # With label
    ],
    # Error codes: ERR-XXXX, 0xXXXX, Error XXXX
    "error_code": [
        r"\b(?:ERR|ERROR)[-]?(\d{3,6})\b",
        r"\b0x([0-9A-Fa-f]{4,8})\b",
        r"\b(?:error|exception|fault)[:\s]*([A-Z0-9]{3,10})\b",
        r"\b([A-Z]{2,4}[-_]?\d{3,6})\b",  # Generic error code pattern
    ],
    # Product names (common patterns)
    "product_name": [
        r"\b(?:product|item|service)[:\s]*([A-Za-z0-9\s\-]{3,50})\b",
        r"\b(?:using|with|on)\s+(?:the\s+)?([A-Z][A-Za-z0-9\s]{2,30})\b",
    ],
    # URLs
    "url": [
        r"\b(https?://[^\s<>\{\}\|\\\^~\[\]]+)\b",
    ],
    # Account/User IDs
    "account_id": [
        r"\b(?:account|user|customer)\s*(?:id|number)?[:\s]*([A-Z0-9]{4,20})\b",
        r"\b(?:ACC|USR|CUST)[-]?(\d{4,15})\b",
    ],
    # Dates
    "date": [
        r"\b(\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4})\b",
        r"\b(\d{4}[/\-]\d{1,2}[/\-]\d{1,2})\b",
        r"\b((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{4})\b",
    ],
    # Currency/Amounts
    "amount": [
        r"\b\$([\d,]+\.?\d*)\b",
        r"\b([\d,]+\.?\d*)\s*(?:USD|EUR|GBP)\b",
        r"\b(?:amount|total|price|cost)[:\s]*\$?([\d,]+\.?\d*)\b",
    ],
}

# Priority/urgency keywords
PRIORITY_KEYWORDS = [
    "urgent", "asap", "immediately", "critical", "emergency",
    "important", "priority", "quickly", "soon", "now",
    "as soon as possible", "right away", "help me",
]

# Required fields per category
CATEGORY_REQUIRED_FIELDS = {
    "technical": ["error_code"],
    "billing": ["order_id", "amount"],
    "account": ["account_email"],
    "bug_report": ["error_code"],
    "feature_request": [],
    "general": [],
}

# Field validation patterns
VALIDATION_PATTERNS = {
    "account_email": r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
    "order_id": r"^[A-Z0-9\-#]{5,20}$",
    "phone_number": r"^[\d\s\-\+\(\)]{7,20}$",
    "error_code": r"^[A-Z0-9\-_]{3,15}$",
}


class FieldExtractor:
    """
    Field extractor for support tickets.

    This class provides methods to extract structured fields from
    unstructured ticket text using regex patterns and optional
    AI-assisted extraction for context-dependent fields.

    Attributes:
        ai_service: Optional AIService instance for AI-assisted extraction
        patterns: Dictionary of regex patterns for field extraction
        enable_ai: Whether AI-assisted extraction is enabled
        confidence_threshold: Minimum confidence threshold for AI results
    """

    def __init__(
        self,
        ai_service: Optional[Any] = None,
        enable_ai: Optional[bool] = None,
        confidence_threshold: Optional[float] = None,
    ):
        """
        Initialize the field extractor.

        Args:
            ai_service: Optional AIService instance for AI-assisted extraction
            enable_ai: Override for AI extraction enable flag
            confidence_threshold: Override for confidence threshold
        """
        self.ai_service = ai_service
        self.enable_ai = enable_ai if enable_ai is not None else settings.ENABLE_AI_EXTRACTION
        self.confidence_threshold = confidence_threshold or settings.AI_CONFIDENCE_THRESHOLD
        self.patterns = EXTRACTION_PATTERNS.copy()

    async def extract(
        self,
        subject: str,
        body: str,
        category: Optional[str] = None,
        use_ai: Optional[bool] = None,
    ) -> ExtractionResult:
        """
        Extract fields from a support ticket.

        Attempts regex-based extraction first, then optionally enhances
        with AI-assisted extraction for context-dependent fields.

        Args:
            subject: Ticket subject line
            body: Ticket body content
            category: Ticket category for context-aware extraction
            use_ai: Override for whether to use AI extraction

        Returns:
            ExtractionResult with extracted fields and validation info
        """
        combined_text = f"{subject}\n{body}"
        should_use_ai = use_ai if use_ai is not None else self.enable_ai

        # Start with regex-based extraction
        fields = self._extract_with_regex(combined_text)

        # Extract priority keywords
        priority_keywords = self._extract_priority_keywords(combined_text)
        if priority_keywords:
            fields.append(
                ExtractedField(
                    name="priority_keywords",
                    value=priority_keywords,
                    confidence=0.9,
                    source_span=", ".join(priority_keywords),
                )
            )

        # Optionally enhance with AI extraction
        if should_use_ai and self.ai_service:
            try:
                ai_fields = await self._extract_with_ai(subject, body, category)
                fields = self._merge_fields(fields, ai_fields)
            except Exception as e:
                logger.warning(f"AI extraction failed: {e}, using regex-only results")

        # Validate fields and find missing required fields
        validation_errors = self._validate_fields(fields)
        missing_required = self._find_missing_required(fields, category)

        return ExtractionResult(
            fields=fields,
            missing_required=missing_required,
            validation_errors=validation_errors,
        )

    def _extract_with_regex(self, text: str) -> List[ExtractedField]:
        """
        Extract fields using regex patterns.

        Args:
            text: Text to extract fields from

        Returns:
            List of ExtractedField objects
        """
        fields = []
        found_values: Dict[str, set] = {}  # Track found values to avoid duplicates

        for field_name, patterns in self.patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE)
                for match in matches:
                    # Get the full match or first group
                    if match.groups():
                        value = match.group(1) if len(match.groups()) == 1 else "".join(match.groups())
                    else:
                        value = match.group(0)

                    value = value.strip()

                    # Skip empty or very short values
                    if not value or len(value) < 2:
                        continue

                    # Normalize value
                    value = self._normalize_value(field_name, value)

                    # Skip duplicates
                    if field_name in found_values and value in found_values[field_name]:
                        continue

                    if field_name not in found_values:
                        found_values[field_name] = set()
                    found_values[field_name].add(value)

                    # Calculate confidence based on pattern specificity
                    confidence = self._calculate_regex_confidence(field_name, value)

                    fields.append(
                        ExtractedField(
                            name=field_name,
                            value=value,
                            confidence=confidence,
                            source_span=match.group(0),
                        )
                    )

        return fields

    def _normalize_value(self, field_name: str, value: str) -> str:
        """
        Normalize extracted value based on field type.

        Args:
            field_name: Name of the field
            value: Raw extracted value

        Returns:
            Normalized value string
        """
        if field_name == "account_email":
            return value.lower().strip()
        elif field_name == "phone_number":
            # Keep only digits and common separators
            return re.sub(r"[^\d\+\-\(\)\s]", "", value)
        elif field_name == "order_id":
            return value.upper().strip()
        elif field_name == "error_code":
            return value.upper().strip()
        elif field_name == "amount":
            # Remove commas and normalize
            return value.replace(",", "").strip()
        else:
            return value.strip()

    def _calculate_regex_confidence(self, field_name: str, value: str) -> float:
        """
        Calculate confidence score for regex-extracted value.

        Args:
            field_name: Name of the field
            value: Extracted value

        Returns:
            Confidence score between 0.0 and 1.0
        """
        base_confidence = 0.7

        # Boost confidence for fields with validation patterns
        if field_name in VALIDATION_PATTERNS:
            if re.match(VALIDATION_PATTERNS[field_name], value, re.IGNORECASE):
                base_confidence += 0.15

        # Boost confidence for typical lengths
        if field_name == "account_email" and "@" in value and "." in value.split("@")[-1]:
            base_confidence += 0.1
        elif field_name == "order_id" and 5 <= len(value) <= 20:
            base_confidence += 0.1
        elif field_name == "phone_number" and 7 <= len(re.sub(r"\D", "", value)) <= 15:
            base_confidence += 0.1

        return min(0.95, base_confidence)

    def _extract_priority_keywords(self, text: str) -> List[str]:
        """
        Extract priority/urgency keywords from text.

        Args:
            text: Text to search for priority keywords

        Returns:
            List of found priority keywords
        """
        found = []
        text_lower = text.lower()

        for keyword in PRIORITY_KEYWORDS:
            if keyword.lower() in text_lower:
                found.append(keyword)

        return found

    async def _extract_with_ai(
        self,
        subject: str,
        body: str,
        category: Optional[str],
    ) -> List[ExtractedField]:
        """
        Extract fields using AI service.

        Args:
            subject: Ticket subject line
            body: Ticket body content
            category: Ticket category for context

        Returns:
            List of ExtractedField objects from AI extraction

        Raises:
            Exception: If AI service call fails
        """
        if not self.ai_service:
            raise ValueError("AI service not available")

        result = await self.ai_service.extract_fields(subject, body, category or "general")
        return result.fields

    def _merge_fields(
        self,
        regex_fields: List[ExtractedField],
        ai_fields: List[ExtractedField],
    ) -> List[ExtractedField]:
        """
        Merge regex and AI-extracted fields, preferring higher confidence.

        Args:
            regex_fields: Fields extracted via regex
            ai_fields: Fields extracted via AI

        Returns:
            Merged list of ExtractedField objects
        """
        merged: Dict[str, ExtractedField] = {}

        # Add regex fields first
        for field in regex_fields:
            merged[field.name] = field

        # Merge AI fields, preferring higher confidence
        for ai_field in ai_fields:
            if ai_field.name in merged:
                existing = merged[ai_field.name]
                # Keep the one with higher confidence
                if ai_field.confidence > existing.confidence:
                    merged[ai_field.name] = ai_field
            else:
                merged[ai_field.name] = ai_field

        return list(merged.values())

    def _validate_fields(self, fields: List[ExtractedField]) -> List[str]:
        """
        Validate extracted fields against patterns.

        Args:
            fields: List of extracted fields

        Returns:
            List of validation error messages
        """
        errors = []

        for field in fields:
            if field.name in VALIDATION_PATTERNS:
                pattern = VALIDATION_PATTERNS[field.name]
                if not re.match(pattern, str(field.value), re.IGNORECASE):
                    errors.append(
                        f"Field '{field.name}' with value '{field.value}' "
                        f"does not match expected format"
                    )

        return errors

    def _find_missing_required(
        self,
        fields: List[ExtractedField],
        category: Optional[str],
    ) -> List[str]:
        """
        Find required fields that are missing based on category.

        Args:
            fields: List of extracted fields
            category: Ticket category

        Returns:
            List of missing required field names
        """
        if not category or category not in CATEGORY_REQUIRED_FIELDS:
            return []

        required = CATEGORY_REQUIRED_FIELDS[category]
        found_fields = {field.name for field in fields}

        return [field for field in required if field not in found_fields]

    def get_fields_by_name(
        self,
        fields: List[ExtractedField],
        name: str,
    ) -> List[ExtractedField]:
        """
        Get all fields with a specific name.

        Args:
            fields: List of extracted fields
            name: Field name to filter by

        Returns:
            List of matching ExtractedField objects
        """
        return [f for f in fields if f.name == name]

    def get_highest_confidence_field(
        self,
        fields: List[ExtractedField],
        name: str,
    ) -> Optional[ExtractedField]:
        """
        Get the field with highest confidence for a given name.

        Args:
            fields: List of extracted fields
            name: Field name to find

        Returns:
            ExtractedField with highest confidence, or None if not found
        """
        matching = self.get_fields_by_name(fields, name)
        if not matching:
            return None
        return max(matching, key=lambda f: f.confidence)

    def get_fields_as_dict(
        self,
        fields: List[ExtractedField],
        include_confidence: bool = False,
    ) -> Dict[str, Any]:
        """
        Convert fields list to dictionary format.

        Args:
            fields: List of extracted fields
            include_confidence: Whether to include confidence scores

        Returns:
            Dictionary mapping field names to values (or value/confidence dicts)
        """
        result = {}
        for field in fields:
            if include_confidence:
                result[field.name] = {
                    "value": field.value,
                    "confidence": field.confidence,
                    "source_span": field.source_span,
                }
            else:
                result[field.name] = field.value
        return result

    def add_custom_pattern(self, field_name: str, pattern: str) -> None:
        """
        Add a custom regex pattern for a field.

        Args:
            field_name: Name of the field to extract
            pattern: Regex pattern to use for extraction
        """
        if field_name not in self.patterns:
            self.patterns[field_name] = []
        self.patterns[field_name].append(pattern)

    def get_extraction_patterns(self) -> Dict[str, List[str]]:
        """
        Get the current extraction patterns.

        Returns:
            Dictionary of field names to pattern lists
        """
        return {name: [str(p) for p in patterns] for name, patterns in self.patterns.items()}
