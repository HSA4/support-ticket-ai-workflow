"""
Data access layer for database operations.

This module exports repository classes for interacting with database models.
"""

from app.repositories.ticket import TicketRepository

__all__ = [
    "TicketRepository",
]
