"""
Workflow Orchestrator for support ticket processing.

This module provides the WorkflowOrchestrator class that coordinates
all workflow steps including validation, classification, extraction,
response generation, and routing.
"""

import asyncio
import logging
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Set

from app.core.config import settings
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
from app.services.workflow.routers import TicketRouter
from app.services.workflow.validators import InputValidator, ValidationResult

logger = logging.getLogger(__name__)


@dataclass
class WorkflowContext:
    """
    Context object passed between workflow steps.

    Attributes:
        ticket_id: Unique identifier for this workflow execution
        ticket: Original ticket input
        options: Workflow execution options
        sanitized_ticket: Sanitized ticket after validation
        classification: Classification result
        extraction: Field extraction result
        response: Generated response draft
        routing: Routing decision
        duplicate_of: ID of duplicate ticket if detected
        similarity_score: Similarity score for duplicate detection
        steps: List of workflow step results
        start_time: Workflow start timestamp
        errors: Set of errors encountered during execution
    """

    ticket_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    ticket: Optional[TicketInput] = None
    options: Optional[WorkflowOptions] = None
    sanitized_ticket: Optional[TicketInput] = None
    classification: Optional[ClassificationResult] = None
    extraction: Optional[ExtractionResult] = None
    response: Optional[ResponseDraft] = None
    routing: Optional[RoutingDecision] = None
    duplicate_of: Optional[str] = None
    similarity_score: Optional[float] = None
    steps: List[WorkflowStepResult] = field(default_factory=list)
    start_time: float = field(default_factory=time.time)
    errors: Set[str] = field(default_factory=set)


