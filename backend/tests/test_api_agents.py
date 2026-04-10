"""Tests for agent admin API endpoints.

Tests use the real Neo4j database and FastAPI TestClient.
No mocks — all graph operations hit the real database.
"""

import pytest
from fastapi.testclient import TestClient
from neo4j import Driver

from app.models.agent_identity import AgentStatus, AgentType, ModelTier
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


def _agent_payload(**overrides) -> dict:
    """Build a valid agent registration payload.

    Args:
        **overrides: Fields to override.

    Returns:
        A dict suitable for POST /me/agents.
    """
    defaults = {
        "name": "Test Agent",
        "agent_type": "compliance",
        "scopes": ["read:safety"],
        "model_tier": "standard",
        "daily_budget_cents": 1000,
    }
    defaults.update(overrides)
    return defaults


# ---------------------------------------------------------------------------
# Registration endpoint
# ---------------------------------------------------------------------------


class TestRegisterEndpoint:
    """Tests for POST /api/v1/me/agents."""

    def test_register_agent(self, client: TestClient, test_company: dict) -> None:
        """Register creates an agent and returns 201."""
        resp = client.post("/api/v1/me/agents", json=_agent_payload())
        assert resp.status_code == 201

        body = resp.json()
        assert body["agent_id"].startswith("agt_")
        assert body["name"] == "Test Agent"
        assert body["agent_type"] == "compliance"
        assert body["status"] == "active"
        assert body["scopes"] == ["read:safety"]
        assert body["daily_budget_cents"] == 1000
        assert body["daily_spend_cents"] == 0

    def test_register_invalid_scope_rejected(
        self, client: TestClient, test_company: dict
    ) -> None:
        """Register with invalid scope format returns 422."""
        resp = client.post(
            "/api/v1/me/agents",
            json=_agent_payload(scopes=["bad_scope"]),
        )
        assert resp.status_code == 422

    def test_register_empty_scopes_rejected(
        self, client: TestClient, test_company: dict
    ) -> None:
        """Register with empty scopes returns 422."""
        resp = client.post(
            "/api/v1/me/agents",
            json=_agent_payload(scopes=[]),
        )
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# List endpoint
# ---------------------------------------------------------------------------


class TestListEndpoint:
    """Tests for GET /api/v1/me/agents."""

    def test_list_empty(self, client: TestClient, test_company: dict) -> None:
        """List returns empty array when no agents exist."""
        resp = client.get("/api/v1/me/agents")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_list_returns_agents(self, client: TestClient, test_company: dict) -> None:
        """List returns all registered agents."""
        client.post("/api/v1/me/agents", json=_agent_payload(name="Agent A"))
        client.post("/api/v1/me/agents", json=_agent_payload(name="Agent B"))

        resp = client.get("/api/v1/me/agents")
        assert resp.status_code == 200
        assert len(resp.json()) == 2


# ---------------------------------------------------------------------------
# Get endpoint
# ---------------------------------------------------------------------------


class TestGetEndpoint:
    """Tests for GET /api/v1/me/agents/{agent_id}."""

    def test_get_agent(self, client: TestClient, test_company: dict) -> None:
        """Get returns the specific agent."""
        create_resp = client.post("/api/v1/me/agents", json=_agent_payload())
        agent_id = create_resp.json()["agent_id"]

        resp = client.get(f"/api/v1/me/agents/{agent_id}")
        assert resp.status_code == 200
        assert resp.json()["agent_id"] == agent_id

    def test_get_nonexistent_returns_404(
        self, client: TestClient, test_company: dict
    ) -> None:
        """Get with invalid ID returns 404."""
        resp = client.get("/api/v1/me/agents/agt_nonexistent")
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Update endpoint
# ---------------------------------------------------------------------------


class TestUpdateEndpoint:
    """Tests for PATCH /api/v1/me/agents/{agent_id}."""

    def test_update_name(self, client: TestClient, test_company: dict) -> None:
        """Patch updates the agent's name."""
        create_resp = client.post("/api/v1/me/agents", json=_agent_payload())
        agent_id = create_resp.json()["agent_id"]

        resp = client.patch(
            f"/api/v1/me/agents/{agent_id}",
            json={"name": "Updated Name"},
        )
        assert resp.status_code == 200
        assert resp.json()["name"] == "Updated Name"

    def test_update_nonexistent_returns_404(
        self, client: TestClient, test_company: dict
    ) -> None:
        """Patch with invalid ID returns 404."""
        resp = client.patch(
            "/api/v1/me/agents/agt_nonexistent",
            json={"name": "Nobody"},
        )
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Suspend endpoint
# ---------------------------------------------------------------------------


class TestSuspendEndpoint:
    """Tests for POST /api/v1/me/agents/{agent_id}/suspend."""

    def test_suspend_agent(self, client: TestClient, test_company: dict) -> None:
        """Suspend sets agent status to suspended."""
        create_resp = client.post("/api/v1/me/agents", json=_agent_payload())
        agent_id = create_resp.json()["agent_id"]

        resp = client.post(f"/api/v1/me/agents/{agent_id}/suspend")
        assert resp.status_code == 200
        assert resp.json()["status"] == "suspended"


# ---------------------------------------------------------------------------
# Spend report endpoint
# ---------------------------------------------------------------------------


class TestSpendReportEndpoint:
    """Tests for GET /api/v1/me/agents/spend/report."""

    def test_spend_report_empty(self, client: TestClient, test_company: dict) -> None:
        """Spend report returns empty list with no agents."""
        resp = client.get("/api/v1/me/agents/spend/report")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_spend_report_with_agents(
        self, client: TestClient, test_company: dict, agent_service: AgentIdentityService
    ) -> None:
        """Spend report includes registered agents."""
        create_resp = client.post("/api/v1/me/agents", json=_agent_payload())
        agent_id = create_resp.json()["agent_id"]

        # Record some spend directly via service
        agent_service.record_spend(agent_id, 250)

        resp = client.get("/api/v1/me/agents/spend/report")
        assert resp.status_code == 200
        report = resp.json()
        assert len(report) == 1
        assert report[0]["daily_spend_cents"] == 250
        assert report[0]["budget_utilisation_pct"] == 25.0


# ---------------------------------------------------------------------------
# Reset spend endpoint
# ---------------------------------------------------------------------------


class TestResetSpendEndpoint:
    """Tests for POST /api/v1/me/agents/spend/reset."""

    def test_reset_spend(
        self, client: TestClient, test_company: dict, agent_service: AgentIdentityService
    ) -> None:
        """Reset zeroes all agents' daily spend."""
        create_resp = client.post("/api/v1/me/agents", json=_agent_payload())
        agent_id = create_resp.json()["agent_id"]
        agent_service.record_spend(agent_id, 300)

        resp = client.post("/api/v1/me/agents/spend/reset")
        assert resp.status_code == 200
        assert resp.json()["reset_count"] == 1

        # Verify spend is zero
        get_resp = client.get(f"/api/v1/me/agents/{agent_id}")
        assert get_resp.json()["daily_spend_cents"] == 0
