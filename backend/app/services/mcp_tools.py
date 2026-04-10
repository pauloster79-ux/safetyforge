"""MCP tool implementations — intent-based tools wrapping domain services.

These are the 8 tools specified for Phase 5. Each tool:
1. Enforces agent scopes via GuardrailsService
2. Records provenance via the Actor model
3. Returns structured results (not raw DB records)

Tools are plain functions, not FastAPI endpoints. The MCP server (future)
will call these functions. For now they are testable units.
"""

import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from neo4j import Driver

from app.models.actor import Actor
from app.models.events import EventType
from app.models.guardrails import ActionClass, GuardrailCheckResult
from app.services.base_service import BaseService
from app.services.event_bus import EventBus
from app.services.guardrails_service import GuardrailsService

logger = logging.getLogger(__name__)


class MCPToolService(BaseService):
    """Intent-based MCP tool implementations.

    Each tool wraps one or more graph traversals to produce
    a structured result. Tools are the agent-facing API — they
    express intent, not CRUD operations.

    Attributes:
        guardrails: GuardrailsService for pre-execution checks.
        event_bus: EventBus for emitting events on mutations.
    """

    def __init__(
        self,
        driver: Driver,
        guardrails: GuardrailsService,
        event_bus: EventBus,
    ) -> None:
        """Initialise the MCP tool service.

        Args:
            driver: Neo4j driver.
            guardrails: GuardrailsService for scope/rate/budget checks.
            event_bus: EventBus for emitting domain events.
        """
        super().__init__(driver)
        self.guardrails = guardrails
        self.event_bus = event_bus

    # ------------------------------------------------------------------
    # Tool 1: check_worker_compliance
    # ------------------------------------------------------------------

    def check_worker_compliance(
        self, actor: Actor, company_id: str, project_id: str, worker_id: str
    ) -> dict[str, Any]:
        """Check if a worker meets all requirements for a project.

        Traverses the graph to find:
        - Worker's current certifications
        - Project's jurisdiction requirements (if encoded)
        - Certification gaps

        Args:
            actor: The agent actor.
            company_id: Tenant scope.
            project_id: The project to check against.
            worker_id: The worker to check.

        Returns:
            Dict with compliance status, held certs, and gaps.
        """
        result = self._read_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
            MATCH (c)-[:HAS_WORKER]->(w:Worker {id: $worker_id})
            WHERE w.deleted = false AND p.deleted = false

            OPTIONAL MATCH (w)-[:HOLDS_CERT]->(cert:Certification)

            WITH w, p, collect(CASE WHEN cert IS NOT NULL THEN {
                id: cert.id,
                certification_type: cert.certification_type,
                expiry_date: cert.expiry_date,
                status: cert.status
            } ELSE null END) AS certs

            RETURN w.id AS worker_id,
                   w.first_name AS first_name,
                   w.last_name AS last_name,
                   w.role AS role,
                   p.id AS project_id,
                   p.name AS project_name,
                   certs
            """,
            {
                "company_id": company_id,
                "project_id": project_id,
                "worker_id": worker_id,
            },
        )

        if result is None:
            return {
                "compliant": False,
                "error": f"Worker {worker_id} or project {project_id} not found",
            }

        certs = [c for c in result["certs"] if c is not None]
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        expired = [
            c for c in certs
            if c.get("expiry_date") and c["expiry_date"] < today
        ]
        valid = [
            c for c in certs
            if not c.get("expiry_date") or c["expiry_date"] >= today
        ]

        return {
            "compliant": len(expired) == 0 and len(valid) > 0,
            "worker_id": result["worker_id"],
            "worker_name": f"{result['first_name']} {result['last_name']}",
            "role": result["role"],
            "project_id": result["project_id"],
            "project_name": result["project_name"],
            "valid_certifications": valid,
            "expired_certifications": expired,
            "total_certs": len(certs),
            "checked_at": datetime.now(timezone.utc).isoformat(),
        }

    # ------------------------------------------------------------------
    # Tool 2: check_project_compliance
    # ------------------------------------------------------------------

    def check_project_compliance(
        self, actor: Actor, company_id: str, project_id: str
    ) -> dict[str, Any]:
        """Full compliance status for a project.

        Checks workers, equipment, inspections, and hazards.

        Args:
            actor: The agent actor.
            company_id: Tenant scope.
            project_id: The project to check.

        Returns:
            Dict with project compliance overview.
        """
        result = self._read_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
            WHERE p.deleted = false

            CALL {
                WITH c, p
                OPTIONAL MATCH (c)-[:HAS_WORKER]->(w:Worker)-[:ASSIGNED_TO]->(p)
                WHERE w.deleted = false
                OPTIONAL MATCH (w)-[:HOLDS_CERT]->(cert:Certification)
                WHERE cert.expiry_date IS NOT NULL AND cert.expiry_date < $today
                WITH count(DISTINCT w) AS worker_count,
                     count(DISTINCT cert) AS expired_cert_count
                RETURN worker_count, expired_cert_count
            }

            CALL {
                WITH p
                OPTIONAL MATCH (p)-[:HAS_INSPECTION]->(i:Inspection)
                WHERE i.deleted = false
                WITH count(i) AS total_inspections,
                     sum(CASE WHEN i.overall_status = 'fail' THEN 1 ELSE 0 END) AS failed_inspections,
                     max(i.created_at) AS last_inspection_date
                RETURN total_inspections, failed_inspections, last_inspection_date
            }

            CALL {
                WITH p
                OPTIONAL MATCH (p)-[:HAS_HAZARD_REPORT]->(h:HazardReport)
                WHERE h.deleted = false AND h.status IN ['open', 'in_progress']
                RETURN count(h) AS open_hazards
            }

            CALL {
                WITH p
                OPTIONAL MATCH (p)-[:HAS_INCIDENT]->(inc:Incident)
                WITH count(inc) AS total_incidents,
                     sum(CASE WHEN inc.status = 'open' THEN 1 ELSE 0 END) AS open_incidents
                RETURN total_incidents, open_incidents
            }

            RETURN p.id AS project_id, p.name AS project_name, p.status AS status,
                   worker_count, expired_cert_count,
                   total_inspections, failed_inspections, last_inspection_date,
                   open_hazards,
                   total_incidents, open_incidents
            """,
            {
                "company_id": company_id,
                "project_id": project_id,
                "today": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            },
        )

        if result is None:
            return {"error": f"Project {project_id} not found"}

        issues: list[str] = []
        if result["expired_cert_count"] > 0:
            issues.append(f"{result['expired_cert_count']} expired certifications")
        if result["open_hazards"] > 0:
            issues.append(f"{result['open_hazards']} open hazard reports")
        if result["open_incidents"] > 0:
            issues.append(f"{result['open_incidents']} open incidents")
        if result["failed_inspections"] > 0:
            issues.append(f"{result['failed_inspections']} failed inspections")

        return {
            "project_id": result["project_id"],
            "project_name": result["project_name"],
            "status": result["status"],
            "compliant": len(issues) == 0,
            "issues": issues,
            "workers_assigned": result["worker_count"],
            "expired_certifications": result["expired_cert_count"],
            "total_inspections": result["total_inspections"],
            "failed_inspections": result["failed_inspections"],
            "last_inspection_date": result["last_inspection_date"],
            "open_hazards": result["open_hazards"],
            "total_incidents": result["total_incidents"],
            "open_incidents": result["open_incidents"],
            "checked_at": datetime.now(timezone.utc).isoformat(),
        }

    # ------------------------------------------------------------------
    # Tool 3: get_project_summary
    # ------------------------------------------------------------------

    def get_project_summary(
        self, actor: Actor, company_id: str, project_id: str
    ) -> dict[str, Any]:
        """Get a project overview — workers, equipment, recent activity.

        Args:
            actor: The agent actor.
            company_id: Tenant scope.
            project_id: The project to summarise.

        Returns:
            Dict with project summary data.
        """
        result = self._read_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
            WHERE p.deleted = false

            CALL {
                WITH c, p
                OPTIONAL MATCH (c)-[:HAS_WORKER]->(w:Worker)-[:ASSIGNED_TO]->(p)
                WHERE w.deleted = false
                WITH collect({id: w.id, name: w.first_name + ' ' + w.last_name, role: w.role}) AS workers
                RETURN workers, size(workers) AS worker_count
            }

            CALL {
                WITH p
                OPTIONAL MATCH (p)-[:HAS_EQUIPMENT]->(e:Equipment)
                WHERE e.deleted = false
                RETURN count(e) AS equipment_count
            }

            CALL {
                WITH p
                OPTIONAL MATCH (p)-[:HAS_INSPECTION]->(i:Inspection)
                WHERE i.deleted = false AND i.created_at >= $recent_cutoff
                RETURN count(i) AS recent_inspections
            }

            CALL {
                WITH p
                OPTIONAL MATCH (p)-[:HAS_INCIDENT]->(inc:Incident)
                WHERE inc.created_at >= $recent_cutoff
                RETURN count(inc) AS recent_incidents
            }

            RETURN p.id AS project_id, p.name AS project_name,
                   p.address AS address, p.status AS status,
                   workers, worker_count, equipment_count,
                   recent_inspections, recent_incidents
            """,
            {
                "company_id": company_id,
                "project_id": project_id,
                "recent_cutoff": (
                    datetime.now(timezone.utc) - timedelta(days=7)
                ).isoformat(),
            },
        )

        if result is None:
            return {"error": f"Project {project_id} not found"}

        return {
            "project_id": result["project_id"],
            "project_name": result["project_name"],
            "address": result["address"],
            "status": result["status"],
            "workers": result["workers"],
            "worker_count": result["worker_count"],
            "equipment_count": result["equipment_count"],
            "recent_inspections_7d": result["recent_inspections"],
            "recent_incidents_7d": result["recent_incidents"],
            "assembled_at": datetime.now(timezone.utc).isoformat(),
        }

    # ------------------------------------------------------------------
    # Tool 4: get_worker_profile
    # ------------------------------------------------------------------

    def get_worker_profile(
        self, actor: Actor, company_id: str, worker_id: str
    ) -> dict[str, Any]:
        """Get a worker's profile — certs, assignments, incidents.

        Args:
            actor: The agent actor.
            company_id: Tenant scope.
            worker_id: The worker to profile.

        Returns:
            Dict with worker profile data.
        """
        result = self._read_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:HAS_WORKER]->(w:Worker {id: $worker_id})
            WHERE w.deleted = false

            OPTIONAL MATCH (w)-[:HOLDS_CERT]->(cert:Certification)
            WITH w, c, collect(CASE WHEN cert IS NOT NULL THEN {
                id: cert.id,
                certification_type: cert.certification_type,
                expiry_date: cert.expiry_date,
                issue_date: cert.issue_date,
                status: cert.status
            } ELSE null END) AS certs

            OPTIONAL MATCH (w)-[:ASSIGNED_TO]->(p:Project)
            WHERE p.deleted = false
            WITH w, c, certs, collect({id: p.id, name: p.name, status: p.status}) AS projects

            RETURN w.id AS worker_id,
                   w.first_name AS first_name,
                   w.last_name AS last_name,
                   w.email AS email,
                   w.phone AS phone,
                   w.role AS role,
                   w.trade AS trade,
                   w.status AS status,
                   w.created_at AS created_at,
                   certs, projects
            """,
            {"company_id": company_id, "worker_id": worker_id},
        )

        if result is None:
            return {"error": f"Worker {worker_id} not found"}

        certs = [c for c in result["certs"] if c is not None]

        return {
            "worker_id": result["worker_id"],
            "name": f"{result['first_name']} {result['last_name']}",
            "email": result.get("email"),
            "phone": result.get("phone"),
            "role": result["role"],
            "trade": result.get("trade"),
            "status": result["status"],
            "certifications": certs,
            "active_projects": result["projects"],
            "created_at": result["created_at"],
        }

    # ------------------------------------------------------------------
    # Tool 5: generate_morning_brief (wraps MorningBriefService)
    # ------------------------------------------------------------------

    def generate_morning_brief(
        self, actor: Actor, company_id: str, project_id: str
    ) -> dict[str, Any]:
        """Generate a morning safety brief for a project.

        Assembles data directly from the graph rather than delegating
        to MorningBriefService (avoids circular dependency).

        Args:
            actor: The agent actor.
            company_id: Tenant scope.
            project_id: The project to brief on.

        Returns:
            Dict with morning brief data.
        """
        result = self._read_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
            WHERE p.deleted = false

            CALL {
                WITH c
                OPTIONAL MATCH (c)-[:HAS_WORKER]->(w:Worker)-[:HOLDS_CERT]->(cert:Certification)
                WHERE w.deleted = false AND cert.expiry_date IS NOT NULL
                WITH sum(CASE WHEN cert.expiry_date < $today THEN 1 ELSE 0 END) AS expired,
                     sum(CASE WHEN cert.expiry_date >= $today
                               AND cert.expiry_date <= $expiry_window THEN 1 ELSE 0 END) AS expiring
                RETURN expired, expiring
            }

            CALL {
                WITH p
                OPTIONAL MATCH (p)-[:HAS_INSPECTION]->(i:Inspection)
                WHERE i.deleted = false AND i.created_at >= $recent_cutoff
                RETURN count(i) > 0 AS has_recent_inspection
            }

            CALL {
                WITH p
                OPTIONAL MATCH (p)-[:HAS_HAZARD_REPORT]->(h:HazardReport)
                WHERE h.deleted = false AND h.status IN ['open', 'in_progress']
                RETURN count(h) AS open_hazards
            }

            CALL {
                WITH p
                OPTIONAL MATCH (p)-[:HAS_INCIDENT]->(inc:Incident)
                WHERE inc.created_at >= $recent_cutoff
                RETURN count(inc) AS recent_incidents
            }

            RETURN p.id AS project_id, p.name AS project_name,
                   expired, expiring,
                   has_recent_inspection, open_hazards, recent_incidents
            """,
            {
                "company_id": company_id,
                "project_id": project_id,
                "today": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                "expiry_window": (
                    datetime.now(timezone.utc) + timedelta(days=14)
                ).strftime("%Y-%m-%d"),
                "recent_cutoff": (
                    datetime.now(timezone.utc) - timedelta(days=2)
                ).isoformat(),
            },
        )

        if result is None:
            return {"error": f"Project {project_id} not found"}

        alerts: list[dict[str, str]] = []
        if result["expired"] > 0:
            alerts.append({
                "type": "certification_expired",
                "message": f"{result['expired']} expired certifications",
                "severity": "high",
            })
        if result["expiring"] > 0:
            alerts.append({
                "type": "certification_expiring",
                "message": f"{result['expiring']} certifications expiring within 14 days",
                "severity": "medium",
            })
        if not result["has_recent_inspection"]:
            alerts.append({
                "type": "inspection_overdue",
                "message": "No inspection in the last 48 hours",
                "severity": "medium",
            })
        if result["open_hazards"] > 0:
            alerts.append({
                "type": "open_hazards",
                "message": f"{result['open_hazards']} unresolved hazard reports",
                "severity": "high",
            })
        if result["recent_incidents"] > 0:
            alerts.append({
                "type": "recent_incidents",
                "message": f"{result['recent_incidents']} incidents in the last 48 hours",
                "severity": "high",
            })

        return {
            "project_id": result["project_id"],
            "project_name": result["project_name"],
            "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "alerts": alerts,
            "alert_count": len(alerts),
            "expired_certifications": result["expired"],
            "expiring_certifications": result["expiring"],
            "has_recent_inspection": result["has_recent_inspection"],
            "open_hazards": result["open_hazards"],
            "recent_incidents": result["recent_incidents"],
        }

    # ------------------------------------------------------------------
    # Tool 6: report_hazard (low-risk write)
    # ------------------------------------------------------------------

    def report_hazard(
        self,
        actor: Actor,
        company_id: str,
        project_id: str,
        description: str,
        location: str = "",
        severity: str = "medium",
    ) -> dict[str, Any]:
        """Create a hazard report from structured data.

        Low-risk write — creates a HazardReport node and emits an event.

        Args:
            actor: The agent actor.
            company_id: Tenant scope.
            project_id: The project the hazard is on.
            description: Description of the hazard.
            location: Location of the hazard on site.
            severity: Severity level (low/medium/high/critical).

        Returns:
            Dict with the created hazard report data.
        """
        hazard_id = self._generate_id("haz")
        provenance = self._provenance_create(actor)

        result = self._write_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
            WHERE p.deleted = false
            CREATE (h:HazardReport {
                id: $hazard_id,
                description: $description,
                location: $location,
                severity: $severity,
                status: 'open',
                deleted: false,
                _hazards_json: '[]',
                created_by: $created_by,
                actor_type: $actor_type,
                agent_id: $agent_id,
                model_id: $model_id,
                confidence: $confidence,
                created_at: $created_at,
                updated_by: $updated_by,
                updated_actor_type: $updated_actor_type,
                updated_at: $updated_at
            })
            CREATE (p)-[:HAS_HAZARD_REPORT]->(h)
            RETURN h.id AS hazard_id, p.id AS project_id, p.name AS project_name
            """,
            {
                "company_id": company_id,
                "project_id": project_id,
                "hazard_id": hazard_id,
                "description": description,
                "location": location,
                "severity": severity,
                **provenance,
            },
        )

        if result is None:
            return {"error": f"Project {project_id} not found"}

        # Emit event
        event = self.event_bus.create_event(
            event_type=EventType.HAZARD_REPORTED,
            entity_id=hazard_id,
            entity_type="HazardReport",
            company_id=company_id,
            project_id=project_id,
            actor=actor,
            summary={"description": description, "severity": severity, "location": location},
        )
        self.event_bus.emit(event)

        return {
            "hazard_id": hazard_id,
            "project_id": result["project_id"],
            "project_name": result["project_name"],
            "description": description,
            "severity": severity,
            "status": "open",
            "created_by": actor.id,
            "actor_type": actor.type,
        }

    # ------------------------------------------------------------------
    # Tool 7: report_incident (low-risk write)
    # ------------------------------------------------------------------

    def report_incident(
        self,
        actor: Actor,
        company_id: str,
        project_id: str,
        title: str,
        description: str,
        severity: str = "minor",
        incident_type: str = "near_miss",
    ) -> dict[str, Any]:
        """Create an incident report.

        Low-risk write — creates an Incident node and emits an event.

        Args:
            actor: The agent actor.
            company_id: Tenant scope.
            project_id: The project where the incident occurred.
            title: Short incident title.
            description: Full description.
            severity: Severity level.
            incident_type: Type of incident.

        Returns:
            Dict with the created incident data.
        """
        incident_id = self._generate_id("inc")
        provenance = self._provenance_create(actor)

        result = self._write_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
            WHERE p.deleted = false
            CREATE (inc:Incident {
                id: $incident_id,
                title: $title,
                description: $description,
                severity: $severity,
                incident_type: $incident_type,
                status: 'open',
                incident_date: $today,
                _photo_urls_json: '[]',
                _involved_worker_ids_json: '[]',
                osha_recordable: false,
                osha_reportable: false,
                created_by: $created_by,
                actor_type: $actor_type,
                agent_id: $agent_id,
                model_id: $model_id,
                confidence: $confidence,
                created_at: $created_at,
                updated_by: $updated_by,
                updated_actor_type: $updated_actor_type,
                updated_at: $updated_at
            })
            CREATE (p)-[:HAS_INCIDENT]->(inc)
            RETURN inc.id AS incident_id, p.id AS project_id, p.name AS project_name
            """,
            {
                "company_id": company_id,
                "project_id": project_id,
                "incident_id": incident_id,
                "title": title,
                "description": description,
                "severity": severity,
                "incident_type": incident_type,
                "today": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                **provenance,
            },
        )

        if result is None:
            return {"error": f"Project {project_id} not found"}

        # Emit event
        event = self.event_bus.create_event(
            event_type=EventType.INCIDENT_REPORTED,
            entity_id=incident_id,
            entity_type="Incident",
            company_id=company_id,
            project_id=project_id,
            actor=actor,
            summary={
                "title": title,
                "severity": severity,
                "incident_type": incident_type,
            },
        )
        self.event_bus.emit(event)

        return {
            "incident_id": incident_id,
            "project_id": result["project_id"],
            "project_name": result["project_name"],
            "title": title,
            "severity": severity,
            "status": "open",
            "created_by": actor.id,
            "actor_type": actor.type,
        }

    # ------------------------------------------------------------------
    # Tool 8: get_changes_since (delta query)
    # ------------------------------------------------------------------

    def get_changes_since(
        self,
        actor: Actor,
        company_id: str,
        project_id: str,
        since: str,
    ) -> dict[str, Any]:
        """Delta query — what changed on a project since a timestamp.

        Args:
            actor: The agent actor.
            company_id: Tenant scope.
            project_id: The project to query.
            since: ISO 8601 timestamp to query changes from.

        Returns:
            Dict with categorised changes since the given timestamp.
        """
        result = self._read_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
            WHERE p.deleted = false

            CALL {
                WITH p
                OPTIONAL MATCH (p)-[:HAS_INSPECTION]->(i:Inspection)
                WHERE i.created_at >= $since
                RETURN collect({
                    id: i.id, type: i.inspection_type,
                    status: i.overall_status, created_at: i.created_at
                }) AS new_inspections
            }

            CALL {
                WITH p
                OPTIONAL MATCH (p)-[:HAS_INCIDENT]->(inc:Incident)
                WHERE inc.created_at >= $since
                RETURN collect({
                    id: inc.id, title: inc.title,
                    severity: inc.severity, created_at: inc.created_at
                }) AS new_incidents
            }

            CALL {
                WITH p
                OPTIONAL MATCH (p)-[:HAS_HAZARD_REPORT]->(h:HazardReport)
                WHERE h.created_at >= $since
                RETURN collect({
                    id: h.id, severity: h.severity,
                    status: h.status, created_at: h.created_at
                }) AS new_hazards
            }

            RETURN p.id AS project_id, p.name AS project_name,
                   new_inspections, new_incidents, new_hazards
            """,
            {
                "company_id": company_id,
                "project_id": project_id,
                "since": since,
            },
        )

        if result is None:
            return {"error": f"Project {project_id} not found"}

        inspections = [i for i in result["new_inspections"] if i.get("id")]
        incidents = [i for i in result["new_incidents"] if i.get("id")]
        hazards = [h for h in result["new_hazards"] if h.get("id")]

        return {
            "project_id": result["project_id"],
            "project_name": result["project_name"],
            "since": since,
            "until": datetime.now(timezone.utc).isoformat(),
            "changes": {
                "inspections": inspections,
                "incidents": incidents,
                "hazard_reports": hazards,
            },
            "total_changes": len(inspections) + len(incidents) + len(hazards),
        }

    # ------------------------------------------------------------------
    # Unified tool dispatch (for MCP server integration)
    # ------------------------------------------------------------------

    def invoke_tool(
        self,
        tool_name: str,
        actor: Actor,
        company_id: str,
        parameters: dict[str, Any],
    ) -> dict[str, Any]:
        """Invoke a tool by name with guardrail checks.

        This is the main entry point for the MCP server. It:
        1. Runs pre-execution guardrail checks
        2. Dispatches to the correct tool implementation
        3. Returns the result or error

        Args:
            tool_name: The MCP tool name.
            actor: The agent actor.
            company_id: Tenant scope.
            parameters: Tool-specific parameters.

        Returns:
            The tool result dict, or an error dict.
        """
        # Pre-execution check
        check = self.guardrails.pre_execution_check(
            agent_id=actor.id,
            company_id=company_id,
            tool_name=tool_name,
            parameters=parameters,
        )

        if not check.allowed:
            return {
                "error": check.reason,
                "action_class": check.action_class.value,
                "approval_request_id": check.approval_request_id,
            }

        # Dispatch to tool implementation
        dispatch: dict[str, Any] = {
            "check_worker_compliance": lambda: self.check_worker_compliance(
                actor, company_id,
                parameters["project_id"], parameters["worker_id"],
            ),
            "check_project_compliance": lambda: self.check_project_compliance(
                actor, company_id, parameters["project_id"],
            ),
            "get_project_summary": lambda: self.get_project_summary(
                actor, company_id, parameters["project_id"],
            ),
            "get_worker_profile": lambda: self.get_worker_profile(
                actor, company_id, parameters["worker_id"],
            ),
            "generate_morning_brief": lambda: self.generate_morning_brief(
                actor, company_id, parameters["project_id"],
            ),
            "report_hazard": lambda: self.report_hazard(
                actor, company_id, parameters["project_id"],
                parameters["description"],
                parameters.get("location", ""),
                parameters.get("severity", "medium"),
            ),
            "report_incident": lambda: self.report_incident(
                actor, company_id, parameters["project_id"],
                parameters["title"], parameters["description"],
                parameters.get("severity", "minor"),
                parameters.get("incident_type", "near_miss"),
            ),
            "get_changes_since": lambda: self.get_changes_since(
                actor, company_id, parameters["project_id"],
                parameters["since"],
            ),
        }

        handler = dispatch.get(tool_name)
        if handler is None:
            return {"error": f"Unknown tool: {tool_name}"}

        return handler()
