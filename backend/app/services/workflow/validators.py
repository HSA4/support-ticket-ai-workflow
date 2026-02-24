"""
Input validation for support ticket workflow.

This module provides validation utilities for incoming ticket data,
including sanitization for prompt injection prevention.
"""

import logging
import re
from typing import List, Optional, Tuple
from dataclasses import dataclass, field

from app.schemas.ticket import TicketInput

logger = logging.getLogger(__name__)

# Patterns that might indicate prompt injection attempts
PROMPT_INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?previous\s+instructions",
    r"ignore\s+(all\s+)?prior\s+instructions",
    r"disregard\s+(all\s+)?previous",
    r"you\s+are\s+now\s+a?",
    r"act\s+as\s+(if\s+)?you\s+are",
    r"pretend\s+(to\s+be|you\s+are)",
    r"your\s+new\s+role",
    r"override\s+(previous\s+)?(instructions|rules)",
    r"system\s*:\s*",
    r"<\|.*?\|>",  # Special tokens
    r"\[SYSTEM\]",
    r"\[INST\]",
]

# Maximum allowed text lengths
MAX_SUBJECT_LENGTH = 500
MAX_BODY_LENGTH = 50000


@dataclass
class ValidationResult:
    """
    Result of input validation.

    Attributes:
        is_valid: Whether the input is valid
        errors: List of validation errors
        warnings: List of validation warnings
        sanitized_subject: Sanitized subject text
        sanitized_body: Sanitized body text
    """

    is_valid: bool = True
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    sanitized_subject: Optional[str] = None
    sanitized_body: Optional[str] = None


class InputValidator:
    """
    Validator for support ticket input data.

    Provides methods for validating and sanitizing ticket input
    to prevent prompt injection and ensure data quality.
    """

    def __init__(
        self,
        max_subject_length: int = MAX_SUBJECT_LENGTH,
        max_body_length: int = MAX_BODY_LENGTH,
    ):
        """
        Initialize the input validator.

        Args:
            max_subject_length: Maximum allowed subject length
            max_body_length: Maximum allowed body length
        """
        self.max_subject_length = max_subject_length
        self.max_body_length = max_body_length
        self._injection_patterns = [
            re.compile(pattern, re.IGNORECASE) for pattern in PROMPT_INJECTION_PATTERNS
        ]

    def validate(self, ticket: TicketInput) -> ValidationResult:
        """
        Validate a ticket input.

        Args:
            ticket: Ticket input to validate

        Returns:
            ValidationResult with validation status and any errors/warnings
        """
        result = ValidationResult()

        # Validate subject
        if not ticket.subject or not ticket.subject.strip():
            result.is_valid = False
            result.errors.append("Subject cannot be empty")
        elif len(ticket.subject) > self.max_subject_length:
            result.is_valid = False
            result.errors.append(
                f"Subject exceeds maximum length of {self.max_subject_length}"
            )

        # Validate body
        if not ticket.body or not ticket.body.strip():
            result.is_valid = False
            result.errors.append("Body cannot be empty")
        elif len(ticket.body) > self.max_body_length:
            result.is_valid = False
            result.errors.append(
                f"Body exceeds maximum length of {self.max_body_length}"
            )

        # Check for prompt injection patterns
        injection_warnings = self._check_injection_patterns(
            ticket.subject, ticket.body
        )
        if injection_warnings:
            result.warnings.extend(injection_warnings)
            logger.warning(
                f"Potential prompt injection detected: {injection_warnings}"
            )

        # Sanitize input
        result.sanitized_subject = self._sanitize_text(ticket.subject)
        result.sanitized_body = self._sanitize_text(ticket.body)

        return result

    def _check_injection_patterns(
        self, subject: str, body: str
    ) -> List[str]:
        """
        Check for potential prompt injection patterns.

        Args:
            subject: Ticket subject
            body: Ticket body

        Returns:
            List of warning messages about detected patterns
        """
        warnings = []
        combined_text = f"{subject} {body}"

        for pattern in self._injection_patterns:
            if pattern.search(combined_text):
                warnings.append(f"Potential prompt injection pattern detected: {pattern.pattern}")

        return warnings

    def _sanitize_text(self, text: str) -> str:
        """
        Sanitize text to remove potential injection vectors.

        Args:
            text: Text to sanitize

        Returns:
            Sanitized text
        """
        if not text:
            return ""

        # Remove control characters except newlines and tabs
        sanitized = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]", "", text)

        # Normalize whitespace
        sanitized = re.sub(r"\s+", " ", sanitized).strip()

        return sanitized

    def validate_and_sanitize(
        self, ticket: TicketInput
    ) -> Tuple[bool, Optional[TicketInput], List[str]]:
        """
        Validate and return a sanitized ticket.

        Args:
            ticket: Ticket input to validate

        Returns:
            Tuple of (is_valid, sanitized_ticket_or_none, error_messages)
        """
        result = self.validate(ticket)

        if not result.is_valid:
            return False, None, result.errors

        sanitized_ticket = TicketInput(
            subject=result.sanitized_subject or ticket.subject,
            body=result.sanitized_body or ticket.body,
            customer_id=ticket.customer_id,
            customer_email=ticket.customer_email,
            metadata=ticket.metadata,
        )

        return True, sanitized_ticket, result.warnings


def validate_ticket(ticket: TicketInput) -> ValidationResult:
    """
    Convenience function to validate a ticket.

    Args:
        ticket: Ticket input to validate

    Returns:
        ValidationResult
    """
    validator = InputValidator()
    return validator.validate(ticket)
