"""Tests for the guardrails service — action classification, rate limiting, approval queue."""

import json
import time
from datetime import datetime, timezone

import pytest
from neo4j import Driver

from app.models.actor import Actor
from app.models.guardrails import ActionClass, ApprovalStatus
from app.services.guardrails_service import (
    AgentRateLimiter,
    GuardrailsService,
    TOOL_ACTION_MAP,
    TOOL_SCOPE_MAP,
)
from tests.conftest import TEST_USER


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def guardrails_service(neo4j_driver: Driver) -> GuardrailsService:
    """Provide a GuardrailsService instance."""
    return GuardrailsService(neo4j_driver)


@pytest.fixture()
def rate_limiter() -> AgentRateLimiter:
    """Provide a fresh rate limiter."""
    return AgentRateLimiter()


@pytest.fixture()
def registered_agent(neo4j_driver: Driver, test_company: dict) -> dict:
    """Create a registered agent with safety read/write scopes.

    Returns:
        Dict with agent_id, company_id, and scopes.
    """
    agent_id = "agt_guardrail_test"
    scopes = json.dumps(["read:compliance", "read:projects", "read:workers",
                          "read:briefings", "write:hazards", "write:incidents",
                          "write:inspections", "read:inspections", "write:safety"])
    now = datetime.now(timezone.utc).isoformat()

    with neo4j_driver.session() as session:
        session.run(
            """
            MATCH (c:Company {id: $company_id})
            CREATE (a:AgentIdentity {
                agent_id: $agent_id,
                name: 'Guardrail Test Agent',
                agent_type: 'compliance',
                status: 'active',
                scopes: $scopes,
                model_tier: 'standard',
                daily_budget_cents: 1000,
                daily_spend_cents: 0,
                created_at: $now,
                created_by: $user_id
            })
            CREATE (a)-[:BELONGS_TO {
                scopes: $scopes,
                rate_limit_per_minute: 10
            }]->(c)
            CREATE (c)-[:HAS_AGENT]->(a)
            """,
            {
                "company_id": test_company["id"],
                "agent_id": agent_id,
                "scopes": scopes,
                "now": now,
                "user_id": TEST_USER["uid"],
            },
        )

    return {
        "agent_id": agent_id,
        "company_id": test_company["id"],
    }


# ---------------------------------------------------------------------------
# Action classification tests
# ---------------------------------------------------------------------------


class TestActionClassification:
    """Tests for tool → action class mapping."""

    def test_read_only_tools(self, guardrails_service: GuardrailsService) -> None:
        """Read-only tools should be classified correctly."""
        assert guardrails_service.classify_tool("check_worker_compliance") == ActionClass.READ_ONLY
        assert guardrails_service.classify_tool("get_project_summary") == ActionClass.READ_ONLY
        assert guardrails_service.classify_tool("generate_morning_brief") == ActionClass.READ_ONLY

    def test_low_risk_write_tools(self, guardrails_service: GuardrailsService) -> None:
        """Low-risk write tools should be classified correctly."""
        assert guardrails_service.classify_tool("report_hazard") == ActionClass.LOW_RISK_WRITE
        assert guardrails_service.classify_tool("report_incident") == ActionClass.LOW_RISK_WRITE

    def test_high_risk_write_tools(self, guardrails_service: GuardrailsService) -> None:
        """High-risk write tools should be classified correctly."""
        assert guardrails_service.classify_tool("resolve_corrective_action") == ActionClass.HIGH_RISK_WRITE
        assert guardrails_service.classify_tool("override_compliance_flag") == ActionClass.HIGH_RISK_WRITE

    def test_unknown_tool_defaults_to_high_risk(self, guardrails_service: GuardrailsService) -> None:
        """Unknown tools should default to HIGH_RISK_WRITE for safety."""
        assert guardrails_service.classify_tool("unknown_tool") == ActionClass.HIGH_RISK_WRITE

    def test_all_mapped_tools_have_scopes(self) -> None:
        """Every mapped tool should also have a scope mapping."""
        for tool_name in TOOL_ACTION_MAP:
            assert tool_name in TOOL_SCOPE_MAP, f"Tool {tool_name} missing scope mapping"


# ---------------------------------------------------------------------------
# Scope checking tests
# ---------------------------------------------------------------------------


