"""Tests for AgentIdentityService — agent CRUD, permissions, cost tracking.

Tests use the real Neo4j database via shared fixtures from conftest.py.
No mocks — graph traversals are tested against real nodes and relationships.
"""

import json

import pytest
from neo4j import Driver

from app.exceptions import AgentBudgetExceededError, AgentNotFoundError
from app.models.agent_identity import (
    AgentIdentityCreate,
    AgentIdentityUpdate,
    AgentStatus,
    AgentType,
    ModelTier,
)
from app.services.agent_identity_service import AgentIdentityService


@pytest.fixture()
def agent_service(neo4j_driver: Driver) -> AgentIdentityService:
    """Provide an AgentIdentityService instance.

    Args:
        neo4j_driver: The session-scoped Neo4j driver.

    Returns:
        An AgentIdentityService instance.
    """
    return AgentIdentityService(neo4j_driver)


def _create_agent_data(**overrides) -> AgentIdentityCreate:
    """Build an AgentIdentityCreate with sensible defaults.

    Args:
        **overrides: Fields to override.

    Returns:
        An AgentIdentityCreate instance.
    """
    defaults = {
        "name": "Test Compliance Agent",
        "agent_type": AgentType.COMPLIANCE,
        "scopes": ["read:safety", "read:workers"],
        "model_tier": ModelTier.STANDARD,
        "daily_budget_cents": 1000,
    }
    defaults.update(overrides)
    return AgentIdentityCreate(**defaults)


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------


class TestRegister:
    """Tests for agent registration."""

    def test_register_creates_agent_node(
        self, agent_service: AgentIdentityService, test_company: dict
    ) -> None:
        """Register creates an AgentIdentity node linked to the company."""
        data = _create_agent_data()
        agent = agent_service.register(test_company["id"], data, "test_user_001")

        assert agent.agent_id.startswith("agt_")
        assert agent.name == "Test Compliance Agent"
        assert agent.agent_type == AgentType.COMPLIANCE
        assert agent.status == AgentStatus.ACTIVE
        assert agent.scopes == ["read:safety", "read:workers"]
        assert agent.model_tier == ModelTier.STANDARD
        assert agent.daily_budget_cents == 1000
        assert agent.daily_spend_cents == 0
        assert agent.company_id == test_company["id"]
        assert agent.created_by == "test_user_001"

    def test_register_creates_belongs_to_relationship(
        self, agent_service: AgentIdentityService, test_company: dict, neo4j_driver: Driver
    ) -> None:
        """Register creates BELONGS_TO and HAS_AGENT relationships."""
        data = _create_agent_data()
        agent = agent_service.register(test_company["id"], data, "test_user_001")

        with neo4j_driver.session() as session:
            result = session.run(
                """
                MATCH (a:AgentIdentity {agent_id: $aid})-[r:BELONGS_TO]->(c:Company {id: $cid})
                RETURN r.scopes AS scopes, r.rate_limit_per_minute AS rate_limit
                """,
                aid=agent.agent_id,
                cid=test_company["id"],
            )
            record = result.single()

        assert record is not None
        scopes = json.loads(record["scopes"])
        assert "read:safety" in scopes
        assert record["rate_limit"] == 60

    def test_register_invalid_company_raises(
        self, agent_service: AgentIdentityService
    ) -> None:
        """Register with non-existent company raises CompanyNotFoundError."""
        from app.exceptions import CompanyNotFoundError

        data = _create_agent_data()
        with pytest.raises(CompanyNotFoundError):
            agent_service.register("comp_nonexistent", data, "test_user_001")

    def test_register_multiple_agents(
        self, agent_service: AgentIdentityService, test_company: dict
    ) -> None:
        """A company can have multiple agents."""
        a1 = agent_service.register(
            test_company["id"],
            _create_agent_data(name="Agent A", agent_type=AgentType.COMPLIANCE),
            "test_user_001",
        )
        a2 = agent_service.register(
            test_company["id"],
            _create_agent_data(name="Agent B", agent_type=AgentType.BRIEFING),
            "test_user_001",
        )

        assert a1.agent_id != a2.agent_id
        agents = agent_service.list_for_company(test_company["id"])
        assert len(agents) == 2


# ---------------------------------------------------------------------------
# Get and List
# ---------------------------------------------------------------------------


