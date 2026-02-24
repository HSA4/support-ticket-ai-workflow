"""
FastAPI application entry point for Support Ticket AI Workflow.

This module creates and configures the FastAPI application with:
- API routers for workflow and tickets
- CORS middleware
- Exception handlers
- Health check endpoint
"""

import logging
import sys
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, Dict

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, ValidationError

from app.api.v1 import tickets, workflow
from app.core.config import settings
from app.db.session import close_db, init_db

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stdout,
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.

    Handles startup and shutdown events for the application.
    """
    # Startup
    logger.info(f"Starting {settings.APP_NAME}...")
    logger.info(f"Debug mode: {settings.DEBUG}")
    logger.info(f"AI features enabled: {settings.is_ai_enabled}")

    try:
        # Initialize database
        logger.info("Initializing database connection...")
        await init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.warning(f"Database initialization skipped: {e}")
        logger.info("Running without database persistence")

    yield

    # Shutdown
    logger.info(f"Shutting down {settings.APP_NAME}...")
    try:
        await close_db()
        logger.info("Database connections closed")
    except Exception as e:
        logger.warning(f"Error closing database: {e}")


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    description="""
    AI-powered support ticket workflow system that processes tickets through:

    * **Classification** - Category and severity assignment
    * **Field Extraction** - Structured data extraction from ticket content
    * **Response Drafting** - Contextual response generation
    * **Team Routing** - Intelligent assignment to appropriate teams

    ## Endpoints

    * `/api/v1/workflow/process` - Full pipeline processing
    * `/api/v1/workflow/classify` - Classification only
    * `/api/v1/workflow/extract` - Field extraction only
    * `/api/v1/workflow/respond` - Response generation only
    * `/api/v1/workflow/route` - Routing decision only
    * `/api/v1/tickets` - List processed tickets
    * `/api/v1/tickets/{id}` - Get ticket with workflow details
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)


# ============================================================================
# CORS Middleware
# ============================================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# Exception Handlers
# ============================================================================


@app.exception_handler(ValidationError)
async def validation_exception_handler(
    request: Request,
    exc: ValidationError,
) -> JSONResponse:
    """
    Handle Pydantic validation errors.

    Args:
        request: The request that caused the error
        exc: The validation error

    Returns:
        JSON response with error details
    """
    logger.warning(f"Validation error: {exc}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Validation error",
            "errors": exc.errors(),
        },
    )


@app.exception_handler(ValueError)
async def value_error_handler(
    request: Request,
    exc: ValueError,
) -> JSONResponse:
    """
    Handle value errors.

    Args:
        request: The request that caused the error
        exc: The value error

    Returns:
        JSON response with error details
    """
    logger.warning(f"Value error: {exc}")
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "detail": str(exc),
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """
    Handle unexpected exceptions.

    Args:
        request: The request that caused the error
        exc: The exception

    Returns:
        JSON response with error details
    """
    logger.exception(f"Unexpected error: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Internal server error",
            "message": str(exc) if settings.DEBUG else "An unexpected error occurred",
        },
    )


# ============================================================================
# Routers
# ============================================================================

app.include_router(workflow.router, prefix="/api/v1")
app.include_router(tickets.router, prefix="/api/v1")


# ============================================================================
# Health Check
# ============================================================================


class HealthResponse(BaseModel):
    """Schema for health check response."""

    status: str = "healthy"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    version: str = "1.0.0"
    ai_enabled: bool = True


@app.get(
    "/health",
    response_model=HealthResponse,
    tags=["health"],
    summary="Health check endpoint",
    description="Returns the health status of the API service.",
)
async def health_check() -> HealthResponse:
    """
    Health check endpoint.

    Returns:
        Health status with timestamp and version info
    """
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow(),
        version="1.0.0",
        ai_enabled=settings.is_ai_enabled,
    )


@app.get(
    "/",
    tags=["root"],
    summary="Root endpoint",
    description="Returns basic API information.",
)
async def root() -> Dict[str, Any]:
    """
    Root endpoint providing API information.

    Returns:
        Basic API information
    """
    return {
        "name": settings.APP_NAME,
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
    }


# ============================================================================
# Application Events (for logging)
# ============================================================================


@app.on_event("startup")
async def startup_event():
    """Log application startup."""
    logger.info(f"{settings.APP_NAME} started successfully")


@app.on_event("shutdown")
async def shutdown_event():
    """Log application shutdown."""
    logger.info(f"{settings.APP_NAME} shutting down")
