#!/usr/bin/env python3
"""
Uvicorn server startup script for Support Ticket AI Workflow.

This module provides the entry point for running the FastAPI application
using Uvicorn ASGI server.

Usage:
    python run.py

Environment Variables:
    HOST: Server host (default: 0.0.0.0)
    PORT: Server port (default: 8000)
    RELOAD: Enable auto-reload for development (default: True)
    WORKERS: Number of worker processes (default: 1)
"""

import logging
import os
import sys

import uvicorn

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.config import settings

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stdout,
)

logger = logging.getLogger(__name__)


def main():
    """
    Run the FastAPI application using Uvicorn.

    Server configuration is loaded from environment variables:
    - HOST: Server host address (default: 0.0.0.0)
    - PORT: Server port (default: 8000)
    - RELOAD: Enable auto-reload (default: True in debug mode)
    - WORKERS: Number of worker processes (default: 1)
    """
    # Server configuration
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    reload = os.getenv("RELOAD", str(settings.DEBUG)).lower() in ("true", "1", "yes")
    workers = int(os.getenv("WORKERS", "1"))

    logger.info(f"Starting {settings.APP_NAME}")
    logger.info(f"Host: {host}")
    logger.info(f"Port: {port}")
    logger.info(f"Debug: {settings.DEBUG}")
    logger.info(f"Reload: {reload}")
    logger.info(f"Workers: {workers}")
    logger.info(f"AI enabled: {settings.is_ai_enabled}")

    # Run Uvicorn server
    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=reload,
        workers=workers if not reload else 1,  # Workers not supported with reload
        log_level=settings.LOG_LEVEL.lower(),
        access_log=True,
        use_colors=True,
    )


if __name__ == "__main__":
    main()
