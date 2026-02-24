"""
Field extraction prompt template for support ticket data extraction.

This prompt is used to extract structured fields from unstructured ticket text.
Uses Jinja2-style variable substitution for reusability.
"""

EXTRACTION_PROMPT = """Extract structured information from this support ticket.

TICKET SUBJECT: {{ subject }}
TICKET BODY: {{ body }}
CATEGORY: {{ category }}

Extract the following fields if present:
- order_id: Order or transaction ID (formats: ORD-XXXXX, #XXXXX)
- product_name: Product or service mentioned
- error_code: Error codes or messages (e.g., ERR-XXXX, 0xXXXX)
- account_email: Email addresses mentioned
- phone_number: Phone numbers
- priority_keywords: Urgency words found

Respond with JSON:
{
    "fields": [
        {"name": "field_name", "value": "extracted_value", "confidence": 0.0-1.0, "source_text": "original text"}
    ],
    "missing_critical": ["field1"],
    "validation_errors": []
}"""
