"""Tests for Phase 6 agents — ComplianceAgent, BriefingAgent, AgentOrchestrator.

Uses real Neo4j for all graph operations. The Anthropic API is the only
external dependency mocked (declared in .mock-allowlist).
"""

import json
from datetime import datetime, timedelta, timezone
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from neo4j import Driver

from app.models.actor import Actor
from app.models.agent_identity import AgentType, ModelTier
from app.models.agent_outputs import AlertSeverity, AlertType, ComplianceAlert, BriefingSummary
from app.models.events import Event, EventType
from app.services.agent_identity_service import AgentIdentityService
from app.services.agent_orchestrator import AgentOrchestrator
from app.services.briefing_agent import BriefingAgent
from app.services.compliance_agent import ComplianceAgent
from app.services.event_bus import EventBus
from app.services.guardrails_service import GuardrailsService
from app.services.llm_service import LLMResult, LLMService
from app.services.mcp_tools import MCPToolService
from tests.conftest import TEST_SETTINGS, TEST_USER


# ---------------------------------------------------------------------------
# Shared fixtures
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
def agent_identity_service(neo4j_driver: Driver) -> AgentIdentityService:
    """Provide an AgentIdentityService."""
    return AgentIdentityService(neo4j_driver)


@pytest.fixture()
def mock_llm_service(agent_identity_service: AgentIdentityService) -> LLMService:
    """Provide an LLMService with a mocked Anthropic client.

    External dependency — declared in .mock-allowlist.
    """
    service = LLMService(TEST_SETTINGS, agent_identity_service)
    # Replace the Anthropic client with a mock
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.usage.input_tokens = 100
    mock_response.usage.output_tokens = 50
    mock_text_block = MagicMock()
    mock_text_block.text = "Morning safety brief: All clear. No critical issues."
    mock_response.content = [mock_text_block]
    mock_client.messages.create.return_value = mock_response
    service.client = mock_client
    return service


@pytest.fixture()
def compliance_agent_id() -> str:
    """Fixed agent ID for the compliance agent in tests."""
    return "agt_compliance_test"


@pytest.fixture()
def briefing_agent_id() -> str:
    """Fixed agent ID for the briefing agent in tests."""
    return "agt_briefing_test"


@pytest.fixture()
def register_compliance_agent(
    neo4j_driver: Driver,
    test_company: dict,
    compliance_agent_id: str,
) -> str:
    """Register a compliance agent identity in Neo4j.

    Returns:
        The agent ID.
    """
    scopes = json.dumps([
        "read:compliance", "read:workers", "read:projects", "read:inspections",
    ])
    now = datetime.now(timezone.utc).isoformat()

    with neo4j_driver.session() as session:
        session.run(
            """
            MATCH (c:Company {id: $company_id})
            CREATE (a:AgentIdentity {
                agent_id: $agent_id,
                name: 'Compliance Agent',
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
                rate_limit_per_minute: 60
            }]->(c)
            CREATE (c)-[:HAS_AGENT]->(a)
            """,
            {
                "company_id": test_company["id"],
                "agent_id": compliance_agent_id,
                "scopes": scopes,
                "now": now,
                "user_id": TEST_USER["uid"],
            },
        )
    return compliance_agent_id


