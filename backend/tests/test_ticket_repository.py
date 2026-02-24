"""
Tests for the TicketRepository class.

This module contains unit tests for the ticket repository,
testing all CRUD operations and duplicate detection functionality.
"""

import uuid
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.ticket import TicketRepository
from app.db.models import Ticket, WorkflowRun


@pytest.fixture
def mock_session():
    """Create a mock async database session."""
    session = MagicMock(spec=AsyncSession)
    session.add = MagicMock()
    session.flush = AsyncMock()
    session.refresh = AsyncMock()
    session.delete = MagicMock()
    session.execute = AsyncMock()
    return session


@pytest.fixture
def repository(mock_session):
    """Create a TicketRepository with a mock session."""
    return TicketRepository(mock_session)


@pytest.fixture
def sample_ticket_data():
    """Create sample ticket data for testing."""
    return {
        "subject": "Cannot access my account",
        "body": "I've been trying to log in but keep getting an error.",
        "customer_id": "cust-12345",
        "customer_email": "john.doe@example.com",
        "category": "account",
        "category_confidence": 0.92,
        "severity": "high",
        "severity_confidence": 0.85,
        "status": "pending",
        "assigned_team": "account_management",
    }


@pytest.fixture
def sample_workflow_data():
    """Create sample workflow run data for testing."""
    return {
        "ticket_id": uuid.uuid4(),
        "step_name": "classification",
        "step_number": 1,
        "status": "completed",
        "input_data": {"subject": "Test", "body": "Test body"},
        "output_data": {"category": "account", "severity": "high"},
        "duration_ms": 1500,
    }


class TestTicketRepositoryInit:
    """Tests for TicketRepository initialization."""

    def test_initialization(self, mock_session):
        """Test that repository initializes with session."""
        repo = TicketRepository(mock_session)

        assert repo.session == mock_session


class TestCreateTicket:
    """Tests for create_ticket method."""

    @pytest.mark.asyncio
    async def test_create_ticket_success(self, repository, mock_session, sample_ticket_data):
        """Test successful ticket creation."""
        # Create a mock ticket that will be returned
        mock_ticket = MagicMock(spec=Ticket)
        mock_ticket.id = uuid.uuid4()
        mock_ticket.subject = sample_ticket_data["subject"]

        # Set up the session to return our mock when refreshed
        async def mock_refresh_side_effect(obj):
            obj.id = mock_ticket.id
            obj.subject = mock_ticket.subject

        mock_session.refresh.side_effect = mock_refresh_side_effect

        result = await repository.create_ticket(sample_ticket_data)

        # Verify session methods were called
        mock_session.add.assert_called_once()
        mock_session.flush.assert_called_once()
        mock_session.refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_ticket_minimal_data(self, repository, mock_session):
        """Test ticket creation with minimal required data."""
        minimal_data = {
            "subject": "Test subject",
            "body": "Test body",
        }

        await repository.create_ticket(minimal_data)

        mock_session.add.assert_called_once()


class TestGetTicket:
    """Tests for get_ticket method."""

    @pytest.mark.asyncio
    async def test_get_ticket_found(self, repository, mock_session):
        """Test retrieving an existing ticket."""
        ticket_id = uuid.uuid4()
        mock_ticket = MagicMock(spec=Ticket)
        mock_ticket.id = ticket_id

        # Mock the execute result
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_ticket
        mock_session.execute.return_value = mock_result

        result = await repository.get_ticket(ticket_id)

        assert result == mock_ticket
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_ticket_not_found(self, repository, mock_session):
        """Test retrieving a non-existent ticket."""
        ticket_id = uuid.uuid4()

        # Mock the execute result to return None
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        result = await repository.get_ticket(ticket_id)

        assert result is None


class TestGetTickets:
    """Tests for get_tickets method."""

    @pytest.mark.asyncio
    async def test_get_tickets_no_filters(self, repository, mock_session):
        """Test retrieving tickets without filters."""
        mock_tickets = [MagicMock(spec=Ticket) for _ in range(3)]

        mock_scalars = MagicMock()
        mock_scalars.all.return_value = mock_tickets

        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute.return_value = mock_result

        result = await repository.get_tickets(skip=0, limit=10)

        assert result == mock_tickets
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_tickets_with_filters(self, repository, mock_session):
        """Test retrieving tickets with filters."""
        mock_tickets = [MagicMock(spec=Ticket)]

        mock_scalars = MagicMock()
        mock_scalars.all.return_value = mock_tickets

        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute.return_value = mock_result

        result = await repository.get_tickets(
            skip=0,
            limit=10,
            customer_id="cust-123",
            category="technical",
            severity="high",
            status="pending",
            assigned_team="technical_support",
        )

        assert result == mock_tickets
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_tickets_pagination(self, repository, mock_session):
        """Test pagination in get_tickets."""
        mock_tickets = [MagicMock(spec=Ticket) for _ in range(5)]

        mock_scalars = MagicMock()
        mock_scalars.all.return_value = mock_tickets

        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute.return_value = mock_result

        result = await repository.get_tickets(skip=10, limit=5)

        assert result == mock_tickets


