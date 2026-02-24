"""
Tickets API endpoints for listing and retrieving processed tickets.

This module provides endpoints for:
- Listing processed tickets with filtering
- Getting individual ticket details with workflow information
"""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.dependencies import get_db_session
from app.db.models.ticket import Ticket
from app.db.models.workflow_run import WorkflowRun

router = APIRouter(prefix="/tickets", tags=["tickets"])


# ============================================================================
# Response Schemas
# ============================================================================


class TicketListItem(BaseModel):
    """
    Schema for ticket list item (summary view).
    """

    id: str = Field(..., description="Ticket UUID")
    subject: str = Field(..., description="Ticket subject")
    customer_id: Optional[str] = Field(None, description="Customer ID")
    customer_email: Optional[str] = Field(None, description="Customer email")

    category: Optional[str] = Field(None, description="Classified category")
    severity: Optional[str] = Field(None, description="Assigned severity")
    status: str = Field(..., description="Ticket status")
    assigned_team: Optional[str] = Field(None, description="Assigned team")
    priority: Optional[str] = Field(None, description="Priority level")

    created_at: datetime = Field(..., description="Creation timestamp")
    processed_at: Optional[datetime] = Field(None, description="Processing timestamp")

    model_config = {"from_attributes": True}


class TicketDetail(TicketListItem):
    """
    Schema for detailed ticket view with workflow information.
    """

    body: str = Field(..., description="Ticket body content")

    # Classification details
    category_confidence: Optional[float] = Field(None, description="Category confidence")
    severity_confidence: Optional[float] = Field(None, description="Severity confidence")
    secondary_categories: Optional[List[str]] = Field(None, description="Secondary categories")
    classification_reasoning: Optional[str] = Field(None, description="Classification reasoning")

    # Extraction details
    extracted_fields: Optional[Dict[str, Any]] = Field(None, description="Extracted fields")
    missing_required_fields: Optional[List[str]] = Field(None, description="Missing required fields")
    validation_errors: Optional[List[str]] = Field(None, description="Validation errors")

    # Routing details
    routing_reasoning: Optional[str] = Field(None, description="Routing reasoning")
    alternative_teams: Optional[List[str]] = Field(None, description="Alternative teams")
    escalation_path: Optional[List[str]] = Field(None, description="Escalation path")

    # Response details
    response_draft: Optional[str] = Field(None, description="Generated response draft")
    response_tone: Optional[str] = Field(None, description="Response tone")
    suggested_actions: Optional[List[str]] = Field(None, description="Suggested actions")
    template_used: Optional[str] = Field(None, description="Template used")

    # Duplicate detection
    requires_escalation: bool = Field(False, description="Requires escalation")
    duplicate_of: Optional[str] = Field(None, description="Duplicate of ticket ID")
    similarity_score: Optional[float] = Field(None, description="Similarity score")


class WorkflowRunSummary(BaseModel):
    """
    Schema for workflow run summary.
    """

    id: str = Field(..., description="Workflow run UUID")
    step_name: str = Field(..., description="Step name")
    step_number: int = Field(..., description="Step order")
    status: str = Field(..., description="Step status")
    duration_ms: Optional[int] = Field(None, description="Duration in ms")
    error_message: Optional[str] = Field(None, description="Error message")
    fallback_used: bool = Field(False, description="Fallback used")
    tokens_used: Optional[int] = Field(None, description="Tokens used")

    started_at: Optional[datetime] = Field(None, description="Start timestamp")
    completed_at: Optional[datetime] = Field(None, description="Completion timestamp")

    model_config = {"from_attributes": True}


class TicketWithWorkflow(TicketDetail):
    """
    Schema for ticket with workflow run details.
    """

    workflow_runs: List[WorkflowRunSummary] = Field(
        default_factory=list,
        description="Workflow run history",
    )


class TicketListResponse(BaseModel):
    """
    Schema for paginated ticket list response.
    """

    items: List[TicketListItem] = Field(..., description="List of tickets")
    total: int = Field(..., description="Total count")
    page: int = Field(..., description="Current page")
    page_size: int = Field(..., description="Page size")
    pages: int = Field(..., description="Total pages")


# ============================================================================
# Endpoints
# ============================================================================


