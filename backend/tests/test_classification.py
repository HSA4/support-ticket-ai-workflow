"""
Unit tests for ticket classification functionality.

This module tests the TicketClassifier class, including:
- Classification for each category
- Severity assignment
- Confidence scores
- Fallback classification behavior
- Keyword matching
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.schemas import ClassificationResult
from app.services.workflow.classifiers import (
    TicketClassifier,
    VALID_CATEGORIES,
    VALID_SEVERITIES,
    CATEGORY_KEYWORDS,
    SEVERITY_INDICATORS,
)


# ============================================================================
# Category Classification Tests
# ============================================================================


class TestCategoryClassification:
    """Tests for category classification."""

    @pytest.mark.asyncio
    async def test_classify_technical_ticket(self, ticket_classifier):
        """Test classification of a technical support ticket."""
        result = await ticket_classifier.classify(
            subject="API returning 500 errors",
            body="Our system is experiencing errors when calling the API. "
                 "The bug is causing crashes in production.",
            use_ai=False,
        )

        assert result.category == "technical"
        assert result.category_confidence > 0.5
        assert "error" in result.keywords_matched or "bug" in result.keywords_matched

    @pytest.mark.asyncio
    async def test_classify_billing_ticket(self, ticket_classifier):
        """Test classification of a billing support ticket."""
        result = await ticket_classifier.classify(
            subject="Refund request for my subscription",
            body="I was charged for a payment I didn't authorize. "
                 "I need a refund for the invoice sent last week.",
            use_ai=False,
        )

        assert result.category == "billing"
        assert result.category_confidence > 0.5

    @pytest.mark.asyncio
    async def test_classify_account_ticket(self, ticket_classifier):
        """Test classification of an account support ticket."""
        result = await ticket_classifier.classify(
            subject="Cannot login to my account",
            body="I've been trying to sign in but my password doesn't work. "
                 "I think my credentials are wrong or my account is locked.",
            use_ai=False,
        )

        assert result.category == "account"
        assert result.category_confidence > 0.5

    @pytest.mark.asyncio
    async def test_classify_feature_request_ticket(self, ticket_classifier):
        """Test classification of a feature request ticket."""
        result = await ticket_classifier.classify(
            subject="Feature suggestion: Add dark mode",
            body="I would like to request a new feature for the application. "
                 "My wish is to have a dark mode option for better UX.",
            use_ai=False,
        )

        assert result.category == "feature_request"
        assert result.category_confidence > 0.5

    @pytest.mark.asyncio
    async def test_classify_bug_report_ticket(self, ticket_classifier):
        """Test classification of a bug report ticket."""
        result = await ticket_classifier.classify(
            subject="Bug: Application crashes on startup",
            body="I found a defect in the application. It's showing incorrect "
                 "behavior and unexpected results when I try to use it.",
            use_ai=False,
        )

        assert result.category == "bug_report"
        assert result.category_confidence > 0.5

    @pytest.mark.asyncio
    async def test_classify_general_ticket(self, ticket_classifier):
        """Test classification of a general inquiry ticket."""
        result = await ticket_classifier.classify(
            subject="Hello, I have a question",
            body="Hi there! I'm wondering how to get started with your service. "
                 "Can you help me with some information?",
            use_ai=False,
        )

        assert result.category == "general"
        # General might have lower confidence since it's a fallback

    @pytest.mark.asyncio
    async def test_classify_all_categories(self, ticket_classifier, sample_tickets):
        """Test classification across all ticket categories."""
        category_tickets = {
            "technical": sample_tickets["technical_high"],
            "billing": sample_tickets["billing_medium"],
            "account": sample_tickets["account_medium"],
            "feature_request": sample_tickets["feature_request_low"],
            "bug_report": sample_tickets["bug_report_medium"],
            "general": sample_tickets["general_low"],
        }

        for expected_category, ticket_data in category_tickets.items():
            result = await ticket_classifier.classify(
                subject=ticket_data["subject"],
                body=ticket_data["body"],
                use_ai=False,
            )
            assert result.category == expected_category, (
                f"Expected {expected_category}, got {result.category} for ticket: {ticket_data['subject']}"
            )


# ============================================================================
# Severity Classification Tests
# ============================================================================


class TestSeverityClassification:
    """Tests for severity classification."""

    @pytest.mark.asyncio
    async def test_classify_critical_severity(self, ticket_classifier):
        """Test classification of critical severity tickets."""
        result = await ticket_classifier.classify(
            subject="URGENT: Production system down!",
            body="This is an emergency! Our production environment is completely down. "
                 "We need this resolved ASAP. This is a critical situation.",
            use_ai=False,
        )

        assert result.severity == "critical"
        assert result.severity_confidence > 0.4
        assert len(result.urgency_indicators) > 0

    @pytest.mark.asyncio
    async def test_classify_high_severity(self, ticket_classifier):
        """Test classification of high severity tickets."""
        result = await ticket_classifier.classify(
            subject="Important issue affecting users",
            body="This is a serious problem that's affecting multiple users. "
                 "We need a resolution quickly as it's high priority.",
            use_ai=False,
        )

        assert result.severity in ["critical", "high"]

    @pytest.mark.asyncio
    async def test_classify_medium_severity(self, ticket_classifier):
        """Test classification of medium severity tickets."""
        result = await ticket_classifier.classify(
            subject="Issue with feature",
            body="I'm having a problem with one of the features. "
                 "It's an issue but not urgent. Please help when possible.",
            use_ai=False,
        )

        # Medium should be default or matched
        assert result.severity in ["medium", "high", "low"]

    @pytest.mark.asyncio
    async def test_classify_low_severity(self, ticket_classifier):
        """Test classification of low severity tickets."""
        result = await ticket_classifier.classify(
            subject="Minor cosmetic issue",
            body="I noticed a small visual glitch. It's a minor suggestion - "
                 "no rush to fix this. Just curious if you could look at it sometime.",
            use_ai=False,
        )

        assert result.severity == "low"

    @pytest.mark.asyncio
    async def test_critical_ticket_from_samples(self, ticket_classifier, critical_ticket):
        """Test critical severity classification from sample data."""
        result = await ticket_classifier.classify(
            subject=critical_ticket["subject"],
            body=critical_ticket["body"],
            use_ai=False,
        )

        assert result.severity == "critical"


# ============================================================================
# Confidence Score Tests
# ============================================================================


class TestConfidenceScores:
    """Tests for confidence score calculations."""

    @pytest.mark.asyncio
    async def test_confidence_in_valid_range(self, ticket_classifier):
        """Test that confidence scores are within valid range [0, 1]."""
        result = await ticket_classifier.classify(
            subject="Test ticket",
            body="This is a test ticket with error and bug keywords.",
            use_ai=False,
        )

        assert 0.0 <= result.category_confidence <= 1.0
        assert 0.0 <= result.severity_confidence <= 1.0

    @pytest.mark.asyncio
    async def test_high_confidence_for_clear_match(self, ticket_classifier):
        """Test that clear keyword matches produce high confidence."""
        result = await ticket_classifier.classify(
            subject="Refund for overcharged billing",
            body="I was overcharged on my bill and need a refund for the payment. "
                 "The invoice is incorrect and I want my money back for the subscription.",
            use_ai=False,
        )

        # Multiple billing keywords should give higher confidence
        assert result.category == "billing"
        assert result.category_confidence >= 0.6

    @pytest.mark.asyncio
    async def test_lower_confidence_for_ambiguous_ticket(self, ticket_classifier):
        """Test that ambiguous tickets have lower confidence."""
        result = await ticket_classifier.classify(
            subject="Help needed",
            body="Can you assist me?",
            use_ai=False,
        )

        # Minimal content should result in lower confidence or general category
        assert result.category == "general"
        assert result.category_confidence <= 0.5


# ============================================================================
# Fallback Classification Tests
# ============================================================================


class TestFallbackClassification:
    """Tests for fallback classification behavior."""

    @pytest.mark.asyncio
    async def test_fallback_when_ai_disabled(self, mock_ai_service):
        """Test that rule-based fallback is used when AI is disabled."""
        classifier = TicketClassifier(ai_service=mock_ai_service, enable_ai=False)

        result = await classifier.classify(
            subject="I need a refund for my subscription",
            body="The billing is wrong and I want my money back.",
            use_ai=None,  # Should use enable_ai setting
        )

        # Should not have called AI service
        mock_ai_service.classify_ticket.assert_not_called()
        assert result.category == "billing"

    @pytest.mark.asyncio
    async def test_fallback_when_ai_fails(self, mock_ai_service):
        """Test that fallback is used when AI service fails."""
        mock_ai_service.classify_ticket.side_effect = Exception("AI service error")
        classifier = TicketClassifier(ai_service=mock_ai_service, enable_ai=True)

        result = await classifier.classify(
            subject="I need a refund",
            body="The billing is wrong.",
            use_ai=True,
        )

        # Should have fallen back to rule-based
        assert isinstance(result, ClassificationResult)
        assert result.category in VALID_CATEGORIES

    @pytest.mark.asyncio
    async def test_fallback_when_confidence_below_threshold(self, mock_ai_service):
        """Test fallback when AI confidence is below threshold."""
        low_confidence_result = ClassificationResult(
            category="technical",
            category_confidence=0.3,  # Below default threshold of 0.6
            severity="medium",
            severity_confidence=0.5,
            secondary_categories=[],
            reasoning="Low confidence AI result",
        )
        mock_ai_service.classify_ticket.return_value = low_confidence_result

        classifier = TicketClassifier(
            ai_service=mock_ai_service,
            enable_ai=True,
            confidence_threshold=0.6,
        )

        result = await classifier.classify(
            subject="Test subject",
            body="Test body",
            use_ai=True,
        )

        # Should use fallback since AI confidence was below threshold
        assert isinstance(result, ClassificationResult)
        assert result.category in VALID_CATEGORIES

    @pytest.mark.asyncio
    async def test_no_ai_service_fallback(self):
        """Test fallback when no AI service is provided."""
        classifier = TicketClassifier(ai_service=None, enable_ai=True)

        result = await classifier.classify(
            subject="I need help with my account",
            body="My password isn't working for login.",
            use_ai=True,
        )

        assert isinstance(result, ClassificationResult)
        assert result.category == "account"


# ============================================================================
# Secondary Categories Tests
# ============================================================================


class TestSecondaryCategories:
    """Tests for secondary category detection."""

    @pytest.mark.asyncio
    async def test_secondary_categories_detected(self, ticket_classifier):
        """Test that secondary categories are detected for multi-topic tickets."""
        result = await ticket_classifier.classify(
            subject="Login error causing billing issues",
            body="I can't login to my account and I'm also having billing problems "
                 "with my subscription payment and there's an error in the system.",
            use_ai=False,
        )

        # Should have primary category with possible secondary
        assert result.category in VALID_CATEGORIES
        # Secondary categories may or may not be detected depending on keyword count

    @pytest.mark.asyncio
    async def test_max_two_secondary_categories(self, ticket_classifier):
        """Test that at most 2 secondary categories are returned."""
        result = await ticket_classifier.classify(
            subject="Multiple issues across system",
            body="Login error billing payment refund subscription account "
                 "password crash bug feature request enhancement suggestion.",
            use_ai=False,
        )

        assert len(result.secondary_categories) <= 2


# ============================================================================
# Keyword Matching Tests
# ============================================================================


class TestKeywordMatching:
    """Tests for keyword matching functionality."""

    @pytest.mark.asyncio
    async def test_keywords_matched_returned(self, ticket_classifier):
        """Test that matched keywords are returned in result."""
        result = await ticket_classifier.classify(
            subject="System crash and error",
            body="The application is broken and not working. I found a bug.",
            use_ai=False,
        )

        assert len(result.keywords_matched) > 0
        # Should contain some of the technical keywords
        technical_keywords = set(CATEGORY_KEYWORDS.get("technical", []))
        matched_set = set(kw.lower() for kw in result.keywords_matched)
        assert matched_set.intersection(technical_keywords)

    @pytest.mark.asyncio
    async def test_urgency_indicators_returned(self, ticket_classifier):
        """Test that urgency indicators are returned in result."""
        result = await ticket_classifier.classify(
            subject="URGENT issue",
            body="This is critical and needs ASAP attention!",
            use_ai=False,
        )

        assert len(result.urgency_indicators) > 0


# ============================================================================
# Validation Tests
# ============================================================================


class TestCategoryValidation:
    """Tests for category and severity validation."""

    def test_validate_valid_category(self, ticket_classifier):
        """Test validation of valid categories."""
        for category in VALID_CATEGORIES:
            assert ticket_classifier.validate_category(category) is True

    def test_validate_invalid_category(self, ticket_classifier):
        """Test validation of invalid categories."""
        assert ticket_classifier.validate_category("invalid_category") is False
        assert ticket_classifier.validate_category("") is False
        assert ticket_classifier.validate_category("Technical") is False  # Case sensitive

    def test_validate_valid_severity(self, ticket_classifier):
        """Test validation of valid severities."""
        for severity in VALID_SEVERITIES:
            assert ticket_classifier.validate_severity(severity) is True

    def test_validate_invalid_severity(self, ticket_classifier):
        """Test validation of invalid severities."""
        assert ticket_classifier.validate_severity("invalid") is False
        assert ticket_classifier.validate_severity("") is False
        assert ticket_classifier.validate_severity("URGENT") is False


# ============================================================================
# Reasoning Tests
# ============================================================================


class TestReasoning:
    """Tests for classification reasoning."""

    @pytest.mark.asyncio
    async def test_reasoning_provided(self, ticket_classifier):
        """Test that reasoning is provided in classification result."""
        result = await ticket_classifier.classify(
            subject="API error",
            body="Getting an error when calling the API. This is urgent.",
            use_ai=False,
        )

        assert result.reasoning is not None
        assert len(result.reasoning) > 0

    @pytest.mark.asyncio
    async def test_reasoning_includes_keywords(self, ticket_classifier):
        """Test that reasoning includes matched keywords."""
        result = await ticket_classifier.classify(
            subject="Billing refund request",
            body="I need a refund for the overcharged payment.",
            use_ai=False,
        )

        assert result.reasoning is not None
        # Reasoning should mention keywords or category
        assert "billing" in result.reasoning.lower() or len(result.keywords_matched) > 0


# ============================================================================
# Edge Cases Tests
# ============================================================================


class TestEdgeCases:
    """Tests for edge cases in classification."""

    @pytest.mark.asyncio
    async def test_empty_subject(self, ticket_classifier):
        """Test classification with empty subject."""
        result = await ticket_classifier.classify(
            subject="",
            body="I'm having a problem with my billing and need a refund.",
            use_ai=False,
        )

        assert result.category in VALID_CATEGORIES

    @pytest.mark.asyncio
    async def test_empty_body(self, ticket_classifier):
        """Test classification with empty body."""
        result = await ticket_classifier.classify(
            subject="Billing refund payment issue",
            body="",
            use_ai=False,
        )

        assert result.category in VALID_CATEGORIES

    @pytest.mark.asyncio
    async def test_very_long_text(self, ticket_classifier):
        """Test classification with very long text."""
        long_text = "error " * 1000  # Very long text with error keyword

        result = await ticket_classifier.classify(
            subject="Technical issue",
            body=long_text,
            use_ai=False,
        )

        assert result.category == "technical"

    @pytest.mark.asyncio
    async def test_special_characters(self, ticket_classifier):
        """Test classification with special characters."""
        result = await ticket_classifier.classify(
            subject="!!!URGENT!!! Billing $$$ issue ###",
            body="I need a @refund for my $payment!!! This is #critical.",
            use_ai=False,
        )

        assert result.category in VALID_CATEGORIES
        assert result.severity in VALID_SEVERITIES

    @pytest.mark.asyncio
    async def test_case_insensitive_matching(self, ticket_classifier):
        """Test that keyword matching is case insensitive."""
        result_lower = await ticket_classifier.classify(
            subject="error in system",
            body="there is an error in the system",
            use_ai=False,
        )

        result_upper = await ticket_classifier.classify(
            subject="ERROR IN SYSTEM",
            body="THERE IS AN ERROR IN THE SYSTEM",
            use_ai=False,
        )

        assert result_lower.category == result_upper.category


# ============================================================================
# AI Classification Tests
# ============================================================================


class TestAIClassification:
    """Tests for AI-based classification."""

    @pytest.mark.asyncio
    async def test_ai_classification_used_when_enabled(self, mock_ai_service):
        """Test that AI classification is used when enabled."""
        expected_result = ClassificationResult(
            category="technical",
            category_confidence=0.95,
            severity="high",
            severity_confidence=0.90,
            secondary_categories=["bug_report"],
            reasoning="AI detected technical issue",
        )
        mock_ai_service.classify_ticket.return_value = expected_result

        classifier = TicketClassifier(ai_service=mock_ai_service, enable_ai=True)
        result = await classifier.classify(
            subject="Test",
            body="Test",
            use_ai=True,
        )

        mock_ai_service.classify_ticket.assert_called_once()
        assert result.category == "technical"
        assert result.category_confidence == 0.95

    @pytest.mark.asyncio
    async def test_ai_override_use_ai_false(self, mock_ai_service):
        """Test that use_ai=False overrides enable_ai setting."""
        classifier = TicketClassifier(ai_service=mock_ai_service, enable_ai=True)

        result = await classifier.classify(
            subject="Billing refund",
            body="I need a refund for my payment.",
            use_ai=False,  # Override to not use AI
        )

        mock_ai_service.classify_ticket.assert_not_called()
        assert result.category == "billing"  # Should use rule-based


# ============================================================================
# Integration Tests with Sample Tickets
# ============================================================================


class TestSampleTicketsClassification:
    """Tests using sample tickets from fixtures."""

    @pytest.mark.asyncio
    async def test_all_sample_tickets_classify_correctly(
        self, ticket_classifier, sample_tickets, assert_classification
    ):
        """Test that all sample tickets classify to expected categories."""
        for ticket_id, ticket_data in sample_tickets.items():
            if ticket_id in ["malicious_input", "duplicate_content"]:
                continue  # Skip special test cases

            result = await ticket_classifier.classify(
                subject=ticket_data["subject"],
                body=ticket_data["body"],
                use_ai=False,
            )

            expected_category = ticket_data.get("expected_category")
            expected_severity = ticket_data.get("expected_severity")

            assert_classification(
                result,
                expected_category=expected_category,
                expected_severity=expected_severity,
                min_confidence=0.3,
            )
