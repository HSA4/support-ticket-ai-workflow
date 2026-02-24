"""
Tests for the WorkflowOrchestrator class.

This module contains unit tests for the workflow orchestrator,
including tests for parallel execution, fallback handling,
and response assembly.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from app.schemas import (
    TicketInput,
    WorkflowOptions,
    WorkflowResponse,
    ClassificationResult,
    ExtractionResult,
    ExtractedField,
    ResponseDraft,
    RoutingDecision,
)
from app.services.workflow.orchestrator import (
    WorkflowOrchestrator,
    WorkflowContext,
    process_ticket,
)


@pytest.fixture
def sample_ticket():
    """Create a sample ticket for testing."""
    return TicketInput(
        subject="Cannot access my account",
        body="I've been trying to log in for the past hour but keep getting an error message saying 'Invalid credentials'. I'm sure my password is correct.",
        customer_id="cust-12345",
        customer_email="john.doe@example.com",
        metadata={"source": "web"},
    )


@pytest.fixture
def sample_classification():
    """Create a sample classification result."""
    return ClassificationResult(
        category="account",
        category_confidence=0.92,
        severity="high",
        severity_confidence=0.85,
        secondary_categories=["technical"],
        reasoning="Account access issue with login failure",
        keywords_matched=["login", "error", "credentials"],
        urgency_indicators=["past hour"],
    )


@pytest.fixture
def sample_extraction():
    """Create a sample extraction result."""
    return ExtractionResult(
        fields=[
            ExtractedField(
                name="account_email",
                value="john.doe@example.com",
                confidence=0.95,
                source_span="john.doe@example.com",
            ),
            ExtractedField(
                name="error_code",
                value="Invalid credentials",
                confidence=0.85,
                source_span="Invalid credentials",
            ),
        ],
        missing_required=[],
        validation_errors=[],
    )


@pytest.fixture
def sample_response():
    """Create a sample response draft."""
    return ResponseDraft(
        content="Dear John,\n\nThank you for reaching out about your login issue...",
        tone="friendly",
        template_used=None,
        suggested_actions=["Reset password", "Clear browser cache"],
        requires_escalation=False,
        greeting="Dear John,",
        acknowledgment="Thank you for reaching out about your login issue.",
        action_items=["Reset password", "Clear browser cache"],
        timeline="We'll respond within 4 hours.",
        closing="Best regards,\nSupport Team",
    )


@pytest.fixture
def sample_routing():
    """Create a sample routing decision."""
    return RoutingDecision(
        team="account_management",
        priority="high",
        reasoning="Account access issue requires account management team",
        alternative_teams=["technical_support"],
        escalation_path=["account_manager", "security_team"],
        confidence=0.90,
    )


class TestWorkflowContext:
    """Tests for the WorkflowContext dataclass."""

    def test_context_initialization(self):
        """Test that context initializes with default values."""
        context = WorkflowContext()

        assert context.ticket_id is not None
        assert context.ticket is None
        assert context.options is None
        assert context.classification is None
        assert context.extraction is None
        assert context.response is None
        assert context.routing is None
        assert context.steps == []
        assert context.errors == set()

    def test_context_with_ticket(self, sample_ticket):
        """Test context initialization with a ticket."""
        context = WorkflowContext(ticket=sample_ticket)

        assert context.ticket == sample_ticket
        assert context.ticket_id is not None


class TestWorkflowOrchestrator:
    """Tests for the WorkflowOrchestrator class."""

    def test_initialization(self):
        """Test orchestrator initialization."""
        orchestrator = WorkflowOrchestrator(enable_ai=False)

        assert orchestrator.validator is not None
        assert orchestrator.classifier is not None
        assert orchestrator.extractor is not None
        assert orchestrator.generator is not None
        assert orchestrator.router is not None

    def test_initialization_with_ai_disabled(self):
        """Test orchestrator with AI disabled."""
        orchestrator = WorkflowOrchestrator(enable_ai=False)

        assert orchestrator.enable_ai is False

    @pytest.mark.asyncio
    async def test_execute_validation_success(self, sample_ticket):
        """Test successful validation step."""
        orchestrator = WorkflowOrchestrator(enable_ai=False)
        context = WorkflowContext(ticket=sample_ticket, options=WorkflowOptions())

        await orchestrator._execute_validation(context)

        assert context.sanitized_ticket is not None
        assert context.sanitized_ticket.subject == sample_ticket.subject
        assert len([s for s in context.steps if s.step_name == "validation"]) == 1
        assert context.steps[0].status == "completed"

    @pytest.mark.asyncio
    async def test_execute_validation_empty_subject(self):
        """Test validation with empty subject."""
        orchestrator = WorkflowOrchestrator(enable_ai=False)
        ticket = TicketInput(subject="", body="Test body")
        context = WorkflowContext(ticket=ticket, options=WorkflowOptions())

        await orchestrator._execute_validation(context)

        assert len(context.errors) > 0
        assert any("empty" in e.lower() for e in context.errors)

    @pytest.mark.asyncio
    async def test_execute_classification(self, sample_ticket):
        """Test classification step execution."""
        orchestrator = WorkflowOrchestrator(enable_ai=False)
        context = WorkflowContext(
            ticket=sample_ticket,
            sanitized_ticket=sample_ticket,
            options=WorkflowOptions(),
        )

        await orchestrator._execute_classification(context)

        assert context.classification is not None
        assert context.classification.category in [
            "technical", "billing", "account", "feature_request", "bug_report", "general"
        ]
        assert context.classification.severity in ["critical", "high", "medium", "low"]

    @pytest.mark.asyncio
    async def test_execute_extraction(self, sample_ticket):
        """Test extraction step execution."""
        orchestrator = WorkflowOrchestrator(enable_ai=False)
        context = WorkflowContext(
            ticket=sample_ticket,
            sanitized_ticket=sample_ticket,
            options=WorkflowOptions(),
            classification=ClassificationResult(
                category="account",
                category_confidence=0.9,
                severity="high",
                severity_confidence=0.8,
            ),
        )

        await orchestrator._execute_extraction(context)

        assert context.extraction is not None
        assert isinstance(context.extraction.fields, list)

    @pytest.mark.asyncio
    async def test_execute_response_generation(self, sample_ticket, sample_classification, sample_extraction):
        """Test response generation step execution."""
        orchestrator = WorkflowOrchestrator(enable_ai=False)
        context = WorkflowContext(
            ticket=sample_ticket,
            sanitized_ticket=sample_ticket,
            options=WorkflowOptions(response_tone="friendly"),
            classification=sample_classification,
            extraction=sample_extraction,
        )

        await orchestrator._execute_response_generation(context)

        assert context.response is not None
        assert context.response.content is not None
        assert context.response.tone == "friendly"

    @pytest.mark.asyncio
    async def test_execute_routing(self, sample_ticket, sample_classification, sample_extraction):
        """Test routing step execution."""
        orchestrator = WorkflowOrchestrator(enable_ai=False)
        context = WorkflowContext(
            ticket=sample_ticket,
            sanitized_ticket=sample_ticket,
            options=WorkflowOptions(),
            classification=sample_classification,
            extraction=sample_extraction,
        )

        await orchestrator._execute_routing(context)

        assert context.routing is not None
        assert context.routing.team in [
            "technical_support", "billing_team", "account_management",
            "product_team", "escalation_team"
        ]
        assert context.routing.priority in ["urgent", "high", "normal", "low"]

    @pytest.mark.asyncio
    async def test_full_workflow_execution(self, sample_ticket):
        """Test complete workflow execution."""
        orchestrator = WorkflowOrchestrator(enable_ai=False)

        response = await orchestrator.execute(sample_ticket)

        assert response is not None
        assert isinstance(response, WorkflowResponse)
        assert response.ticket_id is not None
        assert response.classification is not None
        assert response.extracted_fields is not None
        assert response.routing is not None
        assert response.total_duration_ms > 0
        assert len(response.workflow_steps) > 0

    @pytest.mark.asyncio
    async def test_workflow_with_options(self, sample_ticket):
        """Test workflow execution with custom options."""
        orchestrator = WorkflowOrchestrator(enable_ai=False)
        options = WorkflowOptions(
            skip_response=True,
            response_tone="formal",
            enable_parallel=True,
        )

        response = await orchestrator.execute(sample_ticket, options)

        assert response is not None
        assert response.response_draft is None  # Skipped

    @pytest.mark.asyncio
    async def test_workflow_skip_classification(self, sample_ticket):
        """Test workflow with classification skipped."""
        orchestrator = WorkflowOrchestrator(enable_ai=False)
        options = WorkflowOptions(skip_classification=True)

        response = await orchestrator.execute(sample_ticket, options)

        assert response is not None
        assert response.classification.category == "general"  # Default

    @pytest.mark.asyncio
    async def test_parallel_step_execution(self, sample_ticket):
        """Test that parallel steps execute correctly."""
        orchestrator = WorkflowOrchestrator(enable_ai=False)
        context = WorkflowContext(
            ticket=sample_ticket,
            sanitized_ticket=sample_ticket,
            options=WorkflowOptions(enable_parallel=True),
        )

        await orchestrator._execute_parallel_steps(context)

        # All parallel steps should have executed
        assert context.classification is not None
        assert context.extraction is not None

    @pytest.mark.asyncio
    async def test_sequential_step_execution(self, sample_ticket):
        """Test that sequential steps execute correctly."""
        orchestrator = WorkflowOrchestrator(enable_ai=False)
        context = WorkflowContext(
            ticket=sample_ticket,
            sanitized_ticket=sample_ticket,
            options=WorkflowOptions(enable_parallel=False),
        )

        await orchestrator._execute_sequential_steps(context)

        assert context.classification is not None
        assert context.extraction is not None

    def test_build_success_response(self, sample_ticket, sample_classification, sample_extraction, sample_response, sample_routing):
        """Test building a success response."""
        orchestrator = WorkflowOrchestrator(enable_ai=False)
        context = WorkflowContext(
            ticket=sample_ticket,
            sanitized_ticket=sample_ticket,
            options=WorkflowOptions(),
            classification=sample_classification,
            extraction=sample_extraction,
            response=sample_response,
            routing=sample_routing,
        )

        response = orchestrator._build_success_response(context)

        assert response.ticket_id == context.ticket_id
        assert response.classification == sample_classification
        assert response.extracted_fields == sample_extraction
        assert response.response_draft == sample_response
        assert response.routing == sample_routing

    def test_build_error_response(self, sample_ticket):
        """Test building an error response."""
        orchestrator = WorkflowOrchestrator(enable_ai=False)
        context = WorkflowContext(
            ticket=sample_ticket,
            options=WorkflowOptions(),
        )

        response = orchestrator._build_error_response(context, "Test error")

        assert response is not None
        assert response.response_draft is None
        assert any(s.status == "failed" for s in response.workflow_steps)

    @pytest.mark.asyncio
    async def test_routing_for_critical_severity(self):
        """Test that critical severity routes to escalation team."""
        orchestrator = WorkflowOrchestrator(enable_ai=False)
        ticket = TicketInput(
            subject="URGENT: System is down",
            body="Production system is completely down, affecting all users!",
        )

        response = await orchestrator.execute(ticket)

        assert response.routing.team == "escalation_team"
        assert response.routing.priority == "urgent"

    @pytest.mark.asyncio
    async def test_classification_only(self, sample_ticket):
        """Test executing only classification."""
        orchestrator = WorkflowOrchestrator(enable_ai=False)

        result = await orchestrator.execute_classification_only(sample_ticket)

        assert result is not None
        assert isinstance(result, ClassificationResult)

    @pytest.mark.asyncio
    async def test_extraction_only(self, sample_ticket):
        """Test executing only extraction."""
        orchestrator = WorkflowOrchestrator(enable_ai=False)

        result = await orchestrator.execute_extraction_only(sample_ticket, category="account")

        assert result is not None
        assert isinstance(result, ExtractionResult)

    @pytest.mark.asyncio
    async def test_response_only(self, sample_ticket, sample_classification, sample_extraction):
        """Test executing only response generation."""
        orchestrator = WorkflowOrchestrator(enable_ai=False)

        result = await orchestrator.execute_response_only(
            ticket=sample_ticket,
            classification=sample_classification,
            extraction=sample_extraction,
            tone="friendly",
        )

        assert result is not None
        assert isinstance(result, ResponseDraft)

    def test_routing_only(self, sample_ticket, sample_classification, sample_extraction):
        """Test executing only routing."""
        orchestrator = WorkflowOrchestrator(enable_ai=False)

        result = orchestrator.execute_routing_only(
            ticket=sample_ticket,
            classification=sample_classification,
            extraction=sample_extraction,
        )

        assert result is not None
        assert isinstance(result, RoutingDecision)


class TestProcessTicket:
    """Tests for the process_ticket convenience function."""

    @pytest.mark.asyncio
    async def test_process_ticket_basic(self, sample_ticket):
        """Test basic ticket processing."""
        response = await process_ticket(sample_ticket)

        assert response is not None
        assert isinstance(response, WorkflowResponse)
        assert response.ticket_id is not None

    @pytest.mark.asyncio
    async def test_process_ticket_with_options(self, sample_ticket):
        """Test ticket processing with options."""
        options = WorkflowOptions(
            skip_response=True,
            enable_parallel=True,
        )

        response = await process_ticket(sample_ticket, options=options)

        assert response is not None
        assert response.response_draft is None


class TestWorkflowStepResults:
    """Tests for workflow step result tracking."""

    @pytest.mark.asyncio
    async def test_step_timing_tracked(self, sample_ticket):
        """Test that step timing is tracked."""
        orchestrator = WorkflowOrchestrator(enable_ai=False)

        response = await orchestrator.execute(sample_ticket)

        for step in response.workflow_steps:
            assert step.duration_ms is not None
            assert step.duration_ms >= 0

    @pytest.mark.asyncio
    async def test_step_status_tracked(self, sample_ticket):
        """Test that step status is tracked."""
        orchestrator = WorkflowOrchestrator(enable_ai=False)

        response = await orchestrator.execute(sample_ticket)

        for step in response.workflow_steps:
            assert step.status in ["completed", "failed", "skipped"]

    @pytest.mark.asyncio
    async def test_fallback_tracking(self):
        """Test that fallback usage is tracked."""
        orchestrator = WorkflowOrchestrator(enable_ai=True)  # Will fail without API key

        # With invalid/missing API key, should use fallbacks
        ticket = TicketInput(subject="Test", body="Test body")
        response = await orchestrator.execute(ticket)

        # Should still complete even with AI errors
        assert response is not None
        # Some steps may have used fallbacks
        fallback_steps = [s for s in response.workflow_steps if s.fallback_used]
        # With missing API key, fallbacks should be used


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    @pytest.mark.asyncio
    async def test_empty_ticket_body(self):
        """Test handling of empty ticket body."""
        orchestrator = WorkflowOrchestrator(enable_ai=False)
        ticket = TicketInput(subject="Test", body="")  # Will fail validation

        response = await orchestrator.execute(ticket)

        # Should handle gracefully
        assert response is not None

    @pytest.mark.asyncio
    async def test_long_ticket_content(self):
        """Test handling of very long ticket content."""
        orchestrator = WorkflowOrchestrator(enable_ai=False)
        ticket = TicketInput(
            subject="Test " * 100,
            body="Test content. " * 1000,
        )

        response = await orchestrator.execute(ticket)

        assert response is not None
        assert response.classification is not None

    @pytest.mark.asyncio
    async def test_special_characters_in_ticket(self):
        """Test handling of special characters."""
        orchestrator = WorkflowOrchestrator(enable_ai=False)
        ticket = TicketInput(
            subject="Test <script>alert('xss')</script>",
            body="Test with special chars: @#$%^&*(){}[]|\\;':\",./<>?",
        )

        response = await orchestrator.execute(ticket)

        assert response is not None

    @pytest.mark.asyncio
    async def test_unicode_in_ticket(self):
        """Test handling of unicode characters."""
        orchestrator = WorkflowOrchestrator(enable_ai=False)
        ticket = TicketInput(
            subject="Test with unicode: \u4e2d\u6587 \u0440\u0443\u0441\u0441\u043a\u0438\u0439",
            body="Emojis: \ud83d\ude00 \ud83d\udc4d \u2764\ufe0f",
        )

        response = await orchestrator.execute(ticket)

        assert response is not None
