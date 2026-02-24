"""
SQLAlchemy model for support tickets.

This module defines the Ticket model for storing support ticket data
and workflow processing results.
"""

import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    String,
    Text,
    JSON,
    Index,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class Ticket(Base):
    """
    Support ticket model for storing ticket data and workflow results.

    Attributes:
        id: Unique identifier (UUID)
        subject: Ticket subject line
        body: Full ticket body/content
        customer_id: External customer identifier
        customer_email: Customer email address

        category: Classified category (technical, billing, account, etc.)
        category_confidence: Confidence score for category classification
        severity: Assigned severity level (critical, high, medium, low)
        severity_confidence: Confidence score for severity assignment
        secondary_categories: Additional categories identified

        extracted_fields: JSON object containing extracted field data
        raw_extracted_fields: Raw extraction results before processing

        status: Current ticket status
        assigned_team: Team assigned to handle the ticket
        priority: Calculated priority level

        requires_escalation: Whether ticket needs escalation
        duplicate_of: ID of original ticket if this is a duplicate
        similarity_score: Similarity score if detected as potential duplicate

        response_draft: Generated response draft content
        response_tone: Tone used in response generation

        created_at: Record creation timestamp
        updated_at: Record last update timestamp
        processed_at: When workflow processing completed
    """

    __tablename__ = "tickets"

    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )

    # Ticket input data
    subject: Mapped[str] = mapped_column(String(500), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    customer_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    customer_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    ticket_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON, nullable=True, default=dict
    )

    # Classification results
    category: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    category_confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    severity: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    severity_confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    secondary_categories: Mapped[Optional[list]] = mapped_column(
        JSON, nullable=True, default=list
    )
    classification_reasoning: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )

    # Extraction results
    extracted_fields: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON, nullable=True, default=dict
    )
    missing_required_fields: Mapped[Optional[list]] = mapped_column(
        JSON, nullable=True, default=list
    )
    validation_errors: Mapped[Optional[list]] = mapped_column(
        JSON, nullable=True, default=list
    )

    # Routing results
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending"
    )
    assigned_team: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    priority: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    routing_reasoning: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    alternative_teams: Mapped[Optional[list]] = mapped_column(
        JSON, nullable=True, default=list
    )
    escalation_path: Mapped[Optional[list]] = mapped_column(
        JSON, nullable=True, default=list
    )

    # Escalation and duplicate detection
    requires_escalation: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    duplicate_of: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    similarity_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Response generation
    response_draft: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    response_tone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    suggested_actions: Mapped[Optional[list]] = mapped_column(
        JSON, nullable=True, default=list
    )
    template_used: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    processed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Indexes for common queries
    __table_args__ = (
        Index("ix_tickets_customer_id", "customer_id"),
        Index("ix_tickets_category", "category"),
        Index("ix_tickets_severity", "severity"),
        Index("ix_tickets_status", "status"),
        Index("ix_tickets_assigned_team", "assigned_team"),
        Index("ix_tickets_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<Ticket {self.id}: {self.subject[:50]}...>"
