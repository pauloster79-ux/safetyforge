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


_HOURS_IN_TIME_UNIT = {
    "per_hour": 1.0,
    "per_day": 8.0,
    "per_week": 40.0,
}


def _hours_per_unit(rate: float | None, time_unit: str | None) -> float | None:
    """Convert a productivity rate into hours per unit of output.

    Example: 80 LF/day → 8 hours / 80 LF = 0.1 hours per LF.
    The agent multiplies by quantity to get total labour hours.

    Returns None if rate or time_unit is missing or unrecognised.
    """
    if rate is None or time_unit is None or rate <= 0:
        return None
    hours = _HOURS_IN_TIME_UNIT.get(time_unit)
    if hours is None:
        return None
    return hours / rate


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
            MATCH (c)-[:EMPLOYS]->(w:Worker {id: $worker_id})
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
                OPTIONAL MATCH (c)-[:EMPLOYS]->(w:Worker)-[:ASSIGNED_TO_PROJECT]->(p)
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

        # Fetch cert expiry details (expired + expiring within 90 days)
        cert_details = self._read_tx(
            """
            MATCH (c:Company {id: $company_id})-[:EMPLOYS]->(w:Worker)-[:ASSIGNED_TO_PROJECT]->(p:Project {id: $project_id})
            WHERE w.deleted = false
            MATCH (w)-[:HOLDS_CERT]->(cert:Certification)
            WHERE cert.expiry_date IS NOT NULL
              AND cert.expiry_date < date($cutoff_date)
            RETURN w.id AS worker_id,
                   w.first_name + ' ' + w.last_name AS worker_name,
                   cert.name AS certification,
                   cert.expiry_date AS expiry_date,
                   CASE WHEN cert.expiry_date < date($today) THEN 'expired'
                        ELSE 'expiring_soon' END AS status
            ORDER BY cert.expiry_date ASC
            """,
            {
                "company_id": company_id,
                "project_id": project_id,
                "today": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                "cutoff_date": (datetime.now(timezone.utc) + timedelta(days=90)).strftime("%Y-%m-%d"),
            },
        )
        cert_expiry_list = []
        for row in cert_details:
            exp_date = row["expiry_date"]
            cert_expiry_list.append({
                "worker_id": row["worker_id"],
                "worker_name": row["worker_name"],
                "certification": row["certification"],
                "expiry_date": exp_date.isoformat() if hasattr(exp_date, "isoformat") else str(exp_date),
                "status": row["status"],
            })

        issues: list[str] = []
        if result["expired_cert_count"] > 0:
            issues.append(f"{result['expired_cert_count']} expired certifications")
        if cert_expiry_list:
            expiring_soon = [c for c in cert_expiry_list if c["status"] == "expiring_soon"]
            if expiring_soon:
                issues.append(f"{len(expiring_soon)} certifications expiring within 90 days")
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
            "certification_expiry_details": cert_expiry_list,
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
                OPTIONAL MATCH (c)-[:EMPLOYS]->(w:Worker)-[:ASSIGNED_TO_PROJECT]->(p)
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
            MATCH (c:Company {id: $company_id})-[:EMPLOYS]->(w:Worker {id: $worker_id})
            WHERE w.deleted = false

            OPTIONAL MATCH (w)-[:HOLDS_CERT]->(cert:Certification)
            WITH w, c, collect(CASE WHEN cert IS NOT NULL THEN {
                id: cert.id,
                certification_type: cert.certification_type,
                expiry_date: cert.expiry_date,
                issue_date: cert.issue_date,
                status: cert.status
            } ELSE null END) AS certs

            OPTIONAL MATCH (w)-[:ASSIGNED_TO_PROJECT]->(p:Project)
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
                OPTIONAL MATCH (c)-[:EMPLOYS]->(w:Worker)-[:HOLDS_CERT]->(cert:Certification)
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
                hazard_count: 0,
                created_by: $created_by,
                actor_type: $actor_type,
                agent_id: $agent_id,
                agent_version: $agent_version,
                model_id: $model_id,
                confidence: $confidence,
                agent_cost_cents: $agent_cost_cents,
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
                agent_version: $agent_version,
                model_id: $model_id,
                confidence: $confidence,
                agent_cost_cents: $agent_cost_cents,
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
    # Tool 8: get_daily_log_status
    # ------------------------------------------------------------------

    def get_daily_log_status(
        self, actor: Actor, company_id: str, project_id: str
    ) -> dict[str, Any]:
        """Get daily log status for a project — which dates have/haven't submitted.

        Queries the most recent 7 daily logs for the project, checks whether
        today has a submitted or approved log, and identifies missing dates
        in the last 7 calendar days.

        Args:
            actor: The agent actor.
            company_id: Tenant scope.
            project_id: The project to check.

        Returns:
            Dict with today's log status, recent logs, and missing dates.
        """
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        week_ago = (datetime.now(timezone.utc) - timedelta(days=7)).strftime("%Y-%m-%d")

        result = self._read_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
            WHERE p.deleted = false

            CALL {
                WITH p
                OPTIONAL MATCH (p)-[:HAS_DAILY_LOG]->(dl:DailyLog)
                WHERE dl.deleted = false
                WITH dl ORDER BY dl.log_date DESC LIMIT 7
                RETURN collect({
                    id: dl.id,
                    log_date: dl.log_date,
                    status: dl.status,
                    created_by: dl.created_by,
                    created_at: dl.created_at
                }) AS recent_logs
            }

            CALL {
                WITH p
                OPTIONAL MATCH (p)-[:HAS_DAILY_LOG]->(dl:DailyLog)
                WHERE dl.deleted = false AND dl.log_date = $today
                      AND dl.status IN ['submitted', 'approved']
                RETURN count(dl) > 0 AS today_submitted
            }

            RETURN p.id AS project_id, p.name AS project_name,
                   recent_logs, today_submitted
            """,
            {
                "company_id": company_id,
                "project_id": project_id,
                "today": today,
            },
        )

        if result is None:
            return {"error": f"Project {project_id} not found"}

        recent_logs = [r for r in result["recent_logs"] if r.get("id")]
        logged_dates = {r["log_date"] for r in recent_logs if r.get("log_date")}

        # Calculate missing dates in the last 7 calendar days
        missing_dates: list[str] = []
        for i in range(7):
            d = (datetime.now(timezone.utc) - timedelta(days=i)).strftime("%Y-%m-%d")
            if d not in logged_dates:
                missing_dates.append(d)

        return {
            "project_id": result["project_id"],
            "project_name": result["project_name"],
            "today": today,
            "today_submitted": result["today_submitted"],
            "recent_logs": recent_logs,
            "missing_dates": missing_dates,
            "missing_count": len(missing_dates),
            "checked_at": datetime.now(timezone.utc).isoformat(),
        }

    # ------------------------------------------------------------------
    # Tool 9: get_changes_since (delta query)
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
                    id: i.id, type: i.category,
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
    # Tool 10: capture_lead (low-risk write)
    # ------------------------------------------------------------------

    def capture_lead(
        self,
        actor: Actor,
        company_id: str,
        name: str,
        description: str = "",
        project_type: str = "",
        address: str = "",
        client_name: str = "",
        client_email: str = "",
        client_phone: str = "",
        contract_type: str | None = None,
    ) -> dict[str, Any]:
        """Create a new lead (Project with state='lead').

        Optionally creates a Contact node for the client and links via CLIENT_IS.

        Args:
            actor: The agent actor.
            company_id: Tenant scope.
            name: Lead/project name.
            description: Description of the potential work.
            project_type: Type of project (residential, commercial, etc.).
            address: Project address. If blank/short, "Address TBC" is used.
            client_name: Client contact name.
            client_email: Client email address.
            client_phone: Client phone number.
            contract_type: Optional contract type — one of
                'lump_sum', 'schedule_of_rates', 'cost_plus',
                'time_and_materials'. Set this when the user has specified
                the billing basis (e.g. "T&M", "cost plus", "fixed price").

        Returns:
            Dict with the created lead data.
        """
        from app.services.lead_service import LeadService

        lead_svc = LeadService(self.driver)
        result = lead_svc.capture_lead(
            company_id=company_id,
            data={
                "name": name,
                "description": description,
                "project_type": project_type,
                "address": address,
                "client_name": client_name,
                "client_email": client_email,
                "client_phone": client_phone,
                "contract_type": contract_type,
            },
            actor=actor,
        )

        # Emit event
        event = self.event_bus.create_event(
            event_type=EventType.WORKER_ASSIGNED,  # closest coarse type
            entity_id=result["project_id"],
            entity_type="Project",
            company_id=company_id,
            actor=actor,
            summary={"name": name, "state": "lead", "client": client_name},
        )
        self.event_bus.emit(event)

        return result

    # ------------------------------------------------------------------
    # Tool 11: qualify_project (read-only)
    # ------------------------------------------------------------------

    def qualify_project(
        self,
        actor: Actor,
        company_id: str,
        project_id: str,
    ) -> dict[str, Any]:
        """Check if the company can take on a project.

        Checks worker certs, scheduling capacity, and GC payment history.

        Args:
            actor: The agent actor.
            company_id: Tenant scope.
            project_id: The project/lead to qualify.

        Returns:
            Dict with qualification assessment.
        """
        from app.services.lead_service import LeadService

        lead_svc = LeadService(self.driver)
        return lead_svc.qualify_project(company_id, project_id)

    # ------------------------------------------------------------------
    # Tool 12: check_capacity (read-only)
    # ------------------------------------------------------------------

    def check_capacity(
        self,
        actor: Actor,
        company_id: str,
    ) -> dict[str, Any]:
        """Assess whether the company can take on new work.

        Looks at active projects, worker utilisation, and upcoming schedule.

        Args:
            actor: The agent actor.
            company_id: Tenant scope.

        Returns:
            Dict with capacity assessment.
        """
        from app.services.lead_service import LeadService

        lead_svc = LeadService(self.driver)
        return lead_svc.check_capacity(company_id)

    # ------------------------------------------------------------------
    # Tool 13: get_schedule (read-only)
    # ------------------------------------------------------------------

    def get_schedule(
        self,
        actor: Actor,
        company_id: str,
        project_id: str,
        weeks_ahead: int = 4,
    ) -> dict[str, Any]:
        """Get rolling schedule view for a project, grouped by week.

        Returns work items with planned dates and assigned workers/crews.

        Args:
            actor: The agent actor.
            company_id: Tenant scope.
            project_id: The project to schedule.
            weeks_ahead: Number of weeks to look ahead.

        Returns:
            Dict with schedule data grouped by week.
        """
        from app.services.scheduling_service import SchedulingService

        sched_svc = SchedulingService(self.driver)
        return sched_svc.get_schedule(company_id, project_id, weeks_ahead)

    # ------------------------------------------------------------------
    # Tool 14: assign_workers (low-risk write)
    # ------------------------------------------------------------------

    def assign_workers(
        self,
        actor: Actor,
        company_id: str,
        project_id: str,
        work_item_id: str,
        worker_ids: list[str] | None = None,
        crew_id: str | None = None,
    ) -> dict[str, Any]:
        """Assign workers or a crew to a work item.

        Creates ASSIGNED_TO_WORKER / ASSIGNED_TO_CREW relationships.

        Args:
            actor: The agent actor.
            company_id: Tenant scope.
            project_id: The parent project ID.
            work_item_id: The work item to assign to.
            worker_ids: List of worker IDs to assign.
            crew_id: Crew ID to assign instead.

        Returns:
            Dict with assignment confirmation.
        """
        from app.services.scheduling_service import SchedulingService

        sched_svc = SchedulingService(self.driver)
        return sched_svc.assign_workers(
            company_id, project_id, work_item_id,
            worker_ids=worker_ids, crew_id=crew_id, actor=actor,
        )

    # ------------------------------------------------------------------
    # Tool 15: detect_conflicts (read-only)
    # ------------------------------------------------------------------

    def detect_conflicts(
        self,
        actor: Actor,
        company_id: str,
        project_id: str,
    ) -> dict[str, Any]:
        """Detect scheduling conflicts for a project.

        Checks cert expiry before planned_end, double-booking, and
        equipment maintenance overlaps.

        Args:
            actor: The agent actor.
            company_id: Tenant scope.
            project_id: The project to check.

        Returns:
            Dict with detected conflicts.
        """
        from app.services.scheduling_service import SchedulingService

        sched_svc = SchedulingService(self.driver)
        return sched_svc.detect_conflicts(company_id, project_id)

    # ------------------------------------------------------------------
    # Tool 16: check_sub_compliance (read-only)
    # ------------------------------------------------------------------

    def check_sub_compliance(
        self,
        actor: Actor,
        company_id: str,
        sub_company_id: str,
    ) -> dict[str, Any]:
        """Check compliance status for a sub-contractor company.

        Checks insurance certificates, worker certifications, and
        safety performance score.

        Args:
            actor: The agent actor.
            company_id: Tenant scope (GC company).
            sub_company_id: The sub-contractor company ID to check.

        Returns:
            Dict with sub compliance status.
        """
        result = self._read_tx_single(
            """
            MATCH (r:GcRelationship {gc_company_id: $gc_id, sub_company_id: $sub_id, status: 'active'})
            RETURN r.id AS rel_id
            """,
            {"gc_id": company_id, "sub_id": sub_company_id},
        )

        if result is None:
            return {"error": f"No active GC relationship with sub {sub_company_id}"}

        # Get sub's worker/cert data
        sub_data = self._read_tx_single(
            """
            MATCH (sc:Company {id: $sub_id})

            CALL {
                WITH sc
                OPTIONAL MATCH (sc)-[:EMPLOYS]->(w:Worker)
                WHERE w.deleted = false AND w.status = 'active'
                OPTIONAL MATCH (w)-[:HOLDS_CERT]->(cert:Certification)
                WHERE cert.expiry_date IS NOT NULL AND cert.expiry_date < $today
                WITH count(DISTINCT w) AS active_workers,
                     count(DISTINCT cert) AS expired_certs
                RETURN active_workers, expired_certs
            }

            CALL {
                WITH sc
                OPTIONAL MATCH (sc)-[:OWNS_PROJECT]->(p:Project)-[:HAS_INSPECTION]->(i:Inspection)
                WHERE i.deleted = false
                WITH count(i) AS total_inspections,
                     sum(CASE WHEN i.overall_status = 'pass' THEN 1 ELSE 0 END) AS passed
                RETURN total_inspections, passed
            }

            CALL {
                WITH sc
                OPTIONAL MATCH (sc)-[:OWNS_PROJECT]->(p:Project)-[:HAS_INCIDENT]->(inc:Incident)
                RETURN count(inc) AS total_incidents
            }

            CALL {
                WITH sc
                OPTIONAL MATCH (sc)-[:HAS_DOCUMENT]->(d:Document)
                WHERE d.deleted = false AND d.document_type = 'insurance'
                RETURN count(d) AS insurance_docs
            }

            RETURN sc.name AS sub_name, active_workers, expired_certs,
                   total_inspections, passed, total_incidents, insurance_docs
            """,
            {
                "sub_id": sub_company_id,
                "today": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            },
        )

        if sub_data is None:
            return {"error": f"Sub company {sub_company_id} not found"}

        inspection_pass_rate = (
            round(sub_data["passed"] / sub_data["total_inspections"] * 100, 1)
            if sub_data["total_inspections"] > 0
            else None
        )

        issues: list[str] = []
        if sub_data["expired_certs"] > 0:
            issues.append(f"{sub_data['expired_certs']} expired certifications")
        if sub_data["insurance_docs"] == 0:
            issues.append("No insurance certificates on file")
        if inspection_pass_rate is not None and inspection_pass_rate < 80:
            issues.append(f"Low inspection pass rate: {inspection_pass_rate}%")

        status = "compliant" if len(issues) == 0 else (
            "at_risk" if len(issues) <= 1 else "non_compliant"
        )

        return {
            "sub_company_id": sub_company_id,
            "sub_name": sub_data["sub_name"],
            "compliance_status": status,
            "active_workers": sub_data["active_workers"],
            "expired_certifications": sub_data["expired_certs"],
            "insurance_certificates": sub_data["insurance_docs"],
            "inspection_pass_rate": inspection_pass_rate,
            "total_inspections": sub_data["total_inspections"],
            "total_incidents": sub_data["total_incidents"],
            "issues": issues,
            "checked_at": datetime.now(timezone.utc).isoformat(),
        }

    # ------------------------------------------------------------------
    # Tool 17: get_sub_performance (read-only)
    # ------------------------------------------------------------------

    def get_sub_performance(
        self,
        actor: Actor,
        company_id: str,
        sub_company_id: str,
    ) -> dict[str, Any]:
        """Calculate sub-contractor performance metrics from graph data.

        Metrics: inspection pass rate, incident frequency, corrective action
        closure rate, and document completeness.

        Args:
            actor: The agent actor.
            company_id: Tenant scope (GC company).
            sub_company_id: The sub-contractor company ID.

        Returns:
            Dict with performance metrics.
        """
        result = self._read_tx_single(
            """
            MATCH (sc:Company {id: $sub_id})

            // Inspection metrics
            CALL {
                WITH sc
                OPTIONAL MATCH (sc)-[:OWNS_PROJECT]->(p:Project)-[:HAS_INSPECTION]->(i:Inspection)
                WHERE i.deleted = false
                WITH count(i) AS total_inspections,
                     sum(CASE WHEN i.overall_status = 'pass' THEN 1 ELSE 0 END) AS passed_inspections,
                     sum(CASE WHEN i.overall_status = 'fail' THEN 1 ELSE 0 END) AS failed_inspections
                RETURN total_inspections, passed_inspections, failed_inspections
            }

            // Incident metrics
            CALL {
                WITH sc
                OPTIONAL MATCH (sc)-[:OWNS_PROJECT]->(p:Project)-[:HAS_INCIDENT]->(inc:Incident)
                WITH count(inc) AS total_incidents,
                     sum(CASE WHEN inc.severity = 'critical' THEN 1 ELSE 0 END) AS critical_incidents,
                     sum(CASE WHEN inc.status = 'open' THEN 1 ELSE 0 END) AS open_incidents
                RETURN total_incidents, critical_incidents, open_incidents
            }

            // Corrective action metrics
            CALL {
                WITH sc
                OPTIONAL MATCH (sc)-[:OWNS_PROJECT]->(p:Project)-[:HAS_HAZARD_REPORT]->(h:HazardReport)
                WHERE h.deleted = false
                WITH count(h) AS total_cas,
                     sum(CASE WHEN h.status = 'resolved' THEN 1 ELSE 0 END) AS closed_cas
                RETURN total_cas, closed_cas
            }

            // Worker count for frequency calculation
            CALL {
                WITH sc
                OPTIONAL MATCH (sc)-[:EMPLOYS]->(w:Worker)
                WHERE w.deleted = false AND w.status = 'active'
                RETURN count(w) AS active_workers
            }

            RETURN sc.name AS sub_name,
                   total_inspections, passed_inspections, failed_inspections,
                   total_incidents, critical_incidents, open_incidents,
                   total_cas, closed_cas,
                   active_workers
            """,
            {"sub_id": sub_company_id},
        )

        if result is None:
            return {"error": f"Sub company {sub_company_id} not found"}

        inspection_pass_rate = (
            round(result["passed_inspections"] / result["total_inspections"] * 100, 1)
            if result["total_inspections"] > 0
            else None
        )

        ca_closure_rate = (
            round(result["closed_cas"] / result["total_cas"] * 100, 1)
            if result["total_cas"] > 0
            else None
        )

        # Simple performance score (0-100)
        score = 100
        if inspection_pass_rate is not None:
            score = min(score, inspection_pass_rate)
        if result["critical_incidents"] > 0:
            score -= result["critical_incidents"] * 10
        if result["open_incidents"] > 0:
            score -= result["open_incidents"] * 5
        if ca_closure_rate is not None and ca_closure_rate < 80:
            score -= 10
        score = max(0, min(100, score))

        return {
            "sub_company_id": sub_company_id,
            "sub_name": result["sub_name"],
            "performance_score": round(score, 1),
            "inspection_pass_rate": inspection_pass_rate,
            "total_inspections": result["total_inspections"],
            "failed_inspections": result["failed_inspections"],
            "total_incidents": result["total_incidents"],
            "critical_incidents": result["critical_incidents"],
            "open_incidents": result["open_incidents"],
            "corrective_action_closure_rate": ca_closure_rate,
            "total_corrective_actions": result["total_cas"],
            "active_workers": result["active_workers"],
            "calculated_at": datetime.now(timezone.utc).isoformat(),
        }

    # ------------------------------------------------------------------
    # Tool 18: list_subs (read-only)
    # ------------------------------------------------------------------

    def list_subs(
        self,
        actor: Actor,
        company_id: str,
    ) -> dict[str, Any]:
        """List sub-contractor companies linked via GC_OVER relationship.

        Returns subs with a quick compliance summary for each.

        Args:
            actor: The agent actor.
            company_id: Tenant scope (GC company).

        Returns:
            Dict with sub-contractor list and compliance summaries.
        """
        results = self._read_tx(
            """
            MATCH (r:GcRelationship {gc_company_id: $gc_id, status: 'active'})
            MATCH (sc:Company {id: r.sub_company_id})

            CALL {
                WITH sc
                OPTIONAL MATCH (sc)-[:EMPLOYS]->(w:Worker)
                WHERE w.deleted = false AND w.status = 'active'
                OPTIONAL MATCH (w)-[:HOLDS_CERT]->(cert:Certification)
                WHERE cert.expiry_date IS NOT NULL AND cert.expiry_date < $today
                WITH count(DISTINCT w) AS active_workers,
                     count(DISTINCT cert) AS expired_certs
                RETURN active_workers, expired_certs
            }

            CALL {
                WITH sc
                OPTIONAL MATCH (sc)-[:HAS_DOCUMENT]->(d:Document)
                WHERE d.deleted = false AND d.document_type = 'insurance'
                RETURN count(d) AS insurance_docs
            }

            RETURN r.id AS relationship_id,
                   sc.id AS sub_company_id,
                   sc.name AS sub_name,
                   r.project_name AS project_name,
                   active_workers, expired_certs, insurance_docs
            ORDER BY sc.name ASC
            """,
            {
                "gc_id": company_id,
                "today": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            },
        )

        subs = []
        for row in results:
            issues: list[str] = []
            if row["expired_certs"] > 0:
                issues.append(f"{row['expired_certs']} expired certs")
            if row["insurance_docs"] == 0:
                issues.append("No insurance on file")

            status = "compliant" if len(issues) == 0 else (
                "at_risk" if len(issues) <= 1 else "non_compliant"
            )

            subs.append({
                "relationship_id": row["relationship_id"],
                "sub_company_id": row["sub_company_id"],
                "sub_name": row["sub_name"],
                "project_name": row["project_name"],
                "active_workers": row["active_workers"],
                "expired_certifications": row["expired_certs"],
                "insurance_certificates": row["insurance_docs"],
                "compliance_status": status,
                "issues": issues,
            })

        return {
            "subs": subs,
            "total": len(subs),
            "compliant_count": sum(1 for s in subs if s["compliance_status"] == "compliant"),
            "at_risk_count": sum(1 for s in subs if s["compliance_status"] == "at_risk"),
            "non_compliant_count": sum(1 for s in subs if s["compliance_status"] == "non_compliant"),
        }

    # ==================================================================
    # ESTIMATE & PRICE tools (Session E)
    # ==================================================================

    # ------------------------------------------------------------------
    # Tool 19: create_work_item (low-risk write)
    # ------------------------------------------------------------------

    def create_work_item(
        self,
        actor: Actor,
        company_id: str,
        project_id: str,
        description: str,
        quantity: float | None = None,
        unit: str | None = None,
        margin_pct: float | None = None,
        work_package_id: str | None = None,
        work_category_id: str | None = None,
    ) -> dict[str, Any]:
        """Create a work item on a project (or within a WorkPackage).

        Sets state to 'draft'. After creation, use create_labour and
        create_item to add cost breakdown as child nodes.

        Performs a deduplication check first: if a non-deleted WorkItem on the
        same project already has a description that overlaps (case-insensitive
        substring match either direction), returns the existing id with a
        message telling the agent to use update_work_item instead.

        Args:
            actor: The agent actor.
            company_id: Tenant scope.
            project_id: The project to add the work item to.
            description: Description of the work.
            quantity: Scope quantity (e.g. 2 floor boxes, 15 LF cable).
            unit: Unit of measurement (EA, LF, SF, CY, LS, etc.).
            margin_pct: Markup percentage (0-100).
            work_package_id: Optional work package to group under.
            work_category_id: Optional canonical or company-extension WorkCategory ID.
                When supplied, writes (wi)-[:CATEGORISED_AS]->(cat) atomically with
                creation. Canonical nodes are globally accessible; extensions are
                validated to belong to the caller's company. See docs/design/
                canonical-work-categories.md.

        Returns:
            Dict with the created work item data, or — if a duplicate is
            detected — the existing work_item_id and a message directing the
            agent to update_work_item. Includes ``category_id`` when category
            was supplied and successfully written.
        """
        # Deduplication check: if a non-deleted WorkItem on this project
        # has an overlapping description (case-insensitive substring either
        # direction), return the existing id rather than creating a duplicate.
        existing = self._read_tx_single(
            """
            MATCH (p:Project {id: $project_id})-[:HAS_WORK_ITEM]->(wi:WorkItem)
            WHERE wi.deleted = false
              AND (toLower(wi.description) CONTAINS toLower($description)
                   OR toLower($description) CONTAINS toLower(wi.description))
            RETURN wi.id AS id, wi.description AS description LIMIT 1
            """,
            {"project_id": project_id, "description": description},
        )
        if existing:
            return {
                "work_item_id": existing["id"],
                "project_id": project_id,
                "description": existing["description"],
                "message": (
                    f"Work item already exists: '{existing['description']}'. "
                    "Returning existing ID. Use update_work_item to modify."
                ),
                "duplicate": True,
            }

        wi_id = self._generate_id("wi")
        provenance = self._provenance_create(actor)

        props: dict[str, Any] = {
            "id": wi_id,
            "description": description,
            "state": "draft",
            "quantity": quantity,
            "unit": unit,
            "labour_total_cents": 0,
            "items_total_cents": 0,
            "margin_pct": margin_pct,
            "sell_price_cents": 0,
            "is_alternate": False,
            "planned_start": None,
            "planned_end": None,
            "actual_start": None,
            "actual_end": None,
            "notes": None,
            "deleted": False,
            **provenance,
        }

        # Compose Cypher based on which optional relationships are present.
        package_match = ""
        package_link = ""
        category_match = ""
        category_link = ""
        params: dict[str, Any] = {
            "company_id": company_id,
            "project_id": project_id,
            "props": props,
        }

        if work_package_id:
            package_match = "MATCH (wp:WorkPackage {id: $work_package_id})\n                "
            package_link = "CREATE (wp)-[:CONTAINS]->(wi)\n                "
            params["work_package_id"] = work_package_id

        if work_category_id:
            # Canonical categories are globally accessible; Extensions must be
            # owned by this company. The WHERE clause enforces the access scope.
            category_match = (
                "MATCH (cat:WorkCategory {id: $work_category_id})\n                "
                "WHERE cat:Canonical "
                "OR EXISTS { MATCH (c)-[:HAS_EXTENSION]->(cat) }\n                "
            )
            category_link = "CREATE (wi)-[:CATEGORISED_AS]->(cat)\n                "
            params["work_category_id"] = work_category_id

        cypher = f"""
                MATCH (c:Company {{id: $company_id}})-[:OWNS_PROJECT]->(p:Project {{id: $project_id}})
                WHERE p.deleted = false
                {package_match}{category_match}CREATE (wi:WorkItem $props)
                CREATE (p)-[:HAS_WORK_ITEM]->(wi)
                {package_link}{category_link}RETURN wi.id AS work_item_id,
                    p.id AS project_id,
                    p.name AS project_name,
                    wi.description AS description,
                    wi.state AS state,
                    $work_category_id AS category_id
            """
        # When category is not requested, the "category_id" return is $work_category_id which is null
        # (NULL in Cypher), which is fine for the caller.
        if "work_category_id" not in params:
            params["work_category_id"] = None

        result = self._write_tx_single(cypher, params)

        if result is None:
            return {
                "error": (
                    f"Project {project_id} not found, or work_category_id "
                    f"{work_category_id} is not a canonical category and is not "
                    f"an extension owned by this company."
                )
            }

        event = self.event_bus.create_event(
            event_type=EventType.WORK_ITEM_CREATED,
            entity_id=wi_id,
            entity_type="WorkItem",
            company_id=company_id,
            project_id=project_id,
            actor=actor,
            summary={
                "description": description,
                "quantity": quantity,
                "unit": unit,
                "category_id": work_category_id,
            },
        )
        self.event_bus.emit(event)

        response = {
            "work_item_id": wi_id,
            "project_id": result["project_id"],
            "project_name": result["project_name"],
            "description": description,
            "state": "draft",
            "quantity": quantity,
            "unit": unit,
            "margin_pct": margin_pct,
            "message": "Work item created. Use create_labour and create_item to add cost breakdown.",
        }
        if work_category_id:
            response["category_id"] = work_category_id
        return response

    # ------------------------------------------------------------------
    # Tool 20: update_work_item (low-risk write)
    # ------------------------------------------------------------------

    def update_work_item(
        self,
        actor: Actor,
        company_id: str,
        project_id: str,
        work_item_id: str,
        description: str | None = None,
        quantity: float | None = None,
        unit: str | None = None,
        margin_pct: float | None = None,
        state: str | None = None,
        scale_children: bool = True,
    ) -> dict[str, Any]:
        """Update a work item's properties.

        Only non-None fields are applied. When quantity changes and the unit
        is unchanged (or not being changed), child Labour hours and Item
        quantities are scaled proportionally so the cost tracks the new scope.
        Pass ``scale_children=False`` to keep costs fixed (e.g. user is
        renaming a unit, not rescaling the work).

        Args:
            actor: The agent actor.
            company_id: Tenant scope.
            project_id: The parent project.
            work_item_id: The work item to update.
            description: New description.
            quantity: New scope quantity.
            unit: New unit of measurement.
            margin_pct: New markup percentage.
            state: New lifecycle state.
            scale_children: If True and only quantity is changing, scale child
                Labour.hours/cost_cents and Item.quantity/total_cents by the
                quantity ratio.

        Returns:
            Dict with updated work item data including cost totals and, when
            applicable, a ``scale_ratio`` field describing how children were
            rescaled.
        """
        update_fields: dict[str, Any] = {}
        if description is not None:
            update_fields["description"] = description
        if quantity is not None:
            update_fields["quantity"] = quantity
        if unit is not None:
            update_fields["unit"] = unit
        if margin_pct is not None:
            update_fields["margin_pct"] = margin_pct
        if state is not None:
            update_fields["state"] = state
        update_fields.update(self._provenance_update(actor))

        should_scale = (
            scale_children
            and quantity is not None
            and unit is None
        )

        result = self._write_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
                  -[:HAS_WORK_ITEM]->(wi:WorkItem {id: $work_item_id})
            WHERE wi.deleted = false
            WITH wi, p, wi.quantity AS old_quantity
            SET wi += $props
            WITH wi, p, old_quantity,
                 CASE
                   WHEN $should_scale AND old_quantity IS NOT NULL
                        AND old_quantity > 0 AND wi.quantity > 0
                   THEN toFloat(wi.quantity) / toFloat(old_quantity)
                   ELSE 1.0
                 END AS ratio
            // Scale Labour children proportionally when ratio ≠ 1
            OPTIONAL MATCH (wi)-[:HAS_LABOUR]->(lab:Labour)
            WITH wi, p, ratio, old_quantity, collect(DISTINCT lab) AS labs
            FOREACH (lab IN labs |
              SET lab.hours = CASE WHEN ratio = 1.0 THEN lab.hours ELSE lab.hours * ratio END,
                  lab.cost_cents = CASE WHEN ratio = 1.0 THEN lab.cost_cents ELSE round(lab.cost_cents * ratio) END
            )
            WITH wi, p, ratio, old_quantity
            OPTIONAL MATCH (wi)-[:HAS_ITEM]->(item:Item)
            WITH wi, p, ratio, old_quantity, collect(DISTINCT item) AS items
            FOREACH (item IN items |
              SET item.quantity = CASE WHEN ratio = 1.0 THEN item.quantity ELSE item.quantity * ratio END,
                  item.total_cents = CASE WHEN ratio = 1.0 THEN item.total_cents ELSE round(item.total_cents * ratio) END
            )
            WITH wi, p, ratio, old_quantity
            OPTIONAL MATCH (wi)-[:HAS_LABOUR]->(lab2:Labour)
            OPTIONAL MATCH (wi)-[:HAS_ITEM]->(item2:Item)
            WITH wi, p, ratio, old_quantity,
                 coalesce(sum(DISTINCT lab2.cost_cents), 0) AS labour_total,
                 coalesce(sum(DISTINCT item2.total_cents), 0) AS items_total
            SET wi.labour_total_cents = labour_total,
                wi.items_total_cents = items_total,
                wi.sell_price_cents = round((labour_total + items_total)
                    * (1 + coalesce(wi.margin_pct, 0) / 100.0))
            RETURN wi.id AS work_item_id, wi.description AS description,
                   wi.state AS state, wi.quantity AS quantity, wi.unit AS unit,
                   wi.margin_pct AS margin_pct,
                   labour_total AS labour_total_cents,
                   items_total AS items_total_cents,
                   wi.sell_price_cents AS sell_price_cents,
                   p.id AS project_id, p.name AS project_name,
                   old_quantity AS previous_quantity,
                   ratio AS scale_ratio
            """,
            {
                "company_id": company_id,
                "project_id": project_id,
                "work_item_id": work_item_id,
                "props": update_fields,
                "should_scale": should_scale,
            },
        )

        if result is None:
            return {"error": f"Work item {work_item_id} not found"}

        event = self.event_bus.create_event(
            event_type=EventType.WORK_ITEM_UPDATED,
            entity_id=work_item_id,
            entity_type="WorkItem",
            company_id=company_id,
            project_id=project_id,
            actor=actor,
            summary={"updated_fields": list(update_fields.keys())},
        )
        self.event_bus.emit(event)

        return dict(result)

    # ------------------------------------------------------------------
    # Tool 20.5: remove_work_item (low-risk write)
    # ------------------------------------------------------------------

    def remove_work_item(
        self,
        actor: Actor,
        company_id: str,
        project_id: str,
        work_item_id: str,
    ) -> dict[str, Any]:
        """Soft-delete a work item from a project.

        Marks the work item and its Labour/Item children as deleted so they
        stop contributing to estimates and proposals. Data is retained for
        audit but hidden from all downstream queries.

        Args:
            actor: The agent actor.
            company_id: Tenant scope.
            project_id: The parent project.
            work_item_id: The work item to remove.

        Returns:
            Dict confirming removal with the description that was removed.
        """
        provenance = self._provenance_update(actor)

        result = self._write_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
                  -[:HAS_WORK_ITEM]->(wi:WorkItem {id: $work_item_id})
            WHERE coalesce(wi.deleted, false) = false
            SET wi.deleted = true,
                wi.updated_at = $updated_at,
                wi.updated_by = $updated_by
            WITH wi, p, wi.description AS description
            OPTIONAL MATCH (wi)-[:HAS_LABOUR]->(lab:Labour)
            OPTIONAL MATCH (wi)-[:HAS_ITEM]->(item:Item)
            WITH wi, p, description, collect(DISTINCT lab) AS labs, collect(DISTINCT item) AS items
            FOREACH (lab IN labs | SET lab.deleted = true)
            FOREACH (item IN items | SET item.deleted = true)
            RETURN wi.id AS work_item_id, description,
                   p.id AS project_id, p.name AS project_name,
                   'removed' AS status
            """,
            {
                "company_id": company_id,
                "project_id": project_id,
                "work_item_id": work_item_id,
                "updated_at": provenance["updated_at"],
                "updated_by": provenance["updated_by"],
            },
        )

        if result is None:
            return {"error": f"Work item {work_item_id} not found"}

        event = self.event_bus.create_event(
            event_type=EventType.WORK_ITEM_UPDATED,
            entity_id=work_item_id,
            entity_type="WorkItem",
            company_id=company_id,
            project_id=project_id,
            actor=actor,
            summary={"action": "removed", "description": result["description"]},
        )
        self.event_bus.emit(event)

        return dict(result)

    # ------------------------------------------------------------------
    # Tool 21: get_estimate_summary (read-only)
    # ------------------------------------------------------------------

    def get_estimate_summary(
        self, actor: Actor, company_id: str, project_id: str
    ) -> dict[str, Any]:
        """Get a full estimate summary for a project.

        Traverses Project -> WorkItems -> Labour/Item children for cost rollup.
        Also includes Assumptions and Exclusions count.

        Args:
            actor: The agent actor.
            company_id: Tenant scope.
            project_id: The project to summarise.

        Returns:
            Dict with itemised breakdown, totals, and assumption/exclusion counts.
        """
        result = self._read_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
            WHERE p.deleted = false

            CALL {
                WITH p
                OPTIONAL MATCH (p)-[:HAS_WORK_ITEM]->(wi:WorkItem)
                WHERE wi.deleted = false
                OPTIONAL MATCH (wi)-[:HAS_LABOUR]->(lab:Labour)
                OPTIONAL MATCH (wi)-[:HAS_ITEM]->(item:Item)
                WITH wi,
                     coalesce(sum(DISTINCT lab.cost_cents), 0) AS labour_cost,
                     coalesce(sum(DISTINCT item.total_cents), 0) AS items_cost,
                     coalesce(wi.margin_pct, 0) AS margin_pct
                WITH wi, labour_cost, items_cost, margin_pct,
                     round((labour_cost + items_cost) * (1 + margin_pct / 100.0)) AS line_total
                RETURN collect({
                    id: wi.id,
                    description: wi.description,
                    state: wi.state,
                    quantity: wi.quantity,
                    unit: wi.unit,
                    labour_cost_cents: labour_cost,
                    items_cost_cents: items_cost,
                    margin_pct: margin_pct,
                    sell_price_cents: line_total,
                    is_alternate: wi.is_alternate
                }) AS items,
                sum(labour_cost) AS total_labour,
                sum(items_cost) AS total_items,
                sum(line_total) AS grand_total,
                count(wi) AS item_count
            }

            CALL {
                WITH p
                OPTIONAL MATCH (p)-[:HAS_ASSUMPTION]->(a:Assumption)
                RETURN count(a) AS assumption_count
            }

            CALL {
                WITH p
                OPTIONAL MATCH (p)-[:HAS_EXCLUSION]->(e:Exclusion)
                RETURN count(e) AS exclusion_count
            }

            RETURN p.id AS project_id, p.name AS project_name,
                   p.state AS project_state, p.status AS project_status,
                   p.estimate_confidence AS estimate_confidence,
                   p.target_margin_percent AS target_margin_percent,
                   items, total_labour, total_items, grand_total, item_count,
                   assumption_count, exclusion_count
            """,
            {"company_id": company_id, "project_id": project_id},
        )

        if result is None:
            return {"error": f"Project {project_id} not found"}

        items = [i for i in result["items"] if i.get("id")]

        return {
            "project_id": result["project_id"],
            "project_name": result["project_name"],
            "project_state": result["project_state"],
            "estimate_confidence": result["estimate_confidence"],
            "target_margin_percent": result["target_margin_percent"],
            "items": items,
            "item_count": result["item_count"] or 0,
            "total_labour_cents": result["total_labour"] or 0,
            "total_items_cents": result["total_items"] or 0,
            "grand_total_cents": result["grand_total"] or 0,
            "assumption_count": result["assumption_count"] or 0,
            "exclusion_count": result["exclusion_count"] or 0,
            "currency": "USD",
        }

    # ------------------------------------------------------------------
    # Tool 22: search_historical_rates (read-only)
    # ------------------------------------------------------------------

    def search_historical_rates(
        self,
        actor: Actor,
        company_id: str,
        description: str | None = None,
        work_category_id: str | None = None,
    ) -> dict[str, Any]:
        """Search past completed projects and company rate library.

        Finds WorkItems on completed projects with Labour/Item cost breakdowns,
        plus matching ResourceRates and ProductivityRates from the company library.

        Args:
            actor: The agent actor.
            company_id: Tenant scope.
            description: Optional text to match against descriptions.
            work_category_id: Optional WorkCategory ID to filter by.

        Returns:
            Dict with historical items, company rates, and statistics.
        """
        where_clauses = [
            "p.deleted = false",
            "wi.deleted = false",
            "p.state IN ['completed', 'closed']",
        ]
        params: dict[str, Any] = {
            "company_id": company_id,
            "limit": 10,
        }

        if work_category_id:
            where_clauses.append("cat.id = $work_category_id")
            params["work_category_id"] = work_category_id

        if description:
            where_clauses.append("toLower(wi.description) CONTAINS toLower($description)")
            params["description"] = description

        where_str = " AND ".join(where_clauses)

        results = self._read_tx(
            f"""
            MATCH (c:Company {{id: $company_id}})-[:OWNS_PROJECT]->(p:Project)
                  -[:HAS_WORK_ITEM]->(wi:WorkItem)
            OPTIONAL MATCH (wi)-[:CATEGORISED_AS]->(cat:WorkCategory)
            WHERE {where_str}
            OPTIONAL MATCH (wi)-[:HAS_LABOUR]->(lab:Labour)
            OPTIONAL MATCH (wi)-[:HAS_ITEM]->(item:Item)
            WITH wi, p, cat,
                 coalesce(sum(DISTINCT lab.cost_cents), 0) AS labour_total_cents,
                 coalesce(sum(DISTINCT item.total_cents), 0) AS items_total_cents
            RETURN wi.id AS work_item_id,
                   wi.description AS description,
                   wi.quantity AS quantity, wi.unit AS unit,
                   labour_total_cents, items_total_cents,
                   wi.margin_pct AS margin_pct,
                   p.id AS project_id, p.name AS project_name,
                   cat.name AS category_name
            ORDER BY p.created_at DESC
            LIMIT $limit
            """,
            params,
        )

        items = [dict(r) for r in results]

        # Fetch matching ResourceRates
        rate_params: dict[str, Any] = {"company_id": company_id}
        rate_filter = ""
        if description:
            rate_filter = " AND toLower(rr.description) CONTAINS toLower($description)"
            rate_params["description"] = description

        rate_results = self._read_tx(
            f"""
            MATCH (c:Company {{id: $company_id}})-[:HAS_RATE]->(rr:ResourceRate)
            WHERE rr.active = true{rate_filter}
            RETURN rr.id AS id, rr.resource_type AS resource_type,
                   rr.description AS description, rr.rate_cents AS rate_cents,
                   rr.unit AS unit, rr.source AS source
            LIMIT 10
            """,
            rate_params,
        )
        resource_rates = [dict(r) for r in rate_results]

        # Fetch matching ProductivityRates
        pr_params: dict[str, Any] = {"company_id": company_id}
        pr_filter = ""
        if description:
            pr_filter = " AND toLower(pr.description) CONTAINS toLower($description)"
            pr_params["description"] = description

        pr_results = self._read_tx(
            f"""
            MATCH (c:Company {{id: $company_id}})-[:HAS_PRODUCTIVITY]->(pr:ProductivityRate)
            WHERE pr.active = true{pr_filter}
            RETURN pr.id AS id, pr.description AS description,
                   pr.rate AS rate, pr.rate_unit AS rate_unit,
                   pr.time_unit AS time_unit, pr.crew_composition AS crew_composition
            LIMIT 10
            """,
            pr_params,
        )
        productivity_rates = [dict(r) for r in pr_results]

        return {
            "historical_items": items,
            "resource_rates": resource_rates,
            "productivity_rates": productivity_rates,
            "total_found": len(items),
        }

    # ------------------------------------------------------------------
    # Source cascade lookup tools (Layer 3)
    # ------------------------------------------------------------------

    def get_rate_suggestion(
        self,
        actor: Actor,
        company_id: str,
        project_id: str,
        trade: str,
        role: str,
    ) -> dict[str, Any]:
        """Find a labour rate for a given trade/role using the source cascade.

        Labour rates must be contractor-stated — we never fall back to a
        training-data guess or an industry baseline for rates. If no
        ResourceRate matches the role, the caller is expected to ask the
        contractor and then call ``capture_rate``.

        Cascade:
          1. Match a company ResourceRate (labour, active, description/
             resource_type contains role — case-insensitive). High confidence.
          2. Otherwise report ``not_found`` with a reasoning string that
             tells the agent to ask the contractor.

        Args:
            actor: The agent actor.
            company_id: Tenant scope.
            project_id: The project the estimate is for (reserved for future
                project-specific overrides; not used today).
            trade: Trade name (e.g. 'electrical').
            role: Role description (e.g. 'journeyman electrician').

        Returns:
            Dict with rate_cents, source_type, source_id, source_reasoning,
            and confidence.
        """
        needle = role.lower().strip()
        # Tokenise into significant words (3+ chars, drop stopwords)
        _STOPWORDS = {
            "the", "and", "for", "with", "from", "your", "our",
            "work", "rate", "loaded", "hour", "per",
        }

        def _stem(w: str) -> str:
            """Cheap stem — chop common suffixes so 'electrical' and
            'electrician' both become 'electric'."""
            for suf in ("icians", "ician", "ical", "ics", "ing", "ers", "er", "ist", "al", "s"):
                if w.endswith(suf) and len(w) - len(suf) >= 4:
                    return w[:-len(suf)]
            return w

        def _toks(s: str) -> set[str]:
            return {
                _stem(w) for w in s.lower().replace("-", " ").split()
                if len(w) >= 3 and w not in _STOPWORDS
            }

        role_tokens = _toks(needle)

        # Fetch all active labour rates, score by token overlap
        rows = self._read_tx(
            """
            MATCH (c:Company {id: $company_id})-[:HAS_RATE]->(rr:ResourceRate)
            WHERE rr.active = true AND rr.resource_type = 'labour'
            RETURN rr {.*, company_id: c.id} AS rate
            """,
            {"company_id": company_id},
        )
        best = None
        best_score = 0
        for row in rows:
            rate = row["rate"]
            desc_tokens = _toks(rate.get("description") or "")
            overlap = role_tokens & desc_tokens
            score = len(overlap)
            if score > best_score:
                best_score = score
                best = rate
        # If no token overlap AND the contractor has only one labour rate
        # for this trade context, fall back to using it (better than
        # not_found — they have one rate, it's clearly what they use).
        if best is None and len(rows) == 1:
            best = rows[0]["rate"]
            best_score = 1

        result = {"rate": best} if best is not None and best_score >= 1 else None

        if result is None:
            return {
                "rate_cents": None,
                "source_type": "not_found",
                "source_id": None,
                "source_reasoning": (
                    f"No rate for {role}. Ask the contractor or use "
                    f"capture_rate to set one."
                ),
                "confidence": 0.0,
            }

        rate = result["rate"]
        return {
            "rate_cents": rate.get("rate_cents"),
            "source_type": "resource_rate",
            "source_id": rate.get("id"),
            "source_reasoning": (
                f"Your {role} rate in your rate library "
                f"({rate.get('description') or role})"
            ),
            "confidence": 0.9,
        }

    def suggest_productivity(
        self,
        actor: Actor,
        company_id: str,
        project_id: str,
        trade: str,
        work_description: str,
    ) -> dict[str, Any]:
        """Find a productivity estimate using the source cascade.

        Cascade:
          1. Company ProductivityRate with description matching the work
             (case-insensitive). High confidence.
          2. Applicable Insights (trade-scoped). Insights refine a base
             rate — if no base rate is available, the agent must still
             fall through to the baseline.
          3. IndustryProductivityBaseline (trade + description). Low
             confidence (0.3).
          4. ``not_found`` otherwise.

        Args:
            actor: The agent actor.
            company_id: Tenant scope.
            project_id: The project the estimate is for.
            trade: Trade name (e.g. 'electrical').
            work_description: Free-text description of the work.

        Returns:
            Dict with rate, rate_unit, time_unit, source_type, source_id,
            source_reasoning, confidence, and (optional) applicable_insights.
        """
        needle = work_description.lower().strip()
        _STOPWORDS = {"the", "and", "for", "with", "from", "your", "our", "install", "installation"}
        desc_tokens_needle = {
            w for w in needle.replace("-", " ").split()
            if len(w) >= 3 and w not in _STOPWORDS
        }

        # Layer 1: company ProductivityRate — score by token overlap
        pr_rows = self._read_tx(
            """
            MATCH (c:Company {id: $company_id})-[:HAS_PRODUCTIVITY]->(pr:ProductivityRate)
            WHERE pr.active = true
            RETURN pr {.*, company_id: c.id} AS rate
            """,
            {"company_id": company_id},
        )
        best_pr = None
        best_pr_score = 0
        for row in pr_rows:
            r = row["rate"]
            candidate_tokens = {
                w for w in (r.get("description") or "").lower().replace("-", " ").split()
                if len(w) >= 3 and w not in _STOPWORDS
            }
            overlap = len(desc_tokens_needle & candidate_tokens)
            if overlap > best_pr_score:
                best_pr_score = overlap
                best_pr = r
        pr_result = {"rate": best_pr} if best_pr is not None and best_pr_score >= 2 else None
        if pr_result is not None:
            rate = pr_result["rate"]
            hpu = _hours_per_unit(rate.get("rate"), rate.get("time_unit"))
            return {
                "rate": rate.get("rate"),
                "rate_unit": rate.get("rate_unit"),
                "time_unit": rate.get("time_unit"),
                "hours_per_unit": hpu,
                "source_type": "productivity_rate",
                "source_id": rate.get("id"),
                "source_reasoning": (
                    f"Your productivity history: {rate.get('description')} "
                    f"({rate.get('rate')} {rate.get('rate_unit')} {rate.get('time_unit')}, "
                    f"= {hpu:.3f} hours per {rate.get('rate_unit')} — "
                    f"multiply by your quantity to get total hours)"
                    if hpu is not None else
                    f"Your productivity history: {rate.get('description')}"
                ),
                "confidence": 0.85,
            }

        # Layer 2: applicable Insights (as refinement signal)
        from app.services.insight_service import InsightService
        insight_svc = InsightService(self.driver)
        insights = insight_svc.find_applicable(
            company_id=company_id, trade=trade, limit=5
        )
        applicable_insights = [
            {
                "id": ins.get("id"),
                "statement": ins.get("statement"),
                "adjustment_type": ins.get("adjustment_type"),
                "adjustment_value": ins.get("adjustment_value"),
                "confidence": ins.get("confidence"),
            }
            for ins in insights
        ]

        # Layer 3: IndustryProductivityBaseline
        from app.services.industry_baseline_service import IndustryBaselineService
        baseline_svc = IndustryBaselineService(self.driver)
        baselines = baseline_svc.find_by_trade_and_description(
            trade=trade, description=work_description, limit=1
        )

        if baselines:
            baseline = baselines[0]
            hpu_b = _hours_per_unit(baseline.get("rate"), baseline.get("time_unit"))
            # If we have applicable insights, mark them so the agent can
            # explain that the baseline will be adjusted.
            reasoning_parts: list[str] = [
                f"Industry baseline for {trade} — {baseline.get('work_description')} "
                f"({baseline.get('rate')} {baseline.get('rate_unit')} {baseline.get('time_unit')}, "
                f"= {hpu_b:.3f} hours per {baseline.get('rate_unit')})"
                if hpu_b is not None else
                f"Industry baseline for {trade} — {baseline.get('work_description')}"
            ]
            if applicable_insights:
                reasoning_parts.append(
                    f"{len(applicable_insights)} applicable insight(s) "
                    f"may refine this rate — review before accepting."
                )
            return {
                "rate": baseline.get("rate"),
                "rate_unit": baseline.get("rate_unit"),
                "time_unit": baseline.get("time_unit"),
                "hours_per_unit": hpu_b,
                "source_type": "industry_baseline",
                "source_id": baseline.get("id"),
                "source_reasoning": " ".join(reasoning_parts),
                "confidence": 0.3,
                "applicable_insights": applicable_insights,
            }

        # Nothing found
        return {
            "rate": None,
            "rate_unit": None,
            "time_unit": None,
            "source_type": "not_found",
            "source_id": None,
            "source_reasoning": (
                f"No productivity data found for {trade}: '{work_description}'. "
                f"Ask the contractor for an estimate."
            ),
            "confidence": 0.0,
            "applicable_insights": applicable_insights,
        }

    def get_material_history(
        self,
        actor: Actor,
        company_id: str,
        project_id: str,
        description: str,
    ) -> dict[str, Any]:
        """Find prior material costs from the contractor's completed projects.

        Args:
            actor: The agent actor.
            company_id: Tenant scope.
            project_id: The project being estimated (context only).
            description: Free-text description of the material.

        Returns:
            Dict with ``matches`` (list of past Item records) and ``has_history``.
        """
        from app.services.material_catalog_service import MaterialCatalogService

        catalog_svc = MaterialCatalogService(self.driver)
        history = catalog_svc.find_from_history(
            company_id=company_id, description=description, limit=5
        )

        matches: list[dict[str, Any]] = []
        for row in history:
            date_raw = row.get("date")
            date_iso = (
                date_raw.isoformat()
                if hasattr(date_raw, "isoformat")
                else date_raw
            )
            matches.append(
                {
                    "supplier": row.get("supplier"),
                    "unit_cost_cents": row.get("unit_cost_cents"),
                    "unit": None,
                    "project_name": row.get("project_name"),
                    "date": date_iso,
                    "source_id": None,
                }
            )

        return {
            "matches": matches,
            "has_history": len(matches) > 0,
        }

    def search_material_price(
        self,
        actor: Actor,
        company_id: str,
        project_id: str,
        description: str,
        unit: str,
    ) -> dict[str, Any]:
        """Find a current supplier price for a material.

        Cascade:
          1. Match a non-stale MaterialCatalogEntry, preferring entries that
             match the project's location (city) when available.
          2. Fall back to stale entries if no fresh match exists (flagged).
          3. Return ``search_pending`` — web search is not yet wired up. The
             agent should ask the contractor or call ``capture_material_price``.

        Args:
            actor: The agent actor.
            company_id: Tenant scope.
            project_id: The project — used to locate the city/state for
                locality-aware catalog matches.
            description: Free-text description of the material.
            unit: Expected unit of measurement (informational).

        Returns:
            Dict with either a matched catalog entry, a stale match, or a
            ``search_pending`` response.
        """
        # Resolve project location (city) for locality-aware matching
        project_location: str | None = None
        us_state: str | None = None
        proj = self._read_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
            WHERE p.deleted = false
            RETURN p.city AS city, p.us_state AS us_state
            """,
            {"company_id": company_id, "project_id": project_id},
        )
        if proj is not None:
            project_location = proj.get("city")
            us_state = proj.get("us_state")

        from app.services.material_catalog_service import MaterialCatalogService
        catalog_svc = MaterialCatalogService(self.driver)

        # Try the project city first, then state, then any location
        location_candidates: list[str | None] = []
        if project_location:
            location_candidates.append(project_location)
        if us_state and us_state != project_location:
            location_candidates.append(us_state)
        # Final pass with no location filter
        location_candidates.append(None)

        for location in location_candidates:
            entries = catalog_svc.find_by_description(
                company_id=company_id,
                description=description,
                location=location,
                limit=5,
            )
            # Prefer non-stale
            for entry in entries:
                if not catalog_svc.is_stale(entry):
                    return {
                        "source_type": "material_catalog",
                        "source_id": entry.get("id"),
                        "unit_cost_cents": entry.get("unit_cost_cents"),
                        "unit": entry.get("unit"),
                        "supplier_name": entry.get("supplier_name"),
                        "source_url": entry.get("source_url"),
                        "location": entry.get("location"),
                        "fetched_at": entry.get("fetched_at"),
                        "is_stale": False,
                        "source_reasoning": (
                            f"Catalog entry from {entry.get('supplier_name') or 'supplier'}"
                            + (f" ({entry.get('location')})" if entry.get("location") else "")
                        ),
                        "confidence": 0.8,
                    }
            # Fall back to a stale match at this locality only if no fresh
            # match is available across any locality. We only flag — the
            # agent can decide whether to accept it or call capture.
            if entries and location == location_candidates[-1]:
                entry = entries[0]
                return {
                    "source_type": "material_catalog",
                    "source_id": entry.get("id"),
                    "unit_cost_cents": entry.get("unit_cost_cents"),
                    "unit": entry.get("unit"),
                    "supplier_name": entry.get("supplier_name"),
                    "source_url": entry.get("source_url"),
                    "location": entry.get("location"),
                    "fetched_at": entry.get("fetched_at"),
                    "is_stale": True,
                    "source_reasoning": (
                        f"Catalog entry from {entry.get('supplier_name') or 'supplier'} "
                        f"— price may be stale, confirm with the contractor."
                    ),
                    "confidence": 0.4,
                }

        # No catalog match — real web search is not yet integrated.
        # Shape matches a future web-search response so callers can swap.
        return {
            "source_type": "search_pending",
            "source_id": None,
            "unit_cost_cents": None,
            "unit": unit,
            "supplier_name": None,
            "source_url": None,
            "location": project_location,
            "fetched_at": None,
            "is_stale": None,
            "source_reasoning": (
                "Web search not yet integrated. Ask the contractor for the "
                "price, then use capture_material_price to store it."
            ),
            "confidence": 0.0,
            "message": (
                "Web search not yet integrated. Ask the contractor for the price."
            ),
        }

    def capture_rate(
        self,
        actor: Actor,
        company_id: str,
        project_id: str,
        trade: str,
        role: str,
        rate_cents: int,
        description: str = "",
    ) -> dict[str, Any]:
        """Just-in-time capture a contractor-stated labour rate.

        Creates a company-scoped ResourceRate (resource_type='labour') so
        that future estimates can reuse it via ``get_rate_suggestion``.
        Inlines the Cypher rather than going through ResourceRateService
        so the agent actor's provenance (actor_type='agent', agent_id,
        model_id, ...) is preserved rather than being rewritten as human.

        Args:
            actor: The agent actor. Used for provenance.
            company_id: Tenant scope.
            project_id: The project where the contractor stated the rate
                (context only — not persisted on the ResourceRate).
            trade: Trade name (e.g. 'electrical').
            role: Role description (e.g. 'journeyman electrician').
            rate_cents: Hourly rate in cents.
            description: Optional richer description for the rate. When
                blank, we construct one from trade + role.

        Returns:
            Dict with the new rate id and a confirmation message.
        """
        desc = description or f"{trade} — {role}"
        rr_id = self._generate_id("rr")
        provenance = self._provenance_create(actor)

        props: dict[str, Any] = {
            "id": rr_id,
            "resource_type": "labour",
            "description": desc,
            "rate_cents": rate_cents,
            "unit": "hour",
            "source": "contractor_stated",
            "base_rate_cents": None,
            "burden_percent": None,
            "non_productive_percent": None,
            "supplier_name": "",
            "quote_valid_until": None,
            "sample_size": None,
            "std_deviation_cents": None,
            "last_derived_at": None,
            "active": True,
            **provenance,
        }

        result = self._write_tx_single(
            """
            MATCH (c:Company {id: $company_id})
            CREATE (rr:ResourceRate $props)
            CREATE (c)-[:HAS_RATE]->(rr)
            RETURN rr.id AS rate_id, rr.description AS description,
                   rr.rate_cents AS rate_cents, rr.unit AS unit
            """,
            {"company_id": company_id, "props": props},
        )
        if result is None:
            return {"error": f"Company {company_id} not found"}

        return {
            "rate_id": result["rate_id"],
            "rate_cents": rate_cents,
            "description": desc,
            "source_type": "resource_rate",
            "message": (
                f"Captured {role} rate at ${rate_cents / 100:,.2f}/hr in "
                f"your rate library."
            ),
        }

    def capture_material_price(
        self,
        actor: Actor,
        company_id: str,
        project_id: str,
        description: str,
        unit: str,
        unit_cost_cents: int,
        supplier_name: str = "",
        source_url: str = "",
    ) -> dict[str, Any]:
        """Persist a material price so it can seed future estimates.

        Creates a MaterialCatalogEntry scoped to the company. The project's
        city (then state) is used as the ``location`` when available so
        future location-aware lookups (``search_material_price``) can prefer it.
        Inlines the Cypher rather than going through MaterialCatalogService
        so the agent actor's provenance is preserved.

        Args:
            actor: The agent actor.
            company_id: Tenant scope.
            project_id: The project the price was stated for — used to pick
                up the city/state as the entry's location.
            description: What the material is.
            unit: Unit of measurement (EA, LF, SF, ...).
            unit_cost_cents: Cost per unit in cents.
            supplier_name: Optional supplier.
            source_url: Optional source URL.

        Returns:
            Dict with the new MaterialCatalogEntry id.
        """
        # Locate project for location tagging
        location: str | None = None
        proj = self._read_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
            WHERE p.deleted = false
            RETURN p.city AS city, p.us_state AS us_state
            """,
            {"company_id": company_id, "project_id": project_id},
        )
        if proj is not None:
            location = proj.get("city") or proj.get("us_state")

        mce_id = self._generate_id("mce")
        now_iso = datetime.now(timezone.utc).isoformat()
        provenance = self._provenance_create(actor)

        props: dict[str, Any] = {
            "id": mce_id,
            "description": description,
            "product_code": None,
            "unit": unit,
            "unit_cost_cents": unit_cost_cents,
            "supplier_name": supplier_name or None,
            "source_url": source_url or None,
            "location": location,
            "fetched_at": now_iso,
            "last_verified_at": None,
            **provenance,
        }

        result = self._write_tx_single(
            """
            MATCH (c:Company {id: $company_id})
            CREATE (mce:MaterialCatalogEntry $props)
            CREATE (c)-[:HAS_CATALOG_ENTRY]->(mce)
            RETURN mce.id AS entry_id, mce.description AS description,
                   mce.unit_cost_cents AS unit_cost_cents,
                   mce.unit AS unit, mce.location AS location
            """,
            {"company_id": company_id, "props": props},
        )
        if result is None:
            return {"error": f"Company {company_id} not found"}

        return {
            "entry_id": result["entry_id"],
            "description": description,
            "unit_cost_cents": unit_cost_cents,
            "location": location,
            "message": (
                f"Captured {description} at ${unit_cost_cents / 100:,.2f}/{unit} "
                f"in your material catalog."
            ),
        }

    def create_insight(
        self,
        actor: Actor,
        company_id: str,
        scope: str,
        scope_value: str,
        statement: str,
        adjustment_type: str,
        adjustment_value: float | None = None,
        confidence: float = 0.5,
        source_context: str = "",
    ) -> dict[str, Any]:
        """Capture contractor reasoning as a reusable Insight.

        Insights feed Layer 3 of the source cascade — they refine future
        productivity/rate estimates on similar work. Inlines the Cypher
        rather than going through InsightService so the agent actor's
        provenance is preserved.

        Args:
            actor: The agent actor.
            company_id: Tenant scope.
            scope: Dimension of context: 'work_type', 'trade', 'jurisdiction',
                'client_type', 'project_size', or 'other'.
            scope_value: Concrete value for the scope (e.g. 'low_ceiling_renovation').
            statement: Human-readable insight text.
            adjustment_type: 'productivity_multiplier', 'rate_adjustment',
                or 'qualitative'.
            adjustment_value: Numeric adjustment (e.g. 1.15 for +15%).
            confidence: 0-1 confidence the insight holds.
            source_context: Optional origin reference (e.g. conversation ID).

        Returns:
            Dict with the new Insight id.
        """
        ins_id = self._generate_id("ins")
        provenance = self._provenance_create(actor)

        # Domain confidence overrides the provenance confidence (which is
        # the agent's self-reported confidence for this tool call).
        props: dict[str, Any] = {
            "id": ins_id,
            "scope": scope,
            "scope_value": scope_value,
            "statement": statement,
            "adjustment_type": adjustment_type,
            "adjustment_value": adjustment_value,
            "source_context": source_context or None,
            "validation_count": 0,
            "last_applied_at": None,
            **provenance,
            "confidence": confidence,
        }

        result = self._write_tx_single(
            """
            MATCH (c:Company {id: $company_id})
            CREATE (ins:Insight $props)
            CREATE (c)-[:HAS_INSIGHT]->(ins)
            RETURN ins.id AS insight_id, ins.scope AS scope,
                   ins.scope_value AS scope_value,
                   ins.statement AS statement,
                   ins.confidence AS confidence
            """,
            {"company_id": company_id, "props": props},
        )
        if result is None:
            return {"error": f"Company {company_id} not found"}

        return {
            "insight_id": result["insight_id"],
            "scope": result["scope"],
            "scope_value": result["scope_value"],
            "statement": result["statement"],
            "confidence": result["confidence"],
            "message": f"Captured insight: {statement[:80]}",
        }

    # ------------------------------------------------------------------
    # Layer 4: Knowledge accumulation tools
    # ------------------------------------------------------------------

    def apply_insight(
        self,
        actor: Actor,
        company_id: str,
        insight_id: str,
        context: str = "",
    ) -> dict[str, Any]:
        """Record that an Insight was applied during a quote.

        Increments ``validation_count``, updates ``last_applied_at``, and
        raises ``confidence`` by 0.05 (capped at 0.95). Silence is consent:
        an Insight that's applied without correction counts as validated.

        Args:
            actor: The agent actor (provenance).
            company_id: Tenant scope.
            insight_id: The Insight being applied.
            context: Optional free-text describing where it was applied
                (e.g. 'On work item wi_abc123 — receptacle rough-in').

        Returns:
            Dict with the updated confidence, validation_count, and
            a confirmation message.
        """
        now_iso = datetime.now(timezone.utc).isoformat()
        provenance = self._provenance_update(actor)

        result = self._write_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:HAS_INSIGHT]->(ins:Insight {id: $insight_id})
            SET ins.validation_count = coalesce(ins.validation_count, 0) + 1,
                ins.confidence = CASE
                    WHEN coalesce(ins.confidence, 0.5) + 0.05 > 0.95 THEN 0.95
                    ELSE coalesce(ins.confidence, 0.5) + 0.05
                END,
                ins.last_applied_at = $now_iso,
                ins += $provenance
            RETURN ins.id AS insight_id,
                   ins.statement AS statement,
                   ins.confidence AS confidence,
                   ins.validation_count AS validation_count
            """,
            {
                "company_id": company_id,
                "insight_id": insight_id,
                "now_iso": now_iso,
                "provenance": provenance,
            },
        )
        if result is None:
            return {"error": f"Insight {insight_id} not found"}

        self._emit_audit(
            event_type="entity.updated",
            entity_id=insight_id,
            entity_type="Insight",
            company_id=company_id,
            actor=actor,
            summary=(
                f"Applied insight — confidence now "
                f"{result['confidence']:.2f} (validation "
                f"#{result['validation_count']})"
                + (f" — {context[:80]}" if context else "")
            ),
        )

        return {
            "insight_id": result["insight_id"],
            "statement": result["statement"],
            "confidence": result["confidence"],
            "validation_count": result["validation_count"],
            "message": (
                f"Applied insight. Confidence now {result['confidence']:.2f} "
                f"after {result['validation_count']} application(s)."
            ),
        }

    def correct_insight(
        self,
        actor: Actor,
        company_id: str,
        insight_id: str,
        correction_note: str,
    ) -> dict[str, Any]:
        """Record that the contractor corrected a previously-applied Insight.

        Decrements ``confidence`` by 0.1 (floor 0.1), decrements
        ``validation_count`` (floor 0), and appends the correction note to
        ``source_context``. If confidence drops below 0.3 the Insight is
        marked ``deprecated: true`` so future surfacing can skip it.

        The contractor always wins — don't argue, adjust confidence down.

        Args:
            actor: The agent actor (provenance).
            company_id: Tenant scope.
            insight_id: The Insight being corrected.
            correction_note: Why the contractor pushed back.

        Returns:
            Dict with new confidence, validation_count, and deprecation flag.
        """
        if not correction_note:
            return {"error": "correction_note is required"}

        provenance = self._provenance_update(actor)
        now_iso = datetime.now(timezone.utc).isoformat()
        # Timestamped correction line appended to source_context so we keep
        # a running history rather than clobbering prior notes.
        correction_line = f"[{now_iso}] correction: {correction_note}"

        result = self._write_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:HAS_INSIGHT]->(ins:Insight {id: $insight_id})
            SET ins.confidence = CASE
                    WHEN coalesce(ins.confidence, 0.5) - 0.1 < 0.1 THEN 0.1
                    ELSE coalesce(ins.confidence, 0.5) - 0.1
                END,
                ins.validation_count = CASE
                    WHEN coalesce(ins.validation_count, 0) - 1 < 0 THEN 0
                    ELSE coalesce(ins.validation_count, 0) - 1
                END,
                ins.source_context = CASE
                    WHEN ins.source_context IS NULL OR ins.source_context = ''
                        THEN $correction_line
                    ELSE ins.source_context + '\n' + $correction_line
                END,
                ins += $provenance
            WITH ins
            SET ins.deprecated = (ins.confidence < 0.3)
            RETURN ins.id AS insight_id,
                   ins.statement AS statement,
                   ins.confidence AS confidence,
                   ins.validation_count AS validation_count,
                   coalesce(ins.deprecated, false) AS deprecated
            """,
            {
                "company_id": company_id,
                "insight_id": insight_id,
                "correction_line": correction_line,
                "provenance": provenance,
            },
        )
        if result is None:
            return {"error": f"Insight {insight_id} not found"}

        deprecated = bool(result["deprecated"])
        self._emit_audit(
            event_type="entity.updated",
            entity_id=insight_id,
            entity_type="Insight",
            company_id=company_id,
            actor=actor,
            summary=(
                f"Corrected insight — confidence now "
                f"{result['confidence']:.2f}"
                + (" (deprecated)" if deprecated else "")
                + f" — {correction_note[:80]}"
            ),
        )

        message_parts = [
            f"Corrected. Confidence now {result['confidence']:.2f}."
        ]
        if deprecated:
            message_parts.append(
                "Insight deprecated — will not be applied on future quotes."
            )
        return {
            "insight_id": result["insight_id"],
            "statement": result["statement"],
            "confidence": result["confidence"],
            "validation_count": result["validation_count"],
            "deprecated": deprecated,
            "message": " ".join(message_parts),
        }

    def find_applicable_insights_for_work(
        self,
        actor: Actor,
        company_id: str,
        project_id: str,
        work_description: str,
        trade: str,
    ) -> dict[str, Any]:
        """Return insights scored and pre-bucketed for quote-time surfacing.

        Richer than ``InsightService.find_applicable`` — this one:
        1. Pulls insights that apply to the project's scopes (trade,
           work_type from the work description, jurisdiction, client_type,
           project_size).
        2. Buckets them by confidence band for the agent to surface appropriately.
        3. Multiplicatively combines ``productivity_multiplier`` insights
           whose confidence >= 0.6 into a single ``combined_productivity_adjustment``.

        Only ``productivity_multiplier`` insights contribute to the combined
        adjustment. ``rate_adjustment`` and ``qualitative`` insights are
        returned as-is for the agent to present and explain.

        Args:
            actor: The agent actor.
            company_id: Tenant scope.
            project_id: Project context — used to look up jurisdiction, client
                type, project size for scope matching.
            work_description: Free-text description of the work item.
            trade: Trade name (e.g. 'electrical').

        Returns:
            Dict with ``high_confidence`` (>= 0.6), ``medium_confidence``
            (0.3-0.6), ``low_confidence`` (< 0.3), ``combined_productivity_adjustment``
            (float, 1.0 if none apply) and ``combined_reasoning`` (narration).
        """
        # Resolve project scopes for richer matching. Include project
        # description so Insights scoped to e.g. "renovation_electrical"
        # match a project that IS a renovation via equivalences.
        proj = self._read_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
            WHERE p.deleted = false
            RETURN p.us_state AS us_state,
                   p.project_type AS project_type,
                   p.client_name AS client_name,
                   p.description AS project_description,
                   p.name AS project_name
            """,
            {"company_id": company_id, "project_id": project_id},
        )
        jurisdiction = proj.get("us_state") if proj else None
        project_type = proj.get("project_type") if proj else None
        project_description = (proj.get("project_description") or "") if proj else ""
        project_name = (proj.get("project_name") or "") if proj else ""

        # Combine project context + work item description to form a rich
        # work_type string. This gives the fuzzy matching in
        # InsightService.find_applicable plenty of tokens to score against.
        _STOPWORDS = {
            "the", "and", "for", "with", "from", "your", "our",
            "install", "installation", "work",
        }
        combined = f"{work_description} {project_name} {project_description} {trade}".lower()
        tokens = [
            w for w in combined.replace("-", " ").replace(",", " ").split()
            if len(w) >= 3 and w not in _STOPWORDS
        ]
        # Use up to 8 significant tokens joined — the fuzzy matcher will
        # score overlap against Insight scope_values.
        work_type = "_".join(tokens[:8]) if tokens else None

        from app.services.insight_service import InsightService
        insight_svc = InsightService(self.driver)
        insights = insight_svc.find_applicable(
            company_id=company_id,
            work_type=work_type,
            trade=trade,
            jurisdiction=jurisdiction,
            client_type=project_type,
            limit=25,
        )

        # Filter out deprecated insights up-front so they never surface.
        active_insights = [
            ins for ins in insights if not ins.get("deprecated", False)
        ]

        high: list[dict[str, Any]] = []
        medium: list[dict[str, Any]] = []
        low: list[dict[str, Any]] = []
        for ins in active_insights:
            confidence = ins.get("confidence") or 0.0
            if confidence >= 0.6:
                high.append(ins)
            elif confidence >= 0.3:
                medium.append(ins)
            else:
                low.append(ins)

        # Combine productivity_multiplier insights (confidence >= 0.6) into
        # a single multiplicative adjustment. Narrate the math so the agent
        # can surface the reasoning.
        combined = 1.0
        narration_parts: list[str] = []
        applied_ids: list[str] = []
        for ins in high:
            if ins.get("adjustment_type") != "productivity_multiplier":
                continue
            adjustment = ins.get("adjustment_value")
            if adjustment is None or adjustment <= 0:
                continue
            combined *= float(adjustment)
            applied_ids.append(ins.get("id"))
            # e.g. "+15% low ceiling" (adjustment=1.15) or "-10% renovation"
            pct = (adjustment - 1.0) * 100.0
            sign = "+" if pct >= 0 else ""
            narration_parts.append(
                f"{sign}{pct:.0f}% {ins.get('scope_value') or 'scope'}"
            )

        if narration_parts:
            combined_reasoning = (
                f"Applying {' x '.join(narration_parts)} "
                f"= {combined:.4f} net"
            )
        else:
            combined_reasoning = (
                "No high-confidence productivity insights apply."
            )

        return {
            "high_confidence": high,
            "medium_confidence": medium,
            "low_confidence": low,
            "combined_productivity_adjustment": combined,
            "combined_productivity_insight_ids": applied_ids,
            "combined_reasoning": combined_reasoning,
        }

    def derive_productivity_from_actuals(
        self,
        actor: Actor,
        company_id: str,
        project_id: str,
        work_item_id: str,
    ) -> dict[str, Any]:
        """Compare estimated vs actual hours on a completed WorkItem.

        Pulls:
        - Estimated hours from the WorkItem's Labour children (sum of ``hours``).
        - Actual hours from TimeEntry nodes — sum of
          ``hours_regular + hours_overtime`` on any TimeEntry linked via
          ``(WorkItem)-[:HAS_TIME_ENTRY]->(TimeEntry)``.
        - The ``productivity_source_id`` that was used on the Labour children
          (first non-null one) so we know which ProductivityRate to potentially
          update.

        Computes an ``implied_rate`` in output-units per actual hour based on
        the WorkItem's own quantity, and compares it to the ProductivityRate
        currently in the library.

        Args:
            actor: The agent actor.
            company_id: Tenant scope.
            project_id: Project scope.
            work_item_id: The work item to derive from.

        Returns:
            Dict with estimated vs actual hours, implied rate, current
            library rate, variance, and a ``should_update`` recommendation.
        """
        result = self._read_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
                  -[:HAS_WORK_ITEM]->(wi:WorkItem {id: $work_item_id})
            WHERE wi.deleted = false
            OPTIONAL MATCH (wi)-[:HAS_LABOUR]->(lab:Labour)
            WITH wi, p,
                 coalesce(sum(lab.hours), 0.0) AS estimated_hours,
                 [lab_id IN collect(DISTINCT lab.productivity_source_id) WHERE lab_id IS NOT NULL][0] AS productivity_source_id
            OPTIONAL MATCH (wi)-[:HAS_TIME_ENTRY]->(te:TimeEntry)
            WHERE coalesce(te.deleted, false) = false
            WITH wi, p, estimated_hours, productivity_source_id,
                 coalesce(sum(coalesce(te.hours_regular, 0.0) + coalesce(te.hours_overtime, 0.0)), 0.0) AS actual_hours
            RETURN wi.id AS work_item_id,
                   wi.description AS work_item_description,
                   wi.quantity AS estimated_quantity,
                   wi.unit AS unit,
                   estimated_hours,
                   actual_hours,
                   productivity_source_id
            """,
            {
                "company_id": company_id,
                "project_id": project_id,
                "work_item_id": work_item_id,
            },
        )
        if result is None:
            return {"error": f"Work item {work_item_id} not found"}

        estimated_quantity = result.get("estimated_quantity") or 0.0
        unit = result.get("unit") or ""
        estimated_hours = float(result.get("estimated_hours") or 0.0)
        actual_hours = float(result.get("actual_hours") or 0.0)
        productivity_source_id = result.get("productivity_source_id")

        if actual_hours <= 0 or estimated_quantity <= 0:
            return {
                "work_item_id": work_item_id,
                "productivity_rate_id": productivity_source_id,
                "estimated_hours": estimated_hours,
                "actual_hours": actual_hours,
                "estimated_quantity": estimated_quantity,
                "unit": unit,
                "implied_rate": None,
                "current_rate": None,
                "variance_pct": None,
                "should_update": False,
                "recommendation": (
                    "No time entries logged against this work item — "
                    "cannot derive actuals."
                    if actual_hours <= 0
                    else "Work item has no quantity — cannot derive a rate."
                ),
            }

        implied_rate = estimated_quantity / actual_hours

        # Fetch the linked ProductivityRate (if any) so we can compare and
        # know whether we're eligible for auto-update.
        current_rate_info: dict[str, Any] | None = None
        if productivity_source_id:
            rate_row = self._read_tx_single(
                """
                MATCH (c:Company {id: $company_id})-[:HAS_PRODUCTIVITY]->(pr:ProductivityRate {id: $rate_id})
                RETURN pr {.*, company_id: c.id} AS rate
                """,
                {
                    "company_id": company_id,
                    "rate_id": productivity_source_id,
                },
            )
            if rate_row is not None:
                current_rate_info = rate_row["rate"]

        current_rate = (
            current_rate_info.get("rate") if current_rate_info else None
        )
        sample_size = (
            int(current_rate_info.get("sample_size") or 0)
            if current_rate_info else 0
        )

        variance_pct: float | None = None
        if current_rate and current_rate > 0:
            variance_pct = ((implied_rate - current_rate) / current_rate) * 100.0

        # Policy:
        #   variance > 10% and sample_size < 5 -> offer to update (ask)
        #   sample_size >= 5 -> auto-update (notify, not ask)
        #   otherwise -> no action needed
        should_update = False
        if variance_pct is not None and abs(variance_pct) > 10.0:
            should_update = True

        if current_rate is None:
            recommendation = (
                f"Actuals imply {implied_rate:.3f} {unit}/hr "
                f"for this work. No ProductivityRate was linked — "
                f"consider capturing this as a new rate."
            )
        elif variance_pct is None:
            recommendation = "Insufficient data to calculate variance."
        elif abs(variance_pct) <= 10.0:
            recommendation = (
                f"Actuals within 10% of library rate "
                f"({current_rate:.3f} vs implied {implied_rate:.3f}). "
                f"No update needed."
            )
        elif sample_size >= 5:
            recommendation = (
                f"Auto-updating — this is data point "
                f"#{sample_size + 1}. Library rate "
                f"{current_rate:.3f} {unit}/hr will be "
                f"weighted-averaged with actual {implied_rate:.3f}."
            )
        else:
            recommendation = (
                f"Variance {variance_pct:+.1f}% "
                f"(library {current_rate:.3f} vs actual "
                f"{implied_rate:.3f}). This is data point "
                f"#{sample_size + 1} — ask the contractor before updating."
            )

        return {
            "work_item_id": work_item_id,
            "work_item_description": result.get("work_item_description"),
            "productivity_rate_id": productivity_source_id,
            "estimated_hours": estimated_hours,
            "actual_hours": actual_hours,
            "estimated_quantity": estimated_quantity,
            "unit": unit,
            "implied_rate": implied_rate,
            "current_rate": current_rate,
            "current_sample_size": sample_size,
            "variance_pct": variance_pct,
            "should_update": should_update,
            "recommendation": recommendation,
        }

    def update_productivity_rate_from_actuals(
        self,
        actor: Actor,
        company_id: str,
        productivity_rate_id: str,
        new_data_point_rate: float,
        new_data_point_sample_size: int = 1,
    ) -> dict[str, Any]:
        """Update a ProductivityRate with a new actuals data point.

        Computes a weighted-average rate:
            new_rate = (old_rate * old_sample_size + new_rate * new_sample_size)
                      / (old_sample_size + new_sample_size)

        Increments ``sample_size`` accordingly and stamps ``last_derived_at``.
        Also flips ``source`` to ``derived_from_actuals`` so downstream
        readers know this rate has been refined from real data.

        Args:
            actor: The agent actor (provenance).
            company_id: Tenant scope.
            productivity_rate_id: The ProductivityRate to update.
            new_data_point_rate: The implied rate from actuals (output units
                per hour).
            new_data_point_sample_size: How many units of data the new point
                represents. Defaults to 1 (one completed work item).

        Returns:
            Dict with the updated rate, new sample_size, and the delta
            from the previous rate.
        """
        if new_data_point_rate <= 0 or new_data_point_sample_size <= 0:
            return {"error": "new_data_point_rate and sample_size must be positive"}

        now_iso = datetime.now(timezone.utc).isoformat()
        provenance = self._provenance_update(actor)

        # Read then write — we need the old values for the audit summary,
        # and writing the weighted average in Cypher keeps the update atomic.
        result = self._write_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:HAS_PRODUCTIVITY]->(pr:ProductivityRate {id: $rate_id})
            WITH pr,
                 coalesce(pr.rate, 0.0) AS old_rate,
                 coalesce(pr.sample_size, 0) AS old_sample_size
            WITH pr, old_rate, old_sample_size,
                 (old_sample_size + $new_sample_size) AS total_sample_size
            SET pr.rate = CASE
                    WHEN total_sample_size = 0 THEN $new_rate
                    ELSE ((old_rate * old_sample_size)
                          + ($new_rate * $new_sample_size)) / total_sample_size
                END,
                pr.sample_size = total_sample_size,
                pr.source = 'derived_from_actuals',
                pr.last_derived_at = $now_iso,
                pr += $provenance
            RETURN pr.id AS rate_id,
                   pr.description AS description,
                   pr.rate AS new_rate,
                   pr.sample_size AS new_sample_size,
                   pr.rate_unit AS rate_unit,
                   pr.time_unit AS time_unit,
                   old_rate AS old_rate,
                   old_sample_size AS old_sample_size
            """,
            {
                "company_id": company_id,
                "rate_id": productivity_rate_id,
                "new_rate": new_data_point_rate,
                "new_sample_size": new_data_point_sample_size,
                "now_iso": now_iso,
                "provenance": provenance,
            },
        )
        if result is None:
            return {"error": f"ProductivityRate {productivity_rate_id} not found"}

        old_rate = float(result.get("old_rate") or 0.0)
        new_rate = float(result.get("new_rate") or 0.0)
        delta_pct = (
            ((new_rate - old_rate) / old_rate * 100.0)
            if old_rate > 0 else None
        )

        self._emit_audit(
            event_type="entity.updated",
            entity_id=productivity_rate_id,
            entity_type="ProductivityRate",
            company_id=company_id,
            actor=actor,
            summary=(
                f"Rate '{result['description'][:60]}' updated from "
                f"{old_rate:.3f} -> {new_rate:.3f} "
                f"(sample size now {result['new_sample_size']})"
            ),
        )

        return {
            "productivity_rate_id": result["rate_id"],
            "description": result["description"],
            "old_rate": old_rate,
            "new_rate": new_rate,
            "old_sample_size": int(result.get("old_sample_size") or 0),
            "new_sample_size": int(result["new_sample_size"]),
            "delta_pct": delta_pct,
            "rate_unit": result.get("rate_unit"),
            "time_unit": result.get("time_unit"),
            "message": (
                f"Updated productivity rate — was "
                f"{old_rate:.3f}, now {new_rate:.3f} "
                f"(sample size {result['new_sample_size']})."
            ),
        }

    def update_material_price_from_purchase(
        self,
        actor: Actor,
        company_id: str,
        description: str,
        unit_cost_cents: int,
        unit: str = "EA",
        supplier_name: str = "",
        location: str = "",
        source_url: str = "",
    ) -> dict[str, Any]:
        """Record an actual material purchase price.

        If a MaterialCatalogEntry exists that matches description + supplier
        + location (case-insensitive on description, exact on the rest),
        update its ``unit_cost_cents`` and set ``last_verified_at`` to now.
        Otherwise create a new entry.

        Args:
            actor: The agent actor (provenance).
            company_id: Tenant scope.
            description: What the material is (matched case-insensitively).
            unit_cost_cents: The price paid, in cents.
            unit: Unit of measurement (EA, LF, SF, ...).
            supplier_name: Supplier the purchase was from (exact match).
            location: City/region the price applies in (exact match).
            source_url: Optional receipt/invoice URL.

        Returns:
            Dict with the entry id, whether it was created or updated,
            and the new price.
        """
        now_iso = datetime.now(timezone.utc).isoformat()
        needle = description.lower().strip()
        supplier_for_match = supplier_name or None
        location_for_match = location or None

        # Try to find an existing entry that matches on description +
        # supplier + location. ``null`` values are treated as matches to
        # prevent duplicate rows when suppliers/locations aren't supplied.
        existing = self._read_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:HAS_CATALOG_ENTRY]->(mce:MaterialCatalogEntry)
            WHERE toLower(mce.description) = $needle
              AND coalesce(mce.supplier_name, '') = coalesce($supplier, '')
              AND coalesce(mce.location, '') = coalesce($location, '')
            RETURN mce {.*, company_id: c.id} AS entry
            ORDER BY mce.fetched_at DESC
            LIMIT 1
            """,
            {
                "company_id": company_id,
                "needle": needle,
                "supplier": supplier_for_match,
                "location": location_for_match,
            },
        )

        if existing is not None:
            entry = existing["entry"]
            entry_id = entry["id"]
            provenance = self._provenance_update(actor)
            updated = self._write_tx_single(
                """
                MATCH (c:Company {id: $company_id})-[:HAS_CATALOG_ENTRY]->(mce:MaterialCatalogEntry {id: $entry_id})
                SET mce.unit_cost_cents = $unit_cost_cents,
                    mce.unit = coalesce($unit, mce.unit),
                    mce.source_url = coalesce($source_url, mce.source_url),
                    mce.last_verified_at = $now_iso,
                    mce.fetched_at = $now_iso,
                    mce += $provenance
                RETURN mce.id AS entry_id,
                       mce.description AS description,
                       mce.unit_cost_cents AS unit_cost_cents,
                       mce.unit AS unit,
                       mce.supplier_name AS supplier_name,
                       mce.location AS location
                """,
                {
                    "company_id": company_id,
                    "entry_id": entry_id,
                    "unit_cost_cents": unit_cost_cents,
                    "unit": unit or None,
                    "source_url": source_url or None,
                    "now_iso": now_iso,
                    "provenance": provenance,
                },
            )
            if updated is None:
                return {"error": f"Catalog entry {entry_id} not found"}

            self._emit_audit(
                event_type="entity.updated",
                entity_id=entry_id,
                entity_type="MaterialCatalogEntry",
                company_id=company_id,
                actor=actor,
                summary=(
                    f"Purchase price updated — "
                    f"{updated['description'][:60]} now "
                    f"${unit_cost_cents / 100:,.2f}/{updated.get('unit') or 'unit'}"
                ),
            )

            return {
                "entry_id": updated["entry_id"],
                "description": updated["description"],
                "unit_cost_cents": updated["unit_cost_cents"],
                "unit": updated["unit"],
                "supplier_name": updated.get("supplier_name"),
                "location": updated.get("location"),
                "created": False,
                "message": (
                    f"Updated price for {updated['description'][:60]} "
                    f"to ${unit_cost_cents / 100:,.2f}/{updated.get('unit') or 'unit'}."
                ),
            }

        # Create a new MaterialCatalogEntry — inlined like capture_material_price
        # so agent provenance is preserved.
        mce_id = self._generate_id("mce")
        provenance = self._provenance_create(actor)
        props: dict[str, Any] = {
            "id": mce_id,
            "description": description,
            "product_code": None,
            "unit": unit,
            "unit_cost_cents": unit_cost_cents,
            "supplier_name": supplier_for_match,
            "source_url": source_url or None,
            "location": location_for_match,
            "fetched_at": now_iso,
            "last_verified_at": now_iso,
            **provenance,
        }

        created = self._write_tx_single(
            """
            MATCH (c:Company {id: $company_id})
            CREATE (mce:MaterialCatalogEntry $props)
            CREATE (c)-[:HAS_CATALOG_ENTRY]->(mce)
            RETURN mce.id AS entry_id,
                   mce.description AS description,
                   mce.unit_cost_cents AS unit_cost_cents,
                   mce.unit AS unit,
                   mce.supplier_name AS supplier_name,
                   mce.location AS location
            """,
            {"company_id": company_id, "props": props},
        )
        if created is None:
            return {"error": f"Company {company_id} not found"}

        self._emit_audit(
            event_type="entity.created",
            entity_id=mce_id,
            entity_type="MaterialCatalogEntry",
            company_id=company_id,
            actor=actor,
            summary=(
                f"Captured purchase — {description[:60]} at "
                f"${unit_cost_cents / 100:,.2f}/{unit}"
            ),
        )

        return {
            "entry_id": created["entry_id"],
            "description": created["description"],
            "unit_cost_cents": created["unit_cost_cents"],
            "unit": created["unit"],
            "supplier_name": created.get("supplier_name"),
            "location": created.get("location"),
            "created": True,
            "message": (
                f"Captured new material price — {description[:60]} at "
                f"${unit_cost_cents / 100:,.2f}/{unit}."
            ),
        }

    def list_contractor_knowledge(
        self,
        actor: Actor,
        company_id: str,
    ) -> dict[str, Any]:
        """Summary read for the Knowledge page.

        Returns everything the contractor has accumulated in their library:
        resource rates, productivity rates (with a confidence score derived
        from sample_size), insights (sorted by confidence DESC), and counts
        for material catalog entries and completed projects.

        ProductivityRate confidence is derived:
          sample_size 0 -> 0.3 (no data)
          sample_size 1-2 -> 0.5
          sample_size 3-4 -> 0.7
          sample_size 5+ -> 0.9

        Args:
            actor: The agent actor.
            company_id: Tenant scope.

        Returns:
            Dict with the four lists/counts plus ``total_completed_projects``.
        """
        resource_rates = self._read_tx(
            """
            MATCH (c:Company {id: $company_id})-[:HAS_RATE]->(rr:ResourceRate)
            WHERE coalesce(rr.active, true) = true
            RETURN rr {.*, company_id: c.id} AS rate
            ORDER BY rr.description
            """,
            {"company_id": company_id},
        )

        productivity_rows = self._read_tx(
            """
            MATCH (c:Company {id: $company_id})-[:HAS_PRODUCTIVITY]->(pr:ProductivityRate)
            WHERE coalesce(pr.active, true) = true
            RETURN pr {.*, company_id: c.id} AS rate
            ORDER BY pr.description
            """,
            {"company_id": company_id},
        )
        productivity_rates: list[dict[str, Any]] = []
        for row in productivity_rows:
            rate = dict(row["rate"])
            sample_size = int(rate.get("sample_size") or 0)
            if sample_size >= 5:
                confidence = 0.9
            elif sample_size >= 3:
                confidence = 0.7
            elif sample_size >= 1:
                confidence = 0.5
            else:
                confidence = 0.3
            rate["confidence"] = confidence
            productivity_rates.append(rate)

        insight_rows = self._read_tx(
            """
            MATCH (c:Company {id: $company_id})-[:HAS_INSIGHT]->(ins:Insight)
            RETURN ins {.*, company_id: c.id} AS insight
            ORDER BY ins.confidence DESC, ins.validation_count DESC
            """,
            {"company_id": company_id},
        )
        insights = [r["insight"] for r in insight_rows]

        counts = self._read_tx_single(
            """
            MATCH (c:Company {id: $company_id})
            OPTIONAL MATCH (c)-[:HAS_CATALOG_ENTRY]->(mce:MaterialCatalogEntry)
            WITH c, count(DISTINCT mce) AS mce_count
            OPTIONAL MATCH (c)-[:OWNS_PROJECT]->(p:Project)
            WHERE coalesce(p.deleted, false) = false
              AND p.state IN ['completed', 'closed']
            RETURN mce_count,
                   count(DISTINCT p) AS completed_count
            """,
            {"company_id": company_id},
        ) or {"mce_count": 0, "completed_count": 0}

        return {
            "resource_rates": [dict(r["rate"]) for r in resource_rates],
            "productivity_rates": productivity_rates,
            "insights": insights,
            "material_catalog_entries_count": int(counts.get("mce_count") or 0),
            "total_completed_projects": int(counts.get("completed_count") or 0),
        }

    # ------------------------------------------------------------------
    # Layer 4 (extended): contractor-confirmation knowledge tools
    # ------------------------------------------------------------------

    def offer_insight_capture(
        self,
        actor: Actor,
        company_id: str,
        project_id: str,
        statement: str,
        scope: str,
        scope_value: str,
        adjustment_type: str,
        adjustment_value: float | None = None,
        confidence: float = 0.5,
    ) -> dict[str, Any]:
        """Propose an Insight for the contractor to confirm before saving.

        This is the read-only "ask before remembering" step. The contractor
        gave reasoning during a correction (e.g. "I add 15% for low ceilings")
        and we want them to decide whether the pattern should be reused.

        Does NOT write anything — the agent should follow up with the
        contractor and call ``create_insight`` if they accept.

        Args:
            actor: The agent actor.
            company_id: Tenant scope.
            project_id: Project the reasoning came from (for source_context).
            statement: Human-readable insight text.
            scope: 'work_type', 'trade', 'jurisdiction', 'client_type',
                'project_size', or 'other'.
            scope_value: Concrete value for the scope.
            adjustment_type: 'productivity_multiplier', 'rate_adjustment',
                or 'qualitative'.
            adjustment_value: Numeric adjustment (e.g. 1.15 for +15%).
            confidence: Initial confidence 0-1, default 0.5.

        Returns:
            Dict with the proposed insight, a prompt message, and
            ``status: 'awaiting_confirmation'``.
        """
        proposed = {
            "scope": scope,
            "scope_value": scope_value,
            "statement": statement,
            "adjustment_type": adjustment_type,
            "adjustment_value": adjustment_value,
            "confidence": confidence,
            "source_context": (
                f"proposed from project {project_id}" if project_id else None
            ),
        }
        # Build a friendly preview of the adjustment
        if adjustment_type == "productivity_multiplier" and adjustment_value:
            pct = (float(adjustment_value) - 1.0) * 100.0
            sign = "+" if pct >= 0 else ""
            preview = f"{sign}{pct:.0f}% productivity adjustment"
        elif adjustment_type == "rate_adjustment" and adjustment_value:
            preview = f"rate adjustment of {adjustment_value}"
        else:
            preview = adjustment_type

        message = (
            f"Capture this pattern for future quotes? [yes/no/edit]\n"
            f"  - Scope: {scope}={scope_value}\n"
            f"  - Statement: {statement}\n"
            f"  - Adjustment: {preview}"
        )
        return {
            "proposed_insight": proposed,
            "message": message,
            "status": "awaiting_confirmation",
        }

    def find_applicable_insights(
        self,
        actor: Actor,
        company_id: str,
        project_id: str,
        work_type: str | None = None,
        trade: str | None = None,
        surface_threshold: float = 0.6,
    ) -> dict[str, Any]:
        """Find Insights for the current work and split into surface vs silent.

        Wraps ``InsightService.find_applicable`` with surfacing logic:
        - ``surface_to_user`` are insights the agent should mention (confidence
          >= surface_threshold, or any time multiple insights agree).
        - ``apply_silently`` are insights that still apply but the agent
          should just note in source_reasoning rather than interrupt.
        - ``combined_productivity_adjustment`` is the multiplicative product
          of every applicable ``productivity_multiplier`` insight.
        - ``reasoning_chain`` narrates the math.
        - ``combined_confidence`` is the lowest confidence of the inputs that
          contributed to the combination.

        Deprecated/inactive insights are filtered out so they never surface.

        Args:
            actor: The agent actor.
            company_id: Tenant scope.
            project_id: Project context — used to resolve jurisdiction,
                client_type, project_size for richer scope matching.
            work_type: Optional work_type tag to match.
            trade: Optional trade to match.
            surface_threshold: Confidence at/above which to surface to user.
                Defaults to 0.6.

        Returns:
            Dict with ``applicable``, ``surface_to_user``, ``apply_silently``,
            ``combined_productivity_adjustment``, ``combined_confidence``,
            and ``reasoning_chain``.
        """
        # Pull scopes from the project so we can match more dimensions
        proj = self._read_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
            WHERE coalesce(p.deleted, false) = false
            RETURN p.us_state AS us_state,
                   p.project_type AS project_type
            """,
            {"company_id": company_id, "project_id": project_id},
        )
        jurisdiction = proj.get("us_state") if proj else None
        client_type = proj.get("project_type") if proj else None

        from app.services.insight_service import InsightService

        insight_svc = InsightService(self.driver)
        raw = insight_svc.find_applicable(
            company_id=company_id,
            work_type=work_type,
            trade=trade,
            jurisdiction=jurisdiction,
            client_type=client_type,
            limit=25,
        )

        # Filter out deprecated/inactive
        applicable: list[dict[str, Any]] = []
        for ins in raw:
            if ins.get("deprecated", False):
                continue
            if ins.get("active") is False:
                continue
            applicable.append(ins)

        # Group by scope_value to detect "multiple agreeing" insights
        by_scope: dict[str, list[dict[str, Any]]] = {}
        for ins in applicable:
            key = f"{ins.get('scope')}={ins.get('scope_value')}"
            by_scope.setdefault(key, []).append(ins)

        surface_to_user: list[dict[str, Any]] = []
        apply_silently: list[dict[str, Any]] = []
        for ins in applicable:
            confidence = float(ins.get("confidence") or 0.0)
            key = f"{ins.get('scope')}={ins.get('scope_value')}"
            multiple_agree = len(by_scope[key]) > 1
            if confidence >= surface_threshold or multiple_agree:
                surface_to_user.append(ins)
            else:
                apply_silently.append(ins)

        # Multiplicative combination of productivity_multiplier insights
        combined = 1.0
        reasoning_chain: list[str] = []
        contributing_confidences: list[float] = []
        applied_ids: list[str] = []
        for ins in applicable:
            if ins.get("adjustment_type") != "productivity_multiplier":
                continue
            adjustment = ins.get("adjustment_value")
            if adjustment is None or adjustment <= 0:
                continue
            combined *= float(adjustment)
            applied_ids.append(ins.get("id"))
            contributing_confidences.append(float(ins.get("confidence") or 0.0))
            pct = (float(adjustment) - 1.0) * 100.0
            sign = "+" if pct >= 0 else ""
            label = ins.get("scope_value") or ins.get("scope") or "scope"
            reasoning_chain.append(f"{label} {sign}{pct:.0f}%")

        if reasoning_chain:
            reasoning_chain.append(f"combined: {combined:.4f}")
        combined_confidence = (
            min(contributing_confidences) if contributing_confidences else None
        )

        return {
            "applicable": applicable,
            "surface_to_user": surface_to_user,
            "apply_silently": apply_silently,
            "combined_productivity_adjustment": combined,
            "combined_productivity_insight_ids": applied_ids,
            "combined_confidence": combined_confidence,
            "reasoning_chain": reasoning_chain,
        }

    def reject_insight(
        self,
        actor: Actor,
        company_id: str,
        insight_id: str,
        reason: str,
    ) -> dict[str, Any]:
        """Record contractor rejection of an Insight.

        Decreases confidence by 0.10, logs the reason in ``source_context``.
        If confidence drops below 0.2, the insight is marked
        ``active = false`` so future surfacing skips it. Wraps
        ``InsightService.decrement_validation``.

        The contractor always wins. This is the simpler counterpart to
        ``correct_insight`` — use this when the contractor explicitly
        rejects an applied insight on this quote.

        Args:
            actor: The agent actor (provenance).
            company_id: Tenant scope.
            insight_id: The Insight being rejected.
            reason: Why the contractor pushed back (required).

        Returns:
            Dict with the new confidence, deactivation flag, and message.
        """
        if not reason:
            return {"error": "reason is required"}

        from app.exceptions import InsightNotFoundError
        from app.services.insight_service import InsightService

        insight_svc = InsightService(self.driver)
        # decrement_validation expects a Clerk user_id. The actor.id is
        # the agent_id when actor.type == 'agent'. For provenance on the
        # update we want the agent identity, which is what InsightService
        # uses in _provenance_update via Actor.human(user_id). To preserve
        # agent provenance correctly we instead inline the write here.
        now_iso = datetime.now(timezone.utc).isoformat()
        rejection_line = f"[{now_iso}] rejected: {reason}"
        provenance = self._provenance_update(actor)

        result = self._write_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:HAS_INSIGHT]->(ins:Insight {id: $insight_id})
            SET ins.confidence = CASE
                    WHEN coalesce(ins.confidence, 0.5) - 0.10 < 0.0 THEN 0.0
                    ELSE coalesce(ins.confidence, 0.5) - 0.10
                END,
                ins.source_context = CASE
                    WHEN ins.source_context IS NULL OR ins.source_context = ''
                        THEN $rejection_line
                    ELSE ins.source_context + '\n' + $rejection_line
                END,
                ins += $provenance
            WITH ins
            SET ins.active = (ins.confidence >= 0.2),
                ins.deprecated = (ins.confidence < 0.2)
            RETURN ins.id AS insight_id,
                   ins.statement AS statement,
                   ins.confidence AS confidence,
                   (ins.confidence < 0.2) AS deactivated
            """,
            {
                "company_id": company_id,
                "insight_id": insight_id,
                "rejection_line": rejection_line,
                "provenance": provenance,
            },
        )
        if result is None:
            return {"error": f"Insight {insight_id} not found"}

        deactivated = bool(result["deactivated"])
        self._emit_audit(
            event_type="entity.updated",
            entity_id=insight_id,
            entity_type="Insight",
            company_id=company_id,
            actor=actor,
            summary=(
                f"Rejected insight — confidence now "
                f"{result['confidence']:.2f}"
                + (" (deactivated)" if deactivated else "")
                + f" — {reason[:80]}"
            ),
        )

        message_parts = [
            f"Rejected. Confidence now {result['confidence']:.2f}."
        ]
        if deactivated:
            message_parts.append(
                "Insight deactivated — won't surface on future quotes."
            )
        return {
            "insight_id": result["insight_id"],
            "statement": result["statement"],
            "confidence": result["confidence"],
            "deactivated": deactivated,
            "message": " ".join(message_parts),
        }

    def derive_productivity_from_completion(
        self,
        actor: Actor,
        company_id: str,
        project_id: str,
    ) -> dict[str, Any]:
        """Compare estimated vs actual hours across a completed project.

        For each WorkItem on the project:
        1. Sum estimated hours from the Labour children.
        2. Sum actual hours from TimeEntry children
           (``hours_regular + hours_overtime``).
        3. If the variance vs. the linked ProductivityRate exceeds 10%,
           propose a refinement.

        Returns the proposed updates plus a flag indicating whether
        contractor confirmation is required (False once the rate has 5+
        prior data points; True otherwise).

        Args:
            actor: The agent actor.
            company_id: Tenant scope.
            project_id: The project to analyse.

        Returns:
            Dict with ``proposed_updates`` (list) and ``needs_confirmation``.
        """
        rows = self._read_tx(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
                  -[:HAS_WORK_ITEM]->(wi:WorkItem)
            WHERE coalesce(wi.deleted, false) = false
            OPTIONAL MATCH (wi)-[:HAS_LABOUR]->(lab:Labour)
            WITH p, wi,
                 coalesce(sum(lab.hours), 0.0) AS estimated_hours,
                 [lab_id IN collect(DISTINCT lab.productivity_source_id) WHERE lab_id IS NOT NULL][0] AS productivity_source_id
            OPTIONAL MATCH (wi)-[:HAS_TIME_ENTRY]->(te:TimeEntry)
            WHERE coalesce(te.deleted, false) = false
            WITH p, wi, estimated_hours, productivity_source_id,
                 coalesce(sum(coalesce(te.hours_regular, 0.0) + coalesce(te.hours_overtime, 0.0)), 0.0) AS actual_hours
            RETURN wi.id AS work_item_id,
                   wi.description AS work_item_description,
                   wi.quantity AS estimated_quantity,
                   wi.unit AS unit,
                   estimated_hours,
                   actual_hours,
                   productivity_source_id
            """,
            {"company_id": company_id, "project_id": project_id},
        )

        # Resolve project name for the audit/return summary
        proj = self._read_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
            RETURN p.name AS name
            """,
            {"company_id": company_id, "project_id": project_id},
        )
        project_name = proj.get("name") if proj else project_id

        # Group work items by ProductivityRate so multiple WorkItems pointing
        # at the same rate produce a single proposed update.
        groups: dict[str, dict[str, Any]] = {}
        skipped: list[dict[str, Any]] = []

        for row in rows:
            wi_id = row["work_item_id"]
            estimated_hours = float(row["estimated_hours"] or 0.0)
            actual_hours = float(row["actual_hours"] or 0.0)
            estimated_quantity = float(row["estimated_quantity"] or 0.0)
            productivity_source_id = row["productivity_source_id"]

            if not productivity_source_id:
                skipped.append({
                    "work_item_id": wi_id,
                    "reason": "no productivity rate linked",
                })
                continue
            if actual_hours <= 0 or estimated_quantity <= 0:
                skipped.append({
                    "work_item_id": wi_id,
                    "reason": (
                        "no time entries" if actual_hours <= 0
                        else "no quantity"
                    ),
                })
                continue

            implied_rate = estimated_quantity / actual_hours
            grp = groups.setdefault(productivity_source_id, {
                "implied_rates": [],
                "work_item_ids": [],
                "total_estimated_hours": 0.0,
                "total_actual_hours": 0.0,
            })
            grp["implied_rates"].append(implied_rate)
            grp["work_item_ids"].append(wi_id)
            grp["total_estimated_hours"] += estimated_hours
            grp["total_actual_hours"] += actual_hours

        # Fetch the current ProductivityRate rows for any rate ID we matched
        rate_ids = list(groups.keys())
        rate_lookup: dict[str, dict[str, Any]] = {}
        if rate_ids:
            rate_rows = self._read_tx(
                """
                MATCH (c:Company {id: $company_id})-[:HAS_PRODUCTIVITY]->(pr:ProductivityRate)
                WHERE pr.id IN $rate_ids
                RETURN pr {.*, company_id: c.id} AS rate
                """,
                {"company_id": company_id, "rate_ids": rate_ids},
            )
            for r in rate_rows:
                rate = r["rate"]
                rate_lookup[rate["id"]] = rate

        proposed_updates: list[dict[str, Any]] = []
        max_sample_size = 0
        for rate_id, grp in groups.items():
            current = rate_lookup.get(rate_id)
            if current is None:
                continue
            current_rate = float(current.get("rate") or 0.0)
            if current_rate <= 0:
                continue

            implied_rates = grp["implied_rates"]
            avg_implied = sum(implied_rates) / len(implied_rates)
            variance_pct = ((avg_implied - current_rate) / current_rate) * 100.0
            if abs(variance_pct) <= 10.0:
                continue

            sample_size = int(current.get("sample_size") or 0)
            max_sample_size = max(max_sample_size, sample_size)
            sign = "+" if variance_pct >= 0 else ""
            reasoning = (
                f"{project_name} actuals "
                f"{'over' if variance_pct < 0 else 'under'} "
                f"library by {abs(variance_pct):.0f}% across "
                f"{len(implied_rates)} work item(s)"
            )
            proposed_updates.append({
                "productivity_rate_id": rate_id,
                "description": current.get("description"),
                "current_rate": current_rate,
                "proposed_rate": round(avg_implied, 4),
                "rate_unit": current.get("rate_unit"),
                "time_unit": current.get("time_unit"),
                "variance_pct": round(variance_pct, 2),
                "sample_size": sample_size,
                "sample_size_change": f"+{len(implied_rates)}",
                "work_items_analyzed": len(implied_rates),
                "work_item_ids": grp["work_item_ids"],
                "reasoning": reasoning,
                "variance_label": f"{sign}{variance_pct:.0f}%",
            })

        # If every rate involved already has 5+ data points, we can
        # auto-update without asking. Otherwise ask.
        needs_confirmation = max_sample_size < 5

        return {
            "project_id": project_id,
            "project_name": project_name,
            "proposed_updates": proposed_updates,
            "needs_confirmation": needs_confirmation,
            "skipped_work_items": skipped,
        }

    def accept_productivity_update(
        self,
        actor: Actor,
        company_id: str,
        productivity_rate_id: str,
        new_rate: float,
    ) -> dict[str, Any]:
        """Apply a proposed productivity update directly.

        Sets the rate to ``new_rate`` (no weighted averaging — the caller
        already decided what the new rate should be), increments
        ``sample_size`` by 1, sets ``last_derived_at`` to now, and stamps
        ``source = 'derived_from_actuals'``.

        Use this when the contractor confirmed a proposed update from
        ``derive_productivity_from_completion``. For the weighted-average
        variant, use ``update_productivity_rate_from_actuals`` instead.

        Args:
            actor: The agent actor (provenance).
            company_id: Tenant scope.
            productivity_rate_id: The ProductivityRate to update.
            new_rate: The accepted new rate value.

        Returns:
            Dict with the old/new rate, new sample_size, and a message.
        """
        if new_rate <= 0:
            return {"error": "new_rate must be positive"}

        now_iso = datetime.now(timezone.utc).isoformat()
        provenance = self._provenance_update(actor)

        result = self._write_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:HAS_PRODUCTIVITY]->(pr:ProductivityRate {id: $rate_id})
            WITH pr,
                 coalesce(pr.rate, 0.0) AS old_rate,
                 coalesce(pr.sample_size, 0) AS old_sample_size
            SET pr.rate = $new_rate,
                pr.sample_size = old_sample_size + 1,
                pr.source = 'derived_from_actuals',
                pr.last_derived_at = $now_iso,
                pr += $provenance
            RETURN pr.id AS rate_id,
                   pr.description AS description,
                   pr.rate AS new_rate,
                   pr.sample_size AS new_sample_size,
                   pr.rate_unit AS rate_unit,
                   pr.time_unit AS time_unit,
                   old_rate AS old_rate,
                   old_sample_size AS old_sample_size
            """,
            {
                "company_id": company_id,
                "rate_id": productivity_rate_id,
                "new_rate": new_rate,
                "now_iso": now_iso,
                "provenance": provenance,
            },
        )
        if result is None:
            return {"error": f"ProductivityRate {productivity_rate_id} not found"}

        old_rate = float(result.get("old_rate") or 0.0)
        new_rate_value = float(result.get("new_rate") or 0.0)
        delta_pct = (
            ((new_rate_value - old_rate) / old_rate * 100.0)
            if old_rate > 0 else None
        )

        self._emit_audit(
            event_type="entity.updated",
            entity_id=productivity_rate_id,
            entity_type="ProductivityRate",
            company_id=company_id,
            actor=actor,
            summary=(
                f"Productivity '{(result['description'] or '')[:60]}' "
                f"accepted update {old_rate:.3f} -> "
                f"{new_rate_value:.3f} (sample size now "
                f"{result['new_sample_size']})"
            ),
        )

        return {
            "productivity_rate_id": result["rate_id"],
            "description": result["description"],
            "old_rate": old_rate,
            "new_rate": new_rate_value,
            "old_sample_size": int(result.get("old_sample_size") or 0),
            "new_sample_size": int(result["new_sample_size"]),
            "delta_pct": delta_pct,
            "rate_unit": result.get("rate_unit"),
            "time_unit": result.get("time_unit"),
            "message": (
                f"Updated productivity rate — was "
                f"{old_rate:.3f}, now {new_rate_value:.3f} "
                f"(sample size {result['new_sample_size']})."
            ),
        }

    def update_rate_from_purchase(
        self,
        actor: Actor,
        company_id: str,
        material_catalog_entry_id: str,
        new_price_cents: int,
        source_url: str = "",
    ) -> dict[str, Any]:
        """Update an existing MaterialCatalogEntry with a fresh purchase price.

        Avoids creating duplicate catalog entries — call this when the
        contractor captures a new price for a material we already track.
        Sets ``last_verified_at`` and ``fetched_at`` to now so future
        staleness checks know the price is fresh.

        For the create-if-missing variant, use
        ``update_material_price_from_purchase`` instead.

        Args:
            actor: The agent actor (provenance).
            company_id: Tenant scope.
            material_catalog_entry_id: The MaterialCatalogEntry to update.
            new_price_cents: New price in cents.
            source_url: Optional receipt/invoice URL.

        Returns:
            Dict with the updated entry.
        """
        if new_price_cents <= 0:
            return {"error": "new_price_cents must be positive"}

        now_iso = datetime.now(timezone.utc).isoformat()
        provenance = self._provenance_update(actor)

        result = self._write_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:HAS_CATALOG_ENTRY]->(mce:MaterialCatalogEntry {id: $entry_id})
            WITH mce,
                 coalesce(mce.unit_cost_cents, 0) AS old_price
            SET mce.unit_cost_cents = $new_price_cents,
                mce.source_url = coalesce($source_url, mce.source_url),
                mce.last_verified_at = $now_iso,
                mce.fetched_at = $now_iso,
                mce += $provenance
            RETURN mce.id AS entry_id,
                   mce.description AS description,
                   mce.unit_cost_cents AS unit_cost_cents,
                   mce.unit AS unit,
                   mce.supplier_name AS supplier_name,
                   mce.location AS location,
                   old_price AS old_price
            """,
            {
                "company_id": company_id,
                "entry_id": material_catalog_entry_id,
                "new_price_cents": new_price_cents,
                "source_url": source_url or None,
                "now_iso": now_iso,
                "provenance": provenance,
            },
        )
        if result is None:
            return {
                "error": (
                    f"MaterialCatalogEntry {material_catalog_entry_id} "
                    f"not found"
                ),
            }

        old_price = int(result.get("old_price") or 0)
        new_price = int(result.get("unit_cost_cents") or 0)
        delta_pct = (
            ((new_price - old_price) / old_price * 100.0)
            if old_price > 0 else None
        )

        self._emit_audit(
            event_type="entity.updated",
            entity_id=material_catalog_entry_id,
            entity_type="MaterialCatalogEntry",
            company_id=company_id,
            actor=actor,
            summary=(
                f"Catalog entry '{(result['description'] or '')[:60]}' "
                f"price updated {old_price / 100:,.2f} -> "
                f"{new_price / 100:,.2f}"
            ),
        )

        return {
            "entry_id": result["entry_id"],
            "description": result["description"],
            "unit_cost_cents": new_price,
            "old_unit_cost_cents": old_price,
            "delta_pct": delta_pct,
            "unit": result["unit"],
            "supplier_name": result.get("supplier_name"),
            "location": result.get("location"),
            "message": (
                f"Updated price for {(result['description'] or '')[:60]} "
                f"to ${new_price / 100:,.2f}/{result.get('unit') or 'unit'}."
            ),
        }

    # ------------------------------------------------------------------
    # Tool 23: add_item_to_work_item (low-risk write)
    # ------------------------------------------------------------------

    def create_item(
        self,
        actor: Actor,
        company_id: str,
        project_id: str,
        work_item_id: str,
        description: str,
        quantity: float,
        unit_cost_cents: int,
        unit: str = "EA",
        product: str = "",
        notes: str = "",
        price_source_id: str | None = None,
        price_source_type: str | None = None,
        source_reasoning: str = "",
        source_url: str | None = None,
    ) -> dict[str, Any]:
        """Create an Item child node on a work item (material, equipment, fixture).

        Source-cascade provenance is strongly recommended on every create:

        * ``price_source_id`` — ID of the MaterialCatalogEntry or past Item
          the price came from (None for contractor-stated prices).
        * ``price_source_type`` — one of ``material_catalog``,
          ``purchase_history``, ``contractor_stated``, ``estimate``.
        * ``source_reasoning`` — human-readable explanation
          (e.g. "From your Buckhead job, Mar 2026" or "Graybar Atlanta, fetched today").
        * ``source_url`` — the URL the price was looked up from, if any.

        ``price_fetched_at`` is set to now on every create so staleness can
        be measured later.

        Args:
            actor: The agent actor.
            company_id: Tenant scope.
            project_id: The parent project.
            work_item_id: The work item.
            description: What the item is (e.g. 'Floor box (Arlington FLBR5420)').
            quantity: Number of units.
            unit_cost_cents: Cost per unit in cents.
            unit: Unit of measurement (EA, LF, SF, etc.).
            product: Specific product name/model.
            notes: Additional notes.
            price_source_id: MaterialCatalogEntry / past Item ID (optional).
            price_source_type: Where the price came from (optional but recommended).
            source_reasoning: Human-readable sourcing explanation (optional).
            source_url: Source URL (optional).

        Returns:
            Dict with the created item data.
        """
        item_id = self._generate_id("item")
        total_cents = round(quantity * unit_cost_cents)
        provenance = self._provenance_create(actor)
        fetched_at = datetime.now(timezone.utc).isoformat()

        props: dict[str, Any] = {
            "id": item_id,
            "description": description,
            "product": product,
            "quantity": quantity,
            "unit": unit,
            "unit_cost_cents": unit_cost_cents,
            "total_cents": total_cents,
            "notes": notes,
            # Source cascade provenance
            "price_source_id": price_source_id,
            "price_source_type": price_source_type,
            "source_reasoning": source_reasoning or None,
            "source_url": source_url,
            "price_fetched_at": fetched_at,
            **provenance,
        }

        result = self._write_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
                  -[:HAS_WORK_ITEM]->(wi:WorkItem {id: $work_item_id})
            WHERE wi.deleted = false
            CREATE (item:Item $props)
            CREATE (wi)-[:HAS_ITEM]->(item)
            RETURN item.id AS item_id, item.description AS description,
                   item.quantity AS quantity, item.unit AS unit,
                   item.unit_cost_cents AS unit_cost_cents,
                   item.total_cents AS total_cents,
                   item.price_source_type AS price_source_type,
                   item.source_reasoning AS source_reasoning,
                   wi.id AS work_item_id, wi.description AS work_item_description
            """,
            {
                "company_id": company_id,
                "project_id": project_id,
                "work_item_id": work_item_id,
                "props": props,
            },
        )

        if result is None:
            return {"error": f"Work item {work_item_id} not found"}

        return dict(result)

    def create_labour(
        self,
        actor: Actor,
        company_id: str,
        project_id: str,
        work_item_id: str,
        task: str,
        rate_cents: int,
        hours: float,
        notes: str = "",
        rate_source_id: str | None = None,
        rate_source_type: str | None = None,
        productivity_source_id: str | None = None,
        productivity_source_type: str | None = None,
        source_reasoning: str = "",
    ) -> dict[str, Any]:
        """Create a Labour child node on a work item.

        Source-cascade provenance is strongly recommended on every create:

        * ``rate_source_id`` — ID of the ResourceRate the rate came from.
          Required when ``rate_source_type`` is ``resource_rate``.
        * ``rate_source_type`` — one of ``resource_rate``, ``contractor_stated``,
          ``inherited_from_similar_project``.
        * ``productivity_source_id`` — ID of the ProductivityRate, Insight,
          or IndustryProductivityBaseline the hours were derived from.
        * ``productivity_source_type`` — one of ``productivity_rate``,
          ``insight``, ``industry_baseline``, ``contractor_estimate``.
        * ``source_reasoning`` — human-readable explanation
          (e.g. "Based on your Peachtree job: 0.38 hrs per receptacle").

        Args:
            actor: The agent actor.
            company_id: Tenant scope.
            project_id: The parent project.
            work_item_id: The work item.
            task: What the labour task is (e.g. 'Install receptacles').
            rate_cents: Hourly rate in cents.
            hours: Estimated hours.
            notes: Additional notes.
            rate_source_id: ResourceRate ID (optional).
            rate_source_type: Where the rate came from (optional, recommended).
            productivity_source_id: ProductivityRate / Insight / baseline ID (optional).
            productivity_source_type: Where the productivity came from (optional, recommended).
            source_reasoning: Human-readable sourcing explanation (optional).

        Returns:
            Dict with the created labour data.
        """
        # If the source type requires an ID, enforce it so the agent cannot
        # claim library provenance without citing the source.
        if rate_source_type == "resource_rate" and not rate_source_id:
            return {
                "error": (
                    "rate_source_type='resource_rate' requires rate_source_id. "
                    "Use get_rate_suggestion to find one."
                )
            }

        lab_id = self._generate_id("lab")
        cost_cents = round(rate_cents * hours)
        provenance = self._provenance_create(actor)

        props: dict[str, Any] = {
            "id": lab_id,
            "task": task,
            "rate_cents": rate_cents,
            "hours": hours,
            "cost_cents": cost_cents,
            "notes": notes,
            # Source cascade provenance
            "rate_source_id": rate_source_id,
            "rate_source_type": rate_source_type,
            "productivity_source_id": productivity_source_id,
            "productivity_source_type": productivity_source_type,
            "source_reasoning": source_reasoning or None,
            **provenance,
        }

        result = self._write_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
                  -[:HAS_WORK_ITEM]->(wi:WorkItem {id: $work_item_id})
            WHERE wi.deleted = false
            CREATE (lab:Labour $props)
            CREATE (wi)-[:HAS_LABOUR]->(lab)
            RETURN lab.id AS labour_id, lab.task AS task,
                   lab.rate_cents AS rate_cents, lab.hours AS hours,
                   lab.cost_cents AS cost_cents,
                   lab.rate_source_type AS rate_source_type,
                   lab.productivity_source_type AS productivity_source_type,
                   lab.source_reasoning AS source_reasoning,
                   wi.id AS work_item_id, wi.description AS work_item_description
            """,
            {
                "company_id": company_id,
                "project_id": project_id,
                "work_item_id": work_item_id,
                "props": props,
            },
        )

        if result is None:
            return {"error": f"Work item {work_item_id} not found"}

        return dict(result)

    def add_assumption(
        self,
        actor: Actor,
        company_id: str,
        project_id: str,
        category: str,
        statement: str,
        variation_trigger: bool = False,
        trigger_description: str = "",
        relied_on_value: str = "",
        relied_on_unit: str = "",
    ) -> dict[str, Any]:
        """Add an assumption to a project quote.

        Args:
            actor: The agent actor.
            company_id: Tenant scope.
            project_id: The project.
            category: Type: schedule, quantities, access, coordination, site_conditions,
                design_completeness, pricing, regulatory.
            statement: Human-readable assumption text for the quote.
            variation_trigger: Whether violation triggers a potential variation.
            trigger_description: What condition would violate this assumption.
            relied_on_value: Specific value relied upon.
            relied_on_unit: Unit for the value.

        Returns:
            Dict with the created assumption.
        """
        asmp_id = self._generate_id("asmp")
        provenance = self._provenance_create(actor)

        props: dict[str, Any] = {
            "id": asmp_id,
            "category": category,
            "statement": statement,
            "relied_on_value": relied_on_value,
            "relied_on_unit": relied_on_unit,
            "source_document": "",
            "variation_trigger": variation_trigger,
            "trigger_description": trigger_description,
            "is_template": False,
            "trade_type": "",
            "status": "active",
            "triggered_at": None,
            "triggered_by_event": None,
            "sort_order": 0,
            **provenance,
        }

        result = self._write_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
            WHERE p.deleted = false
            CREATE (a:Assumption $props)
            CREATE (p)-[:HAS_ASSUMPTION]->(a)
            RETURN a.id AS assumption_id, a.category AS category,
                   a.statement AS statement, a.variation_trigger AS variation_trigger,
                   p.id AS project_id, p.name AS project_name
            """,
            {
                "company_id": company_id,
                "project_id": project_id,
                "props": props,
            },
        )

        if result is None:
            return {"error": f"Project {project_id} not found"}

        return dict(result)

    def add_exclusion(
        self,
        actor: Actor,
        company_id: str,
        project_id: str,
        category: str,
        statement: str,
        partial_inclusion: str = "",
    ) -> dict[str, Any]:
        """Add an exclusion to a project quote.

        Args:
            actor: The agent actor.
            company_id: Tenant scope.
            project_id: The project.
            category: Type: scope, trade_boundary, conditions, risk, regulatory.
            statement: Human-readable exclusion text for the quote.
            partial_inclusion: What IS included despite the exclusion.

        Returns:
            Dict with the created exclusion.
        """
        excl_id = self._generate_id("excl")
        provenance = self._provenance_create(actor)

        props: dict[str, Any] = {
            "id": excl_id,
            "category": category,
            "statement": statement,
            "partial_inclusion": partial_inclusion,
            "is_template": False,
            "trade_type": "",
            "source": "",
            "sort_order": 0,
            **provenance,
        }

        result = self._write_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
            WHERE p.deleted = false
            CREATE (e:Exclusion $props)
            CREATE (p)-[:HAS_EXCLUSION]->(e)
            RETURN e.id AS exclusion_id, e.category AS category,
                   e.statement AS statement,
                   p.id AS project_id, p.name AS project_name
            """,
            {
                "company_id": company_id,
                "project_id": project_id,
                "props": props,
            },
        )

        if result is None:
            return {"error": f"Project {project_id} not found"}

        return dict(result)

    def update_assumption(
        self,
        actor: Actor,
        company_id: str,
        assumption_id: str,
        statement: str | None = None,
        category: str | None = None,
        variation_trigger: bool | None = None,
        trigger_description: str | None = None,
        relied_on_value: str | None = None,
        relied_on_unit: str | None = None,
    ) -> dict[str, Any]:
        """Update an existing assumption on a project quote.

        Args:
            actor: The agent actor.
            company_id: Tenant scope.
            assumption_id: The assumption to update.
            statement: Updated assumption text.
            category: Updated category.
            variation_trigger: Updated variation trigger flag.
            trigger_description: Updated trigger description.
            relied_on_value: Updated relied-on value.
            relied_on_unit: Updated relied-on unit.

        Returns:
            Dict with the updated assumption.
        """
        updates: dict[str, Any] = {}
        if statement is not None:
            updates["statement"] = statement
        if category is not None:
            updates["category"] = category
        if variation_trigger is not None:
            updates["variation_trigger"] = variation_trigger
        if trigger_description is not None:
            updates["trigger_description"] = trigger_description
        if relied_on_value is not None:
            updates["relied_on_value"] = relied_on_value
        if relied_on_unit is not None:
            updates["relied_on_unit"] = relied_on_unit

        if not updates:
            return {"error": "No fields to update"}

        provenance = self._provenance_update(actor)
        updates.update(provenance)

        result = self._write_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project)
                  -[:HAS_ASSUMPTION]->(a:Assumption {id: $assumption_id})
            WHERE p.deleted = false
            SET a += $updates
            RETURN a.id AS assumption_id, a.category AS category,
                   a.statement AS statement, a.variation_trigger AS variation_trigger,
                   a.trigger_description AS trigger_description,
                   a.relied_on_value AS relied_on_value,
                   a.relied_on_unit AS relied_on_unit,
                   p.id AS project_id, p.name AS project_name
            """,
            {
                "company_id": company_id,
                "assumption_id": assumption_id,
                "updates": updates,
            },
        )

        if result is None:
            return {"error": f"Assumption {assumption_id} not found"}

        return dict(result)

    def remove_assumption(
        self,
        actor: Actor,
        company_id: str,
        assumption_id: str,
    ) -> dict[str, Any]:
        """Remove an assumption from a project quote.

        Args:
            actor: The agent actor.
            company_id: Tenant scope.
            assumption_id: The assumption to remove.

        Returns:
            Dict confirming removal.
        """
        result = self._write_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project)
                  -[:HAS_ASSUMPTION]->(a:Assumption {id: $assumption_id})
            WHERE p.deleted = false
            WITH a, p, a.statement AS statement, a.category AS category
            DETACH DELETE a
            RETURN $assumption_id AS assumption_id, statement, category,
                   p.id AS project_id, p.name AS project_name,
                   'removed' AS status
            """,
            {
                "company_id": company_id,
                "assumption_id": assumption_id,
            },
        )

        if result is None:
            return {"error": f"Assumption {assumption_id} not found"}

        return dict(result)

    def update_exclusion(
        self,
        actor: Actor,
        company_id: str,
        exclusion_id: str,
        statement: str | None = None,
        category: str | None = None,
        partial_inclusion: str | None = None,
    ) -> dict[str, Any]:
        """Update an existing exclusion on a project quote.

        Args:
            actor: The agent actor.
            company_id: Tenant scope.
            exclusion_id: The exclusion to update.
            statement: Updated exclusion text.
            category: Updated category.
            partial_inclusion: Updated partial inclusion text.

        Returns:
            Dict with the updated exclusion.
        """
        updates: dict[str, Any] = {}
        if statement is not None:
            updates["statement"] = statement
        if category is not None:
            updates["category"] = category
        if partial_inclusion is not None:
            updates["partial_inclusion"] = partial_inclusion

        if not updates:
            return {"error": "No fields to update"}

        provenance = self._provenance_update(actor)
        updates.update(provenance)

        result = self._write_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project)
                  -[:HAS_EXCLUSION]->(e:Exclusion {id: $exclusion_id})
            WHERE p.deleted = false
            SET e += $updates
            RETURN e.id AS exclusion_id, e.category AS category,
                   e.statement AS statement,
                   e.partial_inclusion AS partial_inclusion,
                   p.id AS project_id, p.name AS project_name
            """,
            {
                "company_id": company_id,
                "exclusion_id": exclusion_id,
                "updates": updates,
            },
        )

        if result is None:
            return {"error": f"Exclusion {exclusion_id} not found"}

        return dict(result)

    def remove_exclusion(
        self,
        actor: Actor,
        company_id: str,
        exclusion_id: str,
    ) -> dict[str, Any]:
        """Remove an exclusion from a project quote.

        Args:
            actor: The agent actor.
            company_id: Tenant scope.
            exclusion_id: The exclusion to remove.

        Returns:
            Dict confirming removal.
        """
        result = self._write_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project)
                  -[:HAS_EXCLUSION]->(e:Exclusion {id: $exclusion_id})
            WHERE p.deleted = false
            WITH e, p, e.statement AS statement, e.category AS category
            DETACH DELETE e
            RETURN $exclusion_id AS exclusion_id, statement, category,
                   p.id AS project_id, p.name AS project_name,
                   'removed' AS status
            """,
            {
                "company_id": company_id,
                "exclusion_id": exclusion_id,
            },
        )

        if result is None:
            return {"error": f"Exclusion {exclusion_id} not found"}

        return dict(result)

    def list_assumption_templates(
        self, actor: Actor, company_id: str, trade_type: str | None = None
    ) -> dict[str, Any]:
        """List company assumption templates for reuse on projects.

        Args:
            actor: The agent actor.
            company_id: Tenant scope.
            trade_type: Optional trade filter.

        Returns:
            Dict with templates list.
        """
        params: dict[str, Any] = {"company_id": company_id}
        trade_filter = ""
        if trade_type:
            trade_filter = " AND a.trade_type = $trade_type"
            params["trade_type"] = trade_type

        results = self._read_tx(
            f"""
            MATCH (c:Company {{id: $company_id}})-[:ASSUMPTION_TEMPLATE_OF]->(a:Assumption)
            WHERE a.is_template = true{trade_filter}
            RETURN a.id AS id, a.category AS category, a.statement AS statement,
                   a.variation_trigger AS variation_trigger, a.trade_type AS trade_type
            ORDER BY a.sort_order ASC
            """,
            params,
        )
        return {"templates": [dict(r) for r in results], "total": len(results)}

    def list_exclusion_templates(
        self, actor: Actor, company_id: str, trade_type: str | None = None
    ) -> dict[str, Any]:
        """List company exclusion templates for reuse on projects.

        Args:
            actor: The agent actor.
            company_id: Tenant scope.
            trade_type: Optional trade filter.

        Returns:
            Dict with templates list.
        """
        params: dict[str, Any] = {"company_id": company_id}
        trade_filter = ""
        if trade_type:
            trade_filter = " AND e.trade_type = $trade_type"
            params["trade_type"] = trade_type

        results = self._read_tx(
            f"""
            MATCH (c:Company {{id: $company_id}})-[:EXCLUSION_TEMPLATE_OF]->(e:Exclusion)
            WHERE e.is_template = true{trade_filter}
            RETURN e.id AS id, e.category AS category, e.statement AS statement,
                   e.trade_type AS trade_type
            ORDER BY e.sort_order ASC
            """,
            params,
        )
        return {"templates": [dict(r) for r in results], "total": len(results)}

    def update_project_state(
        self,
        actor: Actor,
        company_id: str,
        project_id: str,
        new_state: str,
    ) -> dict[str, Any]:
        """Transition project lifecycle state.

        Args:
            actor: The agent actor.
            company_id: Tenant scope.
            project_id: The project.
            new_state: Target state: lead, quoted, active, completed, closed, lost.

        Returns:
            Dict with updated project data.
        """
        valid_states = {"lead", "quoted", "active", "completed", "closed", "lost"}
        if new_state not in valid_states:
            return {"error": f"Invalid state '{new_state}'. Must be one of: {sorted(valid_states)}"}

        # Enforce: cannot activate a project without work items
        if new_state == "active":
            wi_result = self._read_tx_single(
                """
                MATCH (p:Project {id: $project_id})-[:HAS_WORK_ITEM]->(wi:WorkItem)
                RETURN count(wi) AS wi_count
                """,
                {"project_id": project_id},
            )
            wi_count = wi_result["wi_count"] if wi_result else 0
            if wi_count == 0:
                return {
                    "error": "Cannot activate project without work items "
                    "\u2014 build a quote first",
                }

        now = datetime.now(timezone.utc).isoformat()
        extra: dict[str, Any] = {}
        if new_state == "quoted":
            extra["quote_submitted_at"] = now

        result = self._write_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
            WHERE p.deleted = false
            WITH p, p.state AS old_state
            SET p.state = $new_state, p += $extra, p += $provenance
            RETURN p.id AS project_id, p.name AS project_name,
                   old_state, p.state AS state, p.status AS status
            """,
            {
                "company_id": company_id,
                "project_id": project_id,
                "new_state": new_state,
                "extra": extra,
                "provenance": self._provenance_update(actor),
            },
        )

        if result is None:
            return {"error": f"Project {project_id} not found"}

        return dict(result)

    # ------------------------------------------------------------------
    # Tool 23.5: set_contract_type (low-risk write)
    # ------------------------------------------------------------------

    def set_contract_type(
        self,
        actor: Actor,
        company_id: str,
        project_id: str,
        contract_type: str,
    ) -> dict[str, Any]:
        """Set the contract/billing basis on a project.

        Valid values:
          - ``lump_sum`` — fixed price, scope-locked
          - ``time_and_materials`` — hours billed at rate + materials at cost
          - ``cost_plus`` — all costs reimbursed plus a fee, open book
          - ``schedule_of_rates`` — priced per-unit rate sheet, quantities vary

        Args:
            actor: The agent actor.
            company_id: Tenant scope.
            project_id: The project.
            contract_type: One of the four valid values above.

        Returns:
            Dict with project id, name, previous and new contract_type.
        """
        valid = {"lump_sum", "schedule_of_rates", "cost_plus", "time_and_materials"}
        if contract_type not in valid:
            return {
                "error": f"Invalid contract_type '{contract_type}'. "
                f"Must be one of: {sorted(valid)}"
            }
        result = self._write_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
            WHERE p.deleted = false
            WITH p, p.contract_type AS previous_contract_type
            SET p.contract_type = $contract_type, p += $provenance
            RETURN p.id AS project_id, p.name AS project_name,
                   previous_contract_type,
                   p.contract_type AS contract_type
            """,
            {
                "company_id": company_id,
                "project_id": project_id,
                "contract_type": contract_type,
                "provenance": self._provenance_update(actor),
            },
        )
        if result is None:
            return {"error": f"Project {project_id} not found"}
        return dict(result)

    # ==================================================================
    # PROPOSE & WIN tools (Session E)
    # ==================================================================

    # ------------------------------------------------------------------
    # Tool 24: generate_proposal (low-risk write)
    # ------------------------------------------------------------------

    def generate_proposal(
        self,
        actor: Actor,
        company_id: str,
        project_id: str,
        terms: str | None = None,
        timeline: str | None = None,
        notes: str | None = None,
    ) -> dict[str, Any]:
        """Generate a proposal document from a project's work items.

        Creates a Document node with type 'report' containing the
        assembled proposal data.

        Args:
            actor: The agent actor.
            company_id: Tenant scope.
            project_id: The project to generate a proposal for.
            terms: Optional payment terms text.
            timeline: Optional project timeline.
            notes: Optional additional notes.

        Returns:
            Dict with proposal document data and work item breakdown.
        """
        result = self._read_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
            WHERE p.deleted = false

            CALL {
                WITH p
                OPTIONAL MATCH (p)-[:HAS_WORK_ITEM]->(wi:WorkItem)
                WHERE wi.deleted = false AND coalesce(wi.is_alternate, false) = false
                OPTIONAL MATCH (wi)-[:HAS_LABOUR]->(lab:Labour)
                OPTIONAL MATCH (wi)-[:HAS_ITEM]->(item:Item)
                WITH wi,
                     coalesce(sum(DISTINCT lab.cost_cents), 0) AS labour_cost,
                     coalesce(sum(DISTINCT item.total_cents), 0) AS items_cost,
                     coalesce(wi.margin_pct, 0) AS margin_pct
                WITH wi, labour_cost, items_cost, margin_pct,
                     round((labour_cost + items_cost) * (1 + margin_pct / 100.0)) AS line_total
                RETURN collect({
                    id: wi.id,
                    description: wi.description,
                    quantity: wi.quantity,
                    unit: wi.unit,
                    labour_cost_cents: labour_cost,
                    items_cost_cents: items_cost,
                    sell_price_cents: line_total
                }) AS items,
                sum(labour_cost) AS total_labour,
                sum(items_cost) AS total_items,
                sum(line_total) AS grand_total,
                count(wi) AS item_count
            }

            CALL {
                WITH p
                OPTIONAL MATCH (p)-[:HAS_ASSUMPTION]->(a:Assumption)
                WHERE a.status = 'active'
                RETURN collect({
                    category: a.category,
                    statement: a.statement,
                    variation_trigger: a.variation_trigger
                }) AS assumptions
            }

            CALL {
                WITH p
                OPTIONAL MATCH (p)-[:HAS_EXCLUSION]->(e:Exclusion)
                RETURN collect({
                    category: e.category,
                    statement: e.statement,
                    partial_inclusion: e.partial_inclusion
                }) AS exclusions
            }

            CALL {
                WITH p
                OPTIONAL MATCH (contact:Contact)-[:CLIENT_IS]->(p)
                RETURN contact {.name, .email, .phone, .company_name} AS client
            }

            RETURN p.id AS project_id, p.name AS project_name,
                   p.address AS address, p.state AS state,
                   items, total_labour, total_items, grand_total, item_count,
                   assumptions, exclusions, client
            """,
            {"company_id": company_id, "project_id": project_id},
        )

        if result is None:
            return {"error": f"Project {project_id} not found"}

        items = [i for i in result["items"] if i.get("id")]
        assumptions = [a for a in result["assumptions"] if a.get("statement")]
        exclusions = [e for e in result["exclusions"] if e.get("statement")]
        now = datetime.now(timezone.utc).isoformat()

        # Create Document node
        doc_id = self._generate_id("doc")
        provenance = self._provenance_create(actor)

        self._write_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
            CREATE (d:Document {
                id: $doc_id,
                title: $title,
                document_type: 'proposal',
                status: 'draft',
                _content_json: '{}',
                _project_info_json: '{}',
                deleted: false,
                created_by: $created_by,
                actor_type: $actor_type,
                agent_id: $agent_id,
                agent_version: $agent_version,
                model_id: $model_id,
                confidence: $confidence,
                agent_cost_cents: $agent_cost_cents,
                created_at: $created_at,
                updated_by: $updated_by,
                updated_actor_type: $updated_actor_type,
                updated_at: $updated_at
            })
            CREATE (p)-[:HAS_DOCUMENT]->(d)
            RETURN d.id AS doc_id
            """,
            {
                "company_id": company_id,
                "project_id": project_id,
                "doc_id": doc_id,
                "title": f"Proposal — {result['project_name']}",
                **provenance,
            },
        )

        event = self.event_bus.create_event(
            event_type=EventType.PROPOSAL_GENERATED,
            entity_id=doc_id,
            entity_type="Document",
            company_id=company_id,
            project_id=project_id,
            actor=actor,
            summary={
                "project_name": result["project_name"],
                "grand_total": result["grand_total"] or 0,
                "item_count": result["item_count"] or 0,
            },
        )
        self.event_bus.emit(event)

        return {
            "proposal_id": doc_id,
            "project_id": result["project_id"],
            "project_name": result["project_name"],
            "address": result.get("address"),
            "client": result.get("client"),
            "items": items,
            "item_count": result["item_count"] or 0,
            "total_labour_cents": result["total_labour"] or 0,
            "total_items_cents": result["total_items"] or 0,
            "grand_total_cents": result["grand_total"] or 0,
            "assumptions": assumptions,
            "exclusions": exclusions,
            "currency": "USD",
            "terms": terms or "Net 30 days",
            "timeline": timeline,
            "notes": notes,
            "generated_at": now,
            "status": "draft",
        }

    # ------------------------------------------------------------------
    # Tool 25: update_project_status (low-risk write)
    # ------------------------------------------------------------------

    def update_project_status(
        self,
        actor: Actor,
        company_id: str,
        project_id: str,
        new_status: str,
    ) -> dict[str, Any]:
        """Transition project lifecycle state through the sales pipeline.

        NOTE: This tool updates the project 'state' (lifecycle stage),
        not 'status' (operating condition). Kept as update_project_status
        for backward compatibility with existing chat flows.

        Allowed states: lead, quoted, active, completed, closed, lost.

        Args:
            actor: The agent actor.
            company_id: Tenant scope.
            project_id: The project to update.
            new_status: Target lifecycle state.

        Returns:
            Dict with updated project data.
        """
        valid_states = {"lead", "quoted", "active", "completed", "closed", "lost"}
        if new_status not in valid_states:
            return {
                "error": f"Invalid state '{new_status}'. "
                f"Must be one of: {sorted(valid_states)}",
            }

        # Enforce: cannot activate a project without work items
        if new_status == "active":
            wi_result = self._read_tx_single(
                """
                MATCH (p:Project {id: $project_id})-[:HAS_WORK_ITEM]->(wi:WorkItem)
                RETURN count(wi) AS wi_count
                """,
                {"project_id": project_id},
            )
            wi_count = wi_result["wi_count"] if wi_result else 0
            if wi_count == 0:
                return {
                    "error": "Cannot activate project without work items "
                    "\u2014 build a quote first",
                }

        now = datetime.now(timezone.utc).isoformat()
        extra: dict[str, Any] = {}
        if new_status == "quoted":
            extra["quote_submitted_at"] = now

        result = self._write_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
            WHERE p.deleted = false
            WITH p, p.state AS old_state
            SET p.state = $new_state, p += $extra, p += $provenance
            RETURN p.id AS project_id, p.name AS project_name,
                   old_state, p.state AS state, p.status AS status,
                   p.address AS address
            """,
            {
                "company_id": company_id,
                "project_id": project_id,
                "new_state": new_status,
                "extra": extra,
                "provenance": self._provenance_update(actor),
            },
        )

        if result is None:
            return {"error": f"Project {project_id} not found"}

        event = self.event_bus.create_event(
            event_type=EventType.PROJECT_STATUS_CHANGED,
            entity_id=project_id,
            entity_type="Project",
            company_id=company_id,
            project_id=project_id,
            actor=actor,
            summary={
                "old_status": result["old_status"],
                "new_status": new_status,
            },
        )
        self.event_bus.emit(event)

        return {
            "project_id": result["project_id"],
            "project_name": result["project_name"],
            "old_status": result["old_status"],
            "status": result["status"],
            "address": result.get("address"),
        }

    # ==================================================================
    # GET PAID tools (Session E)
    # ==================================================================

    # ------------------------------------------------------------------
    # Tool 26: generate_invoice (low-risk write)
    # ------------------------------------------------------------------

    def generate_invoice(
        self,
        actor: Actor,
        company_id: str,
        project_id: str,
        work_item_ids: list[str] | None = None,
        progress_pct: float | None = None,
        due_date: str | None = None,
        notes: str | None = None,
    ) -> dict[str, Any]:
        """Generate an invoice from selected work items or progress percentage.

        If work_item_ids is provided, invoices those specific items.
        If progress_pct is provided, calculates a progress claim.

        Args:
            actor: The agent actor.
            company_id: Tenant scope.
            project_id: The project to invoice.
            work_item_ids: Optional list of specific work item IDs to invoice.
            progress_pct: Optional progress percentage (0-100).
            due_date: Optional due date (ISO format).
            notes: Optional invoice notes.

        Returns:
            Dict with the created invoice and line items.
        """
        inv_id = self._generate_id("inv")
        provenance = self._provenance_create(actor)

        if work_item_ids:
            result = self._write_tx_single(
                """
                MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
                WHERE p.deleted = false

                OPTIONAL MATCH (p)-[:HAS_WORK_ITEM]->(wi:WorkItem)
                WHERE wi.id IN $work_item_ids AND wi.deleted = false
                OPTIONAL MATCH (wi)-[u:USES_ITEM]->(it:Item)
                WITH p, c, wi,
                     coalesce(wi.labour_hours, 0) * coalesce(wi.labour_rate, 0) AS labour,
                     coalesce(wi.materials_allowance, 0)
                         + sum(coalesce(u.quantity, 0) * coalesce(u.unit_cost, 0)) AS materials,
                     coalesce(wi.margin_pct, 0) AS margin_pct
                WITH p, c, wi, labour, materials,
                     round((labour + materials) * (1 + margin_pct / 100.0), 2) AS line_total
                WITH p, c,
                     collect({id: wi.id, description: wi.description, amount: line_total}) AS lines,
                     sum(line_total) AS total_amount

                CREATE (inv:Invoice {
                    id: $inv_id,
                    direction: 'receivable',
                    number: null,
                    status: 'draft',
                    amount: total_amount,
                    currency: 'USD',
                    due_date: $due_date,
                    sent_date: null,
                    paid_date: null,
                    notes: $notes,
                    deleted: false,
                    created_by: $created_by,
                    actor_type: $actor_type,
                    agent_id: $agent_id,
                    agent_version: $agent_version,
                    model_id: $model_id,
                    confidence: $confidence,
                    agent_cost_cents: $agent_cost_cents,
                    created_at: $created_at,
                    updated_by: $updated_by,
                    updated_actor_type: $updated_actor_type,
                    updated_at: $updated_at
                })
                CREATE (p)-[:HAS_INVOICE]->(inv)

                RETURN inv.id AS invoice_id, p.id AS project_id, p.name AS project_name,
                       total_amount, lines
                """,
                {
                    "company_id": company_id,
                    "project_id": project_id,
                    "work_item_ids": work_item_ids,
                    "inv_id": inv_id,
                    "due_date": due_date,
                    "notes": notes,
                    **provenance,
                },
            )
        else:
            pct = progress_pct or 100.0
            result = self._write_tx_single(
                """
                MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
                WHERE p.deleted = false

                CALL {
                    WITH p
                    OPTIONAL MATCH (p)-[:HAS_WORK_ITEM]->(wi:WorkItem)
                    WHERE wi.deleted = false
                    OPTIONAL MATCH (wi)-[u:USES_ITEM]->(it:Item)
                    WITH wi,
                         coalesce(wi.labour_hours, 0) * coalesce(wi.labour_rate, 0) AS labour,
                         coalesce(wi.materials_allowance, 0)
                             + sum(coalesce(u.quantity, 0) * coalesce(u.unit_cost, 0)) AS materials,
                         coalesce(wi.margin_pct, 0) AS margin_pct
                    WITH round((labour + materials) * (1 + margin_pct / 100.0), 2) AS line_total
                    RETURN sum(line_total) AS project_total
                }

                WITH p, c, round(project_total * $pct / 100.0, 2) AS total_amount, project_total

                CREATE (inv:Invoice {
                    id: $inv_id,
                    direction: 'receivable',
                    number: null,
                    status: 'draft',
                    amount: total_amount,
                    currency: 'USD',
                    due_date: $due_date,
                    sent_date: null,
                    paid_date: null,
                    notes: $notes,
                    deleted: false,
                    created_by: $created_by,
                    actor_type: $actor_type,
                    agent_id: $agent_id,
                    agent_version: $agent_version,
                    model_id: $model_id,
                    confidence: $confidence,
                    agent_cost_cents: $agent_cost_cents,
                    created_at: $created_at,
                    updated_by: $updated_by,
                    updated_actor_type: $updated_actor_type,
                    updated_at: $updated_at
                })
                CREATE (p)-[:HAS_INVOICE]->(inv)

                RETURN inv.id AS invoice_id, p.id AS project_id, p.name AS project_name,
                       total_amount, project_total,
                       [] AS lines
                """,
                {
                    "company_id": company_id,
                    "project_id": project_id,
                    "inv_id": inv_id,
                    "pct": pct,
                    "due_date": due_date,
                    "notes": notes,
                    **provenance,
                },
            )

        if result is None:
            return {"error": f"Project {project_id} not found"}

        event = self.event_bus.create_event(
            event_type=EventType.INVOICE_CREATED,
            entity_id=inv_id,
            entity_type="Invoice",
            company_id=company_id,
            project_id=project_id,
            actor=actor,
            summary={
                "amount": result.get("total_amount"),
                "direction": "receivable",
            },
        )
        self.event_bus.emit(event)

        lines = [ln for ln in (result.get("lines") or []) if ln.get("id")]

        return {
            "invoice_id": inv_id,
            "project_id": result["project_id"],
            "project_name": result["project_name"],
            "amount": result.get("total_amount"),
            "currency": "USD",
            "status": "draft",
            "direction": "receivable",
            "due_date": due_date,
            "lines": lines,
            "notes": notes,
            "created_by": actor.id,
            "actor_type": actor.type,
        }

    # ------------------------------------------------------------------
    # Tool 27: track_payment_status (read-only)
    # ------------------------------------------------------------------

    def track_payment_status(
        self, actor: Actor, company_id: str, project_id: str
    ) -> dict[str, Any]:
        """List outstanding invoices for a project with aging.

        Returns all receivable invoices with days until/overdue calculations.

        Args:
            actor: The agent actor.
            company_id: Tenant scope.
            project_id: The project to check.

        Returns:
            Dict with invoice list, totals, and aging summary.
        """
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        results = self._read_tx(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
                  -[:HAS_INVOICE]->(inv:Invoice)
            WHERE inv.deleted = false AND inv.direction = 'receivable'
            RETURN inv.id AS invoice_id,
                   inv.number AS invoice_number,
                   inv.amount AS amount,
                   inv.status AS status,
                   inv.due_date AS due_date,
                   inv.sent_date AS sent_date,
                   inv.paid_date AS paid_date,
                   inv.created_at AS created_at,
                   p.id AS project_id,
                   p.name AS project_name
            ORDER BY inv.created_at DESC
            """,
            {"company_id": company_id, "project_id": project_id},
        )

        invoices: list[dict[str, Any]] = []
        total_invoiced = 0.0
        total_paid = 0.0
        total_outstanding = 0.0
        total_overdue = 0.0

        for r in results:
            inv = dict(r)
            amount = inv.get("amount") or 0
            total_invoiced += amount

            if inv["status"] == "paid":
                total_paid += amount
            else:
                total_outstanding += amount
                if inv.get("due_date") and inv["due_date"] < today:
                    inv["days_overdue"] = (
                        datetime.strptime(today, "%Y-%m-%d")
                        - datetime.strptime(inv["due_date"], "%Y-%m-%d")
                    ).days
                    total_overdue += amount
                elif inv.get("due_date"):
                    inv["days_until_due"] = (
                        datetime.strptime(inv["due_date"], "%Y-%m-%d")
                        - datetime.strptime(today, "%Y-%m-%d")
                    ).days

            invoices.append(inv)

        return {
            "project_id": project_id,
            "project_name": results[0]["project_name"] if results else None,
            "invoices": invoices,
            "total_invoiced": total_invoiced,
            "total_paid": total_paid,
            "total_outstanding": total_outstanding,
            "total_overdue": total_overdue,
            "invoice_count": len(invoices),
            "as_of": today,
        }

    # ------------------------------------------------------------------
    # Tool 28: record_payment (low-risk write)
    # ------------------------------------------------------------------

    def record_payment(
        self,
        actor: Actor,
        company_id: str,
        project_id: str,
        invoice_id: str,
        amount: float,
        payment_date: str | None = None,
        method: str | None = None,
        reference: str | None = None,
    ) -> dict[str, Any]:
        """Record a payment against an invoice.

        Creates a Payment node linked to the invoice. If the payment
        covers the full amount, transitions status to 'paid';
        otherwise to 'partial'.

        Args:
            actor: The agent actor.
            company_id: Tenant scope.
            project_id: The parent project.
            invoice_id: The invoice being paid.
            amount: Payment amount.
            payment_date: Date payment was received (ISO format).
            method: Payment method (e.g. 'bank_transfer', 'check').
            reference: Payment reference number.

        Returns:
            Dict with payment and updated invoice data.
        """
        pmt_id = self._generate_id("pmt")
        provenance = self._provenance_create(actor)
        pay_date = payment_date or datetime.now(timezone.utc).strftime("%Y-%m-%d")

        result = self._write_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
                  -[:HAS_INVOICE]->(inv:Invoice {id: $invoice_id})
            WHERE inv.deleted = false

            OPTIONAL MATCH (inv)<-[:PAYS]-(existing:Payment)
            WITH inv, p, coalesce(sum(existing.amount), 0) AS already_paid

            CREATE (pmt:Payment {
                id: $pmt_id,
                amount: $amount,
                payment_date: $payment_date,
                method: $method,
                reference: $reference,
                deleted: false,
                created_by: $created_by,
                actor_type: $actor_type,
                agent_id: $agent_id,
                agent_version: $agent_version,
                model_id: $model_id,
                confidence: $confidence,
                agent_cost_cents: $agent_cost_cents,
                created_at: $created_at,
                updated_by: $updated_by,
                updated_actor_type: $updated_actor_type,
                updated_at: $updated_at
            })
            CREATE (pmt)-[:PAYS]->(inv)

            WITH inv, p, pmt, already_paid + $amount AS total_paid
            SET inv.status = CASE
                WHEN total_paid >= coalesce(inv.amount, 0) THEN 'paid'
                ELSE 'partial'
            END,
            inv.paid_date = CASE
                WHEN total_paid >= coalesce(inv.amount, 0) THEN $payment_date
                ELSE inv.paid_date
            END

            RETURN pmt.id AS payment_id, pmt.amount AS payment_amount,
                   inv.id AS invoice_id, inv.amount AS invoice_amount,
                   inv.status AS invoice_status, total_paid,
                   p.id AS project_id, p.name AS project_name
            """,
            {
                "company_id": company_id,
                "project_id": project_id,
                "invoice_id": invoice_id,
                "pmt_id": pmt_id,
                "amount": amount,
                "payment_date": pay_date,
                "method": method,
                "reference": reference,
                **provenance,
            },
        )

        if result is None:
            return {"error": f"Invoice {invoice_id} not found"}

        event = self.event_bus.create_event(
            event_type=EventType.PAYMENT_RECORDED,
            entity_id=pmt_id,
            entity_type="Payment",
            company_id=company_id,
            project_id=project_id,
            actor=actor,
            summary={
                "amount": amount,
                "invoice_id": invoice_id,
                "invoice_status": result["invoice_status"],
            },
        )
        self.event_bus.emit(event)

        return {
            "payment_id": pmt_id,
            "payment_amount": amount,
            "payment_date": pay_date,
            "method": method,
            "reference": reference,
            "invoice_id": result["invoice_id"],
            "invoice_amount": result["invoice_amount"],
            "invoice_status": result["invoice_status"],
            "total_paid": result["total_paid"],
            "project_id": result["project_id"],
            "project_name": result["project_name"],
        }

    # ==================================================================
    # EXECUTE & DOCUMENT + MANAGE MONEY tools (Session D)
    # ==================================================================

    # ------------------------------------------------------------------
    # create_daily_log (low-risk write)
    # ------------------------------------------------------------------

    def create_daily_log(
        self,
        actor: Actor,
        company_id: str,
        project_id: str,
        log_date: str = "",
    ) -> dict[str, Any]:
        """Create a daily log for a project on a given date.

        Creates a DailyLog node in draft status. Defaults to today if
        no date is provided. Fails if a log already exists for that date.

        Args:
            actor: The agent actor.
            company_id: Tenant scope.
            project_id: The project to log.
            log_date: ISO date string (YYYY-MM-DD). Defaults to today.

        Returns:
            Dict with the created daily log data.
        """
        if not log_date:
            log_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        log_id = self._generate_id("dl")
        provenance = self._provenance_create(actor)

        result = self._write_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
            WHERE p.deleted = false
            OPTIONAL MATCH (p)-[:HAS_DAILY_LOG]->(existing:DailyLog {log_date: $log_date})
            WHERE existing.deleted = false
            WITH c, p, existing
            WHERE existing IS NULL
            CREATE (dl:DailyLog {
                id: $log_id,
                log_date: $log_date,
                status: 'draft',
                work_performed: '',
                notes: '',
                _weather_json: '{}',
                _materials_json: '[]',
                _delays_json: '[]',
                _visitors_json: '[]',
                _inspections_summary_json: '[]',
                _toolbox_talks_summary_json: '[]',
                _incidents_summary_json: '[]',
                crew_count: 0,
                deleted: false,
                created_by: $created_by,
                actor_type: $actor_type,
                agent_id: $agent_id,
                agent_version: $agent_version,
                model_id: $model_id,
                confidence: $confidence,
                agent_cost_cents: $agent_cost_cents,
                created_at: $created_at,
                updated_by: $updated_by,
                updated_actor_type: $updated_actor_type,
                updated_at: $updated_at
            })
            CREATE (p)-[:HAS_DAILY_LOG]->(dl)
            RETURN dl.id AS log_id, p.id AS project_id, p.name AS project_name,
                   dl.log_date AS log_date, dl.status AS status
            """,
            {
                "company_id": company_id,
                "project_id": project_id,
                "log_id": log_id,
                "log_date": log_date,
                **provenance,
            },
        )

        if result is None:
            return {
                "error": f"Project {project_id} not found or daily log already exists for {log_date}"
            }

        event = self.event_bus.create_event(
            event_type=EventType.DAILY_LOG_CREATED,
            entity_id=log_id,
            entity_type="DailyLog",
            company_id=company_id,
            project_id=project_id,
            actor=actor,
            summary={"log_date": log_date, "status": "draft"},
        )
        self.event_bus.emit(event)

        return {
            "log_id": result["log_id"],
            "project_id": result["project_id"],
            "project_name": result["project_name"],
            "log_date": result["log_date"],
            "status": result["status"],
            "created_by": actor.id,
            "actor_type": actor.type,
        }

    # ------------------------------------------------------------------
    # auto_populate_daily_log (read-only)
    # ------------------------------------------------------------------

    def auto_populate_daily_log(
        self, actor: Actor, company_id: str, project_id: str, log_date: str = ""
    ) -> dict[str, Any]:
        """Auto-populate a daily log by querying related entities for the day.

        Queries safety inspections, time entries, incidents, and crew count.

        Args:
            actor: The agent actor.
            company_id: Tenant scope.
            project_id: The project.
            log_date: ISO date string. Defaults to today.

        Returns:
            Dict with assembled daily log data from graph.
        """
        if not log_date:
            log_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        result = self._read_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
            WHERE p.deleted = false

            CALL {
                WITH p
                OPTIONAL MATCH (p)<-[:FOR_PROJECT]-(te:TimeEntry)
                WHERE te.deleted = false AND te.date = $log_date
                OPTIONAL MATCH (te)-[:LOGGED_BY]->(w:Worker)
                WITH collect(CASE WHEN te IS NOT NULL THEN {
                    id: te.id,
                    worker_name: COALESCE(w.first_name + ' ' + w.last_name, 'Unknown'),
                    clock_in: te.clock_in,
                    clock_out: te.clock_out,
                    regular_hours: te.regular_hours,
                    work_item_id: te.work_item_id
                } ELSE null END) AS time_entries
                RETURN time_entries
            }

            CALL {
                WITH p
                OPTIONAL MATCH (p)-[:HAS_INSPECTION]->(i:Inspection)
                WHERE i.deleted = false AND i.created_at STARTS WITH $log_date
                RETURN collect(CASE WHEN i IS NOT NULL THEN {
                    id: i.id,
                    category: i.category,
                    overall_status: i.overall_status,
                    created_at: i.created_at
                } ELSE null END) AS inspections
            }

            CALL {
                WITH p
                OPTIONAL MATCH (p)-[:HAS_INCIDENT]->(inc:Incident)
                WHERE inc.incident_date = $log_date
                RETURN collect(CASE WHEN inc IS NOT NULL THEN {
                    id: inc.id,
                    title: inc.title,
                    severity: inc.severity,
                    status: inc.status
                } ELSE null END) AS incidents
            }

            CALL {
                WITH c, p
                OPTIONAL MATCH (c)-[:EMPLOYS]->(w:Worker)-[:ASSIGNED_TO_PROJECT]->(p)
                WHERE w.deleted = false
                RETURN count(w) AS crew_count
            }

            RETURN p.id AS project_id, p.name AS project_name,
                   time_entries, inspections, incidents, crew_count
            """,
            {
                "company_id": company_id,
                "project_id": project_id,
                "log_date": log_date,
            },
        )

        if result is None:
            return {"error": f"Project {project_id} not found"}

        time_entries = [t for t in result["time_entries"] if t is not None]
        inspections = [i for i in result["inspections"] if i is not None]
        incidents = [i for i in result["incidents"] if i is not None]

        total_hours = sum(t.get("regular_hours", 0) or 0 for t in time_entries)
        populated = sum([bool(time_entries), bool(inspections), bool(incidents)])
        auto_pct = round(populated / 3 * 100)

        return {
            "project_id": result["project_id"],
            "project_name": result["project_name"],
            "log_date": log_date,
            "crew_count": result["crew_count"],
            "time_entries": time_entries,
            "time_entry_count": len(time_entries),
            "total_hours": total_hours,
            "inspections": inspections,
            "inspection_count": len(inspections),
            "incidents": incidents,
            "incident_count": len(incidents),
            "auto_populated_pct": auto_pct,
        }

    # ------------------------------------------------------------------
    # record_time (low-risk write)
    # ------------------------------------------------------------------

    def record_time(
        self,
        actor: Actor,
        company_id: str,
        project_id: str,
        worker_id: str,
        work_item_id: str,
        clock_in: str,
        clock_out: str = "",
        date: str = "",
    ) -> dict[str, Any]:
        """Record a time entry for a worker on a work item.

        Creates a TimeEntry node linked to the project, worker, and work item.

        Args:
            actor: The agent actor.
            company_id: Tenant scope.
            project_id: The project.
            worker_id: The worker clocking in.
            work_item_id: The work item being worked on.
            clock_in: Clock-in time (ISO datetime or HH:MM).
            clock_out: Clock-out time. Empty if still on site.
            date: Date for the entry (YYYY-MM-DD). Defaults to today.

        Returns:
            Dict with the created time entry data.
        """
        if not date:
            date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        te_id = self._generate_id("te")
        provenance = self._provenance_create(actor)

        regular_hours = 0.0
        if clock_in and clock_out:
            try:
                fmt = "%H:%M" if len(clock_in) <= 5 else "%Y-%m-%dT%H:%M:%S"
                t_in = datetime.strptime(clock_in, fmt)
                t_out = datetime.strptime(clock_out, fmt)
                regular_hours = round((t_out - t_in).total_seconds() / 3600, 2)
            except ValueError:
                pass

        result = self._write_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
            WHERE p.deleted = false
            MATCH (c)-[:EMPLOYS]->(w:Worker {id: $worker_id})
            WHERE w.deleted = false
            CREATE (te:TimeEntry {
                id: $te_id,
                date: $date,
                clock_in: $clock_in,
                clock_out: $clock_out,
                regular_hours: $regular_hours,
                overtime_hours: 0,
                break_minutes: 0,
                status: 'open',
                work_item_id: $work_item_id,
                deleted: false,
                created_by: $created_by,
                actor_type: $actor_type,
                agent_id: $agent_id,
                agent_version: $agent_version,
                model_id: $model_id,
                confidence: $confidence,
                agent_cost_cents: $agent_cost_cents,
                created_at: $created_at,
                updated_by: $updated_by,
                updated_actor_type: $updated_actor_type,
                updated_at: $updated_at
            })
            CREATE (te)-[:LOGGED_BY]->(w)
            CREATE (te)-[:FOR_PROJECT]->(p)
            WITH te, w, p
            OPTIONAL MATCH (p)-[:HAS_WORK_ITEM]->(wi:WorkItem {id: $work_item_id})
            FOREACH (_ IN CASE WHEN wi IS NOT NULL THEN [1] ELSE [] END |
                CREATE (wi)-[:HAS_TIME_ENTRY]->(te)
            )
            RETURN te.id AS time_entry_id, p.id AS project_id, p.name AS project_name,
                   w.id AS worker_id, w.first_name + ' ' + w.last_name AS worker_name,
                   te.regular_hours AS hours
            """,
            {
                "company_id": company_id,
                "project_id": project_id,
                "worker_id": worker_id,
                "work_item_id": work_item_id,
                "te_id": te_id,
                "date": date,
                "clock_in": clock_in,
                "clock_out": clock_out,
                "regular_hours": regular_hours,
                **provenance,
            },
        )

        if result is None:
            return {"error": f"Project {project_id} or worker {worker_id} not found"}

        event = self.event_bus.create_event(
            event_type=EventType.TIME_ENTRY_RECORDED,
            entity_id=te_id,
            entity_type="TimeEntry",
            company_id=company_id,
            project_id=project_id,
            actor=actor,
            summary={
                "worker_id": worker_id,
                "work_item_id": work_item_id,
                "hours": regular_hours,
                "date": date,
            },
        )
        self.event_bus.emit(event)

        return {
            "time_entry_id": result["time_entry_id"],
            "project_id": result["project_id"],
            "project_name": result["project_name"],
            "worker_id": result["worker_id"],
            "worker_name": result["worker_name"],
            "work_item_id": work_item_id,
            "date": date,
            "clock_in": clock_in,
            "clock_out": clock_out,
            "hours": result["hours"],
            "status": "open",
        }

    # ------------------------------------------------------------------
    # report_quality_observation (low-risk write)
    # ------------------------------------------------------------------

    def report_quality_observation(
        self,
        actor: Actor,
        company_id: str,
        project_id: str,
        description: str,
        location: str = "",
        result_status: str = "pass",
        score: int | None = None,
    ) -> dict[str, Any]:
        """Create a quality observation (Inspection with category='quality').

        Args:
            actor: The agent actor.
            company_id: Tenant scope.
            project_id: The project.
            description: What was observed.
            location: Where on site.
            result_status: 'pass' or 'fail'.
            score: Optional quality score (0-100).

        Returns:
            Dict with the created quality observation data.
        """
        insp_id = self._generate_id("insp")
        provenance = self._provenance_create(actor)

        result = self._write_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
            WHERE p.deleted = false
            CREATE (i:Inspection {
                id: $insp_id,
                category: 'quality',
                inspection_type: 'quality_observation',
                description: $description,
                location: $location,
                overall_status: $result_status,
                score: $score,
                deleted: false,
                created_by: $created_by,
                actor_type: $actor_type,
                agent_id: $agent_id,
                agent_version: $agent_version,
                model_id: $model_id,
                confidence: $confidence,
                agent_cost_cents: $agent_cost_cents,
                created_at: $created_at,
                updated_by: $updated_by,
                updated_actor_type: $updated_actor_type,
                updated_at: $updated_at
            })
            CREATE (p)-[:HAS_INSPECTION]->(i)
            RETURN i.id AS inspection_id, p.id AS project_id, p.name AS project_name
            """,
            {
                "company_id": company_id,
                "project_id": project_id,
                "insp_id": insp_id,
                "description": description,
                "location": location,
                "result_status": result_status,
                "score": score,
                **provenance,
            },
        )

        if result is None:
            return {"error": f"Project {project_id} not found"}

        event = self.event_bus.create_event(
            event_type=EventType.QUALITY_OBSERVATION_REPORTED,
            entity_id=insp_id,
            entity_type="Inspection",
            company_id=company_id,
            project_id=project_id,
            actor=actor,
            summary={
                "category": "quality",
                "description": description,
                "result": result_status,
                "score": score,
            },
        )
        self.event_bus.emit(event)

        return {
            "inspection_id": result["inspection_id"],
            "project_id": result["project_id"],
            "project_name": result["project_name"],
            "category": "quality",
            "description": description,
            "location": location,
            "status": result_status,
            "score": score,
            "created_by": actor.id,
        }

    # ------------------------------------------------------------------
    # get_job_cost_summary (read-only)
    # ------------------------------------------------------------------

    def get_job_cost_summary(
        self, actor: Actor, company_id: str, project_id: str
    ) -> dict[str, Any]:
        """Get actual vs estimated costs for a project.

        Traverses Project -> WorkItems -> TimeEntries + USES_ITEM.

        Args:
            actor: The agent actor.
            company_id: Tenant scope.
            project_id: The project to cost.

        Returns:
            Dict with cost breakdown — estimated, actual, variance, burn rate.
        """
        result = self._read_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
            WHERE p.deleted = false

            CALL {
                WITH p
                OPTIONAL MATCH (p)-[:HAS_WORK_ITEM]->(wi:WorkItem)
                WHERE wi.deleted = false
                OPTIONAL MATCH (wi)-[:HAS_TIME_ENTRY]->(te:TimeEntry)
                WHERE te.deleted = false
                WITH wi,
                     sum(COALESCE(te.regular_hours, 0)) AS actual_hours,
                     count(te) AS te_count
                OPTIONAL MATCH (wi)-[:USES_ITEM]->(item)
                WITH wi, actual_hours, te_count,
                     sum(COALESCE(item.quantity, 0) * COALESCE(item.unit_cost, 0)) AS mat_cost
                WITH collect({
                    id: wi.id,
                    description: wi.description,
                    state: wi.state,
                    estimated_labour_hours: COALESCE(wi.labour_hours, 0),
                    estimated_labour_rate: COALESCE(wi.labour_rate, 0),
                    estimated_labour_cost: COALESCE(wi.labour_hours, 0) * COALESCE(wi.labour_rate, 0),
                    estimated_materials: COALESCE(wi.materials_allowance, 0),
                    actual_hours: actual_hours,
                    actual_labour_cost: actual_hours * COALESCE(wi.labour_rate, 0),
                    actual_material_cost: mat_cost,
                    time_entry_count: te_count
                }) AS work_items
                RETURN work_items
            }

            RETURN p.id AS project_id, p.name AS project_name,
                   p.status AS status,
                   COALESCE(p.contract_value, 0) AS contract_value,
                   work_items
            """,
            {"company_id": company_id, "project_id": project_id},
        )

        if result is None:
            return {"error": f"Project {project_id} not found"}

        items = [wi for wi in result["work_items"] if wi.get("id")]
        est_l = sum(wi["estimated_labour_cost"] for wi in items)
        est_m = sum(wi["estimated_materials"] for wi in items)
        act_l = sum(wi["actual_labour_cost"] for wi in items)
        act_m = sum(wi["actual_material_cost"] for wi in items)
        est_total = est_l + est_m
        act_total = act_l + act_m
        contract = result["contract_value"]

        return {
            "project_id": result["project_id"],
            "project_name": result["project_name"],
            "status": result["status"],
            "contract_value": contract,
            "estimated_cost": {"labour": est_l, "materials": est_m, "total": est_total},
            "actual_cost": {"labour": act_l, "materials": act_m, "total": act_total},
            "variance": act_total - est_total,
            "margin": contract - act_total if contract else None,
            "burn_rate": round(act_total / est_total * 100, 1) if est_total > 0 else 0,
            "work_items": items,
            "work_item_count": len(items),
        }

    # ------------------------------------------------------------------
    # detect_variation (read-only)
    # ------------------------------------------------------------------

    def detect_variation(
        self, actor: Actor, company_id: str, project_id: str
    ) -> dict[str, Any]:
        """Detect potential out-of-scope work by comparing daily logs to work items.

        Args:
            actor: The agent actor.
            company_id: Tenant scope.
            project_id: The project to check.

        Returns:
            Dict with flagged potential variations.
        """
        cutoff = (datetime.now(timezone.utc) - timedelta(days=14)).strftime("%Y-%m-%d")

        results = self._read_tx(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
            MATCH (p)-[:HAS_DAILY_LOG]->(dl:DailyLog)
            WHERE dl.deleted = false AND dl.log_date >= $cutoff
            OPTIONAL MATCH (p)-[:HAS_WORK_ITEM]->(wi:WorkItem)
            WHERE wi.deleted = false
            RETURN dl.id AS log_id,
                   dl.log_date AS log_date,
                   dl.work_performed AS work_performed,
                   dl.notes AS notes,
                   collect(DISTINCT {id: wi.id, description: wi.description}) AS work_items,
                   p.id AS project_id,
                   p.name AS project_name
            ORDER BY dl.log_date DESC
            LIMIT 14
            """,
            {
                "company_id": company_id,
                "project_id": project_id,
                "cutoff": cutoff,
            },
        )

        if not results:
            return {
                "project_id": project_id,
                "flags": [],
                "flag_count": 0,
                "message": "No recent daily logs to analyse",
            }

        stop_words = {
            "the", "a", "an", "and", "or", "in", "on", "at", "to",
            "for", "of", "with", "is", "was", "are", "were", "been",
            "be", "have", "has", "had", "do", "does", "did", "will",
            "would", "could", "should", "may", "might", "can", "this",
            "that", "these", "those", "it", "its", "not", "no", "all",
        }

        all_scope_words: set[str] = set()
        for wi in results[0]["work_items"]:
            if wi.get("id"):
                all_scope_words.update((wi.get("description") or "").lower().split())

        flags: list[dict[str, Any]] = []
        for row in results:
            log_text = " ".join(
                filter(None, [row.get("work_performed"), row.get("notes")])
            ).lower()
            if not log_text.strip():
                continue
            log_words = set(log_text.split()) - stop_words
            if not log_words:
                continue
            log_unique = log_words - all_scope_words
            overlap = 1.0 - (len(log_unique) / max(len(log_words), 1))
            if overlap < 0.4 and len(log_unique) > 3:
                flags.append({
                    "log_id": row["log_id"],
                    "log_date": row["log_date"],
                    "work_performed": row.get("work_performed") or "",
                    "overlap_ratio": round(overlap, 2),
                    "unmatched_keywords": sorted(list(log_unique))[:10],
                    "reason": "Daily log describes work not matching any work item scope",
                })

        return {
            "project_id": results[0]["project_id"],
            "project_name": results[0].get("project_name", ""),
            "flags": flags,
            "flag_count": len(flags),
            "logs_analysed": len(results),
        }

    # ------------------------------------------------------------------
    # create_variation (low-risk write)
    # ------------------------------------------------------------------

    def create_variation(
        self,
        actor: Actor,
        company_id: str,
        project_id: str,
        description: str,
        amount: float | None = None,
        work_item_ids: str = "",
        evidence_ids: str = "",
    ) -> dict[str, Any]:
        """Create a variation (change order) with evidence chain.

        Args:
            actor: The agent actor.
            company_id: Tenant scope.
            project_id: The project.
            description: What changed and why.
            amount: Estimated cost impact.
            work_item_ids: Comma-separated WorkItem IDs affected.
            evidence_ids: Comma-separated evidence node IDs.

        Returns:
            Dict with the created variation data.
        """
        var_id = self._generate_id("var")
        provenance = self._provenance_create(actor)

        num_result = self._read_tx_single(
            """
            MATCH (p:Project {id: $project_id})-[:HAS_VARIATION]->(v:Variation)
            RETURN coalesce(max(v.number), 0) + 1 AS next_number
            """,
            {"project_id": project_id},
        )
        number = num_result["next_number"] if num_result else 1

        result = self._write_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
            WHERE p.deleted = false
            CREATE (v:Variation {
                id: $var_id,
                number: $number,
                description: $description,
                amount: $amount,
                status: 'draft',
                deleted: false,
                created_by: $created_by,
                actor_type: $actor_type,
                agent_id: $agent_id,
                agent_version: $agent_version,
                model_id: $model_id,
                confidence: $confidence,
                agent_cost_cents: $agent_cost_cents,
                created_at: $created_at,
                updated_by: $updated_by,
                updated_actor_type: $updated_actor_type,
                updated_at: $updated_at
            })
            CREATE (p)-[:HAS_VARIATION]->(v)
            RETURN v.id AS variation_id, v.number AS number,
                   p.id AS project_id, p.name AS project_name
            """,
            {
                "company_id": company_id,
                "project_id": project_id,
                "var_id": var_id,
                "number": number,
                "description": description,
                "amount": amount,
                **provenance,
            },
        )

        if result is None:
            return {"error": f"Project {project_id} not found"}

        wi_ids = [x.strip() for x in work_item_ids.split(",") if x.strip()] if work_item_ids else []
        for wi_id in wi_ids:
            self._write_tx_single(
                """
                MATCH (v:Variation {id: $var_id})
                MATCH (wi:WorkItem {id: $wi_id})
                MERGE (v)-[:VARIES]->(wi)
                RETURN v.id AS id
                """,
                {"var_id": var_id, "wi_id": wi_id},
            )

        ev_ids = [x.strip() for x in evidence_ids.split(",") if x.strip()] if evidence_ids else []
        for ev_id in ev_ids:
            self._write_tx_single(
                """
                MATCH (v:Variation {id: $var_id})
                MATCH (ev {id: $ev_id})
                WHERE ev:DailyLog OR ev:TimeEntry OR ev:Document
                MERGE (v)-[:EVIDENCED_BY]->(ev)
                RETURN v.id AS id
                """,
                {"var_id": var_id, "ev_id": ev_id},
            )

        event = self.event_bus.create_event(
            event_type=EventType.VARIATION_CREATED,
            entity_id=var_id,
            entity_type="Variation",
            company_id=company_id,
            project_id=project_id,
            actor=actor,
            summary={"number": number, "description": description, "amount": amount},
        )
        self.event_bus.emit(event)

        return {
            "variation_id": result["variation_id"],
            "number": result["number"],
            "project_id": result["project_id"],
            "project_name": result["project_name"],
            "description": description,
            "amount": amount,
            "status": "draft",
            "linked_work_items": len(wi_ids),
            "linked_evidence": len(ev_ids),
            "created_by": actor.id,
        }

    # ------------------------------------------------------------------
    # get_financial_overview (read-only)
    # ------------------------------------------------------------------

    def get_financial_overview(
        self, actor: Actor, company_id: str, project_id: str
    ) -> dict[str, Any]:
        """Project-level financial summary.

        Assembles: contract value, estimated cost, actual cost, variations,
        invoiced total, paid total, profit/loss.

        Args:
            actor: The agent actor.
            company_id: Tenant scope.
            project_id: The project.

        Returns:
            Dict with full financial overview.
        """
        result = self._read_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
            WHERE p.deleted = false

            CALL {
                WITH p
                OPTIONAL MATCH (p)-[:HAS_WORK_ITEM]->(wi:WorkItem)
                WHERE wi.deleted = false
                WITH sum(COALESCE(wi.labour_hours, 0) * COALESCE(wi.labour_rate, 0)
                         + COALESCE(wi.materials_allowance, 0)) AS estimated_total
                RETURN estimated_total
            }

            CALL {
                WITH p
                OPTIONAL MATCH (p)-[:HAS_WORK_ITEM]->(wi:WorkItem)-[:HAS_TIME_ENTRY]->(te:TimeEntry)
                WHERE wi.deleted = false AND te.deleted = false
                WITH sum(COALESCE(te.regular_hours, 0) * COALESCE(wi.labour_rate, 0)) AS actual_labour
                RETURN actual_labour
            }

            CALL {
                WITH p
                OPTIONAL MATCH (p)-[:HAS_WORK_ITEM]->(wi:WorkItem)-[:USES_ITEM]->(item)
                WHERE wi.deleted = false
                WITH sum(COALESCE(item.quantity, 0) * COALESCE(item.unit_cost, 0)) AS actual_materials
                RETURN actual_materials
            }

            CALL {
                WITH p
                OPTIONAL MATCH (p)-[:HAS_VARIATION]->(v:Variation)
                WHERE v.deleted = false AND v.status = 'approved'
                With sum(COALESCE(v.amount, 0)) AS approved_variations,
                     count(v) AS variation_count
                RETURN approved_variations, variation_count
            }

            CALL {
                WITH p
                OPTIONAL MATCH (p)-[:HAS_VARIATION]->(v:Variation)
                WHERE v.deleted = false AND v.status IN ['draft', 'submitted']
                RETURN count(v) AS pending_variations
            }

            CALL {
                WITH p
                OPTIONAL MATCH (p)-[:HAS_INVOICE]->(inv:Invoice)
                WHERE inv.deleted = false AND inv.direction = 'receivable'
                With sum(COALESCE(inv.total_amount, 0)) AS invoiced_total,
                     count(inv) AS invoice_count
                RETURN invoiced_total, invoice_count
            }

            CALL {
                WITH p
                OPTIONAL MATCH (p)-[:HAS_INVOICE]->(inv:Invoice)-[:PAID_BY]->(pay:Payment)
                WHERE inv.deleted = false AND inv.direction = 'receivable'
                With sum(COALESCE(pay.amount, 0)) AS paid_total
                RETURN paid_total
            }

            RETURN p.id AS project_id, p.name AS project_name,
                   p.status AS status,
                   COALESCE(p.contract_value, 0) AS contract_value,
                   estimated_total, actual_labour, actual_materials,
                   approved_variations, variation_count, pending_variations,
                   invoiced_total, invoice_count, paid_total
            """,
            {"company_id": company_id, "project_id": project_id},
        )

        if result is None:
            return {"error": f"Project {project_id} not found"}

        actual = (result["actual_labour"] or 0) + (result["actual_materials"] or 0)
        contract = result["contract_value"] or 0
        approved_var = result["approved_variations"] or 0
        adjusted = contract + approved_var
        invoiced = result["invoiced_total"] or 0
        paid = result["paid_total"] or 0

        return {
            "project_id": result["project_id"],
            "project_name": result["project_name"],
            "status": result["status"],
            "contract_value": contract,
            "approved_variations": approved_var,
            "adjusted_contract_value": adjusted,
            "estimated_cost": result["estimated_total"] or 0,
            "actual_cost": actual,
            "actual_labour": result["actual_labour"] or 0,
            "actual_materials": result["actual_materials"] or 0,
            "projected_profit": adjusted - actual,
            "profit_margin_pct": (
                round((adjusted - actual) / adjusted * 100, 1) if adjusted > 0 else 0
            ),
            "variation_count": result["variation_count"] or 0,
            "pending_variations": result["pending_variations"] or 0,
            "invoiced_total": invoiced,
            "invoice_count": result["invoice_count"] or 0,
            "paid_total": paid,
            "outstanding": invoiced - paid,
        }

    # ------------------------------------------------------------------
    # Contract terms helpers
    # ------------------------------------------------------------------

    def _ensure_contract(
        self, actor: Actor, company_id: str, project_id: str
    ) -> str | None:
        """Ensure a Contract node exists for the project, creating one if needed.

        Args:
            actor: The agent actor.
            company_id: Tenant scope.
            project_id: The project.

        Returns:
            The contract ID, or None if the project was not found.
        """
        provenance = self._provenance_create(actor)
        result = self._write_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
            WHERE p.deleted = false
            WITH p
            OPTIONAL MATCH (p)-[:HAS_CONTRACT]->(existing:Contract)
            WITH p, existing
            WHERE existing IS NULL
            CREATE (ctr:Contract {
                id: $contract_id,
                status: 'draft',
                created_by: $created_by,
                actor_type: $actor_type,
                agent_id: $agent_id,
                agent_version: $agent_version,
                model_id: $model_id,
                confidence: $confidence,
                agent_cost_cents: $agent_cost_cents,
                created_at: $created_at,
                updated_by: $updated_by,
                updated_actor_type: $updated_actor_type,
                updated_at: $updated_at
            })
            CREATE (p)-[:HAS_CONTRACT]->(ctr)
            RETURN ctr.id AS contract_id
            """,
            {
                "company_id": company_id,
                "project_id": project_id,
                "contract_id": self._generate_id("ctr"),
                **provenance,
            },
        )
        if result is not None:
            return result["contract_id"]

        existing = self._read_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
                  -[:HAS_CONTRACT]->(ctr:Contract)
            RETURN ctr.id AS contract_id
            """,
            {"company_id": company_id, "project_id": project_id},
        )
        if existing is None:
            return None
        return existing["contract_id"]

    # ------------------------------------------------------------------
    # Contract terms: Payment milestones
    # ------------------------------------------------------------------

    def create_payment_milestone(
        self,
        actor: Actor,
        company_id: str,
        project_id: str,
        description: str,
        trigger_condition: str,
        percentage: float | None = None,
        fixed_amount_cents: int | None = None,
        sort_order: int = 0,
    ) -> dict[str, Any]:
        """Create a payment milestone on a project's contract.

        Auto-creates the Contract node if it doesn't exist yet.

        Args:
            actor: The agent actor.
            company_id: Tenant scope.
            project_id: The project.
            description: Milestone description.
            trigger_condition: What triggers this payment.
            percentage: Percentage of contract value (mutually exclusive with fixed_amount_cents).
            fixed_amount_cents: Fixed amount in cents (mutually exclusive with percentage).
            sort_order: Display ordering.

        Returns:
            Dict with the created milestone.
        """
        contract_id = self._ensure_contract(actor, company_id, project_id)
        if contract_id is None:
            return {"error": f"Project {project_id} not found"}

        pms_id = self._generate_id("pms")
        provenance = self._provenance_create(actor)

        props: dict[str, Any] = {
            "id": pms_id,
            "description": description,
            "percentage": percentage,
            "fixed_amount_cents": fixed_amount_cents,
            "trigger_condition": trigger_condition,
            "sort_order": sort_order,
            "status": "pending",
            **provenance,
        }

        result = self._write_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
                  -[:HAS_CONTRACT]->(ctr:Contract {id: $contract_id})
            CREATE (pm:PaymentMilestone $props)
            CREATE (ctr)-[:HAS_PAYMENT_MILESTONE]->(pm)
            RETURN pm.id AS milestone_id, pm.description AS description,
                   pm.percentage AS percentage,
                   pm.fixed_amount_cents AS fixed_amount_cents,
                   pm.trigger_condition AS trigger_condition,
                   pm.sort_order AS sort_order, pm.status AS status,
                   p.id AS project_id, p.name AS project_name
            """,
            {
                "company_id": company_id,
                "project_id": project_id,
                "contract_id": contract_id,
                "props": props,
            },
        )

        if result is None:
            return {"error": f"Project {project_id} not found"}

        return dict(result)

    def update_payment_milestone(
        self,
        actor: Actor,
        company_id: str,
        project_id: str,
        milestone_id: str,
        description: str | None = None,
        percentage: float | None = None,
        fixed_amount_cents: int | None = None,
        trigger_condition: str | None = None,
        sort_order: int | None = None,
        status: str | None = None,
    ) -> dict[str, Any]:
        """Update a payment milestone on a project's contract.

        Args:
            actor: The agent actor.
            company_id: Tenant scope.
            project_id: The project.
            milestone_id: The milestone to update.
            description: Updated description.
            percentage: Updated percentage.
            fixed_amount_cents: Updated fixed amount.
            trigger_condition: Updated trigger condition.
            sort_order: Updated sort order.
            status: Updated status (pending, invoiced, paid).

        Returns:
            Dict with the updated milestone.
        """
        updates: dict[str, Any] = {}
        if description is not None:
            updates["description"] = description
        if percentage is not None:
            updates["percentage"] = percentage
        if fixed_amount_cents is not None:
            updates["fixed_amount_cents"] = fixed_amount_cents
        if trigger_condition is not None:
            updates["trigger_condition"] = trigger_condition
        if sort_order is not None:
            updates["sort_order"] = sort_order
        if status is not None:
            updates["status"] = status

        if not updates:
            return {"error": "No fields to update"}

        provenance = self._provenance_update(actor)
        updates.update(provenance)

        result = self._write_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
                  -[:HAS_CONTRACT]->(ctr:Contract)
                  -[:HAS_PAYMENT_MILESTONE]->(pm:PaymentMilestone {id: $milestone_id})
            SET pm += $updates
            RETURN pm.id AS milestone_id, pm.description AS description,
                   pm.percentage AS percentage,
                   pm.fixed_amount_cents AS fixed_amount_cents,
                   pm.trigger_condition AS trigger_condition,
                   pm.sort_order AS sort_order, pm.status AS status,
                   p.id AS project_id, p.name AS project_name
            """,
            {
                "company_id": company_id,
                "project_id": project_id,
                "milestone_id": milestone_id,
                "updates": updates,
            },
        )

        if result is None:
            return {"error": f"PaymentMilestone {milestone_id} not found"}

        return dict(result)

    def remove_payment_milestone(
        self,
        actor: Actor,
        company_id: str,
        project_id: str,
        milestone_id: str,
    ) -> dict[str, Any]:
        """Remove a payment milestone from a project's contract.

        Args:
            actor: The agent actor.
            company_id: Tenant scope.
            project_id: The project.
            milestone_id: The milestone to remove.

        Returns:
            Dict confirming removal.
        """
        result = self._write_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
                  -[:HAS_CONTRACT]->(ctr:Contract)
                  -[:HAS_PAYMENT_MILESTONE]->(pm:PaymentMilestone {id: $milestone_id})
            WITH pm, p, pm.description AS description
            DETACH DELETE pm
            RETURN $milestone_id AS milestone_id, description,
                   p.id AS project_id, p.name AS project_name,
                   'removed' AS status
            """,
            {
                "company_id": company_id,
                "project_id": project_id,
                "milestone_id": milestone_id,
            },
        )

        if result is None:
            return {"error": f"PaymentMilestone {milestone_id} not found"}

        return dict(result)

    # ------------------------------------------------------------------
    # Contract terms: Conditions
    # ------------------------------------------------------------------

    def create_condition(
        self,
        actor: Actor,
        company_id: str,
        project_id: str,
        category: str,
        description: str,
        responsible_party: str | None = None,
    ) -> dict[str, Any]:
        """Create a condition on a project's contract.

        Auto-creates the Contract node if it doesn't exist yet.

        Args:
            actor: The agent actor.
            company_id: Tenant scope.
            project_id: The project.
            category: Condition type (site_access, working_hours, permits,
                materials, client_obligations, insurance, other).
            description: Condition text.
            responsible_party: Who is responsible for this condition.

        Returns:
            Dict with the created condition.
        """
        contract_id = self._ensure_contract(actor, company_id, project_id)
        if contract_id is None:
            return {"error": f"Project {project_id} not found"}

        cond_id = self._generate_id("cond")
        provenance = self._provenance_create(actor)

        props: dict[str, Any] = {
            "id": cond_id,
            "category": category,
            "description": description,
            "responsible_party": responsible_party,
            **provenance,
        }

        result = self._write_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
                  -[:HAS_CONTRACT]->(ctr:Contract {id: $contract_id})
            CREATE (cond:Condition $props)
            CREATE (ctr)-[:HAS_CONDITION]->(cond)
            RETURN cond.id AS condition_id, cond.category AS category,
                   cond.description AS description,
                   cond.responsible_party AS responsible_party,
                   p.id AS project_id, p.name AS project_name
            """,
            {
                "company_id": company_id,
                "project_id": project_id,
                "contract_id": contract_id,
                "props": props,
            },
        )

        if result is None:
            return {"error": f"Project {project_id} not found"}

        return dict(result)

    def update_condition(
        self,
        actor: Actor,
        company_id: str,
        project_id: str,
        condition_id: str,
        category: str | None = None,
        description: str | None = None,
        responsible_party: str | None = None,
    ) -> dict[str, Any]:
        """Update a condition on a project's contract.

        Args:
            actor: The agent actor.
            company_id: Tenant scope.
            project_id: The project.
            condition_id: The condition to update.
            category: Updated category.
            description: Updated description.
            responsible_party: Updated responsible party.

        Returns:
            Dict with the updated condition.
        """
        updates: dict[str, Any] = {}
        if category is not None:
            updates["category"] = category
        if description is not None:
            updates["description"] = description
        if responsible_party is not None:
            updates["responsible_party"] = responsible_party

        if not updates:
            return {"error": "No fields to update"}

        provenance = self._provenance_update(actor)
        updates.update(provenance)

        result = self._write_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
                  -[:HAS_CONTRACT]->(ctr:Contract)
                  -[:HAS_CONDITION]->(cond:Condition {id: $condition_id})
            SET cond += $updates
            RETURN cond.id AS condition_id, cond.category AS category,
                   cond.description AS description,
                   cond.responsible_party AS responsible_party,
                   p.id AS project_id, p.name AS project_name
            """,
            {
                "company_id": company_id,
                "project_id": project_id,
                "condition_id": condition_id,
                "updates": updates,
            },
        )

        if result is None:
            return {"error": f"Condition {condition_id} not found"}

        return dict(result)

    def remove_condition(
        self,
        actor: Actor,
        company_id: str,
        project_id: str,
        condition_id: str,
    ) -> dict[str, Any]:
        """Remove a condition from a project's contract.

        Args:
            actor: The agent actor.
            company_id: Tenant scope.
            project_id: The project.
            condition_id: The condition to remove.

        Returns:
            Dict confirming removal.
        """
        result = self._write_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
                  -[:HAS_CONTRACT]->(ctr:Contract)
                  -[:HAS_CONDITION]->(cond:Condition {id: $condition_id})
            WITH cond, p, cond.description AS description, cond.category AS category
            DETACH DELETE cond
            RETURN $condition_id AS condition_id, description, category,
                   p.id AS project_id, p.name AS project_name,
                   'removed' AS status
            """,
            {
                "company_id": company_id,
                "project_id": project_id,
                "condition_id": condition_id,
            },
        )

        if result is None:
            return {"error": f"Condition {condition_id} not found"}

        return dict(result)

    # ------------------------------------------------------------------
    # Contract terms: Warranty
    # ------------------------------------------------------------------

    def set_warranty_terms(
        self,
        actor: Actor,
        company_id: str,
        project_id: str,
        period_months: int,
        scope: str,
        start_trigger: str = "practical_completion",
        terms: str | None = None,
    ) -> dict[str, Any]:
        """Upsert warranty terms on a project's contract.

        Replaces any existing warranty. Auto-creates Contract if needed.

        Args:
            actor: The agent actor.
            company_id: Tenant scope.
            project_id: The project.
            period_months: Warranty duration in months.
            scope: What the warranty covers.
            start_trigger: Event that starts the warranty period.
            terms: Additional terms and conditions.

        Returns:
            Dict with the warranty details.
        """
        contract_id = self._ensure_contract(actor, company_id, project_id)
        if contract_id is None:
            return {"error": f"Project {project_id} not found"}

        wrty_id = self._generate_id("wrty")
        provenance = self._provenance_create(actor)

        props: dict[str, Any] = {
            "id": wrty_id,
            "period_months": period_months,
            "scope": scope,
            "start_trigger": start_trigger,
            "terms": terms,
            "start_date": None,
            "end_date": None,
            **provenance,
        }

        result = self._write_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
                  -[:HAS_CONTRACT]->(ctr:Contract {id: $contract_id})
            OPTIONAL MATCH (ctr)-[:HAS_WARRANTY]->(old:Warranty)
            WITH ctr, p, old
            FOREACH (_ IN CASE WHEN old IS NOT NULL THEN [1] ELSE [] END |
                DETACH DELETE old
            )
            WITH ctr, p
            CREATE (w:Warranty $props)
            CREATE (ctr)-[:HAS_WARRANTY]->(w)
            RETURN w.id AS warranty_id, w.period_months AS period_months,
                   w.scope AS scope, w.start_trigger AS start_trigger,
                   w.terms AS terms,
                   p.id AS project_id, p.name AS project_name
            """,
            {
                "company_id": company_id,
                "project_id": project_id,
                "contract_id": contract_id,
                "props": props,
            },
        )

        if result is None:
            return {"error": f"Project {project_id} not found"}

        return dict(result)

    # ------------------------------------------------------------------
    # Contract terms: Retention
    # ------------------------------------------------------------------

    def set_retention_terms(
        self,
        actor: Actor,
        company_id: str,
        project_id: str,
        retention_pct: float,
        payment_terms_days: int | None = None,
    ) -> dict[str, Any]:
        """Set retention percentage and payment terms on a project's contract.

        Auto-creates Contract if needed.

        Args:
            actor: The agent actor.
            company_id: Tenant scope.
            project_id: The project.
            retention_pct: Retention percentage (0-100).
            payment_terms_days: Payment terms in days (e.g. 30 = Net 30).

        Returns:
            Dict with the updated contract terms.
        """
        contract_id = self._ensure_contract(actor, company_id, project_id)
        if contract_id is None:
            return {"error": f"Project {project_id} not found"}

        provenance = self._provenance_update(actor)
        updates: dict[str, Any] = {
            "retention_pct": retention_pct,
            **provenance,
        }
        if payment_terms_days is not None:
            updates["payment_terms"] = f"Net {payment_terms_days}"

        result = self._write_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
                  -[:HAS_CONTRACT]->(ctr:Contract {id: $contract_id})
            SET ctr += $updates
            RETURN ctr.id AS contract_id,
                   ctr.retention_pct AS retention_pct,
                   ctr.payment_terms AS payment_terms,
                   ctr.status AS contract_status,
                   p.id AS project_id, p.name AS project_name
            """,
            {
                "company_id": company_id,
                "project_id": project_id,
                "contract_id": contract_id,
                "updates": updates,
            },
        )

        if result is None:
            return {"error": f"Project {project_id} not found"}

        return dict(result)

    # ------------------------------------------------------------------
    # Contract terms: Summary
    # ------------------------------------------------------------------

    def get_contract_summary(
        self,
        actor: Actor,
        company_id: str,
        project_id: str,
    ) -> dict[str, Any]:
        """Get a full contract summary — contract, milestones, conditions, warranty.

        Args:
            actor: The agent actor.
            company_id: Tenant scope.
            project_id: The project.

        Returns:
            Dict with complete contract terms overview.
        """
        result = self._read_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
            WHERE p.deleted = false
            OPTIONAL MATCH (p)-[:HAS_CONTRACT]->(ctr:Contract)
            RETURN p.id AS project_id, p.name AS project_name,
                   p.project_type AS project_type,
                   ctr.id AS contract_id,
                   ctr.status AS contract_status,
                   ctr.retention_pct AS retention_pct,
                   ctr.payment_terms AS payment_terms,
                   ctr.value AS contract_value
            """,
            {"company_id": company_id, "project_id": project_id},
        )

        if result is None:
            return {"error": f"Project {project_id} not found"}

        summary: dict[str, Any] = {
            "project_id": result["project_id"],
            "project_name": result["project_name"],
            "project_type": result["project_type"],
            "has_contract": result["contract_id"] is not None,
            "contract_id": result["contract_id"],
            "contract_status": result["contract_status"],
            "retention_pct": result["retention_pct"],
            "payment_terms": result["payment_terms"],
            "contract_value": result["contract_value"],
            "payment_milestones": [],
            "conditions": [],
            "warranty": None,
        }

        if result["contract_id"] is None:
            return summary

        # Fetch payment milestones
        milestones = self._read_tx(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
                  -[:HAS_CONTRACT]->(ctr:Contract)
                  -[:HAS_PAYMENT_MILESTONE]->(pm:PaymentMilestone)
            RETURN pm.id AS milestone_id, pm.description AS description,
                   pm.percentage AS percentage,
                   pm.fixed_amount_cents AS fixed_amount_cents,
                   pm.trigger_condition AS trigger_condition,
                   pm.sort_order AS sort_order, pm.status AS status
            ORDER BY pm.sort_order ASC
            """,
            {"company_id": company_id, "project_id": project_id},
        )
        summary["payment_milestones"] = [dict(m) for m in milestones]

        # Fetch conditions
        conditions = self._read_tx(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
                  -[:HAS_CONTRACT]->(ctr:Contract)
                  -[:HAS_CONDITION]->(cond:Condition)
            RETURN cond.id AS condition_id, cond.category AS category,
                   cond.description AS description,
                   cond.responsible_party AS responsible_party
            ORDER BY cond.category ASC
            """,
            {"company_id": company_id, "project_id": project_id},
        )
        summary["conditions"] = [dict(c) for c in conditions]

        # Fetch warranty
        warranty = self._read_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
                  -[:HAS_CONTRACT]->(ctr:Contract)
                  -[:HAS_WARRANTY]->(w:Warranty)
            RETURN w.id AS warranty_id, w.period_months AS period_months,
                   w.scope AS scope, w.start_trigger AS start_trigger,
                   w.terms AS terms
            """,
            {"company_id": company_id, "project_id": project_id},
        )
        if warranty is not None:
            summary["warranty"] = dict(warranty)

        return summary

    # ------------------------------------------------------------------
    # Contract terms: Intelligence — suggest_contract_terms
    # ------------------------------------------------------------------

    def suggest_contract_terms(
        self,
        actor: Actor,
        company_id: str,
        project_id: str,
    ) -> dict[str, Any]:
        """Suggest contract terms based on project type, value, and company history.

        Queries:
        - The current project's type, value, client
        - Completed projects of similar type/value that have contract terms
        - Returns suggested payment milestones, conditions, retention, warranty

        Falls back to industry defaults if no historical data exists.

        Args:
            actor: The agent actor.
            company_id: Tenant scope.
            project_id: The project to suggest terms for.

        Returns:
            Dict with suggested contract terms and reasoning.
        """
        # 1. Get current project details
        project = self._read_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
            WHERE p.deleted = false
            OPTIONAL MATCH (p)-[:HAS_WORK_ITEM]->(wi:WorkItem)
            WHERE wi.deleted IS NULL OR wi.deleted = false
            WITH p,
                 sum(COALESCE(wi.sell_price_cents, 0)) AS estimated_value_cents,
                 count(wi) AS work_item_count
            RETURN p.id AS project_id, p.name AS project_name,
                   p.project_type AS project_type,
                   p.client_name AS client_name,
                   p.address AS address,
                   estimated_value_cents,
                   work_item_count
            """,
            {"company_id": company_id, "project_id": project_id},
        )

        if project is None:
            return {"error": f"Project {project_id} not found"}

        project_type = project["project_type"] or "residential"
        estimated_value = project["estimated_value_cents"] or 0

        # 2. Query historical projects with contract terms
        history = self._read_tx(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(hp:Project)
            WHERE hp.deleted = false
              AND hp.id <> $project_id
              AND hp.state IN ['active', 'completed', 'closed']
            OPTIONAL MATCH (hp)-[:HAS_CONTRACT]->(hctr:Contract)
            WHERE hctr IS NOT NULL
            OPTIONAL MATCH (hctr)-[:HAS_PAYMENT_MILESTONE]->(hpm:PaymentMilestone)
            OPTIONAL MATCH (hctr)-[:HAS_CONDITION]->(hcond:Condition)
            OPTIONAL MATCH (hctr)-[:HAS_WARRANTY]->(hw:Warranty)
            WITH hp, hctr,
                 collect(DISTINCT CASE WHEN hpm IS NOT NULL THEN {
                     description: hpm.description,
                     percentage: hpm.percentage,
                     trigger_condition: hpm.trigger_condition
                 } ELSE null END) AS milestones,
                 collect(DISTINCT CASE WHEN hcond IS NOT NULL THEN {
                     category: hcond.category,
                     description: hcond.description
                 } ELSE null END) AS conditions,
                 hw
            WHERE hctr IS NOT NULL
            RETURN hp.project_type AS project_type,
                   hp.name AS project_name,
                   hctr.retention_pct AS retention_pct,
                   hctr.payment_terms AS payment_terms,
                   milestones,
                   conditions,
                   CASE WHEN hw IS NOT NULL THEN {
                       period_months: hw.period_months,
                       scope: hw.scope,
                       start_trigger: hw.start_trigger
                   } ELSE null END AS warranty
            ORDER BY hp.created_at DESC
            LIMIT 5
            """,
            {"company_id": company_id, "project_id": project_id},
        )
        history_rows = [dict(r) for r in history]

        # 3. Build suggestions with reasoning
        suggestions: dict[str, Any] = {
            "project_id": project["project_id"],
            "project_name": project["project_name"],
            "project_type": project_type,
            "estimated_value_cents": estimated_value,
            "based_on_history": len(history_rows) > 0,
            "historical_projects_analysed": len(history_rows),
            "suggested_payment_milestones": [],
            "suggested_conditions": [],
            "suggested_retention": None,
            "suggested_warranty": None,
        }

        # -- Payment milestones --
        # Check if historical projects of similar type have patterns
        historical_milestones: list[dict[str, Any]] = []
        for row in history_rows:
            ms_list = [m for m in row.get("milestones", []) if m is not None]
            if ms_list:
                historical_milestones.extend(ms_list)

        if historical_milestones:
            # Use pattern from company history
            seen_triggers: set[str] = set()
            for hm in historical_milestones:
                trigger = hm.get("trigger_condition", "")
                if trigger not in seen_triggers:
                    seen_triggers.add(trigger)
                    suggestions["suggested_payment_milestones"].append({
                        "description": hm.get("description", ""),
                        "percentage": hm.get("percentage"),
                        "trigger_condition": trigger,
                        "reasoning": "Based on your payment structure from previous projects",
                    })
        else:
            # Industry defaults based on project type and value
            if project_type in ("commercial", "industrial") and estimated_value > 5_000_000:
                suggestions["suggested_payment_milestones"] = [
                    {
                        "description": "Deposit on contract signing",
                        "percentage": 10.0,
                        "trigger_condition": "Contract execution",
                        "reasoning": "Standard 10% deposit for commercial projects over $50K to cover mobilisation costs",
                    },
                    {
                        "description": "Rough-in complete",
                        "percentage": 30.0,
                        "trigger_condition": "Rough-in inspection passed",
                        "reasoning": "Progress payment at rough-in covers the bulk of labour and materials already committed",
                    },
                    {
                        "description": "Substantial completion",
                        "percentage": 50.0,
                        "trigger_condition": "Substantial completion certificate issued",
                        "reasoning": "Major payment at substantial completion to cover remaining materials and close out most costs",
                    },
                    {
                        "description": "Final payment on completion",
                        "percentage": 10.0,
                        "trigger_condition": "Final inspection passed and punch list complete",
                        "reasoning": "Final 10% held until all work is verified complete, covers retention release",
                    },
                ]
            elif project_type in ("commercial", "industrial"):
                suggestions["suggested_payment_milestones"] = [
                    {
                        "description": "Deposit on contract signing",
                        "percentage": 20.0,
                        "trigger_condition": "Contract execution",
                        "reasoning": "20% deposit for smaller commercial work to cover material procurement",
                    },
                    {
                        "description": "Progress payment at 50% complete",
                        "percentage": 40.0,
                        "trigger_condition": "50% of scope items marked complete",
                        "reasoning": "Mid-project payment keeps cash flow healthy",
                    },
                    {
                        "description": "Balance on completion",
                        "percentage": 40.0,
                        "trigger_condition": "Final inspection passed",
                        "reasoning": "Remaining balance on verified completion",
                    },
                ]
            else:
                # Residential default — simpler structure
                suggestions["suggested_payment_milestones"] = [
                    {
                        "description": "Deposit",
                        "percentage": 50.0,
                        "trigger_condition": "Contract signed and work scheduled",
                        "reasoning": "Standard residential deposit — covers material procurement and mobilisation",
                    },
                    {
                        "description": "Balance on completion",
                        "percentage": 50.0,
                        "trigger_condition": "Work complete and client walkthrough done",
                        "reasoning": "Simple 50/50 split works well for residential — easy for homeowners to understand",
                    },
                ]

        # -- Conditions --
        historical_conditions: list[dict[str, Any]] = []
        for row in history_rows:
            cond_list = [c for c in row.get("conditions", []) if c is not None]
            if cond_list:
                historical_conditions.extend(cond_list)

        if historical_conditions:
            seen_descs: set[str] = set()
            for hc in historical_conditions:
                desc = hc.get("description", "")
                if desc not in seen_descs:
                    seen_descs.add(desc)
                    suggestions["suggested_conditions"].append({
                        "category": hc.get("category", "other"),
                        "description": desc,
                        "reasoning": "Used in your previous projects",
                    })
        else:
            # Defaults based on project type
            base_conditions = [
                {
                    "category": "site_access",
                    "description": "Client to provide clear access to the work area during normal working hours",
                    "reasoning": "Protects you from delays caused by blocked access — common issue on renovation work",
                },
                {
                    "category": "working_hours",
                    "description": "Work performed during normal business hours (7:00 AM - 4:00 PM, Monday-Friday)",
                    "reasoning": "Sets expectations on scheduling and avoids uncompensated overtime disputes",
                },
                {
                    "category": "permits",
                    "description": "Client responsible for all permits and approvals unless otherwise agreed",
                    "reasoning": "Avoids permit cost surprises — clarifies who handles the permitting process and fees",
                },
            ]

            if project_type in ("commercial", "industrial"):
                base_conditions.append({
                    "category": "materials",
                    "description": "Material prices valid for 30 days from quote date; subject to re-pricing if project start is delayed beyond this period",
                    "reasoning": "Material price volatility protection — critical for commercial projects where procurement lead times are long",
                })
                base_conditions.append({
                    "category": "client_obligations",
                    "description": "Client to provide clean, powered workspace with adequate lighting for safe work",
                    "reasoning": "Common for commercial fit-outs — ensures you are not paying for temporary power and lighting",
                })
            else:
                base_conditions.append({
                    "category": "materials",
                    "description": "Material selections and colours to be confirmed before ordering; changes after ordering may incur additional cost",
                    "reasoning": "Residential clients often change their minds on finishes — this protects against reorder costs",
                })

            suggestions["suggested_conditions"] = base_conditions

        # -- Retention --
        historical_retentions = [
            r["retention_pct"] for r in history_rows
            if r.get("retention_pct") is not None and r["retention_pct"] > 0
        ]

        if historical_retentions:
            avg_retention = sum(historical_retentions) / len(historical_retentions)
            suggestions["suggested_retention"] = {
                "retention_pct": round(avg_retention, 1),
                "payment_terms_days": 30,
                "reasoning": f"Your average retention across {len(historical_retentions)} previous projects is {round(avg_retention, 1)}%",
            }
        elif project_type in ("commercial", "industrial") and estimated_value > 5_000_000:
            suggestions["suggested_retention"] = {
                "retention_pct": 5.0,
                "payment_terms_days": 30,
                "reasoning": "5% retention is standard for commercial projects over $50K — held until defects liability period ends",
            }
        elif project_type in ("commercial", "industrial"):
            suggestions["suggested_retention"] = {
                "retention_pct": 10.0,
                "payment_terms_days": 30,
                "reasoning": "10% retention common for smaller commercial jobs — released after final inspection",
            }
        else:
            suggestions["suggested_retention"] = {
                "retention_pct": 0.0,
                "payment_terms_days": None,
                "reasoning": "Retention is uncommon for residential work — the deposit/balance structure handles risk instead",
            }

        # -- Warranty --
        historical_warranties = [
            r["warranty"] for r in history_rows
            if r.get("warranty") is not None
        ]

        if historical_warranties:
            hw = historical_warranties[0]
            suggestions["suggested_warranty"] = {
                "period_months": hw.get("period_months", 12),
                "scope": hw.get("scope", "All work performed under this contract"),
                "start_trigger": hw.get("start_trigger", "practical_completion"),
                "reasoning": "Based on warranty terms from your previous projects",
            }
        elif project_type in ("commercial", "industrial"):
            suggestions["suggested_warranty"] = {
                "period_months": 12,
                "scope": "All workmanship and materials supplied under this contract",
                "start_trigger": "practical_completion",
                "reasoning": "12-month defects liability period is standard for commercial construction work",
            }
        else:
            suggestions["suggested_warranty"] = {
                "period_months": 12,
                "scope": "All workmanship performed under this contract",
                "start_trigger": "practical_completion",
                "reasoning": "12-month warranty gives homeowners confidence and is standard in residential trades",
            }

        return suggestions

    # ------------------------------------------------------------------
    # Unified tool dispatch (for MCP server integration)
    # ------------------------------------------------------------------

    def invoke_tool(
        self,
        tool_name: str,
        actor: Actor,
        company_id: str,
        parameters: dict[str, Any],
        guardrail_actor: Actor | None = None,
    ) -> dict[str, Any]:
        """Invoke a tool by name with guardrail checks.

        This is the main entry point for the MCP server. It:
        1. Runs pre-execution guardrail checks
        2. Dispatches to the correct tool implementation
        3. Returns the result or error

        Args:
            tool_name: The MCP tool name.
            actor: The actor for entity provenance on mutations.
            company_id: Tenant scope.
            parameters: Tool-specific parameters.
            guardrail_actor: Optional separate actor for guardrail checks.
                When the chat agent invokes tools on behalf of an
                authenticated human user, pass the human actor here
                so the user's Clerk authentication bypasses agent-specific
                guardrails (scope, rate limit, budget), while ``actor``
                carries agent provenance for entity creation.

        Returns:
            The tool result dict, or an error dict.
        """
        # Pre-execution check — use guardrail_actor when provided so
        # human-initiated chat tool calls bypass agent guardrails.
        check_actor = guardrail_actor or actor
        check = self.guardrails.pre_execution_check(
            agent_id=check_actor.id,
            company_id=company_id,
            tool_name=tool_name,
            parameters=parameters,
            actor_type=check_actor.type,
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
            "get_daily_log_status": lambda: self.get_daily_log_status(
                actor, company_id, parameters["project_id"],
            ),
            "capture_lead": lambda: self.capture_lead(
                actor, company_id,
                parameters.get("name", "Untitled Lead"),
                parameters.get("description", ""),
                parameters.get("project_type", ""),
                parameters.get("address", ""),
                parameters.get("client_name", ""),
                parameters.get("client_email", ""),
                parameters.get("client_phone", ""),
                parameters.get("contract_type"),
            ),
            "qualify_project": lambda: self.qualify_project(
                actor, company_id, parameters["project_id"],
            ),
            "check_capacity": lambda: self.check_capacity(
                actor, company_id,
            ),
            "get_schedule": lambda: self.get_schedule(
                actor, company_id, parameters["project_id"],
                parameters.get("weeks_ahead", 4),
            ),
            "assign_workers": lambda: self.assign_workers(
                actor, company_id, parameters["project_id"],
                parameters["work_item_id"],
                worker_ids=parameters.get("worker_ids"),
                crew_id=parameters.get("crew_id"),
            ),
            "detect_conflicts": lambda: self.detect_conflicts(
                actor, company_id, parameters["project_id"],
            ),
            "check_sub_compliance": lambda: self.check_sub_compliance(
                actor, company_id, parameters["sub_company_id"],
            ),
            "get_sub_performance": lambda: self.get_sub_performance(
                actor, company_id, parameters["sub_company_id"],
            ),
            "list_subs": lambda: self.list_subs(
                actor, company_id,
            ),
            # Session D: Execute & Document
            "create_daily_log": lambda: self.create_daily_log(
                actor, company_id, parameters["project_id"],
                parameters.get("log_date", ""),
            ),
            "auto_populate_daily_log": lambda: self.auto_populate_daily_log(
                actor, company_id, parameters["project_id"],
                parameters.get("log_date", ""),
            ),
            "record_time": lambda: self.record_time(
                actor, company_id, parameters["project_id"],
                parameters["worker_id"], parameters["work_item_id"],
                parameters["clock_in"],
                parameters.get("clock_out", ""),
                parameters.get("date", ""),
            ),
            "report_quality_observation": lambda: self.report_quality_observation(
                actor, company_id, parameters["project_id"],
                parameters["description"],
                parameters.get("location", ""),
                parameters.get("result_status", "pass"),
                parameters.get("score"),
            ),
            # Session D: Manage Money
            "get_job_cost_summary": lambda: self.get_job_cost_summary(
                actor, company_id, parameters["project_id"],
            ),
            "detect_variation": lambda: self.detect_variation(
                actor, company_id, parameters["project_id"],
            ),
            "create_variation": lambda: self.create_variation(
                actor, company_id, parameters["project_id"],
                parameters["description"],
                parameters.get("amount"),
                parameters.get("work_item_ids", ""),
                parameters.get("evidence_ids", ""),
            ),
            "get_financial_overview": lambda: self.get_financial_overview(
                actor, company_id, parameters["project_id"],
            ),
            # Session E: Estimate & Price
            "create_work_item": lambda: self.create_work_item(
                actor, company_id, parameters["project_id"],
                parameters["description"],
                parameters.get("quantity"),
                parameters.get("unit"),
                parameters.get("margin_pct"),
                parameters.get("work_package_id"),
                parameters.get("work_category_id"),
            ),
            "update_work_item": lambda: self.update_work_item(
                actor, company_id, parameters["project_id"],
                parameters["work_item_id"],
                parameters.get("description"),
                parameters.get("quantity"),
                parameters.get("unit"),
                parameters.get("margin_pct"),
                parameters.get("state"),
                parameters.get("scale_children", True),
            ),
            "remove_work_item": lambda: self.remove_work_item(
                actor, company_id, parameters["project_id"],
                parameters["work_item_id"],
            ),
            "get_estimate_summary": lambda: self.get_estimate_summary(
                actor, company_id, parameters["project_id"],
            ),
            "search_historical_rates": lambda: self.search_historical_rates(
                actor, company_id,
                parameters.get("description"),
                parameters.get("work_category_id"),
            ),
            "create_labour": lambda: self.create_labour(
                actor, company_id, parameters["project_id"],
                parameters["work_item_id"],
                parameters["task"],
                parameters["rate_cents"],
                parameters["hours"],
                parameters.get("notes", ""),
                rate_source_id=parameters.get("rate_source_id"),
                rate_source_type=parameters.get("rate_source_type"),
                productivity_source_id=parameters.get("productivity_source_id"),
                productivity_source_type=parameters.get("productivity_source_type"),
                source_reasoning=parameters.get("source_reasoning", ""),
            ),
            "create_item": lambda: self.create_item(
                actor, company_id, parameters["project_id"],
                parameters["work_item_id"],
                parameters["description"],
                parameters["quantity"],
                parameters["unit_cost_cents"],
                parameters.get("unit", "EA"),
                parameters.get("product", ""),
                parameters.get("notes", ""),
                price_source_id=parameters.get("price_source_id"),
                price_source_type=parameters.get("price_source_type"),
                source_reasoning=parameters.get("source_reasoning", ""),
                source_url=parameters.get("source_url"),
            ),
            # Source cascade lookup + capture tools
            "get_rate_suggestion": lambda: self.get_rate_suggestion(
                actor, company_id,
                parameters.get("project_id", ""),
                parameters["trade"],
                parameters["role"],
            ),
            "suggest_productivity": lambda: self.suggest_productivity(
                actor, company_id,
                parameters.get("project_id", ""),
                parameters["trade"],
                parameters["work_description"],
            ),
            "get_material_history": lambda: self.get_material_history(
                actor, company_id,
                parameters.get("project_id", ""),
                parameters["description"],
            ),
            "search_material_price": lambda: self.search_material_price(
                actor, company_id,
                parameters.get("project_id", ""),
                parameters["description"],
                parameters.get("unit", "EA"),
            ),
            "capture_rate": lambda: self.capture_rate(
                actor, company_id,
                parameters.get("project_id", ""),
                parameters["trade"],
                parameters["role"],
                parameters["rate_cents"],
                parameters.get("description", ""),
            ),
            "capture_material_price": lambda: self.capture_material_price(
                actor, company_id,
                parameters.get("project_id", ""),
                parameters["description"],
                parameters["unit"],
                parameters["unit_cost_cents"],
                parameters.get("supplier_name", ""),
                parameters.get("source_url", ""),
            ),
            "create_insight": lambda: self.create_insight(
                actor, company_id,
                parameters["scope"],
                parameters["scope_value"],
                parameters["statement"],
                parameters["adjustment_type"],
                parameters.get("adjustment_value"),
                parameters.get("confidence", 0.5),
                parameters.get("source_context", ""),
            ),
            # Layer 4: Knowledge accumulation
            "apply_insight": lambda: self.apply_insight(
                actor, company_id,
                parameters["insight_id"],
                parameters.get("context", ""),
            ),
            "correct_insight": lambda: self.correct_insight(
                actor, company_id,
                parameters["insight_id"],
                parameters["correction_note"],
            ),
            "find_applicable_insights_for_work": lambda: self.find_applicable_insights_for_work(
                actor, company_id,
                parameters["project_id"],
                parameters["work_description"],
                parameters["trade"],
            ),
            "derive_productivity_from_actuals": lambda: self.derive_productivity_from_actuals(
                actor, company_id,
                parameters["project_id"],
                parameters["work_item_id"],
            ),
            "update_productivity_rate_from_actuals": lambda: self.update_productivity_rate_from_actuals(
                actor, company_id,
                parameters["productivity_rate_id"],
                parameters["new_data_point_rate"],
                parameters.get("new_data_point_sample_size", 1),
            ),
            "update_material_price_from_purchase": lambda: self.update_material_price_from_purchase(
                actor, company_id,
                parameters["description"],
                parameters["unit_cost_cents"],
                parameters.get("unit", "EA"),
                parameters.get("supplier_name", ""),
                parameters.get("location", ""),
                parameters.get("source_url", ""),
            ),
            "list_contractor_knowledge": lambda: self.list_contractor_knowledge(
                actor, company_id,
            ),
            # Layer 4 (extended): contractor-confirmation knowledge tools
            "offer_insight_capture": lambda: self.offer_insight_capture(
                actor, company_id,
                parameters.get("project_id", ""),
                parameters["statement"],
                parameters["scope"],
                parameters["scope_value"],
                parameters["adjustment_type"],
                parameters.get("adjustment_value"),
                parameters.get("confidence", 0.5),
            ),
            "find_applicable_insights": lambda: self.find_applicable_insights(
                actor, company_id,
                parameters["project_id"],
                parameters.get("work_type"),
                parameters.get("trade"),
                parameters.get("surface_threshold", 0.6),
            ),
            "reject_insight": lambda: self.reject_insight(
                actor, company_id,
                parameters["insight_id"],
                parameters["reason"],
            ),
            "derive_productivity_from_completion": lambda: self.derive_productivity_from_completion(
                actor, company_id,
                parameters["project_id"],
            ),
            "accept_productivity_update": lambda: self.accept_productivity_update(
                actor, company_id,
                parameters["productivity_rate_id"],
                parameters["new_rate"],
            ),
            "update_rate_from_purchase": lambda: self.update_rate_from_purchase(
                actor, company_id,
                parameters["material_catalog_entry_id"],
                parameters["new_price_cents"],
                parameters.get("source_url", ""),
            ),
            "add_assumption": lambda: self.add_assumption(
                actor, company_id, parameters["project_id"],
                parameters["category"],
                parameters["statement"],
                parameters.get("variation_trigger", False),
                parameters.get("trigger_description", ""),
                parameters.get("relied_on_value", ""),
                parameters.get("relied_on_unit", ""),
            ),
            "add_exclusion": lambda: self.add_exclusion(
                actor, company_id, parameters["project_id"],
                parameters["category"],
                parameters["statement"],
                parameters.get("partial_inclusion", ""),
            ),
            "update_assumption": lambda: self.update_assumption(
                actor, company_id, parameters["assumption_id"],
                parameters.get("statement"),
                parameters.get("category"),
                parameters.get("variation_trigger"),
                parameters.get("trigger_description"),
                parameters.get("relied_on_value"),
                parameters.get("relied_on_unit"),
            ),
            "remove_assumption": lambda: self.remove_assumption(
                actor, company_id, parameters["assumption_id"],
            ),
            "update_exclusion": lambda: self.update_exclusion(
                actor, company_id, parameters["exclusion_id"],
                parameters.get("statement"),
                parameters.get("category"),
                parameters.get("partial_inclusion"),
            ),
            "remove_exclusion": lambda: self.remove_exclusion(
                actor, company_id, parameters["exclusion_id"],
            ),
            "list_assumption_templates": lambda: self.list_assumption_templates(
                actor, company_id, parameters.get("trade_type"),
            ),
            "list_exclusion_templates": lambda: self.list_exclusion_templates(
                actor, company_id, parameters.get("trade_type"),
            ),
            "update_project_state": lambda: self.update_project_state(
                actor, company_id, parameters["project_id"],
                parameters["new_state"],
            ),
            "set_contract_type": lambda: self.set_contract_type(
                actor, company_id, parameters["project_id"],
                parameters["contract_type"],
            ),
            # Session E: Propose & Win
            "generate_proposal": lambda: self.generate_proposal(
                actor, company_id, parameters["project_id"],
                parameters.get("terms"),
                parameters.get("timeline"),
                parameters.get("notes"),
            ),
            "update_project_status": lambda: self.update_project_status(
                actor, company_id, parameters["project_id"],
                parameters["new_status"],
            ),
            # Session E: Get Paid
            "generate_invoice": lambda: self.generate_invoice(
                actor, company_id, parameters["project_id"],
                parameters.get("work_item_ids"),
                parameters.get("progress_pct"),
                parameters.get("due_date"),
                parameters.get("notes"),
            ),
            "track_payment_status": lambda: self.track_payment_status(
                actor, company_id, parameters["project_id"],
            ),
            "record_payment": lambda: self.record_payment(
                actor, company_id, parameters["project_id"],
                parameters["invoice_id"],
                parameters["amount"],
                parameters.get("payment_date"),
                parameters.get("method"),
                parameters.get("reference"),
            ),
            # Contract terms
            "create_payment_milestone": lambda: self.create_payment_milestone(
                actor, company_id, parameters["project_id"],
                parameters["description"],
                parameters["trigger_condition"],
                parameters.get("percentage"),
                parameters.get("fixed_amount_cents"),
                parameters.get("sort_order", 0),
            ),
            "update_payment_milestone": lambda: self.update_payment_milestone(
                actor, company_id, parameters["project_id"],
                parameters["milestone_id"],
                parameters.get("description"),
                parameters.get("percentage"),
                parameters.get("fixed_amount_cents"),
                parameters.get("trigger_condition"),
                parameters.get("sort_order"),
                parameters.get("status"),
            ),
            "remove_payment_milestone": lambda: self.remove_payment_milestone(
                actor, company_id, parameters["project_id"],
                parameters["milestone_id"],
            ),
            "create_condition": lambda: self.create_condition(
                actor, company_id, parameters["project_id"],
                parameters["category"],
                parameters["description"],
                parameters.get("responsible_party"),
            ),
            "update_condition": lambda: self.update_condition(
                actor, company_id, parameters["project_id"],
                parameters["condition_id"],
                parameters.get("category"),
                parameters.get("description"),
                parameters.get("responsible_party"),
            ),
            "remove_condition": lambda: self.remove_condition(
                actor, company_id, parameters["project_id"],
                parameters["condition_id"],
            ),
            "set_warranty_terms": lambda: self.set_warranty_terms(
                actor, company_id, parameters["project_id"],
                parameters["period_months"],
                parameters["scope"],
                parameters.get("start_trigger", "practical_completion"),
                parameters.get("terms"),
            ),
            "set_retention_terms": lambda: self.set_retention_terms(
                actor, company_id, parameters["project_id"],
                parameters["retention_pct"],
                parameters.get("payment_terms_days"),
            ),
            "get_contract_summary": lambda: self.get_contract_summary(
                actor, company_id, parameters["project_id"],
            ),
            "suggest_contract_terms": lambda: self.suggest_contract_terms(
                actor, company_id, parameters["project_id"],
            ),
        }

        handler = dispatch.get(tool_name)
        if handler is None:
            return {"error": f"Unknown tool: {tool_name}"}

        return handler()
