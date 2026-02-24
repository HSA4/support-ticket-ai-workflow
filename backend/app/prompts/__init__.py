"""
Prompt templates for the Support Ticket AI Workflow.

This module contains Jinja2-style prompt templates for:
- Classification: Categorize tickets and assign severity
- Extraction: Extract structured fields from ticket content
- Response: Generate contextual response drafts
- Routing: Determine team assignment for tickets
"""

from .classification import CLASSIFICATION_PROMPT
from .extraction import EXTRACTION_PROMPT
from .response import RESPONSE_GENERATION_PROMPT
from .routing import ROUTING_PROMPT

__all__ = [
    "CLASSIFICATION_PROMPT",
    "EXTRACTION_PROMPT",
    "RESPONSE_GENERATION_PROMPT",
    "ROUTING_PROMPT",
]
