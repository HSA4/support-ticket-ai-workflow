"""
Repository layer for ticket data access operations.

This module provides the TicketRepository class with async methods
for CRUD operations on tickets and workflow run logging.
"""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import Ticket, WorkflowRun


class TicketRepository:
    """
    Repository for ticket data access operations.

    Provides async methods for creating, reading, updating tickets,
    finding similar tickets for duplicate detection, and logging workflow runs.

    Attributes:
        session: Async SQLAlchemy session for database operations
    """

    def __init__(self, session: AsyncSession):
        """
        Initialize the repository with a database session.

        Args:
            session: Async SQLAlchemy session
        """
        self.session = session

    async def create_ticket(self, ticket_data: Dict[str, Any]) -> Ticket:
        """
        Create a new ticket in the database.

        Args:
            ticket_data: Dictionary containing ticket attributes.
                Required keys: subject, body
                Optional keys: customer_id, customer_email, ticket_metadata,
                               category, category_confidence, severity,
                               severity_confidence, secondary_categories,
                               classification_reasoning, extracted_fields,
                               missing_required_fields, validation_errors,
                               status, assigned_team, priority, routing_reasoning,
                               alternative_teams, escalation_path,
                               requires_escalation, duplicate_of, similarity_score,
                               response_draft, response_tone, suggested_actions,
                               template_used, processed_at

        Returns:
            Ticket: The created ticket instance with database-generated ID

        Example:
            ticket = await repo.create_ticket({
                "subject": "Login issue",
                "body": "I cannot log in to my account",
                "customer_id": "cust_123",
            })
        """
        ticket = Ticket(**ticket_data)
        self.session.add(ticket)
        await self.session.flush()
        await self.session.refresh(ticket)
        return ticket

    async def get_ticket(self, ticket_id: uuid.UUID) -> Optional[Ticket]:
        """
        Retrieve a ticket by its ID.

        Args:
            ticket_id: UUID of the ticket to retrieve

        Returns:
            Ticket if found, None otherwise

        Example:
            ticket = await repo.get_ticket(uuid.UUID("..."))
        """
        result = await self.session.execute(
            select(Ticket).where(Ticket.id == ticket_id)
        )
        return result.scalar_one_or_none()

    async def get_tickets(
        self,
        skip: int = 0,
        limit: int = 100,
        customer_id: Optional[str] = None,
        category: Optional[str] = None,
        severity: Optional[str] = None,
        status: Optional[str] = None,
        assigned_team: Optional[str] = None,
    ) -> List[Ticket]:
        """
        Retrieve a paginated list of tickets with optional filters.

        Args:
            skip: Number of records to skip for pagination
            limit: Maximum number of records to return
            customer_id: Filter by customer ID
            category: Filter by category
            severity: Filter by severity level
            status: Filter by ticket status
            assigned_team: Filter by assigned team

        Returns:
            List of Ticket instances matching the criteria

        Example:
            tickets = await repo.get_tickets(skip=0, limit=10, status="pending")
        """
        query = select(Ticket)

        # Apply optional filters
        if customer_id is not None:
            query = query.where(Ticket.customer_id == customer_id)
        if category is not None:
            query = query.where(Ticket.category == category)
        if severity is not None:
            query = query.where(Ticket.severity == severity)
        if status is not None:
            query = query.where(Ticket.status == status)
        if assigned_team is not None:
            query = query.where(Ticket.assigned_team == assigned_team)

        # Order by creation date (newest first) and apply pagination
        query = query.order_by(Ticket.created_at.desc())
        query = query.offset(skip).limit(limit)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def update_ticket(
        self,
        ticket_id: uuid.UUID,
        update_data: Dict[str, Any],
    ) -> Optional[Ticket]:
        """
        Update an existing ticket with new data.

        Args:
            ticket_id: UUID of the ticket to update
            update_data: Dictionary containing fields to update.
                Only provided fields will be updated.

        Returns:
            Updated Ticket if found, None otherwise

        Example:
            ticket = await repo.update_ticket(
                ticket_id,
                {"status": "in_progress", "assigned_team": "technical_support"}
            )
        """
        ticket = await self.get_ticket(ticket_id)
        if ticket is None:
            return None

        # Update only provided fields
        for key, value in update_data.items():
            if hasattr(ticket, key):
                setattr(ticket, key, value)

        # Update the updated_at timestamp
        ticket.updated_at = datetime.utcnow()

        await self.session.flush()
        await self.session.refresh(ticket)
        return ticket

    async def find_similar_tickets(
        self,
        customer_id: str,
        subject: str,
        body: str,
        threshold: float = 0.8,
        limit: int = 5,
    ) -> List[Ticket]:
        """
        Find potentially similar tickets from the same customer for duplicate detection.

        This method searches for tickets from the same customer and performs
        basic text similarity matching on subject and body. For production use,
        consider integrating with a vector database for semantic similarity.

        Args:
            customer_id: Customer ID to search within
            subject: Subject of the new ticket to compare against
            body: Body of the new ticket to compare against
            threshold: Minimum similarity score (0.0 to 1.0) for matches
            limit: Maximum number of similar tickets to return

        Returns:
            List of similar Ticket instances with similarity scores

        Note:
            The current implementation uses basic text overlap for similarity.
            For better results, integrate with an embedding-based search:
            - Store embeddings in a vector column or separate vector DB
            - Use cosine similarity on embeddings for semantic matching

        Example:
            similar = await repo.find_similar_tickets(
                customer_id="cust_123",
                subject="Login issue",
                body="Cannot log in",
                threshold=0.7
            )
        """
        # Get recent tickets from the same customer
        query = (
            select(Ticket)
            .where(Ticket.customer_id == customer_id)
            .where(Ticket.status != "closed")
            .order_by(Ticket.created_at.desc())
            .limit(50)  # Limit candidate pool for performance
        )

        result = await self.session.execute(query)
        candidate_tickets = list(result.scalars().all())

        # Calculate similarity scores using simple text overlap
        similar_tickets = []
        subject_lower = subject.lower()
        body_lower = body.lower()

        for ticket in candidate_tickets:
            # Calculate Jaccard-like similarity on words
            ticket_subject_words = set(ticket.subject.lower().split())
            ticket_body_words = set(ticket.body.lower().split())

            new_subject_words = set(subject_lower.split())
            new_body_words = set(body_lower.split())

            # Subject similarity (weighted more heavily)
            if ticket_subject_words and new_subject_words:
                subject_intersection = len(
                    ticket_subject_words & new_subject_words
                )
                subject_union = len(ticket_subject_words | new_subject_words)
                subject_similarity = (
                    subject_intersection / subject_union
                    if subject_union > 0
                    else 0
                )
            else:
                subject_similarity = 0

            # Body similarity
            if ticket_body_words and new_body_words:
                body_intersection = len(ticket_body_words & new_body_words)
                body_union = len(ticket_body_words | new_body_words)
                body_similarity = (
                    body_intersection / body_union if body_union > 0 else 0
                )
            else:
                body_similarity = 0

            # Combined similarity (70% subject, 30% body)
            combined_similarity = (subject_similarity * 0.7) + (
                body_similarity * 0.3
            )

            if combined_similarity >= threshold:
                # Store similarity score on the ticket object for reference
                ticket.similarity_score = combined_similarity
                similar_tickets.append(ticket)

        # Sort by similarity score (highest first) and limit results
        similar_tickets.sort(key=lambda t: t.similarity_score, reverse=True)
        return similar_tickets[:limit]

    async def find_similar_tickets_by_embedding(
        self,
        embedding: List[float],
        threshold: float = 0.8,
        limit: int = 5,
        customer_id: Optional[str] = None,
    ) -> List[Ticket]:
        """
        Find similar tickets using vector embeddings for semantic similarity.

        This method is designed for use with a vector similarity search.
        When embeddings are stored in the database (e.g., with pgvector),
        this method performs efficient semantic similarity matching.

        Args:
            embedding: Vector embedding of the ticket content
            threshold: Minimum cosine similarity score (0.0 to 1.0)
            limit: Maximum number of similar tickets to return
            customer_id: Optional customer ID to filter results

        Returns:
            List of similar Ticket instances with similarity scores

        Note:
            This method requires the database to support vector operations
            (e.g., PostgreSQL with pgvector extension). The embedding column
            should be added to the Ticket model:

            Example model addition:
                from pgvector.sqlalchemy import Vector
                embedding: Mapped[Optional[List[float]]] = mapped_column(
                    Vector(1536),  # OpenAI embedding dimension
                    nullable=True
                )

        Example:
            similar = await repo.find_similar_tickets_by_embedding(
                embedding=[0.1, 0.2, ...],  # 1536-dimensional vector
                threshold=0.85,
                customer_id="cust_123"
            )
        """
        # This is a placeholder implementation for when vector search
        # is not available. It returns an empty list.
        #
        # Full implementation with pgvector would look like:
        #
        # from sqlalchemy import text
        #
        # query = select(
        #     Ticket,
        #     (1 - Ticket.embedding.cosine_distance(embedding)).label(
        #         "similarity"
        #     )
        # ).where(
        #     Ticket.embedding.isnot(None)
        # )
        #
        # if customer_id:
        #     query = query.where(Ticket.customer_id == customer_id)
        #
        # query = query.order_by(
        #     Ticket.embedding.cosine_distance(embedding)
        # ).limit(limit)
        #
        # result = await self.session.execute(query)
        # rows = result.all()
        #
        # similar_tickets = []
        # for row in rows:
        #     ticket = row[0]
        #     similarity = row[1]
        #     if similarity >= threshold:
        #         ticket.similarity_score = similarity
        #         similar_tickets.append(ticket)
        #
        # return similar_tickets

        # Fallback: return empty list when vector search is not configured
        return []

    async def log_workflow_run(
        self,
        workflow_data: Dict[str, Any],
    ) -> WorkflowRun:
        """
        Log a workflow run step execution.

        Creates a WorkflowRun record to track individual step execution
        within the ticket processing pipeline.

        Args:
            workflow_data: Dictionary containing workflow run attributes.
                Required keys: ticket_id, step_name, step_number
                Optional keys: status, input_data, output_data,
                               started_at, completed_at, duration_ms,
                               error_message, error_type, retry_count,
                               ai_model_used, tokens_used, prompt_tokens,
                               completion_tokens, fallback_used, fallback_reason

        Returns:
            WorkflowRun: The created workflow run instance

        Example:
            workflow_run = await repo.log_workflow_run({
                "ticket_id": uuid.UUID("..."),
                "step_name": "classification",
                "step_number": 1,
                "status": "completed",
                "input_data": {"subject": "...", "body": "..."},
                "output_data": {"category": "technical", "severity": "high"},
                "duration_ms": 1500,
            })
        """
        workflow_run = WorkflowRun(**workflow_data)
        self.session.add(workflow_run)
        await self.session.flush()
        await self.session.refresh(workflow_run)
        return workflow_run

    async def get_workflow_runs_for_ticket(
        self,
        ticket_id: uuid.UUID,
    ) -> List[WorkflowRun]:
        """
        Retrieve all workflow runs for a specific ticket.

        Args:
            ticket_id: UUID of the ticket

        Returns:
            List of WorkflowRun instances ordered by step_number

        Example:
            runs = await repo.get_workflow_runs_for_ticket(ticket_id)
        """
        result = await self.session.execute(
            select(WorkflowRun)
            .where(WorkflowRun.ticket_id == ticket_id)
            .order_by(WorkflowRun.step_number)
        )
        return list(result.scalars().all())

    async def count_tickets(
        self,
        customer_id: Optional[str] = None,
        category: Optional[str] = None,
        severity: Optional[str] = None,
        status: Optional[str] = None,
        assigned_team: Optional[str] = None,
    ) -> int:
        """
        Count tickets matching the given filters.

        Args:
            customer_id: Filter by customer ID
            category: Filter by category
            severity: Filter by severity level
            status: Filter by ticket status
            assigned_team: Filter by assigned team

        Returns:
            Count of matching tickets

        Example:
            count = await repo.count_tickets(status="pending")
        """
        query = select(func.count(Ticket.id))

        if customer_id is not None:
            query = query.where(Ticket.customer_id == customer_id)
        if category is not None:
            query = query.where(Ticket.category == category)
        if severity is not None:
            query = query.where(Ticket.severity == severity)
        if status is not None:
            query = query.where(Ticket.status == status)
        if assigned_team is not None:
            query = query.where(Ticket.assigned_team == assigned_team)

        result = await self.session.execute(query)
        return result.scalar_one()

    async def delete_ticket(self, ticket_id: uuid.UUID) -> bool:
        """
        Delete a ticket by its ID.

        Args:
            ticket_id: UUID of the ticket to delete

        Returns:
            True if ticket was deleted, False if not found

        Example:
            deleted = await repo.delete_ticket(ticket_id)
        """
        ticket = await self.get_ticket(ticket_id)
        if ticket is None:
            return False

        await self.session.delete(ticket)
        await self.session.flush()
        return True
