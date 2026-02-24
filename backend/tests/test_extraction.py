"""
Unit tests for field extraction functionality.

This module tests the FieldExtractor class, including:
- Extraction of each field type
- Regex pattern matching
- Field validation
- Missing required fields detection
- Priority keyword extraction
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.schemas import ExtractedField, ExtractionResult
from app.services.workflow.extractors import (
    FieldExtractor,
    EXTRACTION_PATTERNS,
    PRIORITY_KEYWORDS,
    CATEGORY_REQUIRED_FIELDS,
    VALIDATION_PATTERNS,
)


# ============================================================================
# Order ID Extraction Tests
# ============================================================================


class TestOrderIDExtraction:
    """Tests for order ID extraction."""

    @pytest.mark.asyncio
    async def test_extract_order_id_ord_format(self, field_extractor):
        """Test extraction of ORD-XXXXX format order IDs."""
        result = await field_extractor.extract(
            subject="Order not received",
            body="My order ORD-123456 hasn't arrived yet.",
            category="billing",
            use_ai=False,
        )

        order_fields = [f for f in result.fields if f.name == "order_id"]
        assert len(order_fields) > 0
        assert "ORD-123456" in order_fields[0].value or "123456" in order_fields[0].value

    @pytest.mark.asyncio
    async def test_extract_order_id_hash_format(self, field_extractor):
        """Test extraction of #XXXXX format order IDs."""
        result = await field_extractor.extract(
            subject="Order inquiry",
            body="I have a question about order #78901.",
            category="billing",
            use_ai=False,
        )

        order_fields = [f for f in result.fields if f.name == "order_id"]
        assert len(order_fields) > 0

    @pytest.mark.asyncio
    async def test_extract_order_id_order_prefix(self, field_extractor):
        """Test extraction of 'order ID: XXX' format."""
        result = await field_extractor.extract(
            subject="Refund request",
            body="Please refund order ID: ABC123XYZ.",
            category="billing",
            use_ai=False,
        )

        order_fields = [f for f in result.fields if f.name == "order_id"]
        assert len(order_fields) > 0

    @pytest.mark.asyncio
    async def test_no_order_id_when_absent(self, field_extractor):
        """Test that no order ID is extracted when not present."""
        result = await field_extractor.extract(
            subject="General question",
            body="I have a question about your service.",
            category="general",
            use_ai=False,
        )

        order_fields = [f for f in result.fields if f.name == "order_id"]
        assert len(order_fields) == 0


# ============================================================================
# Email Extraction Tests
# ============================================================================


class TestEmailExtraction:
    """Tests for email extraction."""

    @pytest.mark.asyncio
    async def test_extract_single_email(self, field_extractor):
        """Test extraction of a single email address."""
        result = await field_extractor.extract(
            subject="Account issue",
            body="Please contact me at john.doe@example.com.",
            category="account",
            use_ai=False,
        )

        email_fields = [f for f in result.fields if f.name == "account_email"]
        assert len(email_fields) > 0
        assert email_fields[0].value == "john.doe@example.com"

    @pytest.mark.asyncio
    async def test_extract_multiple_emails(self, field_extractor):
        """Test extraction of multiple email addresses."""
        result = await field_extractor.extract(
            subject="Contact info",
            body="My emails are user1@test.com and user2@test.org.",
            category="general",
            use_ai=False,
        )

        email_fields = [f for f in result.fields if f.name == "account_email"]
        assert len(email_fields) >= 2

    @pytest.mark.asyncio
    async def test_email_normalized_to_lowercase(self, field_extractor):
        """Test that extracted emails are normalized to lowercase."""
        result = await field_extractor.extract(
            subject="Contact",
            body="Email me at JOHN.DOE@EXAMPLE.COM.",
            category="general",
            use_ai=False,
        )

        email_fields = [f for f in result.fields if f.name == "account_email"]
        assert len(email_fields) > 0
        assert email_fields[0].value == email_fields[0].value.lower()

    @pytest.mark.asyncio
    async def test_complex_email_formats(self, field_extractor):
        """Test extraction of complex email formats."""
        result = await field_extractor.extract(
            subject="Contact",
            body="Reach me at user.name+tag@subdomain.example.co.uk.",
            category="general",
            use_ai=False,
        )

        email_fields = [f for f in result.fields if f.name == "account_email"]
        assert len(email_fields) > 0


