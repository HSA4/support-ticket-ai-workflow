"""
Configuration management for the Support Ticket AI Workflow.

This module defines application settings using pydantic-settings for
environment variable parsing and validation.
"""

from functools import lru_cache
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    Attributes:
        APP_NAME: Name of the application
        DEBUG: Debug mode flag
        LOG_LEVEL: Logging level

        DATABASE_URL: PostgreSQL connection URL with asyncpg driver

        OPENAI_API_KEY: OpenAI API key for LLM calls
        DEFAULT_MODEL: Default OpenAI model to use
        MAX_TOKENS: Maximum tokens for LLM responses

        WORKFLOW_TIMEOUT_SECONDS: Timeout for workflow execution

        ENABLE_AI_CLASSIFICATION: Feature flag for AI classification
        ENABLE_AI_EXTRACTION: Feature flag for AI field extraction
        ENABLE_RESPONSE_GENERATION: Feature flag for AI response generation

        AI_CONFIDENCE_THRESHOLD: Minimum confidence to use AI results
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )

    # Application Configuration
    APP_NAME: str = "Support Ticket AI Workflow"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    # Database Configuration
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/ticket_workflow",
        description="PostgreSQL connection URL with asyncpg driver",
    )

    # OpenAI Configuration
    OPENAI_API_KEY: str = Field(
        default="",
        description="OpenAI API key for LLM calls",
    )
    DEFAULT_MODEL: str = Field(
        default="gpt-4-turbo-preview",
        description="Default OpenAI model to use",
    )
    MAX_TOKENS: int = Field(
        default=4096,
        description="Maximum tokens for LLM responses",
        ge=1,
        le=128000,
    )

    # Workflow Configuration
    WORKFLOW_TIMEOUT_SECONDS: int = Field(
        default=30,
        description="Timeout for workflow execution in seconds",
        ge=5,
        le=300,
    )

    # Feature Flags
    ENABLE_AI_CLASSIFICATION: bool = Field(
        default=True,
        description="Enable AI-based classification (fallback to rule-based if False)",
    )
    ENABLE_AI_EXTRACTION: bool = Field(
        default=True,
        description="Enable AI-based field extraction",
    )
    ENABLE_RESPONSE_GENERATION: bool = Field(
        default=True,
        description="Enable AI response generation (fallback to templates if False)",
    )

    # AI Configuration
    AI_CONFIDENCE_THRESHOLD: float = Field(
        default=0.6,
        description="Minimum confidence score to use AI results",
        ge=0.0,
        le=1.0,
    )

    @property
    def is_ai_enabled(self) -> bool:
        """Check if any AI features are enabled."""
        return (
            self.ENABLE_AI_CLASSIFICATION
            or self.ENABLE_AI_EXTRACTION
            or self.ENABLE_RESPONSE_GENERATION
        )

    @property
    def async_database_url(self) -> str:
        """Get the async database URL."""
        if self.DATABASE_URL.startswith("postgresql://"):
            return self.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)
        return self.DATABASE_URL


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached application settings.

    Uses lru_cache to ensure settings are only loaded once.

    Returns:
        Settings: Application settings instance
    """
    return Settings()


# Global settings instance for convenience
settings = get_settings()
