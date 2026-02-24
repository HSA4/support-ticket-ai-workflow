"""
Pytest fixtures for support ticket workflow tests.

This module provides fixtures for testing the support ticket workflow system,
including async session management, test clients, mock AI services,
and sample ticket data.
"""

import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio

# Add the parent directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.schemas import (
    ClassificationResult,
    ExtractedField,
    ExtractionResult,
    ResponseDraft,
    RoutingDecision,
    TicketInput,
    WorkflowOptions,
    WorkflowResponse,
    WorkflowStepResult,
)
from app.services.ai_service import AIService
from app.services.workflow.classifiers import TicketClassifier
from app.services.workflow.extractors import FieldExtractor
from app.services.workflow.generators import ResponseGenerator
from app.services.workflow.orchestrator import WorkflowOrchestrator
from app.services.workflow.routers import TicketRouter
from app.services.workflow.validators import InputValidator


# ============================================================================
# Configuration Fixtures
# ============================================================================


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_settings():
    """Provide test-specific settings."""
    return {
        "OPENAI_API_KEY": "test-api-key",
        "DATABASE_URL": "postgresql+asyncpg://test:test@localhost:5432/test_db",
        "DEFAULT_MODEL": "gpt-4-turbo-preview",
        "MAX_TOKENS": 4096,
        "WORKFLOW_TIMEOUT_SECONDS": 30,
        "ENABLE_AI_CLASSIFICATION": True,
        "ENABLE_AI_EXTRACTION": True,
        "ENABLE_RESPONSE_GENERATION": True,
        "AI_CONFIDENCE_THRESHOLD": 0.6,
    }


@pytest.fixture
def mock_settings(test_settings):
    """Mock the settings for testing."""
    with patch("app.core.config.settings") as mock:
        for key, value in test_settings.items():
            setattr(mock, key, value)
        mock.OPENAI_API_KEY = test_settings["OPENAI_API_KEY"]
        mock.ENABLE_AI_CLASSIFICATION = test_settings["ENABLE_AI_CLASSIFICATION"]
        mock.ENABLE_AI_EXTRACTION = test_settings["ENABLE_AI_EXTRACTION"]
        mock.ENABLE_RESPONSE_GENERATION = test_settings["ENABLE_RESPONSE_GENERATION"]
        mock.AI_CONFIDENCE_THRESHOLD = test_settings["AI_CONFIDENCE_THRESHOLD"]
        yield mock


# ============================================================================
# Sample Data Fixtures
# ============================================================================


@pytest.fixture(scope="session")
def sample_tickets_data() -> Dict[str, Any]:
    """Load sample ticket data from JSON file."""
    fixtures_path = Path(__file__).parent / "fixtures" / "sample_tickets.json"
    with open(fixtures_path, "r") as f:
        return json.load(f)


@pytest.fixture
def sample_ticket(sample_tickets_data) -> Dict[str, Any]:
    """Provide a basic sample ticket."""
    return sample_tickets_data["tickets"]["technical_low"]


@pytest.fixture
def sample_tickets(sample_tickets_data) -> Dict[str, Dict[str, Any]]:
    """Provide all sample tickets."""
    return sample_tickets_data["tickets"]


@pytest.fixture
def technical_ticket(sample_tickets) -> Dict[str, Any]:
    """Provide a technical support ticket."""
    return sample_tickets["technical_high"]


@pytest.fixture
def billing_ticket(sample_tickets) -> Dict[str, Any]:
    """Provide a billing support ticket."""
    return sample_tickets["billing_medium"]


@pytest.fixture
def account_ticket(sample_tickets) -> Dict[str, Any]:
    """Provide an account support ticket."""
    return sample_tickets["account_medium"]


@pytest.fixture
def critical_ticket(sample_tickets) -> Dict[str, Any]:
    """Provide a critical severity ticket."""
    return sample_tickets["billing_critical"]


@pytest.fixture
def minimal_ticket(sample_tickets) -> Dict[str, Any]:
    """Provide a minimal ticket with little context."""
    return sample_tickets["minimal"]