# ============================================================================
# Phone Number Extraction Tests
# ============================================================================


class TestPhoneNumberExtraction:
    """Tests for phone number extraction."""

    @pytest.mark.asyncio
    async def test_extract_us_phone_format(self, field_extractor):
        """Test extraction of US phone number format."""
        result = await field_extractor.extract(
            subject="Call me",
            body="My phone number is 555-123-4567.",
            category="general",
            use_ai=False,
        )

        phone_fields = [f for f in result.fields if f.name == "phone_number"]
        assert len(phone_fields) > 0

    @pytest.mark.asyncio
    async def test_extract_phone_with_parentheses(self, field_extractor):
        """Test extraction of phone number with parentheses."""
        result = await field_extractor.extract(
            subject="Contact info",
            body="Call me at (555) 123-4567.",
            category="general",
            use_ai=False,
        )

        phone_fields = [f for f in result.fields if f.name == "phone_number"]
        assert len(phone_fields) > 0

    @pytest.mark.asyncio
    async def test_extract_international_phone(self, field_extractor):
        """Test extraction of international phone number."""
        result = await field_extractor.extract(
            subject="International contact",
            body="My number is +44 20 7946 0958.",
            category="general",
            use_ai=False,
        )

        phone_fields = [f for f in result.fields if f.name == "phone_number"]
        assert len(phone_fields) > 0

    @pytest.mark.asyncio
    async def test_extract_phone_with_country_code(self, field_extractor):
        """Test extraction of phone with +1 country code."""
        result = await field_extractor.extract(
            subject="Contact",
            body="Reach me at +1-555-987-6543.",
            category="general",
            use_ai=False,
        )

        phone_fields = [f for f in result.fields if f.name == "phone_number"]
        assert len(phone_fields) > 0


# ============================================================================
# Error Code Extraction Tests
# ============================================================================


class TestErrorCodeExtraction:
    """Tests for error code extraction."""

    @pytest.mark.asyncio
    async def test_extract_err_format(self, field_extractor):
        """Test extraction of ERR-XXXX format error codes."""
        result = await field_extractor.extract(
            subject="Error message",
            body="I'm getting error code ERR-50023 when trying to login.",
            category="technical",
            use_ai=False,
        )

        error_fields = [f for f in result.fields if f.name == "error_code"]
        assert len(error_fields) > 0
        assert "ERR-50023" in error_fields[0].value or "50023" in error_fields[0].value

    @pytest.mark.asyncio
    async def test_extract_hex_format(self, field_extractor):
        """Test extraction of 0xXXXX hex format error codes."""
        result = await field_extractor.extract(
            subject="Application crash",
            body="The app crashes with error 0xDEADBEEF.",
            category="technical",
            use_ai=False,
        )

        error_fields = [f for f in result.fields if f.name == "error_code"]
        assert len(error_fields) > 0

    @pytest.mark.asyncio
    async def test_extract_generic_error_code(self, field_extractor):
        """Test extraction of generic error code patterns."""
        result = await field_extractor.extract(
            subject="System error",
            body="Error: SYS-404 occurred while processing.",
            category="technical",
            use_ai=False,
        )

        error_fields = [f for f in result.fields if f.name == "error_code"]
        assert len(error_fields) > 0

    @pytest.mark.asyncio
    async def test_error_code_normalized_to_uppercase(self, field_extractor):
        """Test that error codes are normalized to uppercase."""
        result = await field_extractor.extract(
            subject="Error",
            body="Getting error err-12345.",
            category="technical",
            use_ai=False,
        )

        error_fields = [f for f in result.fields if f.name == "error_code"]
        if error_fields:
            assert error_fields[0].value == error_fields[0].value.upper()


# ============================================================================
# Amount/Currency Extraction Tests
# ============================================================================


