"""
Unit tests for the AI Service.

These tests cover the AIService class methods including:
- classify_ticket with AI and fallback
- extract_fields with AI and fallback
- generate_response with AI and fallback
- determine_routing with AI and fallback
- JSON parsing utilities
- Error handling
"""

import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.ai_service import (
    AIService,
    AIServiceError,
    AIParseError,
    AVAILABLE_CATEGORIES,
    AVAILABLE_TEAMS,
    SEVERITY_LEVELS,
)
from app.schemas.workflow import (
    ClassificationResult,
    ExtractionResult,
    ExtractedField,
    ResponseDraft,
    RoutingDecision,
)


class TestAIServiceInit:
    """Tests for AIService initialization."""

    def test_init_with_default_api_key(self):
        """Test initialization with default API key from settings."""
        service = AIService()
        assert service.client is not None
        assert service.model is not None
        assert service.max_tokens > 0

    def test_init_with_custom_api_key(self):
        """Test initialization with custom API key."""
        service = AIService(api_key="test-key-123")
        assert service.api_key == "test-key-123"


class TestParseJsonResponse:
    """Tests for JSON response parsing."""

    def test_parse_raw_json(self):
        """Test parsing raw JSON response."""
        service = AIService()
        content = '{"key": "value", "number": 42}'
        result = service._parse_json_response(content)
        assert result == {"key": "value", "number": 42}

    def test_parse_json_in_markdown_block(self):
        """Test parsing JSON wrapped in markdown code block."""
        service = AIService()
        content = '''Here's the response:
```json
{"key": "value"}
```
That's it.'''
        result = service._parse_json_response(content)
        assert result == {"key": "value"}

    def test_parse_json_with_surrounding_text(self):
        """Test parsing JSON with text before and after."""
        service = AIService()
        content = 'Some text before {"key": "value"} some text after'
        result = service._parse_json_response(content)
        assert result == {"key": "value"}

    def test_parse_invalid_json_raises_error(self):
        """Test that invalid JSON raises AIParseError."""
        service = AIService()
        with pytest.raises(AIParseError):
            service._parse_json_response("not valid json")


class TestFallbackClassification:
    """Tests for fallback classification logic."""

    def test_classify_billing_ticket(self):
        """Test classification of billing-related ticket."""
        service = AIService()
        result = service._fallback_classification(
            subject="Refund request",
            body="I want a refund for my order",
        )
        assert isinstance(result, ClassificationResult)
        assert result.category == "billing"
        assert result.category_confidence > 0.5

    def test_classify_technical_ticket(self):
        """Test classification of technical ticket."""
        service = AIService()
        result = service._fallback_classification(
            subject="Error when logging in",
            body="I get an error when I try to log in to my account",
        )
        assert isinstance(result, ClassificationResult)
        assert result.category == "technical"

    def test_classify_account_ticket(self):
        """Test classification of account-related ticket."""
        service = AIService()
        result = service._fallback_classification(
            subject="Cannot access my account",
            body="My password is not working and I'm locked out",
        )
        assert isinstance(result, ClassificationResult)
        assert result.category == "account"

    def test_classify_critical_severity(self):
        """Test severity detection for critical issues."""
        service = AIService()
        result = service._fallback_classification(
            subject="URGENT: System down",
            body="Production is down, this is an emergency!",
        )
        assert isinstance(result, ClassificationResult)
        assert result.severity == "critical"
        assert "urgent" in result.urgency_indicators or "emergency" in result.urgency_indicators

    def test_classify_general_inquiry(self):
        """Test classification of general inquiry."""
        service = AIService()
        result = service._fallback_classification(
            subject="Question about your service",
            body="I have a question about how to use the product",
        )
        assert isinstance(result, ClassificationResult)
        assert result.category == "general"


class TestFallbackExtraction:
    """Tests for fallback field extraction."""

    def test_extract_order_id(self):
        """Test extraction of order ID."""
        service = AIService()
        result = service._fallback_extraction(
            subject="Order issue",
            body="My order ORD-123456 hasn't arrived yet",
        )
        assert isinstance(result, ExtractionResult)
        order_fields = [f for f in result.fields if f.name == "order_id"]
        assert len(order_fields) == 1
        assert order_fields[0].value == "ORD-123456"

    def test_extract_order_id_hash_format(self):
        """Test extraction of order ID in hash format."""
        service = AIService()
        result = service._fallback_extraction(
            subject="Order issue",
            body="Order #12345 is missing items",
        )
        assert isinstance(result, ExtractionResult)
        order_fields = [f for f in result.fields if f.name == "order_id"]
        assert len(order_fields) == 1
        assert order_fields[0].value == "#12345"

    def test_extract_email(self):
        """Test extraction of email address."""
        service = AIService()
        result = service._fallback_extraction(
            subject="Contact",
            body="Please contact me at john.doe@example.com",
        )
        assert isinstance(result, ExtractionResult)
        email_fields = [f for f in result.fields if f.name == "account_email"]
        assert len(email_fields) == 1
        assert email_fields[0].value == "john.doe@example.com"

    def test_extract_error_code(self):
        """Test extraction of error code."""
        service = AIService()
        result = service._fallback_extraction(
            subject="Error",
            body="I'm getting error ERR-5001 when trying to pay",
        )
        assert isinstance(result, ExtractionResult)
        error_fields = [f for f in result.fields if f.name == "error_code"]
        assert len(error_fields) == 1
        assert error_fields[0].value == "ERR-5001"

    def test_extract_priority_keywords(self):
        """Test extraction of priority keywords."""
        service = AIService()
        result = service._fallback_extraction(
            subject="Urgent issue",
            body="This is urgent! I need help ASAP!",
        )
        assert isinstance(result, ExtractionResult)
        priority_fields = [f for f in result.fields if f.name == "priority_keywords"]
        assert len(priority_fields) == 1
        assert "urgent" in priority_fields[0].value

    def test_extract_no_fields(self):
        """Test extraction when no structured fields are present."""
        service = AIService()
        result = service._fallback_extraction(
            subject="Hello",
            body="Just wanted to say hi",
        )
        assert isinstance(result, ExtractionResult)
        assert len(result.fields) == 0


