"""
Workflow API endpoints for support ticket processing.

This module provides endpoints for:
- Full pipeline processing
- Classification only
- Field extraction only
- Response generation only
- Routing decision only
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_workflow_orchestrator
from app.schemas import (
    ClassificationRequest,
    ClassificationResult,
    ExtractionRequest,
    ExtractionResult,
    ResponseDraft,
    ResponseGenerationRequest,
    RoutingDecision,
    RoutingRequest,
    TicketInput,
    WorkflowOptions,
    WorkflowProcessRequest,
    WorkflowResponse,
)
from app.services.workflow.orchestrator import WorkflowOrchestrator

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/workflow", tags=["workflow"])


@router.post(
    "/process",
    response_model=WorkflowResponse,
    status_code=status.HTTP_200_OK,
    summary="Process a support ticket through the full workflow",
    description="""
    Execute the complete workflow for a support ticket including:
    - Classification (category + severity)
    - Field extraction
    - Response draft generation
    - Team routing decision

    Returns all results in a single response.
    """,
)
async def process_ticket(
    request: WorkflowProcessRequest,
    orchestrator: WorkflowOrchestrator = Depends(get_workflow_orchestrator),
) -> WorkflowResponse:
    """
    Process a support ticket through the complete workflow.

    Args:
        request: Workflow process request containing ticket and options
        orchestrator: Injected workflow orchestrator

    Returns:
        WorkflowResponse with all processing results

    Raises:
        HTTPException: If workflow execution fails
    """
    try:
        logger.info(f"Processing ticket: {request.ticket.subject[:50]}...")

        result = await orchestrator.execute(
            ticket=request.ticket,
            options=request.options,
        )

        logger.info(
            f"Ticket {result.ticket_id} processed successfully "
            f"in {result.total_duration_ms}ms"
        )

        return result

    except Exception as e:
        logger.error(f"Workflow processing failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Workflow processing failed: {str(e)}",
        )


@router.post(
    "/classify",
    response_model=ClassificationResult,
    status_code=status.HTTP_200_OK,
    summary="Classify a support ticket",
    description="""
    Classify a support ticket into category and severity.

    Categories: technical, billing, account, feature_request, bug_report, general
    Severities: critical, high, medium, low
    """,
)
async def classify_ticket(
    request: ClassificationRequest,
    orchestrator: WorkflowOrchestrator = Depends(get_workflow_orchestrator),
) -> ClassificationResult:
    """
    Classify a support ticket (category + severity only).

    Args:
        request: Classification request with subject and body
        orchestrator: Injected workflow orchestrator

    Returns:
        ClassificationResult with category and severity

    Raises:
        HTTPException: If classification fails
    """
    try:
        logger.info(f"Classifying ticket: {request.subject[:50]}...")

        # Create a minimal ticket input for classification
        ticket = TicketInput(
            subject=request.subject,
            body=request.body,
        )

        result = await orchestrator.execute_classification_only(ticket=ticket)

        logger.info(
            f"Ticket classified as {result.category}/{result.severity} "
            f"(confidence: {result.category_confidence:.2f})"
        )

        return result

    except Exception as e:
        logger.error(f"Classification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Classification failed: {str(e)}",
        )


@router.post(
    "/extract",
    response_model=ExtractionResult,
    status_code=status.HTTP_200_OK,
    summary="Extract fields from a support ticket",
    description="""
    Extract structured fields from ticket content.

    Extracted fields include:
    - order_id: Order/transaction identifiers
    - product_name: Product/service references
    - error_code: Error codes and messages
    - account_email: Email addresses
    - phone_number: Phone numbers
    - priority_keywords: Urgency indicators
    """,
)
async def extract_fields(
    request: ExtractionRequest,
    orchestrator: WorkflowOrchestrator = Depends(get_workflow_orchestrator),
) -> ExtractionResult:
    """
    Extract structured fields from a support ticket.

    Args:
        request: Extraction request with subject, body, and optional category
        orchestrator: Injected workflow orchestrator

    Returns:
        ExtractionResult with extracted fields

    Raises:
        HTTPException: If extraction fails
    """
    try:
        logger.info(f"Extracting fields from ticket: {request.subject[:50]}...")

        # Create a minimal ticket input for extraction
        ticket = TicketInput(
            subject=request.subject,
            body=request.body,
        )

        result = await orchestrator.execute_extraction_only(
            ticket=ticket,
            category=request.category,
        )

        logger.info(f"Extracted {len(result.fields)} fields")

        return result

    except Exception as e:
        logger.error(f"Field extraction failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Field extraction failed: {str(e)}",
        )


@router.post(
    "/respond",
    response_model=ResponseDraft,
    status_code=status.HTTP_200_OK,
    summary="Generate a response draft",
    description="""
    Generate a contextual response draft for a support ticket.

    The response is personalized using extracted customer information
    and tailored to the specified tone (formal, friendly, technical).
    """,
)
async def generate_response(
    request: ResponseGenerationRequest,
    orchestrator: WorkflowOrchestrator = Depends(get_workflow_orchestrator),
) -> ResponseDraft:
    """
    Generate a response draft for a support ticket.

    Args:
        request: Response generation request with ticket details
        orchestrator: Injected workflow orchestrator

    Returns:
        ResponseDraft with generated response

    Raises:
        HTTPException: If response generation fails
    """
    try:
        logger.info(f"Generating response for ticket: {request.subject[:50]}...")

        # Create a minimal ticket input
        ticket = TicketInput(
            subject=request.subject,
            body=request.body,
        )

        # Create classification result from request
        from app.schemas import ClassificationResult
        classification = ClassificationResult(
            category=request.category,
            category_confidence=1.0,
            severity=request.severity,
            severity_confidence=1.0,
            reasoning="Provided by caller",
        )

        # Create extraction result from request
        from app.schemas import ExtractedField, ExtractionResult
        extracted_fields = []
        for name, value in (request.extracted_fields or {}).items():
            extracted_fields.append(
                ExtractedField(
                    name=name,
                    value=value,
                    confidence=1.0,
                    source_span=None,
                )
            )
        extraction = ExtractionResult(fields=extracted_fields)

        result = await orchestrator.execute_response_only(
            ticket=ticket,
            classification=classification,
            extraction=extraction,
            tone=request.tone,
        )

        logger.info(f"Response generated with {result.tone} tone")

        return result

    except Exception as e:
        logger.error(f"Response generation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Response generation failed: {str(e)}",
        )


@router.post(
    "/route",
    response_model=RoutingDecision,
    status_code=status.HTTP_200_OK,
    summary="Determine routing for a support ticket",
    description="""
    Determine the best team to handle a support ticket.

    Available teams: technical_support, billing_team, account_management,
    product_team, escalation_team

    Routing is based on category, severity, and extracted fields.
    """,
)
async def route_ticket(
    request: RoutingRequest,
    orchestrator: WorkflowOrchestrator = Depends(get_workflow_orchestrator),
) -> RoutingDecision:
    """
    Determine routing decision for a support ticket.

    Args:
        request: Routing request with ticket details
        orchestrator: Injected workflow orchestrator

    Returns:
        RoutingDecision with team assignment

    Raises:
        HTTPException: If routing fails
    """
    try:
        logger.info(f"Routing ticket: {request.subject[:50]}...")

        # Create a minimal ticket input
        ticket = TicketInput(
            subject=request.subject,
            body=request.body,
        )

        # Create classification result from request
        from app.schemas import ClassificationResult
        classification = ClassificationResult(
            category=request.category,
            category_confidence=1.0,
            severity=request.severity,
            severity_confidence=1.0,
            reasoning="Provided by caller",
        )

        # Create extraction result from request
        from app.schemas import ExtractedField, ExtractionResult
        extracted_fields = []
        for name, value in (request.extracted_fields or {}).items():
            extracted_fields.append(
                ExtractedField(
                    name=name,
                    value=value,
                    confidence=1.0,
                    source_span=None,
                )
            )
        extraction = ExtractionResult(fields=extracted_fields)

        result = orchestrator.execute_routing_only(
            ticket=ticket,
            classification=classification,
            extraction=extraction,
        )

        logger.info(f"Ticket routed to {result.team} with priority {result.priority}")

        return result

    except Exception as e:
        logger.error(f"Routing failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Routing failed: {str(e)}",
        )