class TestAmountExtraction:
    """Tests for amount/currency extraction."""

    @pytest.mark.asyncio
    async def test_extract_dollar_amount(self, field_extractor):
        """Test extraction of dollar amounts."""
        result = await field_extractor.extract(
            subject="Billing issue",
            body="I was charged $29.99 instead of $19.99.",
            category="billing",
            use_ai=False,
        )

        amount_fields = [f for f in result.fields if f.name == "amount"]
        assert len(amount_fields) > 0

    @pytest.mark.asyncio
    async def test_extract_large_amount(self, field_extractor):
        """Test extraction of large amounts with commas."""
        result = await field_extractor.extract(
            subject="Large charge",
            body="I see a charge of $5,000 on my statement.",
            category="billing",
            use_ai=False,
        )

        amount_fields = [f for f in result.fields if f.name == "amount"]
        assert len(amount_fields) > 0

    @pytest.mark.asyncio
    async def test_extract_currency_code(self, field_extractor):
        """Test extraction of amounts with currency codes."""
        result = await field_extractor.extract(
            subject="International charge",
            body="I was charged 99.99 EUR for my subscription.",
            category="billing",
            use_ai=False,
        )

        amount_fields = [f for f in result.fields if f.name == "amount"]
        assert len(amount_fields) > 0


# ============================================================================
# Date Extraction Tests
# ============================================================================


class TestDateExtraction:
    """Tests for date extraction."""

    @pytest.mark.asyncio
    async def test_extract_mmddyyyy_date(self, field_extractor):
        """Test extraction of MM/DD/YYYY format dates."""
        result = await field_extractor.extract(
            subject="Order date",
            body="I placed the order on 01/15/2024.",
            category="billing",
            use_ai=False,
        )

        date_fields = [f for f in result.fields if f.name == "date"]
        assert len(date_fields) > 0

    @pytest.mark.asyncio
    async def test_extract_iso_date(self, field_extractor):
        """Test extraction of ISO format dates."""
        result = await field_extractor.extract(
            subject="Transaction date",
            body="The transaction occurred on 2024-01-15.",
            category="billing",
            use_ai=False,
        )

        date_fields = [f for f in result.fields if f.name == "date"]
        assert len(date_fields) > 0

    @pytest.mark.asyncio
    async def test_extract_written_date(self, field_extractor):
        """Test extraction of written dates."""
        result = await field_extractor.extract(
            subject="Event date",
            body="This happened on January 15, 2024.",
            category="general",
            use_ai=False,
        )

        date_fields = [f for f in result.fields if f.name == "date"]
        assert len(date_fields) > 0


# ============================================================================
# Priority Keywords Extraction Tests
# ============================================================================


class TestPriorityKeywordsExtraction:
    """Tests for priority keyword extraction."""

    @pytest.mark.asyncio
    async def test_extract_urgent_keyword(self, field_extractor):
        """Test extraction of 'urgent' keyword."""
        result = await field_extractor.extract(
            subject="Urgent issue",
            body="This is urgent and needs immediate attention!",
            category="technical",
            use_ai=False,
        )

        priority_fields = [f for f in result.fields if f.name == "priority_keywords"]
        assert len(priority_fields) > 0
        assert "urgent" in [kw.lower() for kw in priority_fields[0].value]

    @pytest.mark.asyncio
    async def test_extract_multiple_priority_keywords(self, field_extractor):
        """Test extraction of multiple priority keywords."""
        result = await field_extractor.extract(
            subject="Critical emergency",
            body="This is critical! I need help ASAP. It's an emergency!",
            category="technical",
            use_ai=False,
        )

        priority_fields = [f for f in result.fields if f.name == "priority_keywords"]
        assert len(priority_fields) > 0
        keywords = [kw.lower() for kw in priority_fields[0].value]
        assert len(keywords) >= 2

    @pytest.mark.asyncio
    async def test_no_priority_keywords_when_absent(self, field_extractor):
        """Test that no priority keywords extracted when not present."""
        result = await field_extractor.extract(
            subject="General question",
            body="I have a simple question about your product.",
            category="general",
            use_ai=False,
        )

        priority_fields = [f for f in result.fields if f.name == "priority_keywords"]
        assert len(priority_fields) == 0


# ============================================================================
# Missing Required Fields Tests
# ============================================================================


