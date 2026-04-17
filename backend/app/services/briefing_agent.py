"""Briefing Agent — generates morning safety briefs using LLM.

Subscribes to events: inspection.completed, incident.reported,
certification.expiring, equipment.inspection_due, daily_log.submitted.

Uses MCP tools: generate_morning_brief, get_project_summary, get_changes_since.
Uses LLMService to generate natural language summary from structured data.
"""

import json
import logging
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

from neo4j import Driver

from app.models.actor import Actor
from app.models.agent_outputs import BriefingSummary
from app.models.events import Event, EventType
from app.services.base_service import BaseService
from app.services.llm_service import LLMResult, LLMService
from app.services.mcp_tools import MCPToolService

logger = logging.getLogger(__name__)

BRIEFING_SYSTEM_PROMPT = (
    "You are a safety briefing assistant for a construction company. "
    "Generate a concise morning safety brief from the structured data provided. "
    "Highlight critical alerts first, then summarise recent activity. "
    "Use clear, actionable language. Keep the brief under 500 words."
)


class BriefingAgent(BaseService):
    """Agent that generates morning safety briefs using structured data + LLM.

    Assembles context via MCP tools, then feeds structured data to the LLM
    for natural language summarisation. Cost-controlled via LLMService.

    Attributes:
        mcp_tools: MCPToolService for invoking intent-based tools.
        llm_service: LLMService for generating text summaries.
        agent_id: The registered agent identity ID.
        company_id: Tenant scope this agent operates within.
    """

    AGENT_SCOPES = (
        "read:briefings",
        "read:projects",
        "read:workers",
        "read:inspections",
    )

    AGENT_VERSION = "1.0.0"

    def __init__(
        self,
        driver: Driver,
        mcp_tools: MCPToolService,
        llm_service: LLMService,
        agent_id: str,
        company_id: str,
    ) -> None:
        """Initialise the Briefing Agent.

        Args:
            driver: Neo4j driver.
            mcp_tools: MCPToolService for tool invocation.
            llm_service: LLMService for LLM calls.
            agent_id: Registered agent identity ID.
            company_id: Tenant scope.
        """
        super().__init__(driver)
        self.mcp_tools = mcp_tools
        self.llm_service = llm_service
        self.agent_id = agent_id
        self.company_id = company_id

    def _actor(self) -> Actor:
        """Build the base Actor for this agent (used for read-only tool calls).

        Returns:
            An Actor instance representing this agent.
        """
        return Actor.agent(
            agent_id=self.agent_id,
            company_id=self.company_id,
            scopes=self.AGENT_SCOPES,
            agent_version=self.AGENT_VERSION,
        )

    def _actor_with_llm_result(self, llm_result: LLMResult) -> Actor:
        """Build an Actor enriched with LLM provenance from a completed call.

        Args:
            llm_result: The LLMResult from a completed LLM invocation.

        Returns:
            An Actor with model_id and cost_cents populated.
        """
        return Actor.agent(
            agent_id=self.agent_id,
            company_id=self.company_id,
            scopes=self.AGENT_SCOPES,
            agent_version=self.AGENT_VERSION,
            model_id=llm_result.model_id,
            cost_cents=max(1, int(llm_result.cost_cents)),
        )

    # ------------------------------------------------------------------
    # On-demand briefing generation
    # ------------------------------------------------------------------

    def generate_brief(self, project_id: str) -> BriefingSummary:
        """Generate a morning brief for a project.

        Assembles structured data from MCP tools, then uses the LLM
        to produce a natural language summary.

        Args:
            project_id: The project to generate a brief for.

        Returns:
            A BriefingSummary with both structured and LLM-generated content.
        """
        actor = self._actor()
        briefing_id = f"brief_{secrets.token_hex(8)}"
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        # Step 1: Assemble structured data via MCP tools
        brief_data = self.mcp_tools.invoke_tool(
            tool_name="generate_morning_brief",
            actor=actor,
            company_id=self.company_id,
            parameters={"project_id": project_id},
        )

        summary_data = self.mcp_tools.invoke_tool(
            tool_name="get_project_summary",
            actor=actor,
            company_id=self.company_id,
            parameters={"project_id": project_id},
        )

        since = (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()
        changes_data = self.mcp_tools.invoke_tool(
            tool_name="get_changes_since",
            actor=actor,
            company_id=self.company_id,
            parameters={"project_id": project_id, "since": since},
        )

        # Step 2: Build structured context for the LLM
        structured_data = {
            "morning_brief": brief_data,
            "project_summary": summary_data,
            "changes_24h": changes_data,
        }

        alerts = brief_data.get("alerts", [])
        project_name = (
            brief_data.get("project_name")
            or summary_data.get("project_name")
            or project_id
        )

        # Step 3: Generate LLM summary
        llm_result = self._generate_llm_summary(structured_data, project_name, today)

        # Step 4: Build and persist the briefing with full provenance
        actor = self._actor_with_llm_result(llm_result)

        briefing = BriefingSummary(
            id=briefing_id,
            briefing_id=briefing_id,
            project_id=project_id,
            project_name=project_name,
            company_id=self.company_id,
            date=today,
            alerts=alerts,
            structured_data=structured_data,
            llm_summary=llm_result.content,
            cost_cents=llm_result.cost_cents,
            model_id=llm_result.model_id,
            agent_id=self.agent_id,
        )

        self._persist_briefing(briefing, actor)
        return briefing

    # ------------------------------------------------------------------
    # Event accumulation (tracks events for next brief)
    # ------------------------------------------------------------------

    def handle_event(self, event: Event) -> None:
        """Record an event for inclusion in the next morning brief.

        The briefing agent does not produce output on every event — it
        accumulates events and produces a brief on demand via generate_brief().

        Args:
            event: The domain event to record.
        """
        if event.company_id != self.company_id:
            return

        relevant_types = {
            EventType.INSPECTION_COMPLETED,
            EventType.INCIDENT_REPORTED,
            EventType.CERTIFICATION_EXPIRING,
            EventType.EQUIPMENT_INSPECTION_DUE,
            EventType.DAILY_LOG_SUBMITTED,
        }

        if event.event_type not in relevant_types:
            return

        logger.info(
            "BriefingAgent noted event: type=%s entity=%s project=%s",
            event.event_type.value,
            event.entity_id,
            event.project_id,
        )

    # ------------------------------------------------------------------
    # LLM summary generation
    # ------------------------------------------------------------------

    def _generate_llm_summary(
        self,
        structured_data: dict[str, Any],
        project_name: str,
        date: str,
    ) -> LLMResult:
        """Generate a natural language summary from structured data.

        Args:
            structured_data: Assembled data from MCP tools.
            project_name: Name of the project.
            date: Date for the brief.

        Returns:
            An LLMResult with the generated summary text.
        """
        user_message = (
            f"Generate a morning safety brief for project '{project_name}' "
            f"dated {date}.\n\n"
            f"Structured data:\n{json.dumps(structured_data, indent=2, default=str)}"
        )

        return self.llm_service.complete(
            agent_id=self.agent_id,
            messages=[{"role": "user", "content": user_message}],
            system=BRIEFING_SYSTEM_PROMPT,
            max_tokens=2048,
        )

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def _persist_briefing(self, briefing: BriefingSummary, actor: Actor) -> None:
        """Store a BriefingSummary node in Neo4j with full agent provenance.

        Args:
            briefing: The briefing to persist.
            actor: The agent Actor with model_id/cost_cents populated.
        """
        self._write_tx_single(
            """
            MATCH (c:Company {id: $company_id})
            CREATE (b:BriefingSummary {
                id: $briefing_id,
                project_id: $project_id,
                project_name: $project_name,
                company_id: $company_id,
                date: $date,
                alerts_json: $alerts_json,
                structured_data_json: $structured_data_json,
                llm_summary: $llm_summary,
                cost_cents: $cost_cents,
                model_id: $model_id,
                agent_id: $agent_id,
                agent_version: $agent_version,
                actor_type: $actor_type,
                created_at: $created_at
            })
            CREATE (c)-[:HAS_BRIEFING]->(b)
            RETURN b.id AS briefing_id
            """,
            {
                "company_id": briefing.company_id,
                "briefing_id": briefing.briefing_id,
                "project_id": briefing.project_id,
                "project_name": briefing.project_name,
                "date": briefing.date,
                "alerts_json": json.dumps(briefing.alerts),
                "structured_data_json": json.dumps(
                    briefing.structured_data, default=str
                ),
                "llm_summary": briefing.llm_summary,
                "cost_cents": briefing.cost_cents,
                "model_id": actor.model_id,
                "agent_id": briefing.agent_id,
                "agent_version": actor.agent_version,
                "actor_type": actor.type,
                "created_at": briefing.created_at,
            },
        )
        logger.info(
            "BriefingSummary persisted: id=%s project=%s cost=%.2f cents",
            briefing.briefing_id,
            briefing.project_id,
            briefing.cost_cents,
        )
