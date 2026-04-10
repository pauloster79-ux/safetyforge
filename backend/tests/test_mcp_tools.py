"""Tests for MCP tool implementations — intent-based tools over Neo4j."""

import json
from datetime import datetime, timedelta, timezone

import pytest
from neo4j import Driver

from app.models.actor import Actor
from app.models.events import EventType
from app.services.event_bus import EventBus
from app.services.guardrails_service import GuardrailsService
from app.services.mcp_tools import MCPToolService
from tests.conftest import TEST_USER


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def event_bus() -> EventBus:
    """Provide a fresh EventBus."""
    return EventBus()


@pytest.fixture()
def guardrails_service(neo4j_driver: Driver) -> GuardrailsService:
    """Provide a GuardrailsService."""
    return GuardrailsService(neo4j_driver)


@pytest.fixture()
def mcp_tools(
    neo4j_driver: Driver,
    guardrails_service: GuardrailsService,
    event_bus: EventBus,
) -> MCPToolService:
    """Provide an MCPToolService."""
    return MCPToolService(neo4j_driver, guardrails_service, event_bus)


@pytest.fixture()
def agent_actor(neo4j_driver: Driver, test_company: dict) -> Actor:
    """Create a registered agent and return its Actor.

    The agent has broad read/write scopes for testing all tools.
    """
    agent_id = "agt_mcp_test"
    scopes = json.dumps([
        "read:compliance", "read:projects", "read:workers",
        "read:briefings", "read:inspections",
        "write:hazards", "write:incidents", "write:inspections",
    ])
    now = datetime.now(timezone.utc).isoformat()

    with neo4j_driver.session() as session:
        session.run(
            """
            MATCH (c:Company {id: $company_id})
            CREATE (a:AgentIdentity {
                agent_id: $agent_id,
                name: 'MCP Test Agent',
                agent_type: 'compliance',
                status: 'active',
                scopes: $scopes,
                model_tier: 'standard',
                daily_budget_cents: 5000,
                daily_spend_cents: 0,
                created_at: $now,
                created_by: $user_id
            })
            CREATE (a)-[:BELONGS_TO {
                scopes: $scopes,
                rate_limit_per_minute: 60
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

    return Actor.agent(
        agent_id=agent_id,
        company_id=test_company["id"],
        scopes=tuple(json.loads(scopes)),
    )


@pytest.fixture()
def test_worker(neo4j_driver: Driver, test_company: dict) -> dict:
    """Create a test worker with a certification."""
    now = datetime.now(timezone.utc).isoformat()
    worker_data = {
        "id": "wkr_mcp_test_001",
        "first_name": "John",
        "last_name": "Builder",
        "email": "john@test.com",
        "phone": "555-111-2222",
        "role": "foreman",
        "trade": "general",
        "status": "active",
        "deleted": False,
        "created_by": TEST_USER["uid"],
        "actor_type": "human",
        "agent_id": None,
        "model_id": None,
        "confidence": None,
        "created_at": now,
        "updated_by": TEST_USER["uid"],
        "updated_actor_type": "human",
        "updated_at": now,
    }

    cert_data = {
        "id": "cert_mcp_001",
        "certification_type": "OSHA 30-Hour",
        "expiry_date": (datetime.now(timezone.utc) + timedelta(days=180)).strftime("%Y-%m-%d"),
        "issue_date": "2025-01-01",
        "status": "active",
    }

    with neo4j_driver.session() as session:
        session.run(
            """
            MATCH (c:Company {id: $company_id})
            CREATE (w:Worker $worker_props)
            CREATE (c)-[:HAS_WORKER]->(w)
            CREATE (cert:Certification $cert_props)
            CREATE (w)-[:HOLDS_CERT]->(cert)
            """,
            {
                "company_id": test_company["id"],
                "worker_props": worker_data,
                "cert_props": cert_data,
            },
        )

    return worker_data


@pytest.fixture()
def assigned_worker(
    neo4j_driver: Driver, test_worker: dict, test_project: dict
) -> dict:
    """Assign the test worker to the test project."""
    with neo4j_driver.session() as session:
        session.run(
            """
            MATCH (w:Worker {id: $worker_id})
            MATCH (p:Project {id: $project_id})
            CREATE (w)-[:ASSIGNED_TO]->(p)
            """,
            {"worker_id": test_worker["id"], "project_id": test_project["id"]},
        )
    return test_worker


# ---------------------------------------------------------------------------
# Tool 1: check_worker_compliance
# ---------------------------------------------------------------------------


class TestCheckWorkerCompliance:
    """Tests for the check_worker_compliance tool."""

    def test_compliant_worker(
        self,
        mcp_tools: MCPToolService,
        agent_actor: Actor,
        test_company: dict,
        test_project: dict,
        test_worker: dict,
    ) -> None:
        """Worker with valid certs should be compliant."""
        result = mcp_tools.check_worker_compliance(
            agent_actor, test_company["id"], test_project["id"], test_worker["id"]
        )
        assert result["compliant"] is True
        assert result["worker_name"] == "John Builder"
        assert len(result["valid_certifications"]) == 1
        assert len(result["expired_certifications"]) == 0

    def test_nonexistent_worker(
        self,
        mcp_tools: MCPToolService,
        agent_actor: Actor,
        test_company: dict,
        test_project: dict,
    ) -> None:
        """Missing worker should return error."""
        result = mcp_tools.check_worker_compliance(
            agent_actor, test_company["id"], test_project["id"], "wkr_ghost"
        )
        assert result["compliant"] is False
        assert "not found" in result.get("error", "").lower()

    def test_expired_cert_non_compliant(
        self,
        neo4j_driver: Driver,
        mcp_tools: MCPToolService,
        agent_actor: Actor,
        test_company: dict,
        test_project: dict,
        test_worker: dict,
    ) -> None:
        """Worker with expired cert should be non-compliant."""
        # Expire the certification
        with neo4j_driver.session() as session:
            session.run(
                """
                MATCH (w:Worker {id: $worker_id})-[:HOLDS_CERT]->(c:Certification)
                SET c.expiry_date = '2020-01-01'
                """,
                {"worker_id": test_worker["id"]},
            )

        result = mcp_tools.check_worker_compliance(
            agent_actor, test_company["id"], test_project["id"], test_worker["id"]
        )
        assert result["compliant"] is False
        assert len(result["expired_certifications"]) == 1


# ---------------------------------------------------------------------------
# Tool 2: check_project_compliance
# ---------------------------------------------------------------------------


class TestCheckProjectCompliance:
    """Tests for the check_project_compliance tool."""

    def test_clean_project_compliant(
        self,
        mcp_tools: MCPToolService,
        agent_actor: Actor,
        test_company: dict,
        test_project: dict,
    ) -> None:
        """Project with no issues should be compliant."""
        result = mcp_tools.check_project_compliance(
            agent_actor, test_company["id"], test_project["id"]
        )
        assert result["compliant"] is True
        assert result["issues"] == []

    def test_nonexistent_project(
        self,
        mcp_tools: MCPToolService,
        agent_actor: Actor,
        test_company: dict,
    ) -> None:
        """Missing project should return error."""
        result = mcp_tools.check_project_compliance(
            agent_actor, test_company["id"], "proj_ghost"
        )
        assert "error" in result


# ---------------------------------------------------------------------------
# Tool 3: get_project_summary
# ---------------------------------------------------------------------------


class TestGetProjectSummary:
    """Tests for the get_project_summary tool."""

    def test_summary_returns_data(
        self,
        mcp_tools: MCPToolService,
        agent_actor: Actor,
        test_company: dict,
        test_project: dict,
    ) -> None:
        """Summary should return project metadata."""
        result = mcp_tools.get_project_summary(
            agent_actor, test_company["id"], test_project["id"]
        )
        assert result["project_name"] == "Test Construction Site"
        assert "worker_count" in result
        assert "equipment_count" in result

    def test_summary_nonexistent(
        self,
        mcp_tools: MCPToolService,
        agent_actor: Actor,
        test_company: dict,
    ) -> None:
        """Missing project should return error."""
        result = mcp_tools.get_project_summary(
            agent_actor, test_company["id"], "proj_ghost"
        )
        assert "error" in result


# ---------------------------------------------------------------------------
# Tool 4: get_worker_profile
# ---------------------------------------------------------------------------


class TestGetWorkerProfile:
    """Tests for the get_worker_profile tool."""

    def test_profile_returns_data(
        self,
        mcp_tools: MCPToolService,
        agent_actor: Actor,
        test_company: dict,
        test_worker: dict,
    ) -> None:
        """Profile should return worker details and certs."""
        result = mcp_tools.get_worker_profile(
            agent_actor, test_company["id"], test_worker["id"]
        )
        assert result["name"] == "John Builder"
        assert result["role"] == "foreman"
        assert len(result["certifications"]) == 1

    def test_profile_nonexistent(
        self,
        mcp_tools: MCPToolService,
        agent_actor: Actor,
        test_company: dict,
    ) -> None:
        """Missing worker should return error."""
        result = mcp_tools.get_worker_profile(
            agent_actor, test_company["id"], "wkr_ghost"
        )
        assert "error" in result


# ---------------------------------------------------------------------------
# Tool 5: generate_morning_brief
# ---------------------------------------------------------------------------


class TestGenerateMorningBrief:
    """Tests for the generate_morning_brief tool."""

    def test_brief_for_clean_project(
        self,
        mcp_tools: MCPToolService,
        agent_actor: Actor,
        test_company: dict,
        test_project: dict,
    ) -> None:
        """Brief for a project with no issues should have inspection_overdue alert."""
        result = mcp_tools.generate_morning_brief(
            agent_actor, test_company["id"], test_project["id"]
        )
        assert result["project_name"] == "Test Construction Site"
        # No recent inspection → should have at least the overdue alert
        alert_types = [a["type"] for a in result["alerts"]]
        assert "inspection_overdue" in alert_types

    def test_brief_nonexistent_project(
        self,
        mcp_tools: MCPToolService,
        agent_actor: Actor,
        test_company: dict,
    ) -> None:
        """Missing project should return error."""
        result = mcp_tools.generate_morning_brief(
            agent_actor, test_company["id"], "proj_ghost"
        )
        assert "error" in result


# ---------------------------------------------------------------------------
# Tool 6: report_hazard
# ---------------------------------------------------------------------------


class TestReportHazard:
    """Tests for the report_hazard tool (low-risk write)."""

    def test_creates_hazard_report(
        self,
        mcp_tools: MCPToolService,
        agent_actor: Actor,
        test_company: dict,
        test_project: dict,
    ) -> None:
        """Should create a HazardReport node in the graph."""
        result = mcp_tools.report_hazard(
            actor=agent_actor,
            company_id=test_company["id"],
            project_id=test_project["id"],
            description="Unsecured scaffolding at level 3",
            location="Floor 3 East Wing",
            severity="high",
        )
        assert result["hazard_id"].startswith("haz_")
        assert result["severity"] == "high"
        assert result["status"] == "open"
        assert result["actor_type"] == "agent"

    def test_emits_event(
        self,
        mcp_tools: MCPToolService,
        event_bus: EventBus,
        agent_actor: Actor,
        test_company: dict,
        test_project: dict,
    ) -> None:
        """Should emit a HAZARD_REPORTED event."""
        received = []
        event_bus.subscribe(
            "test_listener",
            lambda e: received.append(e),
            event_types={EventType.HAZARD_REPORTED},
        )
        mcp_tools.report_hazard(
            actor=agent_actor,
            company_id=test_company["id"],
            project_id=test_project["id"],
            description="Loose cable",
        )
        assert len(received) == 1
        assert received[0].event_type == EventType.HAZARD_REPORTED


# ---------------------------------------------------------------------------
# Tool 7: report_incident
# ---------------------------------------------------------------------------


class TestReportIncident:
    """Tests for the report_incident tool (low-risk write)."""

    def test_creates_incident(
        self,
        mcp_tools: MCPToolService,
        agent_actor: Actor,
        test_company: dict,
        test_project: dict,
    ) -> None:
        """Should create an Incident node in the graph."""
        result = mcp_tools.report_incident(
            actor=agent_actor,
            company_id=test_company["id"],
            project_id=test_project["id"],
            title="Minor slip on wet floor",
            description="Worker slipped near stairwell. No injuries.",
            severity="minor",
            incident_type="near_miss",
        )
        assert result["incident_id"].startswith("inc_")
        assert result["severity"] == "minor"
        assert result["status"] == "open"

    def test_emits_event(
        self,
        mcp_tools: MCPToolService,
        event_bus: EventBus,
        agent_actor: Actor,
        test_company: dict,
        test_project: dict,
    ) -> None:
        """Should emit an INCIDENT_REPORTED event."""
        received = []
        event_bus.subscribe(
            "test_listener",
            lambda e: received.append(e),
            event_types={EventType.INCIDENT_REPORTED},
        )
        mcp_tools.report_incident(
            actor=agent_actor,
            company_id=test_company["id"],
            project_id=test_project["id"],
            title="Near miss",
            description="Falling debris near walkway",
        )
        assert len(received) == 1


# ---------------------------------------------------------------------------
# Tool 8: get_changes_since
# ---------------------------------------------------------------------------


class TestGetChangesSince:
    """Tests for the get_changes_since delta query tool."""

    def test_no_changes(
        self,
        mcp_tools: MCPToolService,
        agent_actor: Actor,
        test_company: dict,
        test_project: dict,
    ) -> None:
        """Empty project should have no changes."""
        result = mcp_tools.get_changes_since(
            actor=agent_actor,
            company_id=test_company["id"],
            project_id=test_project["id"],
            since=datetime.now(timezone.utc).isoformat(),
        )
        assert result["total_changes"] == 0

    def test_captures_recent_hazard(
        self,
        mcp_tools: MCPToolService,
        agent_actor: Actor,
        test_company: dict,
        test_project: dict,
    ) -> None:
        """Changes since before a hazard report should include it."""
        before = datetime.now(timezone.utc).isoformat()

        # Create a hazard
        mcp_tools.report_hazard(
            actor=agent_actor,
            company_id=test_company["id"],
            project_id=test_project["id"],
            description="Test hazard for delta query",
        )

        result = mcp_tools.get_changes_since(
            actor=agent_actor,
            company_id=test_company["id"],
            project_id=test_project["id"],
            since=before,
        )
        assert result["total_changes"] >= 1
        assert len(result["changes"]["hazard_reports"]) >= 1


# ---------------------------------------------------------------------------
# invoke_tool dispatch tests
# ---------------------------------------------------------------------------


class TestInvokeToolDispatch:
    """Tests for the unified invoke_tool dispatcher."""

    def test_dispatch_read_tool(
        self,
        mcp_tools: MCPToolService,
        agent_actor: Actor,
        test_company: dict,
        test_project: dict,
    ) -> None:
        """invoke_tool should dispatch to correct handler."""
        result = mcp_tools.invoke_tool(
            tool_name="get_project_summary",
            actor=agent_actor,
            company_id=test_company["id"],
            parameters={"project_id": test_project["id"]},
        )
        assert "project_name" in result

    def test_dispatch_unknown_tool(
        self,
        mcp_tools: MCPToolService,
        agent_actor: Actor,
        test_company: dict,
    ) -> None:
        """Unknown tools should return error via guardrails (high-risk default)."""
        result = mcp_tools.invoke_tool(
            tool_name="totally_fake_tool",
            actor=agent_actor,
            company_id=test_company["id"],
            parameters={},
        )
        assert "error" in result

    def test_dispatch_denied_scope(
        self,
        neo4j_driver: Driver,
        test_company: dict,
        guardrails_service: GuardrailsService,
        event_bus: EventBus,
    ) -> None:
        """Agent without required scope should get an error from invoke_tool."""
        # Create a limited agent with only read:projects scope
        agent_id = "agt_limited"
        scopes = json.dumps(["read:projects"])
        now = datetime.now(timezone.utc).isoformat()

        with neo4j_driver.session() as session:
            session.run(
                """
                MATCH (c:Company {id: $company_id})
                CREATE (a:AgentIdentity {
                    agent_id: $agent_id, name: 'Limited Agent',
                    agent_type: 'external', status: 'active',
                    scopes: $scopes, model_tier: 'fast',
                    daily_budget_cents: 100, daily_spend_cents: 0,
                    created_at: $now, created_by: 'admin'
                })
                CREATE (a)-[:BELONGS_TO {scopes: $scopes, rate_limit_per_minute: 60}]->(c)
                CREATE (c)-[:HAS_AGENT]->(a)
                """,
                {
                    "company_id": test_company["id"],
                    "agent_id": agent_id,
                    "scopes": scopes,
                    "now": now,
                },
            )

        limited_actor = Actor.agent(agent_id=agent_id, company_id=test_company["id"])
        mcp = MCPToolService(neo4j_driver, guardrails_service, event_bus)

        result = mcp.invoke_tool(
            tool_name="report_hazard",
            actor=limited_actor,
            company_id=test_company["id"],
            parameters={"project_id": "proj_test_000001", "description": "test"},
        )
        assert "error" in result
        assert "scope" in result["error"].lower()
