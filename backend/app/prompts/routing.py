"""
Routing decision prompt template for support ticket team assignment.

This prompt is used to determine the best team to handle a support ticket.
Uses Jinja2-style variable substitution for reusability.
"""

ROUTING_PROMPT = """Determine the best team to handle this support ticket.

TICKET SUBJECT: {{ subject }}
TICKET BODY: {{ body }}
CATEGORY: {{ category }}
SEVERITY: {{ severity }}
EXTRACTED CONTEXT: {{ extracted_fields }}

AVAILABLE TEAMS: {{ teams }}

TEAM DESCRIPTIONS:
- technical_support: Technical issues, bugs, errors
- billing_team: Payment, subscription, refund issues
- account_management: Account access, security, permissions
- product_team: Feature requests, product feedback
- escalation_team: Critical issues requiring senior review

Routing rules:
- CRITICAL severity -> escalation_team
- Billing category -> billing_team
- Account access issues -> account_management
- Technical complexity -> technical_support
- Default -> general_support

Respond with JSON:
{
    "team": "team_name",
    "priority": "urgent/high/normal/low",
    "reasoning": "why this team",
    "alternative_teams": [{"team": "name", "reason": "why also suitable"}],
    "escalation_path": ["next_team_if_needed"]
}"""