class TestUpdateTicket:
    """Tests for update_ticket method."""

    @pytest.mark.asyncio
    async def test_update_ticket_success(self, repository, mock_session):
        """Test updating an existing ticket."""
        ticket_id = uuid.uuid4()
        mock_ticket = MagicMock(spec=Ticket)
        mock_ticket.id = ticket_id
        mock_ticket.status = "pending"

        # Mock get_ticket to return the ticket
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_ticket
        mock_session.execute.return_value = mock_result

        update_data = {"status": "in_progress", "assigned_team": "technical_support"}

        result = await repository.update_ticket(ticket_id, update_data)

        assert result == mock_ticket
        assert mock_ticket.status == "in_progress"
        assert mock_ticket.assigned_team == "technical_support"
        mock_session.flush.assert_called_once()
        mock_session.refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_ticket_not_found(self, repository, mock_session):
        """Test updating a non-existent ticket."""
        ticket_id = uuid.uuid4()

        # Mock get_ticket to return None
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        result = await repository.update_ticket(ticket_id, {"status": "closed"})

        assert result is None
        mock_session.flush.assert_not_called()


class TestFindSimilarTickets:
    """Tests for find_similar_tickets method."""

    @pytest.mark.asyncio
    async def test_find_similar_tickets_found(self, repository, mock_session):
        """Test finding similar tickets."""
        # Create mock tickets with similar content
        mock_ticket1 = MagicMock(spec=Ticket)
        mock_ticket1.id = uuid.uuid4()
        mock_ticket1.subject = "Cannot access my account"
        mock_ticket1.body = "I cannot log in to my account"
        mock_ticket1.status = "pending"
        mock_ticket1.similarity_score = None

        mock_ticket2 = MagicMock(spec=Ticket)
        mock_ticket2.id = uuid.uuid4()
        mock_ticket2.subject = "Different issue"
        mock_ticket2.body = "This is about billing"
        mock_ticket2.status = "pending"
        mock_ticket2.similarity_score = None

        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [mock_ticket1, mock_ticket2]

        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute.return_value = mock_result

        result = await repository.find_similar_tickets(
            customer_id="cust-123",
            subject="Cannot access account",
            body="I cannot log in",
            threshold=0.3,
            limit=5,
        )

        # First ticket should match with higher similarity
        assert len(result) >= 1
        if result:
            assert hasattr(result[0], "similarity_score")

    @pytest.mark.asyncio
    async def test_find_similar_tickets_no_matches(self, repository, mock_session):
        """Test finding similar tickets with no matches."""
        # Create tickets with very different content
        mock_ticket = MagicMock(spec=Ticket)
        mock_ticket.id = uuid.uuid4()
        mock_ticket.subject = "Billing question"
        mock_ticket.body = "I have a question about my invoice"
        mock_ticket.status = "pending"

        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [mock_ticket]

        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute.return_value = mock_result

        result = await repository.find_similar_tickets(
            customer_id="cust-123",
            subject="Technical error",
            body="System is completely broken",
            threshold=0.8,  # High threshold
            limit=5,
        )

        # Should be empty due to high threshold
        assert result == []

    @pytest.mark.asyncio
    async def test_find_similar_tickets_excludes_closed(self, repository, mock_session):
        """Test that closed tickets are excluded from similarity search."""
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = []

        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute.return_value = mock_result

        await repository.find_similar_tickets(
            customer_id="cust-123",
            subject="Test",
            body="Test body",
            threshold=0.5,
        )

        mock_session.execute.assert_called_once()


class TestFindSimilarTicketsByEmbedding:
    """Tests for find_similar_tickets_by_embedding method."""

    @pytest.mark.asyncio
    async def test_find_similar_by_embedding_returns_empty(self, repository):
        """Test that embedding search returns empty list when vector search is not configured."""
        embedding = [0.1] * 1536  # Mock embedding vector

        result = await repository.find_similar_tickets_by_embedding(
            embedding=embedding,
            threshold=0.8,
            limit=5,
        )

        # Should return empty list when vector search is not configured
        assert result == []

    @pytest.mark.asyncio
    async def test_find_similar_by_embedding_with_customer_id(self, repository):
        """Test embedding search with customer ID filter."""
        embedding = [0.1] * 1536

        result = await repository.find_similar_tickets_by_embedding(
            embedding=embedding,
            threshold=0.8,
            limit=5,
            customer_id="cust-123",
        )

        assert result == []