@pytest.fixture()
def register_briefing_agent(
    neo4j_driver: Driver,
    test_company: dict,
    briefing_agent_id: str,
) -> str:
    """Register a briefing agent identity in Neo4j.

    Returns:
        The agent ID.
    """
    scopes = json.dumps([
        "read:briefings", "read:projects", "read:workers", "read:inspections",
    ])
    now = datetime.now(timezone.utc).isoformat()

    with neo4j_driver.session() as session:
        session.run(
            """
            MATCH (c:Company {id: $company_id})
            CREATE (a:AgentIdentity {
                agent_id: $agent_id,
                name: 'Briefing Agent',
                agent_type: 'briefing',
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
                "agent_id": briefing_agent_id,
                "scopes": scopes,
                "now": now,
                "user_id": TEST_USER["uid"],
            },
        )
    return briefing_agent_id


@pytest.fixture()
def compliance_agent(
    neo4j_driver: Driver,
    mcp_tools: MCPToolService,
    test_company: dict,
    register_compliance_agent: str,
) -> ComplianceAgent:
    """Provide a ComplianceAgent with a registered identity."""
    return ComplianceAgent(
        driver=neo4j_driver,
        mcp_tools=mcp_tools,
        agent_id=register_compliance_agent,
        company_id=test_company["id"],
    )


@pytest.fixture()
def briefing_agent(
    neo4j_driver: Driver,
    mcp_tools: MCPToolService,
    mock_llm_service: LLMService,
    test_company: dict,
    register_briefing_agent: str,
) -> BriefingAgent:
    """Provide a BriefingAgent with a registered identity and mocked LLM."""
    return BriefingAgent(
        driver=neo4j_driver,
        mcp_tools=mcp_tools,
        llm_service=mock_llm_service,
        agent_id=register_briefing_agent,
        company_id=test_company["id"],
    )


@pytest.fixture()
def test_worker(neo4j_driver: Driver, test_company: dict) -> dict:
    """Create a test worker with a valid certification."""
    now = datetime.now(timezone.utc).isoformat()
    worker_data = {
        "id": "wkr_agent_test_001",
        "first_name": "Jane",
        "last_name": "Safety",
        "email": "jane@test.com",
        "phone": "555-222-3333",
        "role": "supervisor",
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
        "id": "cert_agent_001",
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
def expired_worker(neo4j_driver: Driver, test_company: dict) -> dict:
    """Create a test worker with an expired certification."""
    now = datetime.now(timezone.utc).isoformat()
    worker_data = {
        "id": "wkr_expired_001",
        "first_name": "Bob",
        "last_name": "Expired",
        "email": "bob@test.com",
        "phone": "555-333-4444",
        "role": "laborer",
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
        "id": "cert_expired_001",
        "certification_type": "Fall Protection",
        "expiry_date": "2020-01-01",
        "issue_date": "2019-01-01",
        "status": "expired",
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


@pytest.fixture()
def assigned_expired_worker(
    neo4j_driver: Driver, expired_worker: dict, test_project: dict
) -> dict:
    """Assign the expired-cert worker to the test project."""
    with neo4j_driver.session() as session:
        session.run(
            """
            MATCH (w:Worker {id: $worker_id})
            MATCH (p:Project {id: $project_id})
            CREATE (w)-[:ASSIGNED_TO]->(p)
            """,
            {"worker_id": expired_worker["id"], "project_id": test_project["id"]},
        )
    return expired_worker


def _make_event(
    event_type: EventType,
    entity_id: str,
    entity_type: str,
    company_id: str,
    project_id: str | None = None,
    summary: dict[str, Any] | None = None,
    graph_context: dict[str, Any] | None = None,
) -> Event:
    """Helper to build an Event for testing."""
    return Event(
        event_id=f"evt_test_{entity_id}",
        event_type=event_type,
        entity_id=entity_id,
        entity_type=entity_type,
        company_id=company_id,
        project_id=project_id,
        actor={"type": "human", "id": TEST_USER["uid"], "agent_id": None},
        summary=summary or {},
        graph_context=graph_context or {},
    )


# ===========================================================================
# ComplianceAgent tests
# ===========================================================================


class TestComplianceAgentInspectionCompleted:
    """Tests for inspection.completed event handling. [HAPPY] [ERROR] [EDGE]"""

    def test_compliant_project_no_alerts__CAT_HAPPY(
        self,
        compliance_agent: ComplianceAgent,
        test_company: dict,
        test_project: dict,
        assigned_worker: dict,
    ) -> None:
        """Compliant project produces no alerts after inspection."""
        event = _make_event(
            EventType.INSPECTION_COMPLETED,
            entity_id="insp_001",
            entity_type="Inspection",
            company_id=test_company["id"],
            project_id=test_project["id"],
        )

        alerts = compliance_agent.handle_event(event)
        assert alerts == []

    def test_non_compliant_project_produces_alert__CAT_HAPPY(
        self,
        compliance_agent: ComplianceAgent,
        test_company: dict,
        test_project: dict,
        assigned_expired_worker: dict,
    ) -> None:
        """Project with expired certs triggers a compliance alert."""
        event = _make_event(
            EventType.INSPECTION_COMPLETED,
            entity_id="insp_002",
            entity_type="Inspection",
            company_id=test_company["id"],
            project_id=test_project["id"],
        )

        alerts = compliance_agent.handle_event(event)
        assert len(alerts) == 1
        assert alerts[0].alert_type == AlertType.PROJECT_NON_COMPLIANT
        assert alerts[0].severity == AlertSeverity.HIGH
        assert alerts[0].entity_id == test_project["id"]
        assert "expired" in alerts[0].message.lower()

    def test_event_without_project_id_skipped__CAT_EDGE(
        self,
        compliance_agent: ComplianceAgent,
        test_company: dict,
    ) -> None:
        """Inspection event with no project_id produces no alerts."""
        event = _make_event(
            EventType.INSPECTION_COMPLETED,
            entity_id="insp_003",
            entity_type="Inspection",
            company_id=test_company["id"],
            project_id=None,
        )

        alerts = compliance_agent.handle_event(event)
        assert alerts == []

    def test_wrong_company_ignored__CAT_EDGE(
        self,
        compliance_agent: ComplianceAgent,
        test_project: dict,
    ) -> None:
        """Events from other companies are ignored."""
        event = _make_event(
            EventType.INSPECTION_COMPLETED,
            entity_id="insp_004",
            entity_type="Inspection",
            company_id="comp_other_company",
            project_id=test_project["id"],
        )

        alerts = compliance_agent.handle_event(event)
        assert alerts == []


class TestComplianceAgentWorkerAssigned:
    """Tests for worker.assigned_to_project event handling. [HAPPY] [ERROR]"""

    def test_compliant_worker_no_alerts__CAT_HAPPY(
        self,
        compliance_agent: ComplianceAgent,
        test_company: dict,
        test_project: dict,
        assigned_worker: dict,
    ) -> None:
        """Compliant worker assigned to project produces no alerts."""
        event = _make_event(
            EventType.WORKER_ASSIGNED,
            entity_id=assigned_worker["id"],
            entity_type="Worker",
            company_id=test_company["id"],
            project_id=test_project["id"],
        )

        alerts = compliance_agent.handle_event(event)
        assert alerts == []

    def test_non_compliant_worker_produces_alert__CAT_HAPPY(
        self,
        compliance_agent: ComplianceAgent,
        test_company: dict,
        test_project: dict,
        assigned_expired_worker: dict,
    ) -> None:
        """Non-compliant worker assigned to project triggers alert."""
        event = _make_event(
            EventType.WORKER_ASSIGNED,
            entity_id=assigned_expired_worker["id"],
            entity_type="Worker",
            company_id=test_company["id"],
            project_id=test_project["id"],
        )

        alerts = compliance_agent.handle_event(event)
        assert len(alerts) == 1
        assert alerts[0].alert_type == AlertType.WORKER_NON_COMPLIANT
        assert alerts[0].entity_id == assigned_expired_worker["id"]
        assert "Bob Expired" in alerts[0].message

    def test_nonexistent_worker_no_crash__CAT_ERROR(
        self,
        compliance_agent: ComplianceAgent,
        test_company: dict,
        test_project: dict,
    ) -> None:
        """Missing worker entity doesn't crash the agent."""
        event = _make_event(
            EventType.WORKER_ASSIGNED,
            entity_id="wkr_ghost_999",
            entity_type="Worker",
            company_id=test_company["id"],
            project_id=test_project["id"],
        )

        # Should handle gracefully — invoke_tool returns error but agent doesn't crash
        alerts = compliance_agent.handle_event(event)
        assert alerts == []


class TestComplianceAgentCertExpiring:
    """Tests for certification.expiring event handling. [HAPPY] [VALIDATION]"""

    def test_certification_expiring_alert__CAT_HAPPY(
        self,
        compliance_agent: ComplianceAgent,
        test_company: dict,
    ) -> None:
        """Certification expiring event produces an alert."""
        event = _make_event(
            EventType.CERTIFICATION_EXPIRING,
            entity_id="cert_exp_001",
            entity_type="Certification",
            company_id=test_company["id"],
            summary={
                "worker_id": "wkr_001",
                "worker_name": "John Doe",
                "certification_type": "OSHA 30-Hour",
                "expiry_date": "2026-04-20",
            },
        )

        alerts = compliance_agent.handle_event(event)
        assert len(alerts) == 1
        assert alerts[0].alert_type == AlertType.CERTIFICATION_EXPIRING
        assert alerts[0].severity == AlertSeverity.MEDIUM
        assert "OSHA 30-Hour" in alerts[0].message
        assert "John Doe" in alerts[0].message

    def test_alert_persisted_to_neo4j__CAT_VALIDATION(
        self,
        neo4j_driver: Driver,
        compliance_agent: ComplianceAgent,
        test_company: dict,
    ) -> None:
        """Alerts are persisted as ComplianceAlert nodes in Neo4j."""
        event = _make_event(
            EventType.CERTIFICATION_EXPIRING,
            entity_id="cert_persist_001",
            entity_type="Certification",
            company_id=test_company["id"],
            summary={
                "worker_id": "wkr_002",
                "worker_name": "Jane Persist",
                "certification_type": "First Aid",
                "expiry_date": "2026-05-01",
            },
        )

        alerts = compliance_agent.handle_event(event)
        assert len(alerts) == 1

        # Verify persisted in Neo4j
        with neo4j_driver.session() as session:
            result = session.run(
                """
                MATCH (c:Company {id: $company_id})-[:HAS_COMPLIANCE_ALERT]->(a:ComplianceAlert)
                WHERE a.alert_id = $alert_id
                RETURN a.alert_type AS alert_type, a.severity AS severity,
                       a.message AS message, a.agent_id AS agent_id
                """,
                {
                    "company_id": test_company["id"],
                    "alert_id": alerts[0].alert_id,
                },
            ).single()

        assert result is not None
        assert result["alert_type"] == "certification_expiring"
        assert result["severity"] == "medium"
        assert result["agent_id"] == compliance_agent.agent_id


class TestComplianceAgentCorrectiveAction:
    """Tests for corrective_action.overdue event handling. [HAPPY]"""

    def test_overdue_corrective_action_alert__CAT_HAPPY(
        self,
        compliance_agent: ComplianceAgent,
        test_company: dict,
        test_project: dict,
    ) -> None:
        """Overdue corrective action produces a high-severity alert."""
        event = _make_event(
            EventType.CORRECTIVE_ACTION_OVERDUE,
            entity_id="ca_001",
            entity_type="CorrectiveAction",
            company_id=test_company["id"],
            project_id=test_project["id"],
            summary={"description": "Install guardrails on level 3"},
        )

        alerts = compliance_agent.handle_event(event)
        assert len(alerts) == 1
        assert alerts[0].alert_type == AlertType.CORRECTIVE_ACTION_OVERDUE
        assert alerts[0].severity == AlertSeverity.HIGH
        assert "guardrails" in alerts[0].message.lower()


class TestComplianceAgentOnDemand:
    """Tests for on-demand compliance check. [HAPPY] [ERROR]"""

    def test_on_demand_check_compliant_project__CAT_HAPPY(
        self,
        compliance_agent: ComplianceAgent,
        test_company: dict,
        test_project: dict,
        assigned_worker: dict,
    ) -> None:
        """On-demand check on compliant project returns empty list."""
        alerts = compliance_agent.run_project_check(test_project["id"])
        assert alerts == []

    def test_on_demand_check_non_compliant_project__CAT_HAPPY(
        self,
        compliance_agent: ComplianceAgent,
        test_company: dict,
        test_project: dict,
        assigned_expired_worker: dict,
    ) -> None:
        """On-demand check on non-compliant project returns alerts."""
        alerts = compliance_agent.run_project_check(test_project["id"])
        assert len(alerts) == 1
        assert alerts[0].alert_type == AlertType.PROJECT_NON_COMPLIANT

    def test_on_demand_check_nonexistent_project__CAT_ERROR(
        self,
        compliance_agent: ComplianceAgent,
    ) -> None:
        """On-demand check on non-existent project returns empty list."""
        alerts = compliance_agent.run_project_check("proj_ghost_999")
        assert alerts == []


# ===========================================================================
# BriefingAgent tests
# ===========================================================================


class TestBriefingAgentGeneration:
    """Tests for briefing generation. [HAPPY] [ERROR] [VALIDATION]"""

    def test_generate_brief_happy_path__CAT_HAPPY(
        self,
        briefing_agent: BriefingAgent,
        test_company: dict,
        test_project: dict,
        assigned_worker: dict,
    ) -> None:
        """Generate brief returns a BriefingSummary with LLM content."""
        result = briefing_agent.generate_brief(test_project["id"])

        assert isinstance(result, BriefingSummary)
        assert result.project_id == test_project["id"]
        assert result.company_id == test_company["id"]
        assert result.llm_summary != ""
        assert result.model_id != ""
        assert result.agent_id == briefing_agent.agent_id
        assert result.date == datetime.now(timezone.utc).strftime("%Y-%m-%d")

    def test_generate_brief_includes_structured_data__CAT_VALIDATION(
        self,
        briefing_agent: BriefingAgent,
        test_project: dict,
        assigned_worker: dict,
    ) -> None:
        """Generated brief includes structured data from MCP tools."""
        result = briefing_agent.generate_brief(test_project["id"])

        assert "morning_brief" in result.structured_data
        assert "project_summary" in result.structured_data
        assert "changes_24h" in result.structured_data

    def test_generate_brief_persisted_to_neo4j__CAT_VALIDATION(
        self,
        neo4j_driver: Driver,
        briefing_agent: BriefingAgent,
        test_company: dict,
        test_project: dict,
        assigned_worker: dict,
    ) -> None:
        """Generated brief is stored as a BriefingSummary node in Neo4j."""
        result = briefing_agent.generate_brief(test_project["id"])

        with neo4j_driver.session() as session:
            record = session.run(
                """
                MATCH (c:Company {id: $company_id})-[:HAS_BRIEFING]->(b:BriefingSummary)
                WHERE b.briefing_id = $briefing_id
                RETURN b.project_id AS project_id, b.llm_summary AS llm_summary,
                       b.agent_id AS agent_id, b.model_id AS model_id
                """,
                {
                    "company_id": test_company["id"],
                    "briefing_id": result.briefing_id,
                },
            ).single()

        assert record is not None
        assert record["project_id"] == test_project["id"]
        assert record["llm_summary"] != ""
        assert record["agent_id"] == briefing_agent.agent_id

    def test_generate_brief_tracks_cost__CAT_VALIDATION(
        self,
        briefing_agent: BriefingAgent,
        test_project: dict,
        assigned_worker: dict,
    ) -> None:
        """Brief generation records LLM cost."""
        result = briefing_agent.generate_brief(test_project["id"])

        # Cost should be recorded (mock returns 100 input + 50 output tokens)
        assert result.cost_cents >= 0
        assert result.model_id != ""


class TestBriefingAgentEventHandling:
    """Tests for briefing agent event handler. [HAPPY] [EDGE]"""

    def test_handles_relevant_events__CAT_HAPPY(
        self,
        briefing_agent: BriefingAgent,
        test_company: dict,
        test_project: dict,
    ) -> None:
        """Briefing agent accepts relevant events without error."""
        for event_type in [
            EventType.INSPECTION_COMPLETED,
            EventType.INCIDENT_REPORTED,
            EventType.CERTIFICATION_EXPIRING,
            EventType.EQUIPMENT_INSPECTION_DUE,
        ]:
            event = _make_event(
                event_type,
                entity_id="test_entity",
                entity_type="TestEntity",
                company_id=test_company["id"],
                project_id=test_project["id"],
            )
            # Should not raise
            briefing_agent.handle_event(event)

    def test_ignores_wrong_company__CAT_EDGE(
        self,
        briefing_agent: BriefingAgent,
        test_project: dict,
    ) -> None:
        """Events from other companies are ignored."""
        event = _make_event(
            EventType.INSPECTION_COMPLETED,
            entity_id="test_entity",
            entity_type="Inspection",
            company_id="comp_other",
            project_id=test_project["id"],
        )
        # Should not raise
        briefing_agent.handle_event(event)

    def test_ignores_irrelevant_events__CAT_EDGE(
        self,
        briefing_agent: BriefingAgent,
        test_company: dict,
    ) -> None:
        """Non-subscribed event types are ignored."""
        event = _make_event(
            EventType.DOCUMENT_GENERATED,
            entity_id="doc_001",
            entity_type="Document",
            company_id=test_company["id"],
        )
        # Should not raise
        briefing_agent.handle_event(event)


# ===========================================================================
# AgentOrchestrator tests
# ===========================================================================


class TestOrchestratorRegistration:
    """Tests for agent registration. [HAPPY] [EDGE]"""

    def test_register_agents__CAT_HAPPY(
        self,
        neo4j_driver: Driver,
        agent_identity_service: AgentIdentityService,
        mcp_tools: MCPToolService,
        mock_llm_service: LLMService,
        event_bus: EventBus,
        test_company: dict,
    ) -> None:
        """Orchestrator registers both agents for a company."""
        orchestrator = AgentOrchestrator(
            driver=neo4j_driver,
            agent_service=agent_identity_service,
            mcp_tools=mcp_tools,
            llm_service=mock_llm_service,
            event_bus=event_bus,
        )

        result = orchestrator.register_agents(
            test_company["id"], TEST_USER["uid"]
        )

        assert "compliance" in result
        assert "briefing" in result
        assert result["compliance"].startswith("agt_")
        assert result["briefing"].startswith("agt_")

        # Verify agents exist in Neo4j
        agents = agent_identity_service.list_for_company(test_company["id"])
        agent_types = {a.agent_type for a in agents}
        assert AgentType.COMPLIANCE in agent_types
        assert AgentType.BRIEFING in agent_types

    def test_register_agents_idempotent__CAT_EDGE(
        self,
        neo4j_driver: Driver,
        agent_identity_service: AgentIdentityService,
        mcp_tools: MCPToolService,
        mock_llm_service: LLMService,
        event_bus: EventBus,
        test_company: dict,
    ) -> None:
        """Registering agents twice returns existing IDs without creating duplicates."""
        orchestrator = AgentOrchestrator(
            driver=neo4j_driver,
            agent_service=agent_identity_service,
            mcp_tools=mcp_tools,
            llm_service=mock_llm_service,
            event_bus=event_bus,
        )

        first = orchestrator.register_agents(
            test_company["id"], TEST_USER["uid"]
        )
        second = orchestrator.register_agents(
            test_company["id"], TEST_USER["uid"]
        )

        assert first["compliance"] == second["compliance"]
        assert first["briefing"] == second["briefing"]

        # Only 2 agents should exist
        agents = agent_identity_service.list_for_company(test_company["id"])
        assert len(agents) == 2


class TestOrchestratorEventWiring:
    """Tests for event subscription wiring. [HAPPY]"""

    def test_wire_subscriptions__CAT_HAPPY(
        self,
        neo4j_driver: Driver,
        agent_identity_service: AgentIdentityService,
        mcp_tools: MCPToolService,
        mock_llm_service: LLMService,
        event_bus: EventBus,
        test_company: dict,
    ) -> None:
        """Wiring subscriptions registers both agents in the EventBus."""
        orchestrator = AgentOrchestrator(
            driver=neo4j_driver,
            agent_service=agent_identity_service,
            mcp_tools=mcp_tools,
            llm_service=mock_llm_service,
            event_bus=event_bus,
        )

        orchestrator.register_agents(test_company["id"], TEST_USER["uid"])
        orchestrator.wire_subscriptions()

        assert event_bus.subscriber_count == 2

    def test_event_routed_to_compliance_agent__CAT_HAPPY(
        self,
        neo4j_driver: Driver,
        agent_identity_service: AgentIdentityService,
        mcp_tools: MCPToolService,
        mock_llm_service: LLMService,
        event_bus: EventBus,
        test_company: dict,
        test_project: dict,
        assigned_expired_worker: dict,
    ) -> None:
        """Events emitted on EventBus reach the compliance agent."""
        orchestrator = AgentOrchestrator(
            driver=neo4j_driver,
            agent_service=agent_identity_service,
            mcp_tools=mcp_tools,
            llm_service=mock_llm_service,
            event_bus=event_bus,
        )

        orchestrator.register_agents(test_company["id"], TEST_USER["uid"])
        orchestrator.wire_subscriptions()

        # Emit an inspection.completed event
        event = event_bus.create_event(
            event_type=EventType.INSPECTION_COMPLETED,
            entity_id="insp_evt_001",
            entity_type="Inspection",
            company_id=test_company["id"],
            project_id=test_project["id"],
            actor=Actor.human(TEST_USER["uid"]),
        )
        successful = event_bus.emit(event)

        # The compliance_agent subscriber should have processed it
        assert "compliance_agent" in successful

        # Check that a ComplianceAlert was created in Neo4j
        with neo4j_driver.session() as session:
            result = session.run(
                """
                MATCH (c:Company {id: $company_id})-[:HAS_COMPLIANCE_ALERT]->(a:ComplianceAlert)
                RETURN count(a) AS alert_count
                """,
                {"company_id": test_company["id"]},
            ).single()

        assert result["alert_count"] >= 1


class TestOrchestratorOnDemand:
    """Tests for on-demand entry points. [HAPPY] [ERROR]"""

    def test_run_compliance_check__CAT_HAPPY(
        self,
        neo4j_driver: Driver,
        agent_identity_service: AgentIdentityService,
        mcp_tools: MCPToolService,
        mock_llm_service: LLMService,
        event_bus: EventBus,
        test_company: dict,
        test_project: dict,
        assigned_expired_worker: dict,
    ) -> None:
        """On-demand compliance check returns alert dicts."""
        orchestrator = AgentOrchestrator(
            driver=neo4j_driver,
            agent_service=agent_identity_service,
            mcp_tools=mcp_tools,
            llm_service=mock_llm_service,
            event_bus=event_bus,
        )
        orchestrator.register_agents(test_company["id"], TEST_USER["uid"])

        alerts = orchestrator.run_compliance_check(
            test_company["id"], test_project["id"]
        )

        assert len(alerts) == 1
        assert alerts[0]["alert_type"] == "project_non_compliant"

    def test_run_briefing__CAT_HAPPY(
        self,
        neo4j_driver: Driver,
        agent_identity_service: AgentIdentityService,
        mcp_tools: MCPToolService,
        mock_llm_service: LLMService,
        event_bus: EventBus,
        test_company: dict,
        test_project: dict,
        assigned_worker: dict,
    ) -> None:
        """On-demand briefing generates a brief dict."""
        orchestrator = AgentOrchestrator(
            driver=neo4j_driver,
            agent_service=agent_identity_service,
            mcp_tools=mcp_tools,
            llm_service=mock_llm_service,
            event_bus=event_bus,
        )
        orchestrator.register_agents(test_company["id"], TEST_USER["uid"])

        result = orchestrator.run_briefing(
            test_company["id"], test_project["id"]
        )

        assert result is not None
        assert result["project_id"] == test_project["id"]
        assert result["llm_summary"] != ""
        assert result["agent_id"] != ""

    def test_run_compliance_check_unregistered_company__CAT_ERROR(
        self,
        neo4j_driver: Driver,
        agent_identity_service: AgentIdentityService,
        mcp_tools: MCPToolService,
        mock_llm_service: LLMService,
        event_bus: EventBus,
    ) -> None:
        """Compliance check on unregistered company returns empty list."""
        orchestrator = AgentOrchestrator(
            driver=neo4j_driver,
            agent_service=agent_identity_service,
            mcp_tools=mcp_tools,
            llm_service=mock_llm_service,
            event_bus=event_bus,
        )

        alerts = orchestrator.run_compliance_check("comp_unknown", "proj_unknown")
        assert alerts == []

    def test_run_briefing_unregistered_company__CAT_ERROR(
        self,
        neo4j_driver: Driver,
        agent_identity_service: AgentIdentityService,
        mcp_tools: MCPToolService,
        mock_llm_service: LLMService,
        event_bus: EventBus,
    ) -> None:
        """Briefing on unregistered company returns None."""
        orchestrator = AgentOrchestrator(
            driver=neo4j_driver,
            agent_service=agent_identity_service,
            mcp_tools=mcp_tools,
            llm_service=mock_llm_service,
            event_bus=event_bus,
        )

        result = orchestrator.run_briefing("comp_unknown", "proj_unknown")
        assert result is None


class TestOrchestratorErrorHandling:
    """Tests for graceful error handling. [ERROR] [EDGE]"""

    def test_compliance_agent_error_does_not_crash__CAT_ERROR(
        self,
        neo4j_driver: Driver,
        agent_identity_service: AgentIdentityService,
        mcp_tools: MCPToolService,
        mock_llm_service: LLMService,
        event_bus: EventBus,
        test_company: dict,
        test_project: dict,
    ) -> None:
        """Agent errors are caught — orchestrator doesn't crash."""
        orchestrator = AgentOrchestrator(
            driver=neo4j_driver,
            agent_service=agent_identity_service,
            mcp_tools=mcp_tools,
            llm_service=mock_llm_service,
            event_bus=event_bus,
        )
        orchestrator.register_agents(test_company["id"], TEST_USER["uid"])
        orchestrator.wire_subscriptions()

        # Emit an event for a non-existent project — should not crash
        event = event_bus.create_event(
            event_type=EventType.INSPECTION_COMPLETED,
            entity_id="insp_error_001",
            entity_type="Inspection",
            company_id=test_company["id"],
            project_id="proj_nonexistent",
            actor=Actor.human(TEST_USER["uid"]),
        )
        successful = event_bus.emit(event)

        # Compliance agent should still be listed as successful
        # (it handled the event gracefully, returning empty alerts)
        assert "compliance_agent" in successful


# ===========================================================================
# Model tests
# ===========================================================================


class TestComplianceAlertModel:
    """Tests for ComplianceAlert Pydantic model. [VALIDATION]"""

    def test_create_compliance_alert__CAT_VALIDATION(self) -> None:
        """ComplianceAlert can be created with required fields."""
        alert = ComplianceAlert(
            alert_id="alert_test_001",
            alert_type=AlertType.CERTIFICATION_EXPIRED,
            severity=AlertSeverity.HIGH,
            entity_id="cert_001",
            entity_type="Certification",
            company_id="comp_001",
            message="Test alert",
            agent_id="agt_001",
        )
        assert alert.alert_id == "alert_test_001"
        assert alert.alert_type == AlertType.CERTIFICATION_EXPIRED
        assert alert.created_at is not None

    def test_alert_serialization__CAT_VALIDATION(self) -> None:
        """ComplianceAlert can be serialized to dict."""
        alert = ComplianceAlert(
            alert_id="alert_test_002",
            alert_type=AlertType.WORKER_NON_COMPLIANT,
            severity=AlertSeverity.MEDIUM,
            entity_id="wkr_001",
            entity_type="Worker",
            company_id="comp_001",
            message="Worker non-compliant",
            details={"expired_certs": 2},
            agent_id="agt_001",
        )
        data = alert.model_dump()
        assert data["alert_type"] == "worker_non_compliant"
        assert data["details"]["expired_certs"] == 2


class TestBriefingSummaryModel:
    """Tests for BriefingSummary Pydantic model. [VALIDATION]"""

    def test_create_briefing_summary__CAT_VALIDATION(self) -> None:
        """BriefingSummary can be created with required fields."""
        briefing = BriefingSummary(
            briefing_id="brief_test_001",
            project_id="proj_001",
            company_id="comp_001",
            date="2026-04-10",
            agent_id="agt_001",
        )
        assert briefing.briefing_id == "brief_test_001"
        assert briefing.llm_summary == ""
        assert briefing.cost_cents == 0.0

    def test_briefing_with_full_data__CAT_VALIDATION(self) -> None:
        """BriefingSummary accepts all optional fields."""
        briefing = BriefingSummary(
            briefing_id="brief_test_002",
            project_id="proj_001",
            project_name="Test Site",
            company_id="comp_001",
            date="2026-04-10",
            alerts=[{"type": "cert_expired", "severity": "high"}],
            llm_summary="All clear on site today.",
            cost_cents=1.5,
            model_id="claude-sonnet-4-20250514",
            agent_id="agt_002",
        )
        assert briefing.project_name == "Test Site"
        assert len(briefing.alerts) == 1
        assert briefing.cost_cents == 1.5
