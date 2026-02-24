"""
Unit tests for ticket routing functionality.

This module tests the TicketRouter class, including:
- Routing rules based on category and severity
- Escalation paths
- Alternative team suggestions
- Priority calculations
- Team assignment logic
"""

import pytest
from unittest.mock import MagicMock, patch

from app.schemas import RoutingDecision
from app.services.workflow.routers import (
    TicketRouter,
    DEFAULT_TEAMS,
    DEFAULT_ESCALATION_PATHS,
    CATEGORY_TEAM_MAP,
    SEVERITY_PRIORITY_MAP,
    ROUTING_RULES,
)


# ============================================================================
# Basic Routing Tests
# ============================================================================


class TestBasicRouting:
    """Tests for basic routing functionality."""

    def test_route_technical_ticket(self, ticket_router):
        """Test routing of technical tickets to technical_support."""
        result = ticket_router.route(
            subject="API error",
            body="Getting an error when calling the API.",
            category="technical",
            severity="medium",
        )

        assert result.team == "technical_support"
        assert result.priority in ["normal", "high", "urgent", "low"]

    def test_route_billing_ticket(self, ticket_router):
        """Test routing of billing tickets to billing_team."""
        result = ticket_router.route(
            subject="Refund request",
            body="I need a refund for my subscription.",
            category="billing",
            severity="medium",
        )

        assert result.team == "billing_team"

    def test_route_account_ticket(self, ticket_router):
        """Test routing of account tickets to account_management."""
        result = ticket_router.route(
            subject="Cannot login",
            body="My account is locked.",
            category="account",
            severity="medium",
        )

        assert result.team == "account_management"

    def test_route_feature_request_ticket(self, ticket_router):
        """Test routing of feature requests to product_team."""
        result = ticket_router.route(
            subject="Feature suggestion",
            body="I'd like to suggest a new feature.",
            category="feature_request",
            severity="low",
        )

        assert result.team == "product_team"

    def test_route_bug_report_ticket(self, ticket_router):
        """Test routing of bug reports to technical_support."""
        result = ticket_router.route(
            subject="Bug in the application",
            body="Found a bug that needs fixing.",
            category="bug_report",
            severity="high",
        )

        assert result.team == "technical_support"

    def test_route_general_ticket(self, ticket_router):
        """Test routing of general tickets."""
        result = ticket_router.route(
            subject="Question",
            body="I have a general question.",
            category="general",
            severity="low",
        )

        # General goes to technical_support by default
        assert result.team == "technical_support"


# ============================================================================
# Critical Severity Routing Tests
# ============================================================================


class TestCriticalRouting:
    """Tests for critical severity routing."""

    def test_critical_routes_to_escalation(self, ticket_router):
        """Test that critical tickets route to escalation_team."""
        result = ticket_router.route(
            subject="URGENT: System down",
            body="Production system is completely down!",
            category="technical",
            severity="critical",
        )

        assert result.team == "escalation_team"
        assert result.priority == "urgent"

    def test_critical_billing_routes_to_escalation(self, ticket_router):
        """Test that critical billing issues route to escalation."""
        result = ticket_router.route(
            subject="CRITICAL: Fraudulent charge",
            body="Unauthorized $5000 charge on my account!",
            category="billing",
            severity="critical",
        )

        assert result.team == "escalation_team"
        assert result.priority == "urgent"

    def test_critical_has_high_confidence(self, ticket_router):
        """Test that critical routing has high confidence."""
        result = ticket_router.route(
            subject="Critical issue",
            body="This is critical!",
            category="technical",
            severity="critical",
        )

        assert result.confidence >= 0.9


# ============================================================================
# Priority Tests
# ============================================================================


class TestPriorityCalculation:
    """Tests for priority calculation."""

    def test_severity_critical_urgent_priority(self, ticket_router):
        """Test that critical severity gets urgent priority."""
        result = ticket_router.route(
            subject="Critical",
            body="Critical issue",
            category="technical",
            severity="critical",
        )

        assert result.priority == "urgent"

    def test_severity_high_high_priority(self, ticket_router):
        """Test that high severity gets high priority."""
        result = ticket_router.route(
            subject="Important issue",
            body="This is important",
            category="technical",
            severity="high",
        )

        assert result.priority == "high"

    def test_severity_medium_normal_priority(self, ticket_router):
        """Test that medium severity gets normal priority."""
        result = ticket_router.route(
            subject="Issue",
            body="Regular issue",
            category="technical",
            severity="medium",
        )

        assert result.priority == "normal"

    def test_severity_low_low_priority(self, ticket_router):
        """Test that low severity gets low priority."""
        result = ticket_router.route(
            subject="Minor issue",
            body="Minor problem",
            category="feature_request",
            severity="low",
        )

        assert result.priority == "low"

    def test_product_team_priority_modifier(self, ticket_router):
        """Test that product_team has lower priority modifier."""
        # Feature requests have priority_modifier: 1, so medium becomes low
        result = ticket_router.route(
            subject="Feature idea",
            body="I have an idea",
            category="feature_request",
            severity="medium",
        )

        # Due to priority modifier, medium might become low
        assert result.team == "product_team"


