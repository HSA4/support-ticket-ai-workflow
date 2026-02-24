"""
Workflow orchestration and step implementations.

This module provides the core workflow components for processing
support tickets through classification, extraction, response
generation, and routing steps.
"""

from app.services.workflow.orchestrator import (
    WorkflowOrchestrator,
    WorkflowContext,
    process_ticket,
)
from app.services.workflow.classifiers import (
    TicketClassifier,
    CATEGORY_KEYWORDS,
    SEVERITY_INDICATORS,
    VALID_CATEGORIES,
    VALID_SEVERITIES,
)
from app.services.workflow.extractors import (
    FieldExtractor,
    EXTRACTION_PATTERNS,
    PRIORITY_KEYWORDS,
    CATEGORY_REQUIRED_FIELDS,
    VALIDATION_PATTERNS,
)
from app.services.workflow.generators import (
    ResponseGenerator,
    RESPONSE_TEMPLATES,
    RESPONSE_TIMES,
    TEAM_SIGNATURES,
    generate_response,
)
from app.services.workflow.routers import (
    TicketRouter,
    DEFAULT_TEAMS,
    DEFAULT_ESCALATION_PATHS,
    CATEGORY_TEAM_MAP,
    SEVERITY_PRIORITY_MAP,
    route_ticket,
)
from app.services.workflow.validators import (
    InputValidator,
    ValidationResult,
    PROMPT_INJECTION_PATTERNS,
    validate_ticket,
)

__all__ = [
    # Orchestrator
    "WorkflowOrchestrator",
    "WorkflowContext",
    "process_ticket",
    # Classifiers
    "TicketClassifier",
    "CATEGORY_KEYWORDS",
    "SEVERITY_INDICATORS",
    "VALID_CATEGORIES",
    "VALID_SEVERITIES",
    # Extractors
    "FieldExtractor",
    "EXTRACTION_PATTERNS",
    "PRIORITY_KEYWORDS",
    "CATEGORY_REQUIRED_FIELDS",
    "VALIDATION_PATTERNS",
    # Generators
    "ResponseGenerator",
    "RESPONSE_TEMPLATES",
    "RESPONSE_TIMES",
    "TEAM_SIGNATURES",
    "generate_response",
    # Routers
    "TicketRouter",
    "DEFAULT_TEAMS",
    "DEFAULT_ESCALATION_PATHS",
    "CATEGORY_TEAM_MAP",
    "SEVERITY_PRIORITY_MAP",
    "route_ticket",
    # Validators
    "InputValidator",
    "ValidationResult",
    "PROMPT_INJECTION_PATTERNS",
    "validate_ticket",
]
