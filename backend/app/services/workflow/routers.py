"""
Routing decision module for the support ticket workflow.

This module provides routing functionality for support tickets,
including rule-based routing and optional AI-assisted routing.
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from app.core.config import settings
from app.schemas import RoutingDecision

logger = logging.getLogger(__name__)

# Path to routing configuration file
ROUTING_CONFIG_PATH = Path(__file__).parent.parent.parent.parent / "config" / "routing_rules.yaml"

# Default team definitions
DEFAULT_TEAMS = {
    "technical_support": {
        "categories": ["technical", "bug_report"],
        "description": "Technical issues, bugs, errors",
        "priority_modifier": 0,
    },
    "billing_team": {
        "categories": ["billing"],
        "description": "Payment, subscription, refund issues",
        "priority_modifier": 0,
    },
    "account_management": {
        "categories": ["account"],
        "description": "Account access, security, permissions",
        "priority_modifier": 0,
    },
    "product_team": {
        "categories": ["feature_request"],
        "description": "Feature requests, product feedback",
        "priority_modifier": 1,
    },
    "escalation_team": {
        "severities": ["critical"],
        "description": "Critical issues requiring senior review",
        "priority_modifier": -1,
    },
}

# Default escalation paths
DEFAULT_ESCALATION_PATHS = {
    "technical_support": ["senior_technical", "engineering_team"],
    "billing_team": ["billing_manager", "finance_team"],
    "account_management": ["account_manager", "security_team"],
    "product_team": ["product_manager"],
    "escalation_team": ["senior_management"],
}

# Category to team mapping (fallback)
CATEGORY_TEAM_MAP = {
    "technical": "technical_support",
    "billing": "billing_team",
    "account": "account_management",
    "feature_request": "product_team",
    "bug_report": "technical_support",
    "general": "technical_support",
}

# Severity to priority mapping
SEVERITY_PRIORITY_MAP = {
    "critical": "urgent",
    "high": "high",
    "medium": "normal",
    "low": "low",
}

# Routing rules list with conditions
ROUTING_RULES: List[Dict[str, Any]] = [
    {
        "condition": {"severity": "critical"},
        "team": "escalation_team",
        "priority": "urgent",
        "reasoning": "Critical issues require immediate escalation",
    },
    {
        "condition": {"category": "billing"},
        "team": "billing_team",
        "priority": "normal",
        "reasoning": "Billing inquiries are handled by the billing team",
    },
    {
        "condition": {"category": "account"},
        "team": "account_management",
        "priority": "normal",
        "reasoning": "Account issues are handled by account management",
    },
    {
        "condition": {"category": "technical"},
        "team": "technical_support",
        "priority": "normal",
        "reasoning": "Technical issues are handled by technical support",
    },
    {
        "condition": {"category": "bug_report"},
        "team": "technical_support",
        "priority": "high",
        "reasoning": "Bug reports are handled by technical support with high priority",
    },
    {
        "condition": {"category": "feature_request"},
        "team": "product_team",
        "priority": "low",
        "reasoning": "Feature requests are reviewed by the product team",
    },
]


def _load_routing_config() -> Optional[Dict[str, Any]]:
    """Load routing configuration from YAML file."""
    try:
        if ROUTING_CONFIG_PATH.exists():
            with open(ROUTING_CONFIG_PATH, "r") as f:
                return yaml.safe_load(f)
    except Exception as e:
        logger.warning(f"Failed to load routing config from {ROUTING_CONFIG_PATH}: {e}")
    return None


class TicketRouter:
    """
    Ticket router for team assignment.

    This class provides methods to route support tickets to appropriate
    teams based on category, severity, and extracted fields using
    rule-based logic.

    Attributes:
        teams: Dictionary of team definitions
        escalation_paths: Dictionary of escalation paths by team
    """

    def __init__(self):
        """Initialize the ticket router."""
        # Load configuration if available
        config = _load_routing_config()

        if config and "teams" in config:
            self.teams = {}
            for team in config["teams"]:
                team_name = team.get("name", "")
                if team_name:
                    self.teams[team_name] = {
                        "categories": team.get("categories", []),
                        "severities": team.get("severities", []),
                        "description": team.get("description", ""),
                        "priority_modifier": team.get("priority_modifier", 0),
                    }
        else:
            self.teams = DEFAULT_TEAMS.copy()

        # Load escalation paths
        if config and "escalation_paths" in config:
            self.escalation_paths = config["escalation_paths"]
        else:
            self.escalation_paths = DEFAULT_ESCALATION_PATHS.copy()

        logger.debug(f"Loaded {len(self.teams)} team definitions for routing")

    def route(
        self,
        subject: str,
        body: str,
        category: str,
        severity: str,
        extracted_fields: Optional[Dict[str, Any]] = None,
    ) -> RoutingDecision:
        """
        Route a support ticket to the appropriate team.

        Args:
            subject: Ticket subject line
            body: Ticket body content
            category: Ticket category
            severity: Ticket severity level
            extracted_fields: Dictionary of extracted fields

        Returns:
            RoutingDecision with team assignment and reasoning
        """
        extracted_fields = extracted_fields or {}

        # Step 1: Check for critical severity (escalation team)
        if severity == "critical":
            return self._build_routing_decision(
                team="escalation_team",
                priority="urgent",
                category=category,
                severity=severity,
                reason="Critical severity requires escalation team",
            )

        # Step 2: Find best team based on category
        best_team = self._find_team_by_category(category)

        # Step 3: Determine priority based on severity
        priority = SEVERITY_PRIORITY_MAP.get(severity, "normal")

        # Step 4: Apply priority modifiers
        priority = self._apply_priority_modifier(best_team, priority, severity)

        # Step 5: Find alternative teams
        alternative_teams = self._find_alternative_teams(category, best_team)

        # Build reasoning
        reasoning = self._build_reasoning(best_team, category, severity, extracted_fields)

        return RoutingDecision(
            team=best_team,
            priority=priority,
            reasoning=reasoning,
            alternative_teams=alternative_teams,
            escalation_path=self.escalation_paths.get(best_team),
            confidence=self._calculate_confidence(category, severity),
        )

    def _find_team_by_category(self, category: str) -> str:
        """
        Find the best team for a given category.

        Args:
            category: Ticket category

        Returns:
            Team name
        """
        # Check each team's category list
        for team_name, team_def in self.teams.items():
            if team_name == "escalation_team":
                continue  # Skip escalation team for category matching
            if category in team_def.get("categories", []):
                return team_name

        # Fallback to category mapping
        return CATEGORY_TEAM_MAP.get(category, "technical_support")

    def _apply_priority_modifier(
        self,
        team: str,
        priority: str,
        severity: str,
    ) -> str:
        """
        Apply priority modifier based on team and severity.

        Args:
            team: Team name
            priority: Current priority
            severity: Ticket severity

        Returns:
            Adjusted priority
        """
        team_def = self.teams.get(team, {})
        modifier = team_def.get("priority_modifier", 0)

        priority_levels = ["low", "normal", "high", "urgent"]
        current_idx = priority_levels.index(priority) if priority in priority_levels else 1

        # Apply modifier
        new_idx = max(0, min(len(priority_levels) - 1, current_idx + modifier))

        return priority_levels[new_idx]

    def _find_alternative_teams(
        self,
        category: str,
        primary_team: str,
    ) -> List[str]:
        """
        Find alternative teams that could handle this ticket.

        Args:
            category: Ticket category
            primary_team: The primary team assignment

        Returns:
            List of alternative team names
        """
        alternatives = []

        for team_name, team_def in self.teams.items():
            if team_name == primary_team:
                continue
            if team_name == "escalation_team":
                continue

            # Check if team handles this category
            if category in team_def.get("categories", []):
                alternatives.append(team_name)

        # If no alternatives found by category, add generalist teams
        if not alternatives:
            if primary_team != "technical_support":
                alternatives.append("technical_support")

        return alternatives[:2]  # Limit to 2 alternatives

    def _build_reasoning(
        self,
        team: str,
        category: str,
        severity: str,
        extracted_fields: Dict[str, Any],
    ) -> str:
        """
        Build human-readable reasoning for the routing decision.

        Args:
            team: Team name
            category: Ticket category
            severity: Ticket severity
            extracted_fields: Extracted fields

        Returns:
            Reasoning string
        """
        parts = [f"Routed to {team}"]

        # Add category context
        team_def = self.teams.get(team, {})
        if team_def.get("description"):
            parts.append(f"({team_def['description']})")

        parts.append(f"based on {category} category")

        # Add severity context
        if severity in ["critical", "high"]:
            parts.append(f"with {severity} priority")

        # Add extracted field context
        if extracted_fields:
            field_names = list(extracted_fields.keys())[:3]
            if field_names:
                parts.append(f"and detected fields: {', '.join(field_names)}")

        return " ".join(parts) + "."

    def _build_routing_decision(
        self,
        team: str,
        priority: str,
        category: str,
        severity: str,
        reason: str,
    ) -> RoutingDecision:
        """
        Build a routing decision with standard fields.

        Args:
            team: Team name
            priority: Priority level
            category: Ticket category
            severity: Ticket severity
            reason: Reasoning string

        Returns:
            RoutingDecision instance
        """
        return RoutingDecision(
            team=team,
            priority=priority,
            reasoning=reason,
            alternative_teams=["technical_support"],
            escalation_path=self.escalation_paths.get(team),
            confidence=0.95,  # High confidence for critical/escalation
        )

    def _calculate_confidence(
        self,
        category: str,
        severity: str,
    ) -> float:
        """
        Calculate confidence score for routing decision.

        Args:
            category: Ticket category
            severity: Ticket severity

        Returns:
            Confidence score between 0.0 and 1.0
        """
        base_confidence = 0.8

        # Boost for clear category-team mapping
        for team_def in self.teams.values():
            if category in team_def.get("categories", []):
                base_confidence += 0.1
                break

        # Boost for high severity (clearer routing)
        if severity in ["critical", "high"]:
            base_confidence += 0.05

        return min(0.95, base_confidence)

    def get_team_for_category(self, category: str) -> str:
        """
        Get the default team for a category.

        Args:
            category: Ticket category

        Returns:
            Team name
        """
        return self._find_team_by_category(category)

    def get_escalation_path(self, team: str) -> Optional[List[str]]:
        """
        Get the escalation path for a team.

        Args:
            team: Team name

        Returns:
            List of escalation steps or None
        """
        return self.escalation_paths.get(team)

    def get_available_teams(self) -> List[str]:
        """
        Get list of available teams.

        Returns:
            List of team names
        """
        return list(self.teams.keys())


def route_ticket(
    subject: str,
    body: str,
    category: str,
    severity: str,
    extracted_fields: Optional[Dict[str, Any]] = None,
) -> RoutingDecision:
    """
    Convenience function to route a ticket.

    Args:
        subject: Ticket subject line
        body: Ticket body content
        category: Ticket category
        severity: Ticket severity level
        extracted_fields: Dictionary of extracted fields

    Returns:
        RoutingDecision
    """
    router = TicketRouter()
    return router.route(
        subject=subject,
        body=body,
        category=category,
        severity=severity,
        extracted_fields=extracted_fields,
    )