class TestGetAndList:
    """Tests for fetching agents."""

    def test_get_returns_agent(
        self, agent_service: AgentIdentityService, test_company: dict
    ) -> None:
        """Get returns the agent with correct fields."""
        data = _create_agent_data()
        created = agent_service.register(test_company["id"], data, "test_user_001")

        fetched = agent_service.get(created.agent_id, test_company["id"])
        assert fetched.agent_id == created.agent_id
        assert fetched.name == created.name

    def test_get_wrong_company_raises(
        self, agent_service: AgentIdentityService, test_company: dict
    ) -> None:
        """Get with wrong company ID raises AgentNotFoundError."""
        data = _create_agent_data()
        created = agent_service.register(test_company["id"], data, "test_user_001")

        with pytest.raises(AgentNotFoundError):
            agent_service.get(created.agent_id, "comp_wrong")

    def test_get_nonexistent_raises(
        self, agent_service: AgentIdentityService, test_company: dict
    ) -> None:
        """Get with non-existent agent ID raises AgentNotFoundError."""
        with pytest.raises(AgentNotFoundError):
            agent_service.get("agt_nonexistent", test_company["id"])

    def test_list_empty_company(
        self, agent_service: AgentIdentityService, test_company: dict
    ) -> None:
        """List returns empty list for company with no agents."""
        agents = agent_service.list_for_company(test_company["id"])
        assert agents == []

    def test_list_returns_all_agents(
        self, agent_service: AgentIdentityService, test_company: dict
    ) -> None:
        """List returns all agents for the company."""
        for i in range(3):
            agent_service.register(
                test_company["id"],
                _create_agent_data(name=f"Agent {i}"),
                "test_user_001",
            )

        agents = agent_service.list_for_company(test_company["id"])
        assert len(agents) == 3


# ---------------------------------------------------------------------------
# Update
# ---------------------------------------------------------------------------


class TestUpdate:
    """Tests for agent updates."""

    def test_update_name(
        self, agent_service: AgentIdentityService, test_company: dict
    ) -> None:
        """Update changes the agent's name."""
        created = agent_service.register(
            test_company["id"], _create_agent_data(), "test_user_001"
        )

        updated = agent_service.update(
            created.agent_id,
            test_company["id"],
            AgentIdentityUpdate(name="Renamed Agent"),
        )
        assert updated.name == "Renamed Agent"

    def test_update_budget(
        self, agent_service: AgentIdentityService, test_company: dict
    ) -> None:
        """Update changes the agent's daily budget."""
        created = agent_service.register(
            test_company["id"], _create_agent_data(), "test_user_001"
        )

        updated = agent_service.update(
            created.agent_id,
            test_company["id"],
            AgentIdentityUpdate(daily_budget_cents=5000),
        )
        assert updated.daily_budget_cents == 5000

    def test_update_status(
        self, agent_service: AgentIdentityService, test_company: dict
    ) -> None:
        """Update can change agent status."""
        created = agent_service.register(
            test_company["id"], _create_agent_data(), "test_user_001"
        )

        updated = agent_service.update(
            created.agent_id,
            test_company["id"],
            AgentIdentityUpdate(status=AgentStatus.SUSPENDED),
        )
        assert updated.status == AgentStatus.SUSPENDED

    def test_update_nonexistent_raises(
        self, agent_service: AgentIdentityService, test_company: dict
    ) -> None:
        """Update non-existent agent raises AgentNotFoundError."""
        with pytest.raises(AgentNotFoundError):
            agent_service.update(
                "agt_nonexistent",
                test_company["id"],
                AgentIdentityUpdate(name="Nobody"),
            )

    def test_update_empty_returns_unchanged(
        self, agent_service: AgentIdentityService, test_company: dict
    ) -> None:
        """Update with no changes returns the agent unchanged."""
        created = agent_service.register(
            test_company["id"], _create_agent_data(), "test_user_001"
        )

        updated = agent_service.update(
            created.agent_id,
            test_company["id"],
            AgentIdentityUpdate(),
        )
        assert updated.name == created.name


# ---------------------------------------------------------------------------
# Suspend (kill switch)
# ---------------------------------------------------------------------------


class TestSuspend:
    """Tests for agent suspension."""

    def test_suspend_sets_status(
        self, agent_service: AgentIdentityService, test_company: dict
    ) -> None:
        """Suspend sets the agent status to suspended."""
        created = agent_service.register(
            test_company["id"], _create_agent_data(), "test_user_001"
        )

        suspended = agent_service.suspend(created.agent_id, test_company["id"])
        assert suspended.status == AgentStatus.SUSPENDED

    def test_suspended_agent_fails_verify(
        self, agent_service: AgentIdentityService, test_company: dict
    ) -> None:
        """verify_agent_access rejects suspended agents."""
        created = agent_service.register(
            test_company["id"], _create_agent_data(), "test_user_001"
        )
        agent_service.suspend(created.agent_id, test_company["id"])

        with pytest.raises(AgentNotFoundError):
            agent_service.verify_agent_access(created.agent_id, test_company["id"])