class TestScopeChecking:
    """Tests for agent scope validation."""

    def test_direct_scope_match(self, guardrails_service: GuardrailsService) -> None:
        """Agent with exact scope should have access."""
        assert guardrails_service.check_scope(
            "check_worker_compliance", ["read:compliance"]
        ) is True

    def test_missing_scope_denied(self, guardrails_service: GuardrailsService) -> None:
        """Agent without required scope should be denied."""
        assert guardrails_service.check_scope(
            "report_hazard", ["read:safety"]
        ) is False

    def test_wildcard_scope(self, guardrails_service: GuardrailsService) -> None:
        """read:all should grant access to all read tools."""
        assert guardrails_service.check_scope(
            "check_worker_compliance", ["read:all"]
        ) is True

    def test_write_implies_read(self, guardrails_service: GuardrailsService) -> None:
        """write:X scope should also grant read:X access."""
        assert guardrails_service.check_scope(
            "check_worker_compliance", ["write:compliance"]
        ) is True

    def test_write_all_implies_read(self, guardrails_service: GuardrailsService) -> None:
        """write:all should also grant read access."""
        assert guardrails_service.check_scope(
            "get_project_summary", ["write:all"]
        ) is True

    def test_unknown_tool_denied(self, guardrails_service: GuardrailsService) -> None:
        """Tools not in scope map should be denied."""
        assert guardrails_service.check_scope(
            "nonexistent_tool", ["read:all", "write:all"]
        ) is False


# ---------------------------------------------------------------------------
# Rate limiter tests
# ---------------------------------------------------------------------------


class TestRateLimiter:
    """Tests for the in-memory rate limiter."""

    def test_within_limit(self, rate_limiter: AgentRateLimiter) -> None:
        """Calls within limit should be allowed."""
        allowed, remaining = rate_limiter.check("agt_001", 5)
        assert allowed is True
        assert remaining == 5

    def test_at_limit(self, rate_limiter: AgentRateLimiter) -> None:
        """Calls at the limit should be denied."""
        for _ in range(5):
            rate_limiter.record("agt_001")
        allowed, remaining = rate_limiter.check("agt_001", 5)
        assert allowed is False
        assert remaining == 0

    def test_remaining_decreases(self, rate_limiter: AgentRateLimiter) -> None:
        """Remaining count should decrease with each call."""
        rate_limiter.record("agt_001")
        rate_limiter.record("agt_001")
        allowed, remaining = rate_limiter.check("agt_001", 5)
        assert allowed is True
        assert remaining == 3

    def test_different_agents_independent(self, rate_limiter: AgentRateLimiter) -> None:
        """Rate limits should be per-agent."""
        for _ in range(5):
            rate_limiter.record("agt_001")
        allowed_1, _ = rate_limiter.check("agt_001", 5)
        allowed_2, _ = rate_limiter.check("agt_002", 5)
        assert allowed_1 is False
        assert allowed_2 is True

    def test_clear(self, rate_limiter: AgentRateLimiter) -> None:
        """Clear should reset all windows."""
        for _ in range(5):
            rate_limiter.record("agt_001")
        rate_limiter.clear()
        allowed, remaining = rate_limiter.check("agt_001", 5)
        assert allowed is True
        assert remaining == 5


# ---------------------------------------------------------------------------
# Pre-execution check tests (require Neo4j)
# ---------------------------------------------------------------------------


