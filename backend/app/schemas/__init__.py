"""
Pydantic schemas for API request/response validation.

This module exports all schemas for the support ticket workflow system.
"""

from app.schemas.ticket import TicketInput, TicketMetadata
from app.schemas.workflow import (
    AlternativeTeam,
    ClassificationRequest,
    ClassificationResult,
    ExtractionRequest,
    ExtractionResult,
    ExtractedField,
    ResponseDraft,
    ResponseGenerationRequest,
    RoutingDecision,
    RoutingRequest,
    WorkflowOptions,
    WorkflowProcessRequest,
    WorkflowResponse,
    WorkflowStepResult,
)

__all__ = [
    # Ticket schemas
    "TicketInput",
    "TicketMetadata",
    # Classification schemas
    "ClassificationResult",
    "ClassificationRequest",
    # Extraction schemas
    "ExtractedField",
    "ExtractionResult",
    "ExtractionRequest",
    # Response schemas
    "ResponseDraft",
    "ResponseGenerationRequest",
    # Routing schemas
    "AlternativeTeam",
    "RoutingDecision",
    "RoutingRequest",
    # Workflow schemas
    "WorkflowOptions",
    "WorkflowProcessRequest",
    "WorkflowResponse",
    "WorkflowStepResult",
]