class TestFallbackResponse:
    """Tests for fallback response generation."""

    def test_generate_technical_response(self):
        """Test response generation for technical category."""
        service = AIService()
        result = service._fallback_response({
            "subject": "Error",
            "body": "I have an error",
            "category": "technical",
            "severity": "medium",
            "customer_name": "John",
            "tone": "friendly",
        })
        assert isinstance(result, ResponseDraft)
        assert "Dear John" in result.content
        assert "technical" in result.template_used
        assert len(result.suggested_actions) > 0

    def test_generate_billing_response(self):
        """Test response generation for billing category."""
        service = AIService()
        result = service._fallback_response({
            "subject": "Refund",
            "body": "I need a refund",
            "category": "billing",
            "severity": "medium",
            "customer_name": "Jane",
            "tone": "formal",
        })
        assert isinstance(result, ResponseDraft)
        assert "Dear Jane" in result.content
        assert "billing" in result.template_used

    def test_generate_critical_response(self):
        """Test response generation for critical severity."""
        service = AIService()
        result = service._fallback_response({
            "subject": "System down",
            "body": "Everything is broken",
            "category": "technical",
            "severity": "critical",
            "customer_name": "Admin",
            "tone": "technical",
        })
        assert isinstance(result, ResponseDraft)
        assert result.requires_escalation is True
        assert "1 hour" in result.timeline or "escalated" in result.content.lower()


class TestFallbackRouting:
    """Tests for fallback routing logic."""

    def test_route_billing_ticket(self):
        """Test routing of billing ticket."""
        service = AIService()
        result = service._fallback_routing({
            "category": "billing",
            "severity": "medium",
        })
        assert isinstance(result, RoutingDecision)
        assert result.team == "billing_team"
        assert result.priority == "normal"

    def test_route_technical_ticket(self):
        """Test routing of technical ticket."""
        service = AIService()
        result = service._fallback_routing({
            "category": "technical",
            "severity": "high",
        })
        assert isinstance(result, RoutingDecision)
        assert result.team == "technical_support"
        assert result.priority == "high"

    def test_route_critical_to_escalation(self):
        """Test that critical tickets go to escalation team."""
        service = AIService()
        result = service._fallback_routing({
            "category": "technical",
            "severity": "critical",
        })
        assert isinstance(result, RoutingDecision)
        assert result.team == "escalation_team"
        assert result.priority == "urgent"

    def test_route_feature_request(self):
        """Test routing of feature requests."""
        service = AIService()
        result = service._fallback_routing({
            "category": "feature_request",
            "severity": "low",
        })
        assert isinstance(result, RoutingDecision)
        assert result.team == "product_team"

    def test_route_has_escalation_path(self):
        """Test that routing includes escalation path."""
        service = AIService()
        result = service._fallback_routing({
            "category": "technical",
            "severity": "medium",
        })
        assert isinstance(result, RoutingDecision)
        assert result.escalation_path is not None
        assert len(result.escalation_path) > 0