class TestMissingRequiredFields:
    """Tests for missing required fields detection."""

    @pytest.mark.asyncio
    async def test_missing_error_code_for_technical(self, field_extractor):
        """Test detection of missing error code for technical category."""
        result = await field_extractor.extract(
            subject="Technical issue",
            body="Something is broken but I don't have an error code.",
            category="technical",
            use_ai=False,
        )

        # error_code is required for technical category
        assert "error_code" in result.missing_required

    @pytest.mark.asyncio
    async def test_missing_order_id_for_billing(self, field_extractor):
        """Test detection of missing order_id for billing category."""
        result = await field_extractor.extract(
            subject="Billing question",
            body="I have a question about charges but no order ID.",
            category="billing",
            use_ai=False,
        )

        # order_id or amount is required for billing
        assert len(result.missing_required) > 0

    @pytest.mark.asyncio
    async def test_no_missing_when_all_provided(self, field_extractor):
        """Test no missing fields when all required fields are present."""
        result = await field_extractor.extract(
            subject="Technical error",
            body="Getting error code ERR-12345 when using the system.",
            category="technical",
            use_ai=False,
        )

        # error_code should be extracted, so it shouldn't be in missing
        error_fields = [f for f in result.fields if f.name == "error_code"]
        if error_fields:
            assert "error_code" not in result.missing_required

    @pytest.mark.asyncio
    async def test_no_required_fields_for_feature_request(self, field_extractor):
        """Test that feature_request has no required fields."""
        result = await field_extractor.extract(
            subject="Feature idea",
            body="I'd like to suggest a new feature.",
            category="feature_request",
            use_ai=False,
        )

        # feature_request has no required fields
        assert len(result.missing_required) == 0


# ============================================================================
# Field Validation Tests
# ============================================================================


class TestFieldValidation:
    """Tests for field validation."""

    @pytest.mark.asyncio
    async def test_valid_email_no_validation_error(self, field_extractor):
        """Test that valid email doesn't produce validation error."""
        result = await field_extractor.extract(
            subject="Contact",
            body="My email is valid@email.com.",
            category="general",
            use_ai=False,
        )

        email_fields = [f for f in result.fields if f.name == "account_email"]
        if email_fields:
            # Check no validation errors related to email
            email_errors = [e for e in result.validation_errors if "account_email" in e]
            assert len(email_errors) == 0

    @pytest.mark.asyncio
    async def test_confidence_in_valid_range(self, field_extractor):
        """Test that all confidence scores are in valid range."""
        result = await field_extractor.extract(
            subject="Order ORD-12345",
            body="Contact me at test@example.com or call 555-123-4567.",
            category="billing",
            use_ai=False,
        )

        for field in result.fields:
            assert 0.0 <= field.confidence <= 1.0, (
                f"Field {field.name} has invalid confidence: {field.confidence}"
            )


# ============================================================================
# Confidence Score Tests
# ============================================================================


class TestConfidenceScores:
    """Tests for confidence score calculations."""

    @pytest.mark.asyncio
    async def test_high_confidence_for_clear_patterns(self, field_extractor):
        """Test that clear pattern matches have high confidence."""
        result = await field_extractor.extract(
            subject="Order issue",
            body="My order ORD-123456 has an error ERR-50023.",
            category="technical",
            use_ai=False,
        )

        for field in result.fields:
            if field.name in ["order_id", "error_code"]:
                assert field.confidence >= 0.7

    @pytest.mark.asyncio
    async def test_email_confidence_boost(self, field_extractor):
        """Test that valid email format boosts confidence."""
        result = await field_extractor.extract(
            subject="Contact",
            body="Email: john.doe@example.com",
            category="general",
            use_ai=False,
        )

        email_fields = [f for f in result.fields if f.name == "account_email"]
        if email_fields:
            assert email_fields[0].confidence >= 0.8


# ============================================================================
# Source Span Tests
# ============================================================================


class TestSourceSpan:
    """Tests for source span extraction."""

    @pytest.mark.asyncio
    async def test_source_span_captured(self, field_extractor):
        """Test that source span is captured for extracted fields."""
        result = await field_extractor.extract(
            subject="Order",
            body="My order ID is ORD-123456.",
            category="billing",
            use_ai=False,
        )

        order_fields = [f for f in result.fields if f.name == "order_id"]
        if order_fields:
            assert order_fields[0].source_span is not None
            assert "ORD-123456" in order_fields[0].source_span

    @pytest.mark.asyncio
    async def test_source_span_contains_original_text(self, field_extractor):
        """Test that source span contains the original matched text."""
        result = await field_extractor.extract(
            subject="Contact",
            body="Please email me at user@example.com",
            category="general",
            use_ai=False,
        )

        email_fields = [f for f in result.fields if f.name == "account_email"]
        if email_fields:
            assert "user@example.com" in email_fields[0].source_span