class WorkflowOrchestrator:
    """
    Orchestrates the complete workflow for processing support tickets.

    This class coordinates all workflow steps:
    1. Input validation
    2. Duplicate detection (parallel)
    3. Classification (AI call)
    4. Field extraction (AI call - parallel with step 3)
    5. Response generation (AI call)
    6. Routing decision (rule-based)
    7. Response assembly

    Attributes:
        ai_service: AIService instance for LLM operations
        validator: InputValidator for ticket validation
        classifier: TicketClassifier for classification
        extractor: FieldExtractor for field extraction
        generator: ResponseGenerator for response generation
        router: TicketRouter for routing decisions
    """

    def __init__(
        self,
        ai_service: Optional[AIService] = None,
        enable_ai: bool = True,
    ):
        """
        Initialize the workflow orchestrator.

        Args:
            ai_service: Optional AIService instance (created if not provided)
            enable_ai: Whether to enable AI features
        """
        self.ai_service = ai_service or AIService()
        self.enable_ai = enable_ai

        # Initialize workflow components
        self.validator = InputValidator()
        self.classifier = TicketClassifier(ai_service=self.ai_service if enable_ai else None)
        self.extractor = FieldExtractor(ai_service=self.ai_service if enable_ai else None)
        self.generator = ResponseGenerator(ai_service=self.ai_service if enable_ai else None)
        self.router = TicketRouter()

        logger.info(
            f"WorkflowOrchestrator initialized with AI {'enabled' if enable_ai else 'disabled'}"
        )

    async def execute(
        self,
        ticket: TicketInput,
        options: Optional[WorkflowOptions] = None,
    ) -> WorkflowResponse:
        """
        Execute the complete workflow for a support ticket.

        This method orchestrates all workflow steps with parallel execution
        where possible and graceful error handling.

        Args:
            ticket: The ticket input to process
            options: Optional workflow execution options

        Returns:
            WorkflowResponse with all processing results
        """
        # Initialize context
        options = options or WorkflowOptions()
        context = WorkflowContext(
            ticket=ticket,
            options=options,
        )

        logger.info(f"Starting workflow execution for ticket {context.ticket_id}")

        try:
            # Step 1: Input validation
            await self._execute_validation(context)

            # Check if validation failed
            if context.errors and not context.sanitized_ticket:
                return self._build_error_response(context, "Validation failed")

            # Step 2 & 3 & 4: Parallel execution of duplicate detection, classification, and extraction
            if options.enable_parallel:
                await self._execute_parallel_steps(context)
            else:
                await self._execute_sequential_steps(context)

            # Step 5: Response generation
            if not options.skip_response:
                await self._execute_response_generation(context)

            # Step 6: Routing decision
            if not options.skip_routing:
                await self._execute_routing(context)

            # Step 7: Build final response
            return self._build_success_response(context)

        except asyncio.TimeoutError:
            logger.error(f"Workflow timeout for ticket {context.ticket_id}")
            return self._build_error_response(context, "Workflow execution timeout")
        except Exception as e:
            logger.exception(f"Workflow error for ticket {context.ticket_id}: {e}")
            return self._build_error_response(context, str(e))

    async def _execute_validation(self, context: WorkflowContext) -> None:
        """
        Execute input validation step.

        Args:
            context: Workflow context
        """
        step_name = "validation"
        step_start = time.time()

        try:
            result = self.validator.validate(context.ticket)

            if result.is_valid:
                context.sanitized_ticket = TicketInput(
                    subject=result.sanitized_subject or context.ticket.subject,
                    body=result.sanitized_body or context.ticket.body,
                    customer_id=context.ticket.customer_id,
                    customer_email=context.ticket.customer_email,
                    metadata=context.ticket.metadata,
                )

                self._add_step_result(
                    context,
                    step_name=step_name,
                    status="completed",
                    duration_ms=int((time.time() - step_start) * 1000),
                    warnings=result.warnings,
                )
            else:
                context.errors.update(result.errors)
                self._add_step_result(
                    context,
                    step_name=step_name,
                    status="failed",
                    duration_ms=int((time.time() - step_start) * 1000),
                    error="; ".join(result.errors),
                )

        except Exception as e:
            logger.error(f"Validation error: {e}")
            context.errors.add(str(e))
            self._add_step_result(
                context,
                step_name=step_name,
                status="failed",
                duration_ms=int((time.time() - step_start) * 1000),
                error=str(e),
            )

    async def _execute_parallel_steps(self, context: WorkflowContext) -> None:
        """
        Execute duplicate detection, classification, and extraction in parallel.

        Args:
            context: Workflow context
        """
        ticket = context.sanitized_ticket or context.ticket
        options = context.options

        # Build list of tasks to execute in parallel
        tasks = []

        # Duplicate detection
        if options.enable_duplicate_detection:
            tasks.append(self._execute_duplicate_detection(context))

        # Classification (if not skipped)
        if not options.skip_classification:
            tasks.append(self._execute_classification(context))
        else:
            # Use default classification if skipped
            context.classification = ClassificationResult(
                category="general",
                category_confidence=1.0,
                severity="medium",
                severity_confidence=1.0,
                reasoning="Classification skipped",
            )

        # Extraction (if not skipped)
        if not options.skip_extraction:
            tasks.append(self._execute_extraction(context))
        else:
            context.extraction = ExtractionResult()

        # Execute all tasks in parallel
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def _execute_sequential_steps(self, context: WorkflowContext) -> None:
        """
        Execute workflow steps sequentially.

        Args:
            context: Workflow context
        """
        options = context.options

        # Duplicate detection
        if options.enable_duplicate_detection:
            await self._execute_duplicate_detection(context)

        # Classification
        if not options.skip_classification:
            await self._execute_classification(context)
        else:
            context.classification = ClassificationResult(
                category="general",
                category_confidence=1.0,
                severity="medium",
                severity_confidence=1.0,
                reasoning="Classification skipped",
            )

        # Extraction
        if not options.skip_extraction:
            await self._execute_extraction(context)
        else:
            context.extraction = ExtractionResult()

    async def _execute_duplicate_detection(self, context: WorkflowContext) -> None:
        """
        Execute duplicate detection step.

        Args:
            context: Workflow context
        """
        step_name = "duplicate_detection"
        step_start = time.time()

        try:
            # Simple duplicate detection based on customer_id and similar content
            # In a real implementation, this would query the database
            is_duplicate, duplicate_of, similarity = await self._check_duplicate(context)

            if is_duplicate:
                context.duplicate_of = duplicate_of
                context.similarity_score = similarity

            self._add_step_result(
                context,
                step_name=step_name,
                status="completed",
                duration_ms=int((time.time() - step_start) * 1000),
            )

        except Exception as e:
            logger.warning(f"Duplicate detection error: {e}")
            # Don't fail the workflow for duplicate detection errors
            self._add_step_result(
                context,
                step_name=step_name,
                status="failed",
                duration_ms=int((time.time() - step_start) * 1000),
                error=str(e),
                fallback_used=True,
            )

    async def _check_duplicate(
        self, context: WorkflowContext
    ) -> tuple[bool, Optional[str], Optional[float]]:
        """
        Check if ticket is a duplicate.

        Args:
            context: Workflow context

        Returns:
            Tuple of (is_duplicate, duplicate_id, similarity_score)
        """
        # Placeholder implementation
        # In a real implementation, this would:
        # 1. Query database for recent tickets from same customer
        # 2. Compare content similarity using embeddings or text comparison
        # 3. Return match if similarity > threshold

        ticket = context.sanitized_ticket or context.ticket

        # For now, just check for exact subject match with same customer
        # This is a simplified placeholder
        if ticket.customer_id:
            # Would query database here
            pass

        return False, None, None

    async def _execute_classification(self, context: WorkflowContext) -> None:
        """
        Execute classification step.

        Args:
            context: Workflow context
        """
        step_name = "classification"
        step_start = time.time()

        try:
            ticket = context.sanitized_ticket or context.ticket

            context.classification = await self.classifier.classify(
                subject=ticket.subject,
                body=ticket.body,
                use_ai=self.enable_ai and settings.ENABLE_AI_CLASSIFICATION,
            )

            tokens_used = self.ai_service.token_usage.get("total", 0) if self.ai_service else None

            self._add_step_result(
                context,
                step_name=step_name,
                status="completed",
                duration_ms=int((time.time() - step_start) * 1000),
                tokens_used=tokens_used,
            )

        except Exception as e:
            logger.error(f"Classification error: {e}")

            # Use fallback classification
            context.classification = await self.classifier.classify(
                subject=context.ticket.subject,
                body=context.ticket.body,
                use_ai=False,
            )

            self._add_step_result(
                context,
                step_name=step_name,
                status="completed",
                duration_ms=int((time.time() - step_start) * 1000),
                error=str(e),
                fallback_used=True,
            )

    async def _execute_extraction(self, context: WorkflowContext) -> None:
        """
        Execute field extraction step.

        Args:
            context: Workflow context
        """
        step_name = "extraction"
        step_start = time.time()

        try:
            ticket = context.sanitized_ticket or context.ticket
            category = context.classification.category if context.classification else "general"

            context.extraction = await self.extractor.extract(
                subject=ticket.subject,
                body=ticket.body,
                category=category,
                use_ai=self.enable_ai and settings.ENABLE_AI_EXTRACTION,
            )

            tokens_used = self.ai_service.token_usage.get("total", 0) if self.ai_service else None

            self._add_step_result(
                context,
                step_name=step_name,
                status="completed",
                duration_ms=int((time.time() - step_start) * 1000),
                tokens_used=tokens_used,
            )

        except Exception as e:
            logger.error(f"Extraction error: {e}")

            # Use fallback extraction
            context.extraction = await self.extractor.extract(
                subject=context.ticket.subject,
                body=context.ticket.body,
                category="general",
                use_ai=False,
            )

            self._add_step_result(
                context,
                step_name=step_name,
                status="completed",
                duration_ms=int((time.time() - step_start) * 1000),
                error=str(e),
                fallback_used=True,
            )

    async def _execute_response_generation(self, context: WorkflowContext) -> None:
        """
        Execute response generation step.

        Args:
            context: Workflow context
        """
        step_name = "response_generation"
        step_start = time.time()

        try:
            ticket = context.sanitized_ticket or context.ticket
            classification = context.classification
            extraction = context.extraction

            # Extract customer name from ticket or extracted fields
            customer_name = ticket.customer_email.split("@")[0] if ticket.customer_email else None
            if extraction and extraction.fields:
                email_field = next(
                    (f for f in extraction.fields if f.name == "account_email"),
                    None,
                )
                if email_field and email_field.value:
                    customer_name = str(email_field.value).split("@")[0]

            context.response = await self.generator.generate(
                subject=ticket.subject,
                body=ticket.body,
                category=classification.category if classification else "general",
                severity=classification.severity if classification else "medium",
                extracted_fields=extraction.fields if extraction else [],
                customer_name=customer_name,
                tone=context.options.response_tone if context.options else "friendly",
                use_ai=self.enable_ai and settings.ENABLE_RESPONSE_GENERATION,
            )

            tokens_used = self.ai_service.token_usage.get("total", 0) if self.ai_service else None

            self._add_step_result(
                context,
                step_name=step_name,
                status="completed",
                duration_ms=int((time.time() - step_start) * 1000),
                tokens_used=tokens_used,
            )

        except Exception as e:
            logger.error(f"Response generation error: {e}")

            # Use fallback template response
            context.response = await self.generator.generate(
                subject=context.ticket.subject,
                body=context.ticket.body,
                category=context.classification.category if context.classification else "general",
                severity=context.classification.severity if context.classification else "medium",
                extracted_fields=[],
                customer_name=None,
                tone="friendly",
                use_ai=False,
            )

            self._add_step_result(
                context,
                step_name=step_name,
                status="completed",
                duration_ms=int((time.time() - step_start) * 1000),
                error=str(e),
                fallback_used=True,
            )

    async def _execute_routing(self, context: WorkflowContext) -> None:
        """
        Execute routing decision step.

        Args:
            context: Workflow context
        """
        step_name = "routing"
        step_start = time.time()

        try:
            ticket = context.sanitized_ticket or context.ticket
            classification = context.classification
            extraction = context.extraction

            # Convert extracted fields to dict for routing
            extracted_dict = {}
            if extraction and extraction.fields:
                for field in extraction.fields:
                    extracted_dict[field.name] = field.value

            context.routing = self.router.route(
                subject=ticket.subject,
                body=ticket.body,
                category=classification.category if classification else "general",
                severity=classification.severity if classification else "medium",
                extracted_fields=extracted_dict,
            )

            self._add_step_result(
                context,
                step_name=step_name,
                status="completed",
                duration_ms=int((time.time() - step_start) * 1000),
            )

        except Exception as e:
            logger.error(f"Routing error: {e}")

            # Use fallback routing
            context.routing = self.router.route(
                subject=context.ticket.subject,
                body=context.ticket.body,
                category="general",
                severity="medium",
                extracted_fields={},
            )

            self._add_step_result(
                context,
                step_name=step_name,
                status="completed",
                duration_ms=int((time.time() - step_start) * 1000),
                error=str(e),
                fallback_used=True,
            )

    def _add_step_result(
        self,
        context: WorkflowContext,
        step_name: str,
        status: str,
        duration_ms: int,
        error: Optional[str] = None,
        fallback_used: bool = False,
        tokens_used: Optional[int] = None,
        warnings: Optional[List[str]] = None,
    ) -> None:
        """
        Add a step result to the context.

        Args:
            context: Workflow context
            step_name: Name of the step
            status: Step status
            duration_ms: Duration in milliseconds
            error: Optional error message
            fallback_used: Whether fallback was used
            tokens_used: Optional token count
            warnings: Optional list of warnings
        """
        step_result = WorkflowStepResult(
            step_name=step_name,
            status=status,
            started_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
            duration_ms=duration_ms,
            error=error,
            fallback_used=fallback_used,
            tokens_used=tokens_used,
        )
        context.steps.append(step_result)

        # Log step completion
        log_level = logging.WARNING if fallback_used else logging.INFO
        logger.log(
            log_level,
            f"Step '{step_name}' {status} in {duration_ms}ms"
            + (" (fallback used)" if fallback_used else ""),
        )

    def _build_success_response(self, context: WorkflowContext) -> WorkflowResponse:
        """
        Build a successful workflow response.

        Args:
            context: Workflow context

        Returns:
            WorkflowResponse with all results
        """
        total_duration = int((time.time() - context.start_time) * 1000)

        return WorkflowResponse(
            ticket_id=context.ticket_id,
            classification=context.classification or ClassificationResult(
                category="general",
                category_confidence=0.5,
                severity="medium",
                severity_confidence=0.5,
                reasoning="Default classification",
            ),
            extracted_fields=context.extraction or ExtractionResult(),
            response_draft=context.response,
            routing=context.routing or RoutingDecision(
                team="technical_support",
                priority="normal",
                reasoning="Default routing",
                alternative_teams=[],
            ),
            duplicate_of=context.duplicate_of,
            similarity_score=context.similarity_score,
            workflow_steps=context.steps,
            total_duration_ms=total_duration,
            created_at=datetime.utcnow(),
        )

    def _build_error_response(
        self,
        context: WorkflowContext,
        error_message: str,
    ) -> WorkflowResponse:
        """
        Build an error workflow response.

        Args:
            context: Workflow context
            error_message: Error message

        Returns:
            WorkflowResponse with error information
        """
        total_duration = int((time.time() - context.start_time) * 1000)

        # Add error step if not already present
        if not any(s.step_name == "error" for s in context.steps):
            self._add_step_result(
                context,
                step_name="error",
                status="failed",
                duration_ms=0,
                error=error_message,
            )

        return WorkflowResponse(
            ticket_id=context.ticket_id,
            classification=context.classification or ClassificationResult(
                category="general",
                category_confidence=0.3,
                severity="medium",
                severity_confidence=0.3,
                reasoning=f"Error occurred: {error_message}",
            ),
            extracted_fields=context.extraction or ExtractionResult(),
            response_draft=None,
            routing=context.routing or RoutingDecision(
                team="technical_support",
                priority="normal",
                reasoning="Default routing due to error",
                alternative_teams=[],
            ),
            duplicate_of=None,
            similarity_score=None,
            workflow_steps=context.steps,
            total_duration_ms=total_duration,
            created_at=datetime.utcnow(),
        )

    async def execute_classification_only(
        self,
        ticket: TicketInput,
    ) -> ClassificationResult:
        """
        Execute only the classification step.

        Args:
            ticket: Ticket input

        Returns:
            ClassificationResult
        """
        return await self.classifier.classify(
            subject=ticket.subject,
            body=ticket.body,
            use_ai=self.enable_ai,
        )

    async def execute_extraction_only(
        self,
        ticket: TicketInput,
        category: Optional[str] = None,
    ) -> ExtractionResult:
        """
        Execute only the extraction step.

        Args:
            ticket: Ticket input
            category: Optional category for context

        Returns:
            ExtractionResult
        """
        return await self.extractor.extract(
            subject=ticket.subject,
            body=ticket.body,
            category=category,
            use_ai=self.enable_ai,
        )

    async def execute_response_only(
        self,
        ticket: TicketInput,
        classification: ClassificationResult,
        extraction: Optional[ExtractionResult] = None,
        tone: str = "friendly",
    ) -> ResponseDraft:
        """
        Execute only the response generation step.

        Args:
            ticket: Ticket input
            classification: Classification result
            extraction: Optional extraction result
            tone: Response tone

        Returns:
            ResponseDraft
        """
        return await self.generator.generate(
            subject=ticket.subject,
            body=ticket.body,
            category=classification.category,
            severity=classification.severity,
            extracted_fields=extraction.fields if extraction else [],
            customer_name=ticket.customer_email.split("@")[0] if ticket.customer_email else None,
            tone=tone,
            use_ai=self.enable_ai,
        )

    def execute_routing_only(
        self,
        ticket: TicketInput,
        classification: ClassificationResult,
        extraction: Optional[ExtractionResult] = None,
    ) -> RoutingDecision:
        """
        Execute only the routing decision step.

        Args:
            ticket: Ticket input
            classification: Classification result
            extraction: Optional extraction result

        Returns:
            RoutingDecision
        """
        extracted_dict = {}
        if extraction and extraction.fields:
            for field in extraction.fields:
                extracted_dict[field.name] = field.value

        return self.router.route(
            subject=ticket.subject,
            body=ticket.body,
            category=classification.category,
            severity=classification.severity,
            extracted_fields=extracted_dict,
        )


async def process_ticket(
    ticket: TicketInput,
    options: Optional[WorkflowOptions] = None,
    ai_service: Optional[AIService] = None,
) -> WorkflowResponse:
    """
    Convenience function to process a ticket through the workflow.

    Args:
        ticket: Ticket input
        options: Optional workflow options
        ai_service: Optional AIService instance

    Returns:
        WorkflowResponse
    """
    orchestrator = WorkflowOrchestrator(ai_service=ai_service)
    return await orchestrator.execute(ticket, options)
