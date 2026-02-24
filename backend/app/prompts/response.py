"""
Response generation prompt template for support ticket responses.

This prompt is used to generate contextual response drafts based on ticket classification.
Uses Jinja2-style variable substitution for reusability.
"""

RESPONSE_GENERATION_PROMPT = """You are drafting a customer support response. Be professional, empathetic, and helpful.

TICKET SUBJECT: {{ subject }}
TICKET BODY: {{ body }}
CATEGORY: {{ category }}
SEVERITY: {{ severity }}
EXTRACTED CONTEXT: {{ extracted_fields }}
CUSTOMER_NAME: {{ customer_name }}

Guidelines:
- Acknowledge the issue specifically
- Show empathy for their situation
- Provide clear next steps
- Set appropriate expectations based on severity
- Use {{ tone }} tone
- Keep response concise but complete

Respond with JSON:
{
    "greeting": "personalized greeting",
    "acknowledgment": "acknowledge specific issue",
    "explanation": "brief explanation if applicable",
    "action_items": ["step 1", "step 2"],
    "timeline": "expected resolution timeframe",
    "closing": "professional closing",
    "full_response": "complete formatted response",
    "requires_escalation": true/false
}"""
