"""
Pydantic schemas for ticket input validation.

This module defines schemas for validating incoming ticket data
before processing by the workflow.
"""

from typing import Any, Dict, Optional

from pydantic import BaseModel, EmailStr, Field


class TicketInput(BaseModel):
    """
    Schema for incoming support ticket data.

    Attributes:
        subject: Ticket subject line (required)
        body: Full ticket body/content (required)
        customer_id: External customer identifier (optional)
        customer_email: Customer email address (optional)
        metadata: Additional metadata as key-value pairs (optional)
    """

    subject: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Ticket subject line",
        examples=["Cannot access my account"],
    )
    body: str = Field(
        ...,
        min_length=1,
        max_length=50000,
        description="Full ticket body/content",
        examples=[
            "I've been trying to log in for the past hour but keep getting an error."
        ],
    )
    customer_id: Optional[str] = Field(
        default=None,
        max_length=100,
        description="External customer identifier",
    )
    customer_email: Optional[EmailStr] = Field(
        default=None,
        description="Customer email address",
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Additional metadata as key-value pairs",
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "subject": "Cannot access my account",
                    "body": "I've been trying to log in for the past hour but keep getting an error message saying 'Invalid credentials'. I'm sure my password is correct.",
                    "customer_id": "cust-12345",
                    "customer_email": "john.doe@example.com",
                    "metadata": {"source": "web", "priority": "normal"},
                }
            ]
        }
    }


class TicketMetadata(BaseModel):
    """
    Schema for ticket metadata.

    Attributes:
        source: Where the ticket was submitted from
        priority: Customer-specified priority
        tags: Additional tags for categorization
    """

    source: Optional[str] = Field(default=None, max_length=50)
    priority: Optional[str] = Field(default=None, max_length=20)
    tags: Optional[list[str]] = Field(default_factory=list)
