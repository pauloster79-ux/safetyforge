"""Compliance Agent — read-only agent that watches for regulatory violations.

Subscribes to events: certification.expiring, worker.assigned_to_project,
inspection.completed, corrective_action.overdue.

Uses MCP tools via invoke_tool(): check_worker_compliance, check_project_compliance.

This agent uses graph traversal only — no LLM calls. It produces structured
ComplianceAlert nodes stored in Neo4j.
"""

import json
import logging
import secrets
from datetime import datetime, timezone
from typing import Any

from neo4j import Driver

from app.models.actor import Actor
from app.models.agent_outputs import AlertSeverity, AlertType, ComplianceAlert
from app.models.events import Event, EventType
from app.services.base_service import BaseService
from app.services.mcp_tools import MCPToolService

logger = logging.getLogger(__name__)


class ComplianceAgent(BaseService):
    """Read-only compliance agent that monitors safety violations.

    Listens to domain events and runs compliance checks via MCP tools.
    Produces ComplianceAlert nodes in Neo4j — never generates text via LLM.

    Attributes:
        mcp_tools: MCPToolService for invoking intent-based tools.
        agent_id: The registered agent identity ID.
        company_id: Tenant scope this agent operates within.
    """

    AGENT_SCOPES = (
        "read:compliance",
        "read:workers",
        "read:projects",
        "read:inspections",
    )

    AGENT_VERSION = "1.0.0"

    def __init__(
        self,
        driver: Driver,
        mcp_tools: MCPToolService,
        agent_id: str,
        company_id: str,
    ) -> None:
        """Initialise the Compliance Agent.

        Args:
            driver: Neo4j driver.
            mcp_tools: MCPToolService for tool invocation.
            agent_id: Registered agent identity ID.
            company_id: Tenant scope.
        """
        super().__init__(driver)
        self.mcp_tools = mcp_tools
        self.agent_id = agent_id
        self.company_id = company_id

    def _actor(self) -> Actor:
        """Build the Actor for this agent.

        This agent uses graph traversal only (no LLM calls), so model_id
        and cost_cents are not populated.

        Returns:
            An Actor instance representing this agent.
        """
        return Actor.agent(
            agent_id=self.agent_id,
            company_id=self.company_id,
            scopes=self.AGENT_SCOPES,
            agent_version=self.AGENT_VERSION,
        )

    # ------------------------------------------------------------------
    # Event handlers
    # ------------------------------------------------------------------

    def handle_event(self, event: Event) -> list[ComplianceAlert]:
        """Route an event to the appropriate handler.

        Args:
            event: The domain event to process.

        Returns:
            List of ComplianceAlerts produced (may be empty).
        """
        if event.company_id != self.company_id:
            return []

        handlers = {
            EventType.INSPECTION_COMPLETED: self._on_inspection_completed,
            EventType.WORKER_ASSIGNED: self._on_worker_assigned,
            EventType.CERTIFICATION_EXPIRING: self._on_certification_expiring,
            EventType.CORRECTIVE_ACTION_OVERDUE: self._on_corrective_action_overdue,
        }

        handler = handlers.get(event.event_type)
        if handler is None:
            return []

        try:
            return handler(event)
        except Exception:
            logger.exception(
                "ComplianceAgent error handling event %s (type=%s)",
                event.event_id,
                event.event_type.value,
            )
            return []

    def _on_inspection_completed(self, event: Event) -> list[ComplianceAlert]:
        """Handle inspection.completed — check project compliance.

        Args:
            event: The inspection.completed event.

        Returns:
            List of alerts for any compliance issues found.
        """
        project_id = event.project_id
        if not project_id:
            project_id = event.summary.get("project_id")
        if not project_id:
            return []

        result = self.mcp_tools.invoke_tool(
            tool_name="check_project_compliance",
            actor=self._actor(),
            company_id=self.company_id,
            parameters={"project_id": project_id},
        )

        if result.get("error"):
            logger.warning(
                "ComplianceAgent: check_project_compliance failed: %s",
                result["error"],
            )
            return []

        alerts: list[ComplianceAlert] = []

        if not result.get("compliant", True):
            alert = self._create_alert(
                alert_type=AlertType.PROJECT_NON_COMPLIANT,
                severity=AlertSeverity.HIGH,
                entity_id=project_id,
                entity_type="Project",
                project_id=project_id,
                message=f"Project non-compliant: {', '.join(result.get('issues', []))}",
                details={
                    "issues": result.get("issues", []),
                    "failed_inspections": result.get("failed_inspections", 0),
                    "expired_certifications": result.get("expired_certifications", 0),
                    "open_hazards": result.get("open_hazards", 0),
                    "open_incidents": result.get("open_incidents", 0),
                },
                graph_evidence={"check_result": result},
                event_id=event.event_id,
            )
            alerts.append(alert)

        return alerts

    def _on_worker_assigned(self, event: Event) -> list[ComplianceAlert]:
        """Handle worker.assigned_to_project — check worker compliance.

        Args:
            event: The worker.assigned_to_project event.

        Returns:
            List of alerts if the worker is non-compliant.
        """
        worker_id = event.entity_id
        project_id = event.project_id
        if not project_id:
            project_id = event.summary.get("project_id")
        if not project_id:
            return []

        result = self.mcp_tools.invoke_tool(
            tool_name="check_worker_compliance",
            actor=self._actor(),
            company_id=self.company_id,
            parameters={"project_id": project_id, "worker_id": worker_id},
        )

        if result.get("error"):
            logger.warning(
                "ComplianceAgent: check_worker_compliance failed: %s",
                result["error"],
            )
            return []

        alerts: list[ComplianceAlert] = []

        if not result.get("compliant", True):
            expired = result.get("expired_certifications", [])
            alert = self._create_alert(
                alert_type=AlertType.WORKER_NON_COMPLIANT,
                severity=AlertSeverity.HIGH,
                entity_id=worker_id,
                entity_type="Worker",
                project_id=project_id,
                message=(
                    f"Worker {result.get('worker_name', worker_id)} "
                    f"non-compliant for project {result.get('project_name', project_id)}: "
                    f"{len(expired)} expired certification(s)"
                ),
                details={
                    "worker_name": result.get("worker_name"),
                    "project_name": result.get("project_name"),
                    "expired_certifications": expired,
                    "valid_certifications": result.get("valid_certifications", []),
                },
                graph_evidence={"check_result": result},
                event_id=event.event_id,
            )
            alerts.append(alert)

        return alerts

    def _on_certification_expiring(self, event: Event) -> list[ComplianceAlert]:
        """Handle certification.expiring — flag expiring certs.

        Args:
            event: The certification.expiring event.

        Returns:
            List with a single alert for the expiring certification.
        """
        cert_id = event.entity_id
        worker_id = event.summary.get("worker_id", "")
        worker_name = event.summary.get("worker_name", "")
        expiry_date = event.summary.get("expiry_date", "")
        cert_type = event.summary.get("certification_type", "")

        alert = self._create_alert(
            alert_type=AlertType.CERTIFICATION_EXPIRING,
            severity=AlertSeverity.MEDIUM,
            entity_id=cert_id,
            entity_type="Certification",
            project_id=event.project_id,
            message=(
                f"Certification '{cert_type}' for {worker_name or worker_id} "
                f"expiring on {expiry_date}"
            ),
            details={
                "worker_id": worker_id,
                "worker_name": worker_name,
                "certification_type": cert_type,
                "expiry_date": expiry_date,
            },
            graph_evidence=event.graph_context,
            event_id=event.event_id,
        )
        return [alert]

    def _on_corrective_action_overdue(self, event: Event) -> list[ComplianceAlert]:
        """Handle corrective_action.overdue — flag overdue actions.

        Args:
            event: The corrective_action.overdue event.

        Returns:
            List with a single alert for the overdue corrective action.
        """
        alert = self._create_alert(
            alert_type=AlertType.CORRECTIVE_ACTION_OVERDUE,
            severity=AlertSeverity.HIGH,
            entity_id=event.entity_id,
            entity_type="CorrectiveAction",
            project_id=event.project_id,
            message=f"Corrective action overdue: {event.summary.get('description', event.entity_id)}",
            details=event.summary,
            graph_evidence=event.graph_context,
            event_id=event.event_id,
        )
        return [alert]

    # ------------------------------------------------------------------
    # On-demand check
    # ------------------------------------------------------------------

    def run_project_check(self, project_id: str) -> list[ComplianceAlert]:
        """Run an on-demand compliance check for a project.

        Args:
            project_id: The project to check.

        Returns:
            List of ComplianceAlerts for any issues found.
        """
        result = self.mcp_tools.invoke_tool(
            tool_name="check_project_compliance",
            actor=self._actor(),
            company_id=self.company_id,
            parameters={"project_id": project_id},
        )

        if result.get("error"):
            logger.warning(
                "ComplianceAgent: run_project_check failed: %s", result["error"]
            )
            return []

        alerts: list[ComplianceAlert] = []

        if not result.get("compliant", True):
            alert = self._create_alert(
                alert_type=AlertType.PROJECT_NON_COMPLIANT,
                severity=AlertSeverity.HIGH,
                entity_id=project_id,
                entity_type="Project",
                project_id=project_id,
                message=f"Project non-compliant: {', '.join(result.get('issues', []))}",
                details={
                    "issues": result.get("issues", []),
                    "failed_inspections": result.get("failed_inspections", 0),
                    "expired_certifications": result.get("expired_certifications", 0),
                    "open_hazards": result.get("open_hazards", 0),
                    "open_incidents": result.get("open_incidents", 0),
                },
                graph_evidence={"check_result": result},
            )
            alerts.append(alert)

        return alerts

    # ------------------------------------------------------------------
    # Alert persistence
    # ------------------------------------------------------------------

    def _create_alert(
        self,
        alert_type: AlertType,
        severity: AlertSeverity,
        entity_id: str,
        entity_type: str,
        message: str,
        project_id: str | None = None,
        details: dict[str, Any] | None = None,
        graph_evidence: dict[str, Any] | None = None,
        event_id: str | None = None,
    ) -> ComplianceAlert:
        """Create a ComplianceAlert and persist it to Neo4j.

        Args:
            alert_type: Type of compliance alert.
            severity: Severity level.
            entity_id: ID of the entity that triggered the alert.
            entity_type: Type of the triggering entity.
            message: Human-readable message.
            project_id: Project context.
            details: Structured details.
            graph_evidence: Supporting graph evidence.
            event_id: Triggering event ID.

        Returns:
            The persisted ComplianceAlert.
        """
        alert_id = f"alert_{secrets.token_hex(8)}"
        now = datetime.now(timezone.utc).isoformat()

        alert = ComplianceAlert(
            id=alert_id,
            alert_id=alert_id,
            alert_type=alert_type,
            severity=severity,
            entity_id=entity_id,
            entity_type=entity_type,
            company_id=self.company_id,
            project_id=project_id,
            message=message,
            details=details or {},
            graph_evidence=graph_evidence or {},
            event_id=event_id,
            agent_id=self.agent_id,
            created_at=now,
        )

        self._persist_alert(alert)
        return alert

    def _persist_alert(self, alert: ComplianceAlert) -> None:
        """Store a ComplianceAlert node in Neo4j with agent provenance.

        Args:
            alert: The alert to persist.
        """
        self._write_tx_single(
            """
            MATCH (c:Company {id: $company_id})
            CREATE (a:ComplianceAlert {
                id: $alert_id,
                alert_type: $alert_type,
                severity: $severity,
                entity_id: $entity_id,
                entity_type: $entity_type,
                company_id: $company_id,
                project_id: $project_id,
                message: $message,
                details_json: $details_json,
                graph_evidence_json: $graph_evidence_json,
                event_id: $event_id,
                agent_id: $agent_id,
                agent_version: $agent_version,
                actor_type: $actor_type,
                created_at: $created_at
            })
            CREATE (c)-[:HAS_COMPLIANCE_ALERT]->(a)
            RETURN a.id AS alert_id
            """,
            {
                "company_id": alert.company_id,
                "alert_id": alert.alert_id,
                "alert_type": alert.alert_type.value,
                "severity": alert.severity.value,
                "entity_id": alert.entity_id,
                "entity_type": alert.entity_type,
                "project_id": alert.project_id,
                "message": alert.message,
                "details_json": json.dumps(alert.details),
                "graph_evidence_json": json.dumps(
                    alert.graph_evidence, default=str
                ),
                "event_id": alert.event_id,
                "agent_id": alert.agent_id,
                "agent_version": self.AGENT_VERSION,
                "actor_type": "agent",
                "created_at": alert.created_at,
            },
        )
        logger.info(
            "ComplianceAlert persisted: id=%s type=%s severity=%s entity=%s",
            alert.alert_id,
            alert.alert_type.value,
            alert.severity.value,
            alert.entity_id,
        )