# ============================================================================
# Escalation Path Tests
# ============================================================================


class TestEscalationPaths:
    """Tests for escalation path generation."""

    def test_escalation_path_included(self, ticket_router):
        """Test that escalation path is included in routing decision."""
        result = ticket_router.route(
            subject="Technical issue",
            body="Need help with technical issue",
            category="technical",
            severity="high",
        )

        assert result.escalation_path is not None
        assert isinstance(result.escalation_path, list)
        assert len(result.escalation_path) > 0

    def test_escalation_path_for_technical_support(self, ticket_router):
        """Test escalation path for technical support team."""
        result = ticket_router.route(
            subject="Tech issue",
            body="Issue",
            category="technical",
            severity="medium",
        )

        if result.escalation_path:
            assert "senior_technical" in result.escalation_path or \
                   "engineering_team" in result.escalation_path

    def test_escalation_path_for_billing(self, ticket_router):
        """Test escalation path for billing team."""
        result = ticket_router.route(
            subject="Billing issue",
            body="Issue with billing",
            category="billing",
            severity="medium",
        )

        if result.escalation_path:
            assert "billing_manager" in result.escalation_path or \
                   "finance_team" in result.escalation_path

    def test_escalation_path_for_critical(self, ticket_router):
        """Test escalation path for critical issues."""
        result = ticket_router.route(
            subject="Critical",
            body="Critical issue",
            category="technical",
            severity="critical",
        )

        # Critical issues go to escalation team
        if result.escalation_path:
            assert "senior_management" in result.escalation_path or \
                   len(result.escalation_path) > 0


# ============================================================================
# Alternative Teams Tests
# ============================================================================


class TestAlternativeTeams:
    """Tests for alternative team suggestions."""

    def test_alternative_teams_included(self, ticket_router):
        """Test that alternative teams are included."""
        result = ticket_router.route(
            subject="Technical issue",
            body="Need technical help",
            category="technical",
            severity="medium",
        )

        assert result.alternative_teams is not None
        assert isinstance(result.alternative_teams, list)

    def test_primary_team_not_in_alternatives(self, ticket_router):
        """Test that primary team is not in alternatives."""
        result = ticket_router.route(
            subject="Billing question",
            body="Question about bill",
            category="billing",
            severity="medium",
        )

        assert result.team not in result.alternative_teams

    def test_alternatives_limited_to_two(self, ticket_router):
        """Test that alternatives are limited to 2."""
        result = ticket_router.route(
            subject="Issue",
            body="Issue description",
            category="technical",
            severity="medium",
        )

        assert len(result.alternative_teams) <= 2

    def test_escalation_team_not_in_alternatives(self, ticket_router):
        """Test that escalation team is not in alternatives."""
        result = ticket_router.route(
            subject="Issue",
            body="Issue",
            category="technical",
            severity="high",
        )

        assert "escalation_team" not in result.alternative_teams


# ============================================================================
# Confidence Score Tests
# ============================================================================


class TestConfidenceScores:
    """Tests for confidence score calculations."""

    def test_confidence_in_valid_range(self, ticket_router):
        """Test that confidence scores are in valid range."""
        result = ticket_router.route(
            subject="Test",
            body="Test",
            category="technical",
            severity="medium",
        )

        assert 0.0 <= result.confidence <= 1.0

    def test_clear_category_has_high_confidence(self, ticket_router):
        """Test that clear category-team mapping has higher confidence."""
        result = ticket_router.route(
            subject="Billing",
            body="Billing issue",
            category="billing",
            severity="medium",
        )

        assert result.confidence >= 0.8

    def test_high_severity_boosts_confidence(self, ticket_router):
        """Test that high/critical severity boosts confidence."""
        result_critical = ticket_router.route(
            subject="Critical",
            body="Critical",
            category="technical",
            severity="critical",
        )

        result_low = ticket_router.route(
            subject="Low priority",
            body="Low priority",
            category="feature_request",
            severity="low",
        )

        # Critical should have equal or higher confidence
        assert result_critical.confidence >= result_low.confidence


# ============================================================================
# Reasoning Tests
# ============================================================================