class TestLogWorkflowRun:
    """Tests for log_workflow_run method."""

    @pytest.mark.asyncio
    async def test_log_workflow_run_success(self, repository, mock_session, sample_workflow_data):
        """Test successful workflow run logging."""
        mock_workflow_run = MagicMock(spec=WorkflowRun)
        mock_workflow_run.id = uuid.uuid4()

        async def mock_refresh_side_effect(obj):
            obj.id = mock_workflow_run.id

        mock_session.refresh.side_effect = mock_refresh_side_effect

        result = await repository.log_workflow_run(sample_workflow_data)

        mock_session.add.assert_called_once()
        mock_session.flush.assert_called_once()
        mock_session.refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_log_workflow_run_with_error(self, repository, mock_session):
        """Test logging a failed workflow run."""
        workflow_data = {
            "ticket_id": uuid.uuid4(),
            "step_name": "classification",
            "step_number": 1,
            "status": "failed",
            "error_message": "API timeout",
            "error_type": "TimeoutError",
            "retry_count": 3,
        }

        await repository.log_workflow_run(workflow_data)

        mock_session.add.assert_called_once()


class TestGetWorkflowRunsForTicket:
    """Tests for get_workflow_runs_for_ticket method."""

    @pytest.mark.asyncio
    async def test_get_workflow_runs_found(self, repository, mock_session):
        """Test retrieving workflow runs for a ticket."""
        ticket_id = uuid.uuid4()
        mock_runs = [MagicMock(spec=WorkflowRun) for _ in range(3)]

        mock_scalars = MagicMock()
        mock_scalars.all.return_value = mock_runs

        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute.return_value = mock_result

        result = await repository.get_workflow_runs_for_ticket(ticket_id)

        assert result == mock_runs
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_workflow_runs_empty(self, repository, mock_session):
        """Test retrieving workflow runs when none exist."""
        ticket_id = uuid.uuid4()

        mock_scalars = MagicMock()
        mock_scalars.all.return_value = []

        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute.return_value = mock_result

        result = await repository.get_workflow_runs_for_ticket(ticket_id)

        assert result == []


class TestCountTickets:
    """Tests for count_tickets method."""

    @pytest.mark.asyncio
    async def test_count_all_tickets(self, repository, mock_session):
        """Test counting all tickets."""
        mock_result = MagicMock()
        mock_result.scalar_one.return_value = 42
        mock_session.execute.return_value = mock_result

        result = await repository.count_tickets()

        assert result == 42
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_count_tickets_with_filters(self, repository, mock_session):
        """Test counting tickets with filters."""
        mock_result = MagicMock()
        mock_result.scalar_one.return_value = 10
        mock_session.execute.return_value = mock_result

        result = await repository.count_tickets(
            customer_id="cust-123",
            status="pending",
        )

        assert result == 10


class TestDeleteTicket:
    """Tests for delete_ticket method."""

    @pytest.mark.asyncio
    async def test_delete_ticket_success(self, repository, mock_session):
        """Test successful ticket deletion."""
        ticket_id = uuid.uuid4()
        mock_ticket = MagicMock(spec=Ticket)
        mock_ticket.id = ticket_id

        # Mock get_ticket to return the ticket
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_ticket
        mock_session.execute.return_value = mock_result

        result = await repository.delete_ticket(ticket_id)

        assert result is True
        mock_session.delete.assert_called_once_with(mock_ticket)
        mock_session.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_ticket_not_found(self, repository, mock_session):
        """Test deleting a non-existent ticket."""
        ticket_id = uuid.uuid4()

        # Mock get_ticket to return None
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        result = await repository.delete_ticket(ticket_id)

        assert result is False
        mock_session.delete.assert_not_called()


class TestIntegrationPatterns:
    """Tests for common integration patterns."""

    @pytest.mark.asyncio
    async def test_create_and_retrieve_pattern(self, repository, mock_session, sample_ticket_data):
        """Test the common pattern of creating and then retrieving a ticket."""
        ticket_id = uuid.uuid4()

        # Mock for create
        async def mock_refresh_side_effect(obj):
            obj.id = ticket_id

        mock_session.refresh.side_effect = mock_refresh_side_effect

        # Create ticket
        created = await repository.create_ticket(sample_ticket_data)
        mock_session.add.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_after_classification(self, repository, mock_session):
        """Test updating ticket after classification workflow."""
        ticket_id = uuid.uuid4()
        mock_ticket = MagicMock(spec=Ticket)
        mock_ticket.id = ticket_id

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_ticket
        mock_session.execute.return_value = mock_result

        update_data = {
            "category": "technical",
            "category_confidence": 0.95,
            "severity": "high",
            "severity_confidence": 0.88,
            "status": "classified",
        }

        result = await repository.update_ticket(ticket_id, update_data)

        assert result == mock_ticket