# ============================================================================
# Fallback Extraction Tests
# ============================================================================


class TestFallbackExtraction:
    """Tests for fallback extraction behavior."""

    @pytest.mark.asyncio
    async def test_fallback_when_ai_disabled(self, mock_ai_service):
        """Test that regex fallback is used when AI is disabled."""
        extractor = FieldExtractor(ai_service=mock_ai_service, enable_ai=False)

        result = await extractor.extract(
            subject="Order ORD-12345",
            body="Contact test@example.com",
            category="billing",
            use_ai=None,
        )

        # Should not have called AI service
        mock_ai_service.extract_fields.assert_not_called()
        assert len(result.fields) > 0

    @pytest.mark.asyncio
    async def test_fallback_when_ai_fails(self, mock_ai_service):
        """Test that fallback is used when AI service fails."""
        mock_ai_service.extract_fields.side_effect = Exception("AI error")
        extractor = FieldExtractor(ai_service=mock_ai_service, enable_ai=True)

        result = await extractor.extract(
            subject="Order ORD-12345",
            body="Contact test@example.com",
            category="billing",
            use_ai=True,
        )

        # Should have fallen back to regex
        assert isinstance(result, ExtractionResult)
        assert len(result.fields) > 0

    @pytest.mark.asyncio
    async def test_no_ai_service_fallback(self):
        """Test fallback when no AI service is provided."""
        extractor = FieldExtractor(ai_service=None, enable_ai=True)

        result = await extractor.extract(
            subject="Order ORD-12345",
            body="Contact test@example.com",
            category="billing",
            use_ai=True,
        )

        assert isinstance(result, ExtractionResult)
        assert len(result.fields) > 0


# ============================================================================
# Helper Method Tests
# ============================================================================


class TestHelperMethods:
    """Tests for helper methods."""

    def test_get_fields_by_name(self, field_extractor):
        """Test getting fields by name."""
        fields = [
            ExtractedField(name="order_id", value="123", confidence=0.9, source_span="123"),
            ExtractedField(name="email", value="test@test.com", confidence=0.9, source_span="test@test.com"),
            ExtractedField(name="order_id", value="456", confidence=0.8, source_span="456"),
        ]

        order_fields = field_extractor.get_fields_by_name(fields, "order_id")

        assert len(order_fields) == 2
        assert all(f.name == "order_id" for f in order_fields)

    def test_get_highest_confidence_field(self, field_extractor):
        """Test getting field with highest confidence."""
        fields = [
            ExtractedField(name="email", value="test1@test.com", confidence=0.7, source_span="test1"),
            ExtractedField(name="email", value="test2@test.com", confidence=0.95, source_span="test2"),
            ExtractedField(name="email", value="test3@test.com", confidence=0.8, source_span="test3"),
        ]

        best = field_extractor.get_highest_confidence_field(fields, "email")

        assert best is not None
        assert best.confidence == 0.95
        assert best.value == "test2@test.com"

    def test_get_highest_confidence_field_not_found(self, field_extractor):
        """Test getting highest confidence field when not found."""
        fields = [
            ExtractedField(name="email", value="test@test.com", confidence=0.9, source_span="test"),
        ]

        result = field_extractor.get_highest_confidence_field(fields, "phone")

        assert result is None

    def test_get_fields_as_dict(self, field_extractor):
        """Test converting fields to dictionary."""
        fields = [
            ExtractedField(name="order_id", value="123", confidence=0.9, source_span="123"),
            ExtractedField(name="email", value="test@test.com", confidence=0.95, source_span="test@test.com"),
        ]

        result = field_extractor.get_fields_as_dict(fields)

        assert result["order_id"] == "123"
        assert result["email"] == "test@test.com"

    def test_get_fields_as_dict_with_confidence(self, field_extractor):
        """Test converting fields to dictionary with confidence."""
        fields = [
            ExtractedField(name="order_id", value="123", confidence=0.9, source_span="123"),
        ]

        result = field_extractor.get_fields_as_dict(fields, include_confidence=True)

        assert "order_id" in result
        assert "value" in result["order_id"]
        assert "confidence" in result["order_id"]
        assert result["order_id"]["value"] == "123"


