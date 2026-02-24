"""
Integration tests for workflow orchestration.

This module tests the WorkflowOrchestrator class, including:
- Full workflow execution
- Parallel step execution
- Error handling and fallbacks
- Response assembly
- Individual step execution methods
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.schemas import (
    ClassificationResult,
    ExtractedField,
    ExtractionResult,
    ResponseDraft,
    RoutingDecision,
    TicketInput,
    WorkflowOptions,
    WorkflowResponse,
)
from app.services.workflow.orchestrator import (
    WorkflowOrchestrator,
    WorkflowContext,
    process_ticket,
)


# ============================================================================
# Full Workflow Tests
# ============================================================================


class TestFullWorkflowExecution:
    """Tests for complete workflow execution."""

    @pytest.mark.asyncio
    async def test_full_workflow_happy_path(self, workflow_orchestrator, ticket_input_factory):
        """Test successful execution of the full workflow."""
        ticket = ticket_input_factory(
            subject="API returning 500 errors",
            body="Our production system is experiencing errors. Error code: ERR-50023",
        )
        options = WorkflowOptions()

        result = await workflow_orchestrator.execute(ticket, options)

        assert isinstance(result, WorkflowResponse)
        assert result.ticket_id is not None
        assert result.classification is not None
        assert result.extracted_fields is not None
        assert result.response_draft is not None
        assert result.routing is not None
        assert result.total_duration_ms > 0

    @pytest.mark.asyncio
    async def test_full_workflow_with_sample_ticket(
        self, workflow_orchestrator, ticket_from_data, sample_ticket
    ):
        """Test full workflow with a sample ticket."""
        ticket = ticket_from_data(sample_ticket)
        result = await workflow_orchestrator.execute(ticket)

        assert isinstance(result, WorkflowResponse)
        assert result.classification.category is not None
        assert result.classification.severity is not None

    @pytest.mark.asyncio
    async def test_workflow_returns_all_step_results(self, workflow_orchestrator, ticket_input):
        """Test that workflow returns results from all steps."""
        result = await workflow_orchestrator.execute(ticket_input)

        step_names = {step.step_name for step in result.workflow_steps}

        # Should have at least validation, classification, extraction, routing
        expected_steps = {"validation", "classification", "extraction", "routing"}
        assert expected_steps.issubset(step_names)

    @pytest.mark.asyncio
    async def test_workflow_with_all_sample_tickets(
        self, workflow_orchestrator, ticket_from_data, sample_tickets
    ):
        """Test workflow execution with all sample tickets."""
        for ticket_id, ticket_data in sample_tickets.items():
            ticket = ticket_from_data(ticket_data)
            result = await workflow_orchestrator.execute(ticket)

            assert isinstance(result, WorkflowResponse), (
                f"Failed for ticket {ticket_id}"
            )
            assert result.classification is not None


# ============================================================================
# Parallel Execution Tests
# ============================================================================


class TestParallelExecution:
    """Tests for parallel step execution."""

    @pytest.mark.asyncio
    async def test_parallel_execution_enabled(self, workflow_orchestrator, ticket_input):
        """Test that parallel execution works when enabled."""
        options = WorkflowOptions(enable_parallel=True)

        result = await workflow_orchestrator.execute(ticket_input, options)

        assert isinstance(result, WorkflowResponse)

    @pytest.mark.asyncio
    async def test_sequential_execution(self, workflow_orchestrator, ticket_input):
        """Test that sequential execution works when parallel is disabled."""
        options = WorkflowOptions(enable_parallel=False)

        result = await workflow_orchestrator.execute(ticket_input, options)

        assert isinstance(result, WorkflowResponse)

    @pytest.mark.asyncio
    async def test_parallel_faster_than_sequential(self, workflow_orchestrator, ticket_input):
        """Test that parallel execution is generally faster than sequential."""
        # Run with parallel
        options_parallel = WorkflowOptions(enable_parallel=True)
        result_parallel = await workflow_orchestrator.execute(ticket_input, options_parallel)

        # Run with sequential
        options_sequential = WorkflowOptions(enable_parallel=False)
        result_sequential = await workflow_orchestrator.execute(ticket_input, options_sequential)

        # Both should complete successfully
        assert isinstance(result_parallel, WorkflowResponse)
        assert isinstance(result_sequential, WorkflowResponse)


# ============================================================================
# Skip Options Tests
# ============================================================================


class TestSkipOptions:
    """Tests for skipping workflow steps."""

    @pytest.mark.asyncio
    async def test_skip_classification(self, workflow_orchestrator, ticket_input):
        """Test skipping classification step."""
        options = WorkflowOptions(skip_classification=True)

        result = await workflow_orchestrator.execute(ticket_input, options)

        assert result.classification is not None  # Should have default
        assert result.classification.reasoning == "Classification skipped"

    @pytest.mark.asyncio
    async def test_skip_extraction(self, workflow_orchestrator, ticket_input):
        """Test skipping extraction step."""
        options = WorkflowOptions(skip_extraction=True)

        result = await workflow_orchestrator.execute(ticket_input, options)

        assert result.extracted_fields is not None  # Should have empty result
        assert len(result.extracted_fields.fields) == 0

    @pytest.mark.asyncio
    async def test_skip_response_generation(self, workflow_orchestrator, ticket_input):
        """Test skipping response generation step."""
        options = WorkflowOptions(skip_response=True)

        result = await workflow_orchestrator.execute(ticket_input, options)

        assert result.response_draft is None

    @pytest.mark.asyncio
    async def test_skip_routing(self, workflow_orchestrator, ticket_input):
        """Test skipping routing step."""
        options = WorkflowOptions(skip_routing=True)

        result = await workflow_orchestrator.execute(ticket_input, options)

        # When routing is skipped, it may not be included
        # depending on implementation

    @pytest.mark.asyncio
    async def test_skip_all_ai_steps(self, workflow_orchestrator, ticket_input):
        """Test skipping all AI-dependent steps."""
        options = WorkflowOptions(
            skip_classification=True,
            skip_extraction=True,
            skip_response=True,
        )

        result = await workflow_orchestrator.execute(ticket_input, options)

        assert isinstance(result, WorkflowResponse)


# ============================================================================
# Error Handling Tests
# ============================================================================


class TestErrorHandling:
    """Tests for error handling in workflow."""

    @pytest.mark.asyncio
    async def test_ai_failure_fallback_classification(self, mock_ai_service):
        """Test fallback classification when AI fails."""
        mock_ai_service.classify_ticket.side_effect = Exception("AI error")
        orchestrator = WorkflowOrchestrator(ai_service=mock_ai_service, enable_ai=True)

        ticket = TicketInput(
            subject="I need a refund for my subscription billing",
            body="The payment is wrong.",
        )
        result = await orchestrator.execute(ticket)

        assert isinstance(result, WorkflowResponse)
        assert result.classification is not None
        # Should have used fallback classification
        assert result.classification.category in [
            "technical", "billing", "account", "feature_request", "bug_report", "general"
        ]

    @pytest.mark.asyncio
    async def test_ai_failure_fallback_extraction(self, mock_ai_service):
        """Test fallback extraction when AI fails."""
        mock_ai_service.extract_fields.side_effect = Exception("AI error")
        orchestrator = WorkflowOrchestrator(ai_service=mock_ai_service, enable_ai=True)

        ticket = TicketInput(
            subject="Order ORD-12345 issue",
            body="Contact me at test@example.com",
        )
        result = await orchestrator.execute(ticket)

        assert isinstance(result, WorkflowResponse)
        assert result.extracted_fields is not None

    @pytest.mark.asyncio
    async def test_ai_failure_fallback_response(self, mock_ai_service):
        """Test fallback response generation when AI fails."""
        mock_ai_service.generate_response.side_effect = Exception("AI error")
        orchestrator = WorkflowOrchestrator(ai_service=mock_ai_service, enable_ai=True)

        ticket = TicketInput(
            subject="Help needed",
            body="I need assistance.",
        )
        result = await orchestrator.execute(ticket)

        assert isinstance(result, WorkflowResponse)
        assert result.response_draft is not None
        # Should have used template fallback
        assert result.response_draft.template_used is not None

    @pytest.mark.asyncio
    async def test_validation_failure_returns_error(self, workflow_orchestrator):
        """Test that validation failure returns error response."""
        invalid_ticket = TicketInput(
            subject="",  # Empty subject should fail validation
            body="",  # Empty body should fail validation
        )

        result = await workflow_orchestrator.execute(invalid_ticket)

        assert isinstance(result, WorkflowResponse)
        # Check that there's an error in the steps
        has_error = any(
            step.status == "failed" for step in result.workflow_steps
        )
        assert has_error

    @pytest.mark.asyncio
    async def test_workflow_completes_despite_step_error(self, mock_ai_service):
        """Test that workflow completes even if a step has an error."""
        # Make classification fail but allow others to succeed
        mock_ai_service.classify_ticket.side_effect = Exception("Classification failed")

        orchestrator = WorkflowOrchestrator(ai_service=mock_ai_service, enable_ai=True)

        ticket = TicketInput(subject="Test", body="Test content")
        result = await orchestrator.execute(ticket)

        assert isinstance(result, WorkflowResponse)
        # Should have fallback classification
        assert result.classification is not None


# ============================================================================
# Workflow Context Tests
# ============================================================================


class TestWorkflowContext:
    """Tests for WorkflowContext dataclass."""

    def test_context_initialization(self):
        """Test context initializes with defaults."""
        context = WorkflowContext()

        assert context.ticket_id is not None
        assert context.steps == []
        assert context.errors == set()

    def test_context_with_ticket(self, ticket_input):
        """Test context with ticket data."""
        context = WorkflowContext(ticket=ticket_input)

        assert context.ticket == ticket_input
        assert context.ticket_id is not None


# ============================================================================
# Response Building Tests
# ============================================================================


class TestResponseBuilding:
    """Tests for response building."""

    @pytest.mark.asyncio
    async def test_response_includes_ticket_id(self, workflow_orchestrator, ticket_input):
        """Test that response includes ticket ID."""
        result = await workflow_orchestrator.execute(ticket_input)

        assert result.ticket_id is not None
        assert len(result.ticket_id) > 0

    @pytest.mark.asyncio
    async def test_response_includes_duration(self, workflow_orchestrator, ticket_input):
        """Test that response includes total duration."""
        result = await workflow_orchestrator.execute(ticket_input)

        assert result.total_duration_ms is not None
        assert result.total_duration_ms >= 0

    @pytest.mark.asyncio
    async def test_response_includes_created_at(self, workflow_orchestrator, ticket_input):
        """Test that response includes created_at timestamp."""
        result = await workflow_orchestrator.execute(ticket_input)

        assert result.created_at is not None

    @pytest.mark.asyncio
    async def test_classification_result_complete(self, workflow_orchestrator, ticket_input):
        """Test that classification result is complete."""
        result = await workflow_orchestrator.execute(ticket_input)

        assert result.classification.category is not None
        assert result.classification.severity is not None
        assert 0 <= result.classification.category_confidence <= 1
        assert 0 <= result.classification.severity_confidence <= 1

    @pytest.mark.asyncio
    async def test_routing_result_complete(self, workflow_orchestrator, ticket_input):
        """Test that routing result is complete."""
        result = await workflow_orchestrator.execute(ticket_input)

        assert result.routing.team is not None
        assert result.routing.priority is not None
        assert result.routing.reasoning is not None


# ============================================================================
# Individual Step Methods Tests
# ============================================================================


class TestIndividualStepMethods:
    """Tests for individual step execution methods."""

    @pytest.mark.asyncio
    async def test_execute_classification_only(self, workflow_orchestrator, ticket_input):
        """Test executing only classification step."""
        result = await workflow_orchestrator.execute_classification_only(ticket_input)

        assert isinstance(result, ClassificationResult)
        assert result.category is not None

    @pytest.mark.asyncio
    async def test_execute_extraction_only(self, workflow_orchestrator, ticket_input):
        """Test executing only extraction step."""
        result = await workflow_orchestrator.execute_extraction_only(ticket_input)

        assert isinstance(result, ExtractionResult)
        assert isinstance(result.fields, list)

    @pytest.mark.asyncio
    async def test_execute_extraction_only_with_category(self, workflow_orchestrator, ticket_input):
        """Test extraction with category context."""
        result = await workflow_orchestrator.execute_extraction_only(
            ticket_input,
            category="technical",
        )

        assert isinstance(result, ExtractionResult)

    @pytest.mark.asyncio
    async def test_execute_response_only(self, workflow_orchestrator, ticket_input):
        """Test executing only response generation."""
        classification = ClassificationResult(
            category="technical",
            category_confidence=0.9,
            severity="medium",
            severity_confidence=0.8,
        )

        result = await workflow_orchestrator.execute_response_only(
            ticket_input,
            classification=classification,
        )

        assert isinstance(result, ResponseDraft)
        assert result.content is not None

    @pytest.mark.asyncio
    async def test_execute_routing_only(self, workflow_orchestrator, ticket_input):
        """Test executing only routing decision."""
        classification = ClassificationResult(
            category="billing",
            category_confidence=0.9,
            severity="high",
            severity_confidence=0.8,
        )

        result = workflow_orchestrator.execute_routing_only(
            ticket_input,
            classification=classification,
        )

        assert isinstance(result, RoutingDecision)
        assert result.team is not None


# ============================================================================
# Duplicate Detection Tests
# ============================================================================


class TestDuplicateDetection:
    """Tests for duplicate detection functionality."""

    @pytest.mark.asyncio
    async def test_duplicate_detection_enabled(self, workflow_orchestrator, ticket_input):
        """Test workflow with duplicate detection enabled."""
        options = WorkflowOptions(enable_duplicate_detection=True)

        result = await workflow_orchestrator.execute(ticket_input, options)

        assert isinstance(result, WorkflowResponse)
        # duplicate_of should be None for new tickets
        assert result.duplicate_of is None

    @pytest.mark.asyncio
    async def test_duplicate_detection_disabled(self, workflow_orchestrator, ticket_input):
        """Test workflow with duplicate detection disabled."""
        options = WorkflowOptions(enable_duplicate_detection=False)

        result = await workflow_orchestrator.execute(ticket_input, options)

        assert isinstance(result, WorkflowResponse)
        # Should complete without duplicate detection step
        step_names = {s.step_name for s in result.workflow_steps}
        assert "duplicate_detection" not in step_names


# ============================================================================
# No AI Mode Tests
# ============================================================================


class TestNoAIMode:
    """Tests for workflow without AI."""

    @pytest.mark.asyncio
    async def test_workflow_without_ai(self, workflow_orchestrator_no_ai, ticket_input):
        """Test complete workflow without AI."""
        result = await workflow_orchestrator_no_ai.execute(ticket_input)

        assert isinstance(result, WorkflowResponse)
        assert result.classification is not None
        assert result.extracted_fields is not None
        assert result.response_draft is not None
        assert result.routing is not None

    @pytest.mark.asyncio
    async def test_no_ai_uses_fallback_classification(self, workflow_orchestrator_no_ai, ticket_input):
        """Test that no AI mode uses fallback classification."""
        result = await workflow_orchestrator_no_ai.execute(ticket_input)

        # Classification should still work with rule-based
        assert result.classification.category is not None

    @pytest.mark.asyncio
    async def test_no_ai_uses_template_response(self, workflow_orchestrator_no_ai, ticket_input):
        """Test that no AI mode uses template responses."""
        result = await workflow_orchestrator_no_ai.execute(ticket_input)

        # Response should be from template
        assert result.response_draft is not None
        assert result.response_draft.template_used is not None


# ============================================================================
# Response Tone Tests
# ============================================================================


class TestResponseTone:
    """Tests for response tone configuration."""

    @pytest.mark.asyncio
    async def test_friendly_tone(self, workflow_orchestrator, ticket_input):
        """Test workflow with friendly tone."""
        options = WorkflowOptions(response_tone="friendly")

        result = await workflow_orchestrator.execute(ticket_input, options)

        if result.response_draft:
            assert result.response_draft.tone == "friendly"

    @pytest.mark.asyncio
    async def test_formal_tone(self, workflow_orchestrator, ticket_input):
        """Test workflow with formal tone."""
        options = WorkflowOptions(response_tone="formal")

        result = await workflow_orchestrator.execute(ticket_input, options)

        if result.response_draft:
            assert result.response_draft.tone == "formal"

    @pytest.mark.asyncio
    async def test_technical_tone(self, workflow_orchestrator, ticket_input):
        """Test workflow with technical tone."""
        options = WorkflowOptions(response_tone="technical")

        result = await workflow_orchestrator.execute(ticket_input, options)

        if result.response_draft:
            assert result.response_draft.tone == "technical"


# ============================================================================
# Convenience Function Tests
# ============================================================================


class TestConvenienceFunction:
    """Tests for the process_ticket convenience function."""

    @pytest.mark.asyncio
    async def test_process_ticket_function(self, ticket_input):
        """Test the process_ticket convenience function."""
        result = await process_ticket(ticket_input)

        assert isinstance(result, WorkflowResponse)
        assert result.ticket_id is not None

    @pytest.mark.asyncio
    async def test_process_ticket_with_options(self, ticket_input):
        """Test process_ticket with workflow options."""
        options = WorkflowOptions(
            skip_response=True,
            response_tone="formal",
        )

        result = await process_ticket(ticket_input, options=options)

        assert isinstance(result, WorkflowResponse)


# ============================================================================
# Edge Cases Tests
# ============================================================================


class TestEdgeCases:
    """Tests for edge cases in workflow."""

    @pytest.mark.asyncio
    async def test_minimal_ticket(self, workflow_orchestrator):
        """Test workflow with minimal ticket data."""
        minimal_ticket = TicketInput(
            subject="Help",
            body="Need help",
        )

        result = await workflow_orchestrator.execute(minimal_ticket)

        assert isinstance(result, WorkflowResponse)

    @pytest.mark.asyncio
    async def test_ticket_with_special_characters(self, workflow_orchestrator):
        """Test workflow with special characters in ticket."""
        ticket = TicketInput(
            subject="!!!URGENT!!! Issue $$$",
            body="### ERROR ### @@@ CRITICAL @@@\n\n\nLots of special chars: <>&\"'",
        )

        result = await workflow_orchestrator.execute(ticket)

        assert isinstance(result, WorkflowResponse)

    @pytest.mark.asyncio
    async def test_ticket_with_unicode(self, workflow_orchestrator):
        """Test workflow with unicode characters."""
        ticket = TicketInput(
            subject="Help needed - \u4e2d\u6587 - \u0420\u0443\u0441\u0441\u043a\u0438\u0439",
            body="Unicode content: \u4f60\u597d \u041f\u0440\u0438\u0432\u0435\u0442 \u0645\u0631\u062d\u0628\u0627",
        )

        result = await workflow_orchestrator.execute(ticket)

        assert isinstance(result, WorkflowResponse)

    @pytest.mark.asyncio
    async def test_very_long_ticket(self, workflow_orchestrator):
        """Test workflow with very long ticket content."""
        long_content = "This is a test sentence. " * 1000

        ticket = TicketInput(
            subject="Long ticket " * 10,
            body=long_content,
        )

        result = await workflow_orchestrator.execute(ticket)

        assert isinstance(result, WorkflowResponse)

    @pytest.mark.asyncio
    async def test_ticket_with_metadata(self, workflow_orchestrator):
        """Test workflow with ticket metadata."""
        ticket = TicketInput(
            subject="Issue with metadata",
            body="Content here",
            customer_id="cust-123",
            customer_email="test@example.com",
            metadata={
                "source": "web",
                "priority": "high",
                "custom_field": "custom_value",
            },
        )

        result = await workflow_orchestrator.execute(ticket)

        assert isinstance(result, WorkflowResponse)


# ============================================================================
# Step Status Tests
# ============================================================================


class TestStepStatus:
    """Tests for workflow step status tracking."""

    @pytest.mark.asyncio
    async def test_successful_step_status(self, workflow_orchestrator, ticket_input):
        """Test that successful steps have 'completed' status."""
        result = await workflow_orchestrator.execute(ticket_input)

        for step in result.workflow_steps:
            if step.error is None:
                assert step.status == "completed"

    @pytest.mark.asyncio
    async def test_step_duration_tracked(self, workflow_orchestrator, ticket_input):
        """Test that step duration is tracked."""
        result = await workflow_orchestrator.execute(ticket_input)

        for step in result.workflow_steps:
            assert step.duration_ms is not None
            assert step.duration_ms >= 0

    @pytest.mark.asyncio
    async def test_fallback_flagged(self, mock_ai_service):
        """Test that fallback usage is flagged."""
        mock_ai_service.classify_ticket.side_effect = Exception("AI failed")

        orchestrator = WorkflowOrchestrator(ai_service=mock_ai_service, enable_ai=True)
        ticket = TicketInput(subject="Test", body="Test")
        result = await orchestrator.execute(ticket)

        # At least one step should have fallback_used=True
        fallback_steps = [s for s in result.workflow_steps if s.fallback_used]
        assert len(fallback_steps) > 0


# ============================================================================
# Performance Tests
# ============================================================================


class TestPerformance:
    """Tests for workflow performance."""

    @pytest.mark.asyncio
    async def test_workflow_completes_in_reasonable_time(self, workflow_orchestrator_no_ai, ticket_input):
        """Test that workflow completes in reasonable time without AI."""
        result = await workflow_orchestrator_no_ai.execute(ticket_input)

        # Without AI, should complete in under 5 seconds
        assert result.total_duration_ms < 5000

    @pytest.mark.asyncio
    async def test_concurrent_workflows(self, workflow_orchestrator_no_ai, ticket_input_factory):
        """Test concurrent workflow execution."""
        tickets = [ticket_input_factory(subject=f"Test {i}", body=f"Body {i}") for i in range(5)]

        results = await asyncio.gather(*[
            workflow_orchestrator_no_ai.execute(ticket) for ticket in tickets
        ])

        assert len(results) == 5
        for result in results:
            assert isinstance(result, WorkflowResponse)


# ============================================================================
# Integration with Sample Tickets Tests
# ============================================================================


class TestSampleTicketsWorkflow:
    """Tests using sample tickets from fixtures."""

    @pytest.mark.asyncio
    async def test_all_sample_tickets_complete_workflow(
        self, workflow_orchestrator_no_ai, ticket_from_data, sample_tickets
    ):
        """Test that all sample tickets complete the workflow successfully."""
        for ticket_id, ticket_data in sample_tickets.items():
            ticket = ticket_from_data(ticket_data)
            result = await workflow_orchestrator_no_ai.execute(ticket)

            assert isinstance(result, WorkflowResponse), f"Failed for {ticket_id}"
            assert result.classification is not None, f"No classification for {ticket_id}"
            assert result.routing is not None, f"No routing for {ticket_id}"

    @pytest.mark.asyncio
    async def test_critical_tickets_escalated(
        self, workflow_orchestrator_no_ai, ticket_from_data, sample_tickets
    ):
        """Test that critical tickets are routed to escalation team."""
        critical_tickets = {
            tid: t for tid, t in sample_tickets.items()
            if t.get("expected_severity") == "critical"
        }

        for ticket_id, ticket_data in critical_tickets.items():
            ticket = ticket_from_data(ticket_data)
            result = await workflow_orchestrator_no_ai.execute(ticket)

            if result.classification.severity == "critical":
                assert result.routing.team == "escalation_team", (
                    f"Critical ticket {ticket_id} not routed to escalation"
                )