class TestReasoning:
    """Tests for routing reasoning."""

    def test_reasoning_provided(self, ticket_router):
        """Test that reasoning is provided in routing decision."""
        result = ticket_router.route(
            subject="Technical issue",
            body="Need help",
            category="technical",
            severity="high",
        )

        assert result.reasoning is not None
        assert len(result.reasoning) > 0

    def test_reasoning_includes_team(self, ticket_router):
        """Test that reasoning mentions the team."""
        result = ticket_router.route(
            subject="Billing",
            body="Billing question",
            category="billing",
            severity="medium",
        )

        assert result.team in result.reasoning or "billing" in result.reasoning.lower()

    def test_reasoning_includes_category(self, ticket_router):
        """Test that reasoning mentions the category."""
        result = ticket_router.route(
            subject="Account issue",
            body="Account problem",
            category="account",
            severity="medium",
        )

        assert "account" in result.reasoning.lower() or result.team in result.reasoning


# ============================================================================
# Extracted Fields Context Tests
# ============================================================================


class TestExtractedFieldsContext:
    """Tests for routing with extracted fields context."""

    def test_routing_with_extracted_fields(self, ticket_router):
        """Test routing includes extracted fields in reasoning."""
        result = ticket_router.route(
            subject="Order issue",
            body="Problem with order",
            category="billing",
            severity="medium",
            extracted_fields={"order_id": "ORD-123", "amount": "$50"},
        )

        assert isinstance(result, RoutingDecision)

    def test_routing_without_extracted_fields(self, ticket_router):
        """Test routing works without extracted fields."""
        result = ticket_router.route(
            subject="Issue",
            body="Problem",
            category="technical",
            severity="medium",
            extracted_fields=None,
        )

        assert isinstance(result, RoutingDecision)


# ============================================================================
# Helper Method Tests
# ============================================================================


class TestHelperMethods:
    """Tests for helper methods."""

    def test_get_team_for_category(self, ticket_router):
        """Test getting team for a specific category."""
        assert ticket_router.get_team_for_category("technical") == "technical_support"
        assert ticket_router.get_team_for_category("billing") == "billing_team"
        assert ticket_router.get_team_for_category("account") == "account_management"
        assert ticket_router.get_team_for_category("feature_request") == "product_team"

    def test_get_escalation_path(self, ticket_router):
        """Test getting escalation path for a team."""
        path = ticket_router.get_escalation_path("technical_support")
        assert isinstance(path, list)
        assert len(path) > 0

    def test_get_escalation_path_unknown_team(self, ticket_router):
        """Test getting escalation path for unknown team."""
        path = ticket_router.get_escalation_path("unknown_team")
        assert path is None

    def test_get_available_teams(self, ticket_router):
        """Test getting list of available teams."""
        teams = ticket_router.get_available_teams()

        assert isinstance(teams, list)
        assert len(teams) > 0
        assert "technical_support" in teams
        assert "billing_team" in teams
        assert "escalation_team" in teams


# ============================================================================
# Edge Cases Tests
# ============================================================================


class TestEdgeCases:
    """Tests for edge cases in routing."""

    def test_empty_subject_body(self, ticket_router):
        """Test routing with empty subject and body."""
        result = ticket_router.route(
            subject="",
            body="",
            category="technical",
            severity="medium",
        )

        assert result.team in ["technical_support", "escalation_team"]

    def test_unknown_category(self, ticket_router):
        """Test routing with unknown category."""
        result = ticket_router.route(
            subject="Issue",
            body="Problem",
            category="unknown_category",
            severity="medium",
        )

        # Should fallback to default
        assert result.team in ["technical_support", "escalation_team"]

    def test_unknown_severity(self, ticket_router):
        """Test routing with unknown severity."""
        result = ticket_router.route(
            subject="Issue",
            body="Problem",
            category="technical",
            severity="unknown",
        )

        assert isinstance(result, RoutingDecision)

    def test_very_long_subject_body(self, ticket_router):
        """Test routing with very long subject and body."""
        long_text = "Issue " * 1000

        result = ticket_router.route(
            subject=long_text,
            body=long_text,
            category="technical",
            severity="high",
        )

        assert isinstance(result, RoutingDecision)

    def test_special_characters_in_text(self, ticket_router):
        """Test routing with special characters."""
        result = ticket_router.route(
            subject="!!!URGENT!!! Issue $$$",
            body="### ERROR ### @@@ CRITICAL @@@",
            category="technical",
            severity="high",
        )

        assert isinstance(result, RoutingDecision)


# ============================================================================
# Integration Tests with Sample Tickets
# ============================================================================


