"""
SQLAlchemy model for workflow run tracking.

This module defines the WorkflowRun model for tracking individual
workflow step executions and their results.
"""

import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy import DateTime, Integer, String, Text, JSON, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class WorkflowRun(Base):
    """
    Workflow run model for tracking step executions.

    Stores detailed information about each step in the ticket processing
    workflow, including input/output data, timing, and errors.

    Attributes:
        id: Unique identifier (UUID)
        ticket_id: Foreign key to the associated ticket

        step_name: Name of the workflow step
        step_number: Order of this step in the workflow
        status: Step execution status (pending, running, completed, failed, skipped)

        input_data: Input data passed to the step
        output_data: Output data produced by the step

        started_at: When step execution started
        completed_at: When step execution completed
        duration_ms: Execution time in milliseconds

        error_message: Error message if step failed
        error_type: Exception type if step failed
        retry_count: Number of retry attempts

        ai_model_used: OpenAI model used (if AI step)
        tokens_used: Total tokens consumed (if AI step)
        prompt_tokens: Tokens in prompt (if AI step)
        completion_tokens: Tokens in completion (if AI step)

        fallback_used: Whether fallback logic was used
        fallback_reason: Why fallback was triggered

        created_at: Record creation timestamp
        updated_at: Record last update timestamp
    """

    __tablename__ = "workflow_runs"

    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )

    # Foreign key to ticket
    ticket_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
    )

    # Step identification
    step_name: Mapped[str] = mapped_column(String(50), nullable=False)
    step_number: Mapped[int] = mapped_column(Integer, nullable=False)

    # Execution status
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="pending",
    )

    # Input/Output data
    input_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON, nullable=True, default=dict
    )
    output_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON, nullable=True, default=dict
    )

    # Timing information
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    duration_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Error tracking
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    error_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # AI-specific tracking
    ai_model_used: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    tokens_used: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    prompt_tokens: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    completion_tokens: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Fallback tracking
    fallback_used: Mapped[bool] = mapped_column(
        nullable=False, default=False
    )
    fallback_reason: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Indexes for common queries
    __table_args__ = (
        Index("ix_workflow_runs_ticket_id", "ticket_id"),
        Index("ix_workflow_runs_step_name", "step_name"),
        Index("ix_workflow_runs_status", "status"),
        Index("ix_workflow_runs_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<WorkflowRun {self.id}: {self.step_name} - {self.status}>"
