"""Agent Orchestrator — registers agents and wires event subscriptions.

Lightweight service that:
1. Registers both agents as AgentIdentity nodes on startup (idempotent)
2. Wires event subscriptions to the EventBus
3. Provides on-demand entry points for compliance checks and briefings
4. Handles agent errors gracefully (log + continue)
"""

import logging
from typing import Any

from neo4j import Driver

from app.models.agent_identity import (
    AgentIdentityCreate,
    AgentType,
    ModelTier,
)
from app.models.events import Event, EventType
from app.services.agent_identity_service import AgentIdentityService
from app.services.briefing_agent import BriefingAgent
from app.services.compliance_agent import ComplianceAgent
from app.services.event_bus import EventBus
from app.services.llm_service import LLMService
from app.services.mcp_tools import MCPToolService

logger = logging.getLogger(__name__)


# Agent registration specs — idempotent
COMPLIANCE_AGENT_SPEC = AgentIdentityCreate(
    name="Compliance Agent",
    agent_type=AgentType.COMPLIANCE,
    scopes=[
        "read:compliance",
        "read:workers",
        "read:projects",
        "read:inspections",
    ],
    model_tier=ModelTier.STANDARD,
    daily_budget_cents=100,  # Read-only agent, no LLM spend expected
)

BRIEFING_AGENT_SPEC = AgentIdentityCreate(
    name="Briefing Agent",
    agent_type=AgentType.BRIEFING,
    scopes=[
        "read:briefings",
        "read:projects",
        "read:workers",
        "read:inspections",
    ],
    model_tier=ModelTier.STANDARD,
    daily_budget_cents=2000,  # LLM calls for summary generation
)