@router.get(
    "",
    response_model=TicketListResponse,
    status_code=status.HTTP_200_OK,
    summary="List processed tickets",
    description="""
    List all processed support tickets with optional filtering.

    Supports filtering by:
    - category: Ticket category (technical, billing, account, etc.)
    - severity: Severity level (critical, high, medium, low)
    - status: Ticket status (pending, in_progress, resolved, closed)
    - assigned_team: Team assignment
    - customer_id: Customer identifier

    Results are paginated and sorted by creation date (newest first).
    """,
)
async def list_tickets(
    db: AsyncSession = Depends(get_db_session),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    category: Optional[str] = Query(None, description="Filter by category"),
    severity: Optional[str] = Query(None, description="Filter by severity"),
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status"),
    assigned_team: Optional[str] = Query(None, description="Filter by assigned team"),
    customer_id: Optional[str] = Query(None, description="Filter by customer ID"),
) -> TicketListResponse:
    """
    List processed tickets with optional filtering and pagination.

    Args:
        db: Database session
        page: Page number (1-indexed)
        page_size: Number of items per page
        category: Filter by category
        severity: Filter by severity
        status_filter: Filter by status
        assigned_team: Filter by assigned team
        customer_id: Filter by customer ID

    Returns:
        Paginated list of tickets
    """
    # Build base query
    query = select(Ticket)

    # Apply filters
    if category:
        query = query.where(Ticket.category == category)
    if severity:
        query = query.where(Ticket.severity == severity)
    if status_filter:
        query = query.where(Ticket.status == status_filter)
    if assigned_team:
        query = query.where(Ticket.assigned_team == assigned_team)
    if customer_id:
        query = query.where(Ticket.customer_id == customer_id)

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Apply pagination and sorting
    query = query.order_by(desc(Ticket.created_at))
    query = query.offset((page - 1) * page_size).limit(page_size)

    # Execute query
    result = await db.execute(query)
    tickets = result.scalars().all()

    # Build response
    items = [
        TicketListItem(
            id=str(ticket.id),
            subject=ticket.subject,
            customer_id=ticket.customer_id,
            customer_email=ticket.customer_email,
            category=ticket.category,
            severity=ticket.severity,
            status=ticket.status,
            assigned_team=ticket.assigned_team,
            priority=ticket.priority,
            created_at=ticket.created_at,
            processed_at=ticket.processed_at,
        )
        for ticket in tickets
    ]

    return TicketListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size,
    )


@router.get(
    "/{ticket_id}",
    response_model=TicketWithWorkflow,
    status_code=status.HTTP_200_OK,
    summary="Get ticket details",
    description="""
    Get detailed information about a specific ticket including:
    - Full ticket content
    - Classification details
    - Extracted fields
    - Generated response
    - Routing decision
    - Workflow execution history
    """,
)
async def get_ticket(
    ticket_id: str,
    db: AsyncSession = Depends(get_db_session),
) -> TicketWithWorkflow:
    """
    Get detailed ticket information with workflow history.

    Args:
        ticket_id: Ticket UUID
        db: Database session

    Returns:
        Detailed ticket information with workflow runs

    Raises:
        HTTPException: If ticket not found
    """
    # Parse ticket ID
    try:
        ticket_uuid = uuid.UUID(ticket_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid ticket ID format",
        )

    # Query ticket
    query = select(Ticket).where(Ticket.id == ticket_uuid)
    result = await db.execute(query)
    ticket = result.scalar_one_or_none()

    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ticket {ticket_id} not found",
        )

    # Query workflow runs
    workflow_query = (
        select(WorkflowRun)
        .where(WorkflowRun.ticket_id == ticket_uuid)
        .order_by(WorkflowRun.step_number)
    )
    workflow_result = await db.execute(workflow_query)
    workflow_runs = workflow_result.scalars().all()

    # Build workflow run summaries
    workflow_summaries = [
        WorkflowRunSummary(
            id=str(run.id),
            step_name=run.step_name,
            step_number=run.step_number,
            status=run.status,
            duration_ms=run.duration_ms,
            error_message=run.error_message,
            fallback_used=run.fallback_used,
            tokens_used=run.tokens_used,
            started_at=run.started_at,
            completed_at=run.completed_at,
        )
        for run in workflow_runs
    ]

    # Build response
    return TicketWithWorkflow(
        id=str(ticket.id),
        subject=ticket.subject,
        body=ticket.body,
        customer_id=ticket.customer_id,
        customer_email=ticket.customer_email,
        category=ticket.category,
        category_confidence=ticket.category_confidence,
        severity=ticket.severity,
        severity_confidence=ticket.severity_confidence,
        secondary_categories=ticket.secondary_categories or [],
        classification_reasoning=ticket.classification_reasoning,
        status=ticket.status,
        assigned_team=ticket.assigned_team,
        priority=ticket.priority,
        routing_reasoning=ticket.routing_reasoning,
        alternative_teams=ticket.alternative_teams or [],
        escalation_path=ticket.escalation_path or [],
        extracted_fields=ticket.extracted_fields or {},
        missing_required_fields=ticket.missing_required_fields or [],
        validation_errors=ticket.validation_errors or [],
        response_draft=ticket.response_draft,
        response_tone=ticket.response_tone,
        suggested_actions=ticket.suggested_actions or [],
        template_used=ticket.template_used,
        requires_escalation=ticket.requires_escalation,
        duplicate_of=str(ticket.duplicate_of) if ticket.duplicate_of else None,
        similarity_score=ticket.similarity_score,
        created_at=ticket.created_at,
        processed_at=ticket.processed_at,
        workflow_runs=workflow_summaries,
    )