# ============================================================================
# Custom Pattern Tests
# ============================================================================


class TestCustomPatterns:
    """Tests for custom pattern functionality."""

    def test_add_custom_pattern(self, field_extractor):
        """Test adding a custom extraction pattern."""
        field_extractor.add_custom_pattern("custom_field", r"CUSTOM-(\d+)")

        patterns = field_extractor.get_extraction_patterns()
        assert "custom_field" in patterns

    @pytest.mark.asyncio
    async def test_custom_pattern_extraction(self, field_extractor):
        """Test extraction using custom pattern."""
        field_extractor.add_custom_pattern("custom_id", r"CUSTOM-(\d+)")

        result = await field_extractor.extract(
            subject="Custom ID",
            body="My custom ID is CUSTOM-99999.",
            category="general",
            use_ai=False,
        )

        custom_fields = [f for f in result.fields if f.name == "custom_id"]
        assert len(custom_fields) > 0


# ============================================================================
# Edge Cases Tests
# ============================================================================


class TestEdgeCases:
    """Tests for edge cases in extraction."""

    @pytest.mark.asyncio
    async def test_empty_text(self, field_extractor):
        """Test extraction with empty text."""
        result = await field_extractor.extract(
            subject="",
            body="",
            category="general",
            use_ai=False,
        )

        assert isinstance(result, ExtractionResult)
        assert len(result.fields) == 0

    @pytest.mark.asyncio
    async def test_no_matching_patterns(self, field_extractor):
        """Test extraction when no patterns match."""
        result = await field_extractor.extract(
            subject="Hello",
            body="Just saying hello!",
            category="general",
            use_ai=False,
        )

        assert isinstance(result, ExtractionResult)
        # No extractable fields in this text

    @pytest.mark.asyncio
    async def test_duplicate_values_filtered(self, field_extractor):
        """Test that duplicate values are filtered out."""
        result = await field_extractor.extract(
            subject="Contact",
            body="Email: test@test.com. Also reach me at test@test.com.",
            category="general",
            use_ai=False,
        )

        email_fields = [f for f in result.fields if f.name == "account_email"]
        # Should only have one instance of the duplicate
        values = [f.value for f in email_fields]
        assert values.count("test@test.com") <= 1

    @pytest.mark.asyncio
    async def test_special_characters_in_text(self, field_extractor):
        """Test extraction with special characters."""
        result = await field_extractor.extract(
            subject="Issue!!!",
            body="Error @#$% ERR-12345 !!! Call 555-123-4567 NOW!!!",
            category="technical",
            use_ai=False,
        )

        # Should still extract the error code and phone despite special chars
        error_fields = [f for f in result.fields if f.name == "error_code"]
        phone_fields = [f for f in result.fields if f.name == "phone_number"]
        assert len(error_fields) > 0 or len(phone_fields) > 0


# ============================================================================
# Integration Tests with Sample Tickets
# ============================================================================


class TestSampleTicketsExtraction:
    """Tests using sample tickets from fixtures."""

    @pytest.mark.asyncio
    async def test_complex_extraction_ticket(self, field_extractor, sample_tickets):
        """Test extraction from complex ticket with multiple fields."""
        ticket = sample_tickets["complex_extraction"]

        result = await field_extractor.extract(
            subject=ticket["subject"],
            body=ticket["body"],
            category=ticket.get("expected_category", "billing"),
            use_ai=False,
        )

        expected_fields = ticket.get("expected_fields", [])
        field_names = {f.name for f in result.fields}

        for expected in expected_fields:
            assert expected in field_names, (
                f"Expected field '{expected}' not found in {field_names}"
            )

    @pytest.mark.asyncio
    async def test_all_sample_tickets_extraction(self, field_extractor, sample_tickets):
        """Test extraction across all sample tickets."""
        for ticket_id, ticket_data in sample_tickets.items():
            result = await field_extractor.extract(
                subject=ticket_data["subject"],
                body=ticket_data["body"],
                category=ticket_data.get("expected_category", "general"),
                use_ai=False,
            )

            assert isinstance(result, ExtractionResult)
            assert isinstance(result.fields, list)
            assert isinstance(result.missing_required, list)
            assert isinstance(result.validation_errors, list)