class TestPreExecutionCheck:
    """Tests for the full pre-execution guardrail pipeline."""

    def test_read_only_allowed(
        self,
        guardrails_service: GuardrailsService,
        registered_agent: dict,
    ) -> None:
        """Read-only tools should be allowed for agents with correct scope."""
        result = guardrails_service.pre_execution_check(
            agent_id=registered_agent["agent_id"],
            company_id=registered_agent["company_id"],
            tool_name="check_worker_compliance",
        )
        assert result.allowed is True
        assert result.action_class == ActionClass.READ_ONLY

    def test_low_risk_write_allowed(
        self,
        guardrails_service: GuardrailsService,
        registered_agent: dict,
    ) -> None:
        """Low-risk write tools should be allowed with correct scope."""
        result = guardrails_service.pre_execution_check(
            agent_id=registered_agent["agent_id"],
            company_id=registered_agent["company_id"],
            tool_name="report_hazard",
        )
        assert result.allowed is True
        assert result.action_class == ActionClass.LOW_RISK_WRITE

    def test_high_risk_write_queued(
        self,
        guardrails_service: GuardrailsService,
        registered_agent: dict,
    ) -> None:
        """High-risk write tools should be queued for approval."""
        result = guardrails_service.pre_execution_check(
            agent_id=registered_agent["agent_id"],
            company_id=registered_agent["company_id"],
            tool_name="resolve_corrective_action",
            parameters={"action_id": "ca_001"},
            reasoning="All items verified",
        )
        assert result.allowed is False
        assert result.action_class == ActionClass.HIGH_RISK_WRITE
        assert result.approval_request_id is not None
        assert result.approval_request_id.startswith("apr_")

    def test_missing_scope_denied(
        self,
        guardrails_service: GuardrailsService,
        registered_agent: dict,
    ) -> None:
        """Tools requiring scopes the agent lacks should be denied."""
        result = guardrails_service.pre_execution_check(
            agent_id=registered_agent["agent_id"],
            company_id=registered_agent["company_id"],
            tool_name="generate_safety_plan",  # requires write:documents
        )
        assert result.allowed is False
        assert "scope" in result.reason.lower()

    def test_nonexistent_agent_denied(
        self,
        guardrails_service: GuardrailsService,
        test_company: dict,
    ) -> None:
        """Non-existent agents should be denied."""
        result = guardrails_service.pre_execution_check(
            agent_id="agt_nonexistent",
            company_id=test_company["id"],
            tool_name="check_worker_compliance",
        )
        assert result.allowed is False
        assert "not found" in result.reason.lower()

    def test_rate_limit_enforced(
        self,
        guardrails_service: GuardrailsService,
        registered_agent: dict,
    ) -> None:
        """Exceeding rate limit should deny the request."""
        # Fill up the rate limit (agent has 10/min)
        for _ in range(10):
            guardrails_service._rate_limiter.record(registered_agent["agent_id"])

        result = guardrails_service.pre_execution_check(
            agent_id=registered_agent["agent_id"],
            company_id=registered_agent["company_id"],
            tool_name="check_worker_compliance",
        )
        assert result.allowed is False
        assert "rate limit" in result.reason.lower()

    def test_budget_exceeded_denied(
        self,
        neo4j_driver: Driver,
        guardrails_service: GuardrailsService,
        registered_agent: dict,
    ) -> None:
        """Agents that exceeded budget should be denied."""
        # Set spend above budget
        with neo4j_driver.session() as session:
            session.run(
                """
                MATCH (a:AgentIdentity {agent_id: $agent_id})
                SET a.daily_spend_cents = 2000
                """,
                {"agent_id": registered_agent["agent_id"]},
            )

        result = guardrails_service.pre_execution_check(
            agent_id=registered_agent["agent_id"],
            company_id=registered_agent["company_id"],
            tool_name="check_worker_compliance",
        )
        assert result.allowed is False
        assert "budget" in result.reason.lower()


# ---------------------------------------------------------------------------
# Approval queue tests
# ---------------------------------------------------------------------------


class TestApprovalQueue:
    """Tests for the approval queue stored in Neo4j."""

    def test_list_pending_approvals(
        self,
        guardrails_service: GuardrailsService,
        registered_agent: dict,
    ) -> None:
        """Pending approvals should be listed."""
        # Create an approval via high-risk check
        guardrails_service.pre_execution_check(
            agent_id=registered_agent["agent_id"],
            company_id=registered_agent["company_id"],
            tool_name="resolve_corrective_action",
        )

        pending = guardrails_service.get_pending_approvals(
            registered_agent["company_id"]
        )
        assert len(pending) >= 1
        assert pending[0].status == ApprovalStatus.PENDING
        assert pending[0].tool_name == "resolve_corrective_action"

    def test_approve_request(
        self,
        guardrails_service: GuardrailsService,
        registered_agent: dict,
    ) -> None:
        """Approving a request should update its status."""
        check = guardrails_service.pre_execution_check(
            agent_id=registered_agent["agent_id"],
            company_id=registered_agent["company_id"],
            tool_name="resolve_corrective_action",
        )

        updated = guardrails_service.review_approval(
            request_id=check.approval_request_id,
            company_id=registered_agent["company_id"],
            reviewer_id=TEST_USER["uid"],
            approved=True,
            comment="Verified in person",
        )

        assert updated is not None
        assert updated.status == ApprovalStatus.APPROVED
        assert updated.reviewed_by == TEST_USER["uid"]
        assert updated.review_comment == "Verified in person"

    def test_reject_request(
        self,
        guardrails_service: GuardrailsService,
        registered_agent: dict,
    ) -> None:
        """Rejecting a request should update its status."""
        check = guardrails_service.pre_execution_check(
            agent_id=registered_agent["agent_id"],
            company_id=registered_agent["company_id"],
            tool_name="resolve_corrective_action",
        )

        updated = guardrails_service.review_approval(
            request_id=check.approval_request_id,
            company_id=registered_agent["company_id"],
            reviewer_id=TEST_USER["uid"],
            approved=False,
            comment="Not ready yet",
        )

        assert updated is not None
        assert updated.status == ApprovalStatus.REJECTED

    def test_review_nonexistent_request(
        self,
        guardrails_service: GuardrailsService,
        test_company: dict,
    ) -> None:
        """Reviewing a non-existent request should return None."""
        result = guardrails_service.review_approval(
            request_id="apr_nonexistent",
            company_id=test_company["id"],
            reviewer_id=TEST_USER["uid"],
            approved=True,
        )
        assert result is None