class TestAIServiceIntegration:
    """Integration tests for AIService methods with mocked OpenAI."""

    @pytest.mark.asyncio
    async def test_classify_ticket_with_ai_enabled(self):
        """Test classification with AI enabled and mocked response."""
        mock_response = {
            "category": "billing",
            "category_confidence": 0.95,
            "severity": "high",
            "severity_confidence": 0.85,
            "secondary_categories": ["account"],
            "reasoning": "Customer mentions refund and payment issues",
            "keywords_matched": ["refund", "payment"],
            "urgency_indicators": ["quickly"],
        }

        service = AIService()
        with patch.object(service, '_call_openai', new_callable=AsyncMock) as mock_call:
            mock_call.return_value = mock_response

            result = await service.classify_ticket(
                subject="Refund needed",
                body="I need a refund quickly",
            )

            assert isinstance(result, ClassificationResult)
            assert result.category == "billing"
            assert result.category_confidence == 0.95
            assert result.severity == "high"

    @pytest.mark.asyncio
    async def test_classify_ticket_fallback_on_error(self):
        """Test that classification falls back on error."""
        service = AIService()
        with patch.object(service, '_call_openai', new_callable=AsyncMock) as mock_call:
            mock_call.side_effect = AIServiceError("API error")

            result = await service.classify_ticket(
                subject="Refund needed",
                body="I need a refund for my payment",
            )

            # Should use fallback
            assert isinstance(result, ClassificationResult)
            assert result.category == "billing"
            assert "Rule-based" in result.reasoning

    @pytest.mark.asyncio
    async def test_extract_fields_with_ai_enabled(self):
        """Test field extraction with AI enabled and mocked response."""
        mock_response = {
            "fields": [
                {"name": "order_id", "value": "ORD-123456", "confidence": 0.95, "source_text": "ORD-123456"},
                {"name": "account_email", "value": "test@example.com", "confidence": 0.98, "source_text": "test@example.com"},
            ],
            "missing_critical": [],
            "validation_errors": [],
        }

        service = AIService()
        with patch.object(service, '_call_openai', new_callable=AsyncMock) as mock_call:
            mock_call.return_value = mock_response

            result = await service.extract_fields(
                subject="Order issue",
                body="My order ORD-123456 at test@example.com has a problem",
                category="technical",
            )

            assert isinstance(result, ExtractionResult)
            assert len(result.fields) == 2

    @pytest.mark.asyncio
    async def test_generate_response_with_ai_enabled(self):
        """Test response generation with AI enabled and mocked response."""
        mock_response = {
            "greeting": "Dear John,",
            "acknowledgment": "Thank you for your message.",
            "explanation": "We are looking into this.",
            "action_items": ["We will investigate", "We will respond within 24 hours"],
            "timeline": "24 hours",
            "closing": "Best regards, Support Team",
            "full_response": "Dear John,\n\nThank you for your message.\n\nWe are looking into this.\n\nBest regards, Support Team",
            "requires_escalation": False,
        }

        service = AIService()
        with patch.object(service, '_call_openai', new_callable=AsyncMock) as mock_call:
            mock_call.return_value = mock_response

            result = await service.generate_response(
                subject="Help needed",
                body="I need help",
                category="technical",
                severity="medium",
                extracted_fields={},
                customer_name="John",
                tone="friendly",
            )

            assert isinstance(result, ResponseDraft)
            assert "Dear John" in result.content
            assert len(result.suggested_actions) == 2

    @pytest.mark.asyncio
    async def test_determine_routing_with_ai_enabled(self):
        """Test routing with AI enabled and mocked response."""
        mock_response = {
            "team": "billing_team",
            "priority": "high",
            "reasoning": "Billing issues require billing team",
            "alternative_teams": ["account_management"],
            "escalation_path": ["billing_manager"],
        }

        service = AIService()
        with patch.object(service, '_call_openai', new_callable=AsyncMock) as mock_call:
            mock_call.return_value = mock_response

            result = await service.determine_routing(
                subject="Refund issue",
                body="I need a refund",
                category="billing",
                severity="high",
                extracted_fields={},
            )

            assert isinstance(result, RoutingDecision)
            assert result.team == "billing_team"
            assert result.priority == "high"

    @pytest.mark.asyncio
    async def test_health_check_success(self):
        """Test health check returns True when API is available."""
        service = AIService()

        mock_choices = [MagicMock()]
        mock_response = MagicMock()
        mock_response.choices = mock_choices

        with patch.object(
            service.client.chat.completions,
            'create',
            new_callable=AsyncMock
        ) as mock_create:
            mock_create.return_value = mock_response

            result = await service.health_check()
            assert result is True

    @pytest.mark.asyncio
    async def test_health_check_failure(self):
        """Test health check returns False when API is unavailable."""
        service = AIService()

        with patch.object(
            service.client.chat.completions,
            'create',
            new_callable=AsyncMock
        ) as mock_create:
            mock_create.side_effect = Exception("Connection failed")

            result = await service.health_check()
            assert result is False


class TestTokenUsage:
    """Tests for token usage tracking."""

    def test_token_usage_property(self):
        """Test token usage property returns correct format."""
        service = AIService()
        usage = service.token_usage

        assert "prompt" in usage
        assert "completion" in usage
        assert "total" in usage

    def test_reset_token_usage(self):
        """Test resetting token usage counters."""
        service = AIService()
        service._token_usage = {"prompt": 100, "completion": 50, "total": 150}

        service.reset_token_usage()

        assert service.token_usage == {"prompt": 0, "completion": 0, "total": 0}


class TestConstants:
    """Tests for module constants."""

    def test_available_categories(self):
        """Test that all expected categories are defined."""
        expected = ["technical", "billing", "account", "feature_request", "bug_report", "general"]
        assert set(AVAILABLE_CATEGORIES) == set(expected)

    def test_available_teams(self):
        """Test that all expected teams are defined."""
        expected = ["technical_support", "billing_team", "account_management", "product_team", "escalation_team"]
        assert set(AVAILABLE_TEAMS) == set(expected)

    def test_severity_levels(self):
        """Test that all expected severity levels are defined."""
        expected = ["critical", "high", "medium", "low"]
        assert set(SEVERITY_LEVELS) == set(expected)
