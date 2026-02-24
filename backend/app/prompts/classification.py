"""
Classification prompt template for support ticket categorization.

This prompt is used to classify tickets into categories and assign severity levels.
Uses Jinja2-style variable substitution for reusability.
"""

CLASSIFICATION_PROMPT = """You are a support ticket classifier. Analyze the following ticket and classify it.

TICKET SUBJECT: {{ subject }}
TICKET BODY: {{ body }}

AVAILABLE CATEGORIES: {{ categories }}
SEVERITY LEVELS: critical, high, medium, low

Respond with JSON:
{
    "category": "category_name",
    "category_confidence": 0.0-1.0,
    "severity": "severity_level",
    "severity_confidence": 0.0-1.0,
    "secondary_categories": ["sub1", "sub2"],
    "reasoning": "brief explanation",
    "keywords_matched": ["keyword1", "keyword2"],
    "urgency_indicators": ["indicator1"]
}"""