@pytest.fixture
def malicious_ticket(sample_tickets) -> Dict[str, Any]:
    """Provide a ticket with potential prompt injection."""
    return sample_tickets["malicious_input"]


# ============================================================================
# Pydantic Model Fixtures
# ============================================================================


@pytest.fixture
def ticket_input(sample_ticket) -> TicketInput:
    """Create a TicketInput instance from sample data."""
    return TicketInput(
        subject=sample_ticket["subject"],
        body=sample_ticket["body"],
        customer_id=sample_ticket.get("customer_id"),
        customer_email=sample_ticket.get("customer_email"),
    )


@pytest.fixture
def ticket_input_factory():
    """Factory fixture to create TicketInput instances."""

    def _create(
        subject: str = "Test Subject",
        body: str = "Test body content",
        customer_id: Optional[str] = None,
        customer_email: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> TicketInput:
        return TicketInput(
            subject=subject,
            body=body,
            customer_id=customer_id,
            customer_email=customer_email,
            metadata=metadata or {},
        )

    return _create


@pytest.fixture
def classification_result() -> ClassificationResult:
    """Provide a sample classification result."""
    return ClassificationResult(
        category="technical",
        category_confidence=0.92,
        severity="high",
        severity_confidence=0.85,
        secondary_categories=[],
        reasoning="User reports technical issue with error messages",
        keywords_matched=["error", "crash"],
        urgency_indicators=["important"],
    )


@pytest.fixture
def extraction_result() -> ExtractionResult:
    """Provide a sample extraction result."""
    return ExtractionResult(
        fields=[
            ExtractedField(
                name="error_code",
                value="ERR-50023",
                confidence=0.95,
                source_span="error code ERR-50023",
            ),
            ExtractedField(
                name="account_email",
                value="user@example.com",
                confidence=0.98,
                source_span="user@example.com",
            ),
        ],
        missing_required=[],
        validation_errors=[],
    )


@pytest.fixture
def response_draft() -> ResponseDraft:
    """Provide a sample response draft."""
    return ResponseDraft(
        content="Dear Customer,\n\nThank you for contacting us...",
        tone="friendly",
        template_used="technical_template",
        suggested_actions=["Try clearing your cache", "Check for updates"],
        requires_escalation=False,
        greeting="Dear Customer,",
        acknowledgment="Thank you for contacting us about your technical issue.",
        action_items=["Try clearing your cache", "Check for updates"],
        timeline="We aim to respond within 24 hours.",
        closing="Best regards,\nSupport Team",
    )


@pytest.fixture
def routing_decision() -> RoutingDecision:
    """Provide a sample routing decision."""
    return RoutingDecision(
        team="technical_support",
        priority="high",
        reasoning="Technical issue with high severity routed to technical support",
        alternative_teams=["account_management"],
        escalation_path=["senior_technical", "engineering_team"],
        confidence=0.90,
    )


@pytest.fixture
def workflow_options() -> WorkflowOptions:
    """Provide default workflow options."""
    return WorkflowOptions(
        skip_classification=False,
        skip_extraction=False,
        skip_response=False,
        skip_routing=False,
        response_tone="friendly",
        enable_duplicate_detection=True,
        enable_parallel=True,
    )


# ============================================================================
# Mock AIService Fixtures
# ============================================================================


@pytest.fixture
def mock_ai_service():
    """Create a mock AIService with configurable behavior."""

    class MockAIService:
        """Mock AI service for testing without actual API calls."""

        def __init__(self):
            self.classify_ticket = AsyncMock(return_value=ClassificationResult(
                category="technical",
                category_confidence=0.92,
                severity="medium",
                severity_confidence=0.85,
                secondary_categories=[],
                reasoning="Mock classification",
                keywords_matched=["test"],
                urgency_indicators=[],
            ))
            self.extract_fields = AsyncMock(return_value=ExtractionResult(
                fields=[],
                missing_required=[],
                validation_errors=[],
            ))
            self.generate_response = AsyncMock(return_value=ResponseDraft(
                content="Mock response content",
                tone="friendly",
                template_used=None,
                suggested_actions=[],
                requires_escalation=False,
            ))
            self.determine_routing = AsyncMock(return_value=RoutingDecision(
                team="technical_support",
                priority="normal",
                reasoning="Mock routing",
                alternative_teams=[],
                confidence=0.9,
            ))
            self.health_check = AsyncMock(return_value=True)
            self._token_usage = {"prompt": 0, "completion": 0, "total": 0}

        @property
        def token_usage(self) -> Dict[str, int]:
            return self._token_usage.copy()

        def reset_token_usage(self):
            self._token_usage = {"prompt": 0, "completion": 0, "total": 0}

        def set_classification_result(self, result: ClassificationResult):
            self.classify_ticket.return_value = result

        def set_extraction_result(self, result: ExtractionResult):
            self.extract_fields.return_value = result

        def set_response_draft(self, draft: ResponseDraft):
            self.generate_response.return_value = draft

        def set_routing_decision(self, decision: RoutingDecision):
            self.determine_routing.return_value = decision

        def set_side_effect(self, method_name: str, side_effect):
            """Set a side effect for any method."""
            getattr(self, method_name).side_effect = side_effect

    return MockAIService()


@pytest.fixture
def mock_ai_service_factory():
    """Factory fixture to create customized mock AI services."""

    def _create(
        category: str = "technical",
        category_confidence: float = 0.9,
        severity: str = "medium",
        severity_confidence: float = 0.85,
        fields: Optional[List[ExtractedField]] = None,
        team: str = "technical_support",
        priority: str = "normal",
        raise_error: bool = False,
    ) -> MagicMock:
        mock = MagicMock(spec=AIService)

        if raise_error:
            mock.classify_ticket = AsyncMock(side_effect=Exception("AI service error"))
            mock.extract_fields = AsyncMock(side_effect=Exception("AI service error"))
            mock.generate_response = AsyncMock(side_effect=Exception("AI service error"))
            mock.determine_routing = AsyncMock(side_effect=Exception("AI service error"))
        else:
            mock.classify_ticket = AsyncMock(return_value=ClassificationResult(
                category=category,
                category_confidence=category_confidence,
                severity=severity,
                severity_confidence=severity_confidence,
                secondary_categories=[],
                reasoning="Mock classification",
                keywords_matched=[],
                urgency_indicators=[],
            ))
            mock.extract_fields = AsyncMock(return_value=ExtractionResult(
                fields=fields or [],
                missing_required=[],
                validation_errors=[],
            ))
            mock.generate_response = AsyncMock(return_value=ResponseDraft(
                content="Mock response",
                tone="friendly",
                template_used=None,
                suggested_actions=[],
                requires_escalation=False,
            ))
            mock.determine_routing = AsyncMock(return_value=RoutingDecision(
                team=team,
                priority=priority,
                reasoning="Mock routing",
                alternative_teams=[],
                confidence=0.9,
            ))

        mock.health_check = AsyncMock(return_value=not raise_error)
        mock._token_usage = {"prompt": 0, "completion": 0, "total": 0}
        mock.token_usage = mock._token_usage.copy()

        return mock

    return _create


# ============================================================================
# Component Fixtures
# ============================================================================


@pytest.fixture
def input_validator() -> InputValidator:
    """Provide an InputValidator instance."""
    return InputValidator()


@pytest.fixture
def ticket_classifier(mock_ai_service) -> TicketClassifier:
    """Provide a TicketClassifier instance with mock AI service."""
    return TicketClassifier(ai_service=mock_ai_service, enable_ai=True)


@pytest.fixture
def field_extractor(mock_ai_service) -> FieldExtractor:
    """Provide a FieldExtractor instance with mock AI service."""
    return FieldExtractor(ai_service=mock_ai_service, enable_ai=True)


@pytest.fixture
def response_generator(mock_ai_service) -> ResponseGenerator:
    """Provide a ResponseGenerator instance with mock AI service."""
    return ResponseGenerator(ai_service=mock_ai_service, enable_ai=True)


@pytest.fixture
def ticket_router() -> TicketRouter:
    """Provide a TicketRouter instance."""
    return TicketRouter()


@pytest.fixture
def workflow_orchestrator(mock_ai_service) -> WorkflowOrchestrator:
    """Provide a WorkflowOrchestrator instance with mock AI service."""
    return WorkflowOrchestrator(ai_service=mock_ai_service, enable_ai=True)


@pytest.fixture
def workflow_orchestrator_no_ai() -> WorkflowOrchestrator:
    """Provide a WorkflowOrchestrator instance without AI."""
    return WorkflowOrchestrator(ai_service=None, enable_ai=False)


# ============================================================================
# Test Data Helper Fixtures
# ============================================================================


@pytest.fixture
def ticket_from_data():
    """Factory to create TicketInput from ticket data dict."""

    def _create(ticket_data: Dict[str, Any]) -> TicketInput:
        return TicketInput(
            subject=ticket_data["subject"],
            body=ticket_data["body"],
            customer_id=ticket_data.get("customer_id"),
            customer_email=ticket_data.get("customer_email"),
            metadata=ticket_data.get("metadata", {}),
        )

    return _create


@pytest.fixture
def assert_classification():
    """Helper to assert classification results."""

    def _assert(
        result: ClassificationResult,
        expected_category: Optional[str] = None,
        expected_severity: Optional[str] = None,
        min_confidence: float = 0.0,
    ):
        if expected_category:
            assert result.category == expected_category, (
                f"Expected category {expected_category}, got {result.category}"
            )
        if expected_severity:
            assert result.severity == expected_severity, (
                f"Expected severity {expected_severity}, got {result.severity}"
            )
        assert result.category_confidence >= min_confidence, (
            f"Category confidence {result.category_confidence} < {min_confidence}"
        )
        assert result.severity_confidence >= min_confidence, (
            f"Severity confidence {result.severity_confidence} < {min_confidence}"
        )

    return _assert


@pytest.fixture
def assert_extraction():
    """Helper to assert extraction results."""

    def _assert(
        result: ExtractionResult,
        expected_fields: Optional[List[str]] = None,
        should_have_fields: bool = True,
    ):
        if should_have_fields:
            assert len(result.fields) > 0, "Expected fields to be extracted"
        if expected_fields:
            field_names = {f.name for f in result.fields}
            for field_name in expected_fields:
                assert field_name in field_names, (
                    f"Expected field '{field_name}' not found in {field_names}"
                )

    return _assert


@pytest.fixture
def assert_routing():
    """Helper to assert routing decisions."""

    def _assert(
        result: RoutingDecision,
        expected_team: Optional[str] = None,
        expected_priority: Optional[str] = None,
        should_have_alternatives: bool = False,
    ):
        if expected_team:
            assert result.team == expected_team, (
                f"Expected team {expected_team}, got {result.team}"
            )
        if expected_priority:
            assert result.priority == expected_priority, (
                f"Expected priority {expected_priority}, got {result.priority}"
            )
        if should_have_alternatives:
            assert len(result.alternative_teams) > 0, "Expected alternative teams"

    return _assert


# ============================================================================
# Async Test Helpers
# ============================================================================


@pytest.fixture
def async_timeout():
    """Provide a timeout for async operations in tests."""
    return 5.0  # seconds


# ============================================================================
# Test Environment Setup
# ============================================================================


@pytest.fixture(autouse=True)
def setup_test_env():
    """Set up test environment variables."""
    original_env = os.environ.copy()

    # Set test environment variables
    os.environ["OPENAI_API_KEY"] = "test-api-key"
    os.environ["DATABASE_URL"] = "postgresql+asyncpg://test:test@localhost:5432/test_db"
    os.environ["DEBUG"] = "true"
    os.environ["LOG_LEVEL"] = "DEBUG"

    yield

    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)


# ============================================================================
# Marker Configuration
# ============================================================================


def pytest_configure(config):
    """Configure custom pytest markers."""
    config.addinivalue_line("markers", "asyncio: mark test as async")
    config.addinivalue_line("markers", "unit: mark test as unit test")
    config.addinivalue_line("markers", "integration: mark test as integration test")
    config.addinivalue_line("markers", "slow: mark test as slow running")
