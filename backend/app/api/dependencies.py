"""
Dependency injection for FastAPI endpoints.

This module provides dependency injection functions for:
- Database sessions
- Workflow orchestrator
- AI service
"""

from functools import lru_cache
from typing import AsyncGenerator, Optional

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import async_session_factory
from app.services.ai_service import AIService
from app.services.workflow.orchestrator import WorkflowOrchestrator


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency that provides an async database session.

    Yields:
        AsyncSession: Database session instance

    The session is automatically committed on success
    and rolled back on error.
    """
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


@lru_cache()
def get_ai_service() -> AIService:
    """
    Get cached AIService instance.

    Uses lru_cache to ensure a single instance is reused.

    Returns:
        AIService: Cached AI service instance
    """
    return AIService()


def get_workflow_orchestrator(
    ai_service: AIService = Depends(get_ai_service),
) -> WorkflowOrchestrator:
    """
    Dependency that provides a WorkflowOrchestrator instance.

    Args:
        ai_service: Injected AIService instance

    Returns:
        WorkflowOrchestrator: Orchestrator configured with AI service
    """
    return WorkflowOrchestrator(
        ai_service=ai_service,
        enable_ai=settings.is_ai_enabled,
    )


def get_optional_ai_service() -> Optional[AIService]:
    """
    Get optional AIService instance (None if not configured).

    Returns:
        Optional[AIService]: AI service instance or None
    """
    if not settings.OPENAI_API_KEY:
        return None
    return AIService()