class AgentOrchestrator:
    """Registers agents, wires events, and provides on-demand entry points.

    Attributes:
        driver: Neo4j driver.
        agent_service: AgentIdentityService for agent CRUD.
        mcp_tools: MCPToolService for tool invocation.
        llm_service: LLMService for LLM calls.
        event_bus: EventBus for event subscriptions.
        compliance_agents: Dict of company_id -> ComplianceAgent.
        briefing_agents: Dict of company_id -> BriefingAgent.
    """

    def __init__(
        self,
        driver: Driver,
        agent_service: AgentIdentityService,
        mcp_tools: MCPToolService,
        llm_service: LLMService,
        event_bus: EventBus,
    ) -> None:
        """Initialise the orchestrator.

        Args:
            driver: Neo4j driver.
            agent_service: AgentIdentityService for registration.
            mcp_tools: MCPToolService for agent tool calls.
            llm_service: LLMService for briefing agent.
            event_bus: EventBus for wiring subscriptions.
        """
        self.driver = driver
        self.agent_service = agent_service
        self.mcp_tools = mcp_tools
        self.llm_service = llm_service
        self.event_bus = event_bus
        self._compliance_agents: dict[str, ComplianceAgent] = {}
        self._briefing_agents: dict[str, BriefingAgent] = {}

    # ------------------------------------------------------------------
    # Agent registration (idempotent)
    # ------------------------------------------------------------------

    def register_agents(
        self, company_id: str, registered_by: str
    ) -> dict[str, str]:
        """Register both agents for a company (idempotent).

        If an agent already exists for the company, skips registration.

        Args:
            company_id: The company to register agents for.
            registered_by: User ID performing the registration.

        Returns:
            Dict with agent_type -> agent_id mapping.
        """
        result: dict[str, str] = {}

        compliance_id = self._register_agent(
            company_id, COMPLIANCE_AGENT_SPEC, registered_by
        )
        result["compliance"] = compliance_id

        briefing_id = self._register_agent(
            company_id, BRIEFING_AGENT_SPEC, registered_by
        )
        result["briefing"] = briefing_id

        # Instantiate agents
        self._compliance_agents[company_id] = ComplianceAgent(
            driver=self.driver,
            mcp_tools=self.mcp_tools,
            agent_id=compliance_id,
            company_id=company_id,
        )
        self._briefing_agents[company_id] = BriefingAgent(
            driver=self.driver,
            mcp_tools=self.mcp_tools,
            llm_service=self.llm_service,
            agent_id=briefing_id,
            company_id=company_id,
        )

        logger.info(
            "Agents registered for company %s: compliance=%s briefing=%s",
            company_id,
            compliance_id,
            briefing_id,
        )
        return result

    def _register_agent(
        self,
        company_id: str,
        spec: AgentIdentityCreate,
        registered_by: str,
    ) -> str:
        """Register a single agent (idempotent — skip if exists).

        Args:
            company_id: Company to register the agent for.
            spec: Agent registration spec.
            registered_by: User performing the registration.

        Returns:
            The agent_id (existing or newly created).
        """
        existing = self.agent_service.list_for_company(company_id)
        for agent in existing:
            if agent.agent_type == spec.agent_type:
                logger.info(
                    "Agent %s (%s) already exists for company %s — skipping",
                    agent.agent_id,
                    spec.agent_type.value,
                    company_id,
                )
                return agent.agent_id

        agent = self.agent_service.register(company_id, spec, registered_by)
        return agent.agent_id

    # ------------------------------------------------------------------
    # Event wiring
    # ------------------------------------------------------------------

    def wire_subscriptions(self) -> None:
        """Wire event subscriptions for all registered agents.

        Subscribes the compliance agent to its event types and the
        briefing agent to its event types via the EventBus.
        """
        self.event_bus.subscribe(
            name="compliance_agent",
            handler=self._compliance_event_handler,
            event_types={
                EventType.CERTIFICATION_EXPIRING,
                EventType.WORKER_ASSIGNED,
                EventType.INSPECTION_COMPLETED,
                EventType.CORRECTIVE_ACTION_OVERDUE,
            },
        )

        self.event_bus.subscribe(
            name="briefing_agent",
            handler=self._briefing_event_handler,
            event_types={
                EventType.INSPECTION_COMPLETED,
                EventType.INCIDENT_REPORTED,
                EventType.CERTIFICATION_EXPIRING,
                EventType.EQUIPMENT_INSPECTION_DUE,
                EventType.DAILY_LOG_SUBMITTED,
            },
        )

        logger.info("Agent event subscriptions wired")

    def _compliance_event_handler(self, event: Event) -> None:
        """Route events to the appropriate company's compliance agent.

        Args:
            event: The domain event.
        """
        agent = self._compliance_agents.get(event.company_id)
        if agent is None:
            logger.debug(
                "No compliance agent for company %s — skipping event %s",
                event.company_id,
                event.event_id,
            )
            return

        try:
            alerts = agent.handle_event(event)
            if alerts:
                logger.info(
                    "ComplianceAgent produced %d alerts from event %s",
                    len(alerts),
                    event.event_id,
                )
        except Exception:
            logger.exception(
                "ComplianceAgent error on event %s", event.event_id
            )

    def _briefing_event_handler(self, event: Event) -> None:
        """Route events to the appropriate company's briefing agent.

        Args:
            event: The domain event.
        """
        agent = self._briefing_agents.get(event.company_id)
        if agent is None:
            logger.debug(
                "No briefing agent for company %s — skipping event %s",
                event.company_id,
                event.event_id,
            )
            return

        try:
            agent.handle_event(event)
        except Exception:
            logger.exception(
                "BriefingAgent error on event %s", event.event_id
            )

    # ------------------------------------------------------------------
    # On-demand entry points
    # ------------------------------------------------------------------

    def run_compliance_check(
        self, company_id: str, project_id: str
    ) -> list[dict[str, Any]]:
        """Run an on-demand compliance check.

        Args:
            company_id: Tenant scope.
            project_id: Project to check.

        Returns:
            List of alert dicts. Empty if agent not registered or no issues.
        """
        agent = self._compliance_agents.get(company_id)
        if agent is None:
            logger.warning(
                "No compliance agent for company %s", company_id
            )
            return []

        try:
            alerts = agent.run_project_check(project_id)
            return [a.model_dump() for a in alerts]
        except Exception:
            logger.exception(
                "ComplianceAgent error during on-demand check: company=%s project=%s",
                company_id,
                project_id,
            )
            return []

    def run_briefing(
        self, company_id: str, project_id: str
    ) -> dict[str, Any] | None:
        """Run an on-demand briefing generation.

        Args:
            company_id: Tenant scope.
            project_id: Project to brief.

        Returns:
            BriefingSummary dict, or None if agent not registered or error.
        """
        agent = self._briefing_agents.get(company_id)
        if agent is None:
            logger.warning(
                "No briefing agent for company %s", company_id
            )
            return None

        try:
            briefing = agent.generate_brief(project_id)
            return briefing.model_dump()
        except Exception:
            logger.exception(
                "BriefingAgent error during on-demand brief: company=%s project=%s",
                company_id,
                project_id,
            )
            return None
