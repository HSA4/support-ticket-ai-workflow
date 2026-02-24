"""
Pydantic schemas for workflow request/response data.

This module defines schemas for all workflow-related data including
classification, extraction, response generation, and routing results.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from app.schemas.ticket import TicketInput


# ============================================================================
# Classification Schemas
# ============================================================================


class ClassificationResult(BaseModel):
    """
    Schema for ticket classification results.

    Attributes:
        category: Primary category classification
        category_confidence: Confidence score for category (0.0-1.0)
        severity: Severity level assignment
        severity_confidence: Confidence score for severity (0.0-1.0)
        secondary_categories: Additional categories identified
        reasoning: Explanation for the classification
        keywords_matched: Keywords that influenced classification
        urgency_indicators: Urgency indicators found in ticket
    """

    category: str = Field(
        ...,
        description="Primary category classification",
        examples=["technical", "billing", "account", "feature_request", "bug_report", "general"],
    )
    category_confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence score for category (0.0-1.0)",
    )
    severity: str = Field(
        ...,
        description="Severity level assignment",
        examples=["critical", "high", "medium", "low"],
    )
    severity_confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence score for severity (0.0-1.0)",
    )
    secondary_categories: List[str] = Field(
        default_factory=list,
        description="Additional categories identified",
    )
    reasoning: Optional[str] = Field(
        default=None,
        description="Explanation for the classification",
    )
    keywords_matched: List[str] = Field(
        default_factory=list,
        description="Keywords that influenced classification",
    )
    urgency_indicators: List[str] = Field(
        default_factory=list,
        description="Urgency indicators found in ticket",
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "category": "technical",
                    "category_confidence": 0.92,
                    "severity": "high",
                    "severity_confidence": 0.85,
                    "secondary_categories": ["account"],
                    "reasoning": "User reports login failure with error message, affecting account access",
                    "keywords_matched": ["login", "error", "credentials"],
                    "urgency_indicators": ["past hour", "keep getting"],
                }
            ]
        }
    }


# ============================================================================
# Extraction Schemas
# ============================================================================


class ExtractedField(BaseModel):
    """
    Schema for a single extracted field.

    Attributes:
        name: Field name (e.g., order_id, product_name)
        value: Extracted value
        confidence: Confidence score for extraction (0.0-1.0)
        source_span: Original text span where value was found
    """

    name: str = Field(
        ...,
        description="Field name (e.g., order_id, product_name)",
    )
    value: Any = Field(
        ...,
        description="Extracted value",
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence score for extraction (0.0-1.0)",
    )
    source_span: Optional[str] = Field(
        default=None,
        description="Original text span where value was found",
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "name": "order_id",
                    "value": "ORD-123456",
                    "confidence": 0.98,
                    "source_span": "My order ORD-123456 hasn't arrived",
                }
            ]
        }
    }


class ExtractionResult(BaseModel):
    """
    Schema for field extraction results.

    Attributes:
        fields: List of extracted fields
        missing_required: Required fields that were not found
        validation_errors: List of validation errors encountered
    """

    fields: List[ExtractedField] = Field(
        default_factory=list,
        description="List of extracted fields",
    )
    missing_required: List[str] = Field(
        default_factory=list,
        description="Required fields that were not found",
    )
    validation_errors: List[str] = Field(
        default_factory=list,
        description="List of validation errors encountered",
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "fields": [
                        {
                            "name": "account_email",
                            "value": "john.doe@example.com",
                            "confidence": 0.95,
                            "source_span": "john.doe@example.com",
                        }
                    ],
                    "missing_required": ["order_id"],
                    "validation_errors": [],
                }
            ]
        }
    }


# ============================================================================
# Response Generation Schemas
# ============================================================================


class ResponseDraft(BaseModel):
    """
    Schema for generated response draft.

    Attributes:
        content: Full response content
        tone: Tone used in the response
        template_used: Template name if template was used
        suggested_actions: List of suggested next steps
        requires_escalation: Whether ticket requires escalation
        greeting: Personalized greeting
        acknowledgment: Acknowledgment of the issue
        explanation: Brief explanation if applicable
        action_items: List of action items
        timeline: Expected resolution timeframe
        closing: Professional closing
    """

    content: str = Field(
        ...,
        description="Full response content",
    )
    tone: str = Field(
        ...,
        description="Tone used in the response",
        examples=["formal", "friendly", "technical"],
    )
    template_used: Optional[str] = Field(
        default=None,
        description="Template name if template was used",
    )
    suggested_actions: List[str] = Field(
        default_factory=list,
        description="List of suggested next steps",
    )
    requires_escalation: bool = Field(
        default=False,
        description="Whether ticket requires escalation",
    )
    greeting: Optional[str] = Field(
        default=None,
        description="Personalized greeting",
    )
    acknowledgment: Optional[str] = Field(
        default=None,
        description="Acknowledgment of the issue",
    )
    explanation: Optional[str] = Field(
        default=None,
        description="Brief explanation if applicable",
    )
    action_items: List[str] = Field(
        default_factory=list,
        description="List of action items",
    )
    timeline: Optional[str] = Field(
        default=None,
        description="Expected resolution timeframe",
    )
    closing: Optional[str] = Field(
        default=None,
        description="Professional closing",
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "content": "Dear John,\n\nThank you for reaching out about your login issue...",
                    "tone": "friendly",
                    "template_used": None,
                    "suggested_actions": ["Reset password", "Clear browser cache"],
                    "requires_escalation": False,
                }
            ]
        }
    }


# ============================================================================
# Routing Schemas
# ============================================================================


class AlternativeTeam(BaseModel):
    """
    Schema for alternative team suggestion.

    Attributes:
        team: Team name
        reason: Why this team is also suitable
    """

    team: str = Field(
        ...,
        description="Team name",
    )
    reason: str = Field(
        ...,
        description="Why this team is also suitable",
    )


class RoutingDecision(BaseModel):
    """
    Schema for routing decision.

    Attributes:
        team: Primary team assignment
        priority: Assigned priority level
        reasoning: Explanation for routing decision
        alternative_teams: Other suitable teams
        escalation_path: Escalation path if needed
        confidence: Confidence score for routing decision
    """

    team: str = Field(
        ...,
        description="Primary team assignment",
        examples=["technical_support", "billing_team", "account_management", "product_team", "escalation_team"],
    )
    priority: str = Field(
        ...,
        description="Assigned priority level",
        examples=["urgent", "high", "normal", "low"],
    )
    reasoning: str = Field(
        ...,
        description="Explanation for routing decision",
    )
    alternative_teams: List[str] = Field(
        default_factory=list,
        description="Other suitable teams",
    )
    escalation_path: Optional[List[str]] = Field(
        default=None,
        description="Escalation path if needed",
    )
    confidence: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Confidence score for routing decision",
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "team": "technical_support",
                    "priority": "high",
                    "reasoning": "Login issues with error messages require technical investigation",
                    "alternative_teams": ["account_management"],
                    "escalation_path": ["senior_technical", "engineering_team"],
                    "confidence": 0.90,
                }
            ]
        }
    }


# ============================================================================
# Workflow Step Schemas
# ============================================================================


class WorkflowStepResult(BaseModel):
    """
    Schema for individual workflow step result.

    Attributes:
        step_name: Name of the workflow step
        status: Step execution status
        started_at: When step started
        completed_at: When step completed
        duration_ms: Execution time in milliseconds
        error: Error message if step failed
        fallback_used: Whether fallback logic was used
        tokens_used: Tokens consumed (if AI step)
    """

    step_name: str = Field(
        ...,
        description="Name of the workflow step",
    )
    status: str = Field(
        ...,
        description="Step execution status",
        examples=["completed", "failed", "skipped"],
    )
    started_at: Optional[datetime] = Field(
        default=None,
        description="When step started",
    )
    completed_at: Optional[datetime] = Field(
        default=None,
        description="When step completed",
    )
    duration_ms: Optional[int] = Field(
        default=None,
        description="Execution time in milliseconds",
    )
    error: Optional[str] = Field(
        default=None,
        description="Error message if step failed",
    )
    fallback_used: bool = Field(
        default=False,
        description="Whether fallback logic was used",
    )
    tokens_used: Optional[int] = Field(
        default=None,
        description="Tokens consumed (if AI step)",
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "step_name": "classification",
                    "status": "completed",
                    "started_at": "2024-01-15T10:30:00Z",
                    "completed_at": "2024-01-15T10:30:02Z",
                    "duration_ms": 2000,
                    "error": None,
                    "fallback_used": False,
                    "tokens_used": 150,
                }
            ]
        }
    }


# ============================================================================
# Workflow Request/Response Schemas
# ============================================================================


class WorkflowOptions(BaseModel):
    """
    Schema for workflow execution options.

    Attributes:
        skip_classification: Skip classification step
        skip_extraction: Skip field extraction step
        skip_response: Skip response generation step
        skip_routing: Skip routing decision step
        response_tone: Desired response tone
        enable_duplicate_detection: Enable duplicate detection
        enable_parallel: Enable parallel step execution
    """

    skip_classification: bool = Field(
        default=False,
        description="Skip classification step",
    )
    skip_extraction: bool = Field(
        default=False,
        description="Skip field extraction step",
    )
    skip_response: bool = Field(
        default=False,
        description="Skip response generation step",
    )
    skip_routing: bool = Field(
        default=False,
        description="Skip routing decision step",
    )
    response_tone: str = Field(
        default="friendly",
        description="Desired response tone",
        examples=["formal", "friendly", "technical"],
    )
    enable_duplicate_detection: bool = Field(
        default=True,
        description="Enable duplicate detection",
    )
    enable_parallel: bool = Field(
        default=True,
        description="Enable parallel step execution",
    )


class WorkflowResponse(BaseModel):
    """
    Schema for complete workflow response.

    Attributes:
        ticket_id: Unique identifier for the processed ticket
        classification: Classification results
        extracted_fields: Field extraction results
        response_draft: Generated response draft
        routing: Routing decision
        duplicate_of: ID of original ticket if duplicate detected
        similarity_score: Similarity score if duplicate detected
        workflow_steps: Results from each workflow step
        total_duration_ms: Total workflow execution time
        created_at: Response timestamp
    """

    ticket_id: str = Field(
        ...,
        description="Unique identifier for the processed ticket",
    )
    classification: ClassificationResult = Field(
        ...,
        description="Classification results",
    )
    extracted_fields: ExtractionResult = Field(
        ...,
        description="Field extraction results",
    )
    response_draft: Optional[ResponseDraft] = Field(
        default=None,
        description="Generated response draft",
    )
    routing: RoutingDecision = Field(
        ...,
        description="Routing decision",
    )
    duplicate_of: Optional[str] = Field(
        default=None,
        description="ID of original ticket if duplicate detected",
    )
    similarity_score: Optional[float] = Field(
        default=None,
        description="Similarity score if duplicate detected",
    )
    workflow_steps: List[WorkflowStepResult] = Field(
        default_factory=list,
        description="Results from each workflow step",
    )
    total_duration_ms: int = Field(
        ...,
        description="Total workflow execution time in milliseconds",
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Response timestamp",
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "ticket_id": "550e8400-e29b-41d4-a716-446655440000",
                    "classification": {
                        "category": "technical",
                        "category_confidence": 0.92,
                        "severity": "high",
                        "severity_confidence": 0.85,
                        "secondary_categories": [],
                        "reasoning": "Login issue with error message",
                    },
                    "extracted_fields": {
                        "fields": [],
                        "missing_required": [],
                        "validation_errors": [],
                    },
                    "response_draft": {
                        "content": "Dear customer...",
                        "tone": "friendly",
                        "suggested_actions": [],
                        "requires_escalation": False,
                    },
                    "routing": {
                        "team": "technical_support",
                        "priority": "high",
                        "reasoning": "Technical login issue",
                        "alternative_teams": [],
                        "escalation_path": None,
                    },
                    "duplicate_of": None,
                    "similarity_score": None,
                    "workflow_steps": [],
                    "total_duration_ms": 3500,
                    "created_at": "2024-01-15T10:30:00Z",
                }
            ]
        }
    }


# ============================================================================
# API Request Schemas
# ============================================================================


class WorkflowProcessRequest(BaseModel):
    """
    Schema for workflow process request.

    Attributes:
        ticket: Ticket input data
        options: Workflow execution options
    """

    ticket: TicketInput = Field(
        ...,
        description="Ticket input data",
    )
    options: Optional[WorkflowOptions] = Field(
        default=None,
        description="Workflow execution options",
    )


class ClassificationRequest(BaseModel):
    """
    Schema for classification-only request.

    Attributes:
        subject: Ticket subject
        body: Ticket body
    """

    subject: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Ticket subject",
    )
    body: str = Field(
        ...,
        min_length=1,
        max_length=50000,
        description="Ticket body",
    )


class ExtractionRequest(BaseModel):
    """
    Schema for extraction-only request.

    Attributes:
        subject: Ticket subject
        body: Ticket body
        category: Ticket category (optional, improves extraction)
    """

    subject: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Ticket subject",
    )
    body: str = Field(
        ...,
        min_length=1,
        max_length=50000,
        description="Ticket body",
    )
    category: Optional[str] = Field(
        default=None,
        description="Ticket category (optional, improves extraction)",
    )


class ResponseGenerationRequest(BaseModel):
    """
    Schema for response generation request.

    Attributes:
        subject: Ticket subject
        body: Ticket body
        category: Ticket category
        severity: Ticket severity
        extracted_fields: Extracted fields
        tone: Desired response tone
        customer_name: Customer name for personalization
    """

    subject: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Ticket subject",
    )
    body: str = Field(
        ...,
        min_length=1,
        max_length=50000,
        description="Ticket body",
    )
    category: str = Field(
        ...,
        description="Ticket category",
    )
    severity: str = Field(
        ...,
        description="Ticket severity",
    )
    extracted_fields: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Extracted fields",
    )
    tone: str = Field(
        default="friendly",
        description="Desired response tone",
    )
    customer_name: Optional[str] = Field(
        default=None,
        description="Customer name for personalization",
    )


class RoutingRequest(BaseModel):
    """
    Schema for routing decision request.

    Attributes:
        subject: Ticket subject
        body: Ticket body
        category: Ticket category
        severity: Ticket severity
        extracted_fields: Extracted fields
    """

    subject: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Ticket subject",
    )
    body: str = Field(
        ...,
        min_length=1,
        max_length=50000,
        description="Ticket body",
    )
    category: str = Field(
        ...,
        description="Ticket category",
    )
    severity: str = Field(
        ...,
        description="Ticket severity",
    )
    extracted_fields: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Extracted fields",
    )