# ---------------------------------------------------------------------------
# Cost tracking
# ---------------------------------------------------------------------------


class TestCostTracking:
    """Tests for spend recording and budget enforcement."""

    def test_record_spend_increments(
        self, agent_service: AgentIdentityService, test_company: dict
    ) -> None:
        """record_spend increments daily_spend_cents."""
        created = agent_service.register(
            test_company["id"], _create_agent_data(daily_budget_cents=500), "test_user_001"
        )

        agent_service.record_spend(created.agent_id, 100)
        agent_service.record_spend(created.agent_id, 50)

        fetched = agent_service.get(created.agent_id, test_company["id"])
        assert fetched.daily_spend_cents == 150

    def test_record_spend_exceeds_budget_raises(
        self, agent_service: AgentIdentityService, test_company: dict
    ) -> None:
        """record_spend raises when daily budget is exceeded."""
        created = agent_service.register(
            test_company["id"], _create_agent_data(daily_budget_cents=100), "test_user_001"
        )

        with pytest.raises(AgentBudgetExceededError):
            agent_service.record_spend(created.agent_id, 150)

    def test_reset_daily_spend(
        self, agent_service: AgentIdentityService, test_company: dict
    ) -> None:
        """reset_daily_spend zeroes all agents' spend."""
        created = agent_service.register(
            test_company["id"], _create_agent_data(), "test_user_001"
        )
        agent_service.record_spend(created.agent_id, 200)

        count = agent_service.reset_daily_spend(test_company["id"])
        assert count == 1

        fetched = agent_service.get(created.agent_id, test_company["id"])
        assert fetched.daily_spend_cents == 0


# ---------------------------------------------------------------------------
# Spend report
# ---------------------------------------------------------------------------


class TestSpendReport:
    """Tests for spend reporting."""

    def test_spend_report_empty(
        self, agent_service: AgentIdentityService, test_company: dict
    ) -> None:
        """Spend report returns empty list for company with no agents."""
        report = agent_service.get_spend_report(test_company["id"])
        assert report == []

    def test_spend_report_calculates_utilisation(
        self, agent_service: AgentIdentityService, test_company: dict
    ) -> None:
        """Spend report correctly calculates budget utilisation."""
        created = agent_service.register(
            test_company["id"],
            _create_agent_data(daily_budget_cents=1000),
            "test_user_001",
        )
        agent_service.record_spend(created.agent_id, 250)

        report = agent_service.get_spend_report(test_company["id"])
        assert len(report) == 1
        assert report[0].daily_spend_cents == 250
        assert report[0].budget_remaining_cents == 750
        assert report[0].budget_utilisation_pct == 25.0


# ---------------------------------------------------------------------------
# Graph-native permission verification
# ---------------------------------------------------------------------------


class TestVerifyAgentAccess:
    """Tests for agent access verification."""

    def test_active_agent_passes(
        self, agent_service: AgentIdentityService, test_company: dict
    ) -> None:
        """Active agent passes verification."""
        created = agent_service.register(
            test_company["id"], _create_agent_data(), "test_user_001"
        )

        agent = agent_service.verify_agent_access(created.agent_id, test_company["id"])
        assert agent.status == AgentStatus.ACTIVE

    def test_nonexistent_agent_fails(
        self, agent_service: AgentIdentityService, test_company: dict
    ) -> None:
        """Non-existent agent fails verification."""
        with pytest.raises(AgentNotFoundError):
            agent_service.verify_agent_access("agt_fake", test_company["id"])

    def test_revoked_agent_fails(
        self, agent_service: AgentIdentityService, test_company: dict
    ) -> None:
        """Revoked agent fails verification."""
        created = agent_service.register(
            test_company["id"], _create_agent_data(), "test_user_001"
        )
        agent_service.update(
            created.agent_id,
            test_company["id"],
            AgentIdentityUpdate(status=AgentStatus.REVOKED),
        )

        with pytest.raises(AgentNotFoundError):
            agent_service.verify_agent_access(created.agent_id, test_company["id"])