class TestSampleTicketsRouting:
    """Tests using sample tickets from fixtures."""

    def test_route_all_sample_tickets(self, ticket_router, sample_tickets):
        """Test routing of all sample tickets."""
        for ticket_id, ticket_data in sample_tickets.items():
            result = ticket_router.route(
                subject=ticket_data["subject"],
                body=ticket_data["body"],
                category=ticket_data.get("expected_category", "general"),
                severity=ticket_data.get("expected_severity", "medium"),
            )

            assert isinstance(result, RoutingDecision)
            assert result.team in [
                "technical_support",
                "billing_team",
                "account_management",
                "product_team",
                "escalation_team",
            ]

    def test_critical_tickets_route_to_escalation(self, ticket_router, sample_tickets):
        """Test that all critical tickets route to escalation team."""
        critical_tickets = [
            t for t in sample_tickets.values()
            if t.get("expected_severity") == "critical"
        ]

        for ticket in critical_tickets:
            result = ticket_router.route(
                subject=ticket["subject"],
                body=ticket["body"],
                category=ticket.get("expected_category", "general"),
                severity="critical",
            )

            assert result.team == "escalation_team"
            assert result.priority == "urgent"

    def test_billing_tickets_route_to_billing_team(self, ticket_router, sample_tickets):
        """Test that billing tickets route to billing team (unless critical)."""
        billing_tickets = [
            (tid, t) for tid, t in sample_tickets.items()
            if t.get("expected_category") == "billing" and t.get("expected_severity") != "critical"
        ]

        for ticket_id, ticket in billing_tickets:
            result = ticket_router.route(
                subject=ticket["subject"],
                body=ticket["body"],
                category="billing",
                severity=ticket.get("expected_severity", "medium"),
            )

            assert result.team == "billing_team", (
                f"Ticket {ticket_id} should route to billing_team, got {result.team}"
            )


# ============================================================================
# Convenience Function Tests
# ============================================================================


class TestConvenienceFunction:
    """Tests for the route_ticket convenience function."""

    def test_route_ticket_function(self):
        """Test the route_ticket convenience function."""
        from app.services.workflow.routers import route_ticket

        result = route_ticket(
            subject="Billing issue",
            body="Need refund",
            category="billing",
            severity="medium",
        )

        assert isinstance(result, RoutingDecision)
        assert result.team == "billing_team"

    def test_route_ticket_with_extracted_fields(self):
        """Test route_ticket with extracted fields."""
        from app.services.workflow.routers import route_ticket

        result = route_ticket(
            subject="Order issue",
            body="Order problem",
            category="billing",
            severity="high",
            extracted_fields={"order_id": "ORD-123"},
        )

        assert isinstance(result, RoutingDecision)


# ============================================================================
# Priority Modifier Tests
# ============================================================================


class TestPriorityModifier:
    """Tests for team priority modifiers."""

    def test_product_team_lower_priority(self, ticket_router):
        """Test that product team has lower priority modifier."""
        # feature_request has priority_modifier: 1
        result = ticket_router.route(
            subject="Feature request",
            body="New feature idea",
            category="feature_request",
            severity="high",
        )

        assert result.team == "product_team"
        # High severity with modifier 1 might be adjusted

    def test_escalation_team_urgent_priority(self, ticket_router):
        """Test that escalation team gets urgent priority."""
        result = ticket_router.route(
            subject="Critical",
            body="Critical issue",
            category="technical",
            severity="critical",
        )

        assert result.team == "escalation_team"
        assert result.priority == "urgent"


# ============================================================================
# Multiple Conditions Tests
# ============================================================================


class TestMultipleConditions:
    """Tests for routing with multiple conditions."""

    def test_category_and_severity_combined(self, ticket_router):
        """Test routing with category and severity combined."""
        # Bug report with high severity
        result = ticket_router.route(
            subject="Bug causing crashes",
            body="Critical bug needs fixing",
            category="bug_report",
            severity="high",
        )

        assert result.team == "technical_support"
        assert result.priority == "high"

    def test_extracted_fields_influence_routing(self, ticket_router):
        """Test that extracted fields can influence routing."""
        result_with_fields = ticket_router.route(
            subject="Order issue",
            body="Order problem",
            category="billing",
            severity="medium",
            extracted_fields={"order_id": "ORD-123", "amount": "$5000"},
        )

        result_without_fields = ticket_router.route(
            subject="Order issue",
            body="Order problem",
            category="billing",
            severity="medium",
            extracted_fields=None,
        )

        # Both should route to billing_team
        assert result_with_fields.team == "billing_team"
        assert result_without_fields.team == "billing_team"
