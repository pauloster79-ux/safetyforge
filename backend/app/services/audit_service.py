"""Audit event query service.

Provides read access to AuditEvent nodes for activity streams and timelines.
Uses domain-aware traversals — e.g. a Project's activity includes events on
its child WorkItems / Inspections / Incidents / DailyLogs / ToolboxTalks.

Emission happens in BaseService._emit_audit; this service is read-only.
See docs/design/phase-0-foundations.md §3.4.
"""

import json
import re
from datetime import datetime
from typing import Any

from app.models.audit_event import ActivityStreamResponse, AuditEvent
from app.services.base_service import BaseService


_VALID_LABEL_RE = re.compile(r"^[A-Za-z][A-Za-z0-9]*$")


class AuditService(BaseService):
    """Query AuditEvent nodes for activity streams."""

    def _row_to_event(self, row: dict[str, Any]) -> AuditEvent:
        """Convert a Neo4j row (with JSON-serialised changes) to an AuditEvent.

        Changes are stored as a JSON string in Neo4j because property graph
        databases don't support nested-dict properties. Deserialise here.
        """
        data = dict(row)
        changes = data.get("changes")
        if changes and isinstance(changes, str):
            try:
                data["changes"] = json.loads(changes)
            except json.JSONDecodeError:
                data["changes"] = None
        return AuditEvent(**data)

    def list_events_for_entity(
        self,
        company_id: str,
        entity_type: str,
        entity_id: str,
        limit: int = 50,
        before: datetime | None = None,
    ) -> ActivityStreamResponse:
        """List audit events directly emitted by a single entity, newest first.

        For aggregated streams (e.g. Project including its WorkItems), use the
        entity-specific method such as list_events_for_project.

        Args:
            company_id: Tenant scope.
            entity_type: Neo4j label of the entity (validated).
            entity_id: The entity's ID.
            limit: Maximum events to return.
            before: Cursor — only return events strictly before this timestamp.

        Returns:
            ActivityStreamResponse with events sorted newest first.

        Raises:
            ValueError: If entity_type is not a valid Neo4j label identifier.
        """
        if not _VALID_LABEL_RE.match(entity_type):
            raise ValueError(
                f"Invalid entity_type (not a valid Neo4j label): {entity_type!r}"
            )

        where_extra = ""
        params: dict[str, Any] = {
            "company_id": company_id,
            "entity_id": entity_id,
            "limit": limit,
        }
        if before is not None:
            where_extra = " AND ev.occurred_at < $before"
            params["before"] = before.isoformat()

        # Label interpolation safe: entity_type validated above
        cypher = f"""
            MATCH (e:{entity_type} {{id: $entity_id}})
            MATCH (e)-[:EMITTED]->(ev:AuditEvent)
            WHERE ev.company_id = $company_id{where_extra}
            RETURN ev {{.*}} AS event
            ORDER BY ev.occurred_at DESC
            LIMIT $limit
        """
        results = self._read_tx(cypher, params)
        events = [self._row_to_event(r["event"]) for r in results]
        return ActivityStreamResponse(
            events=events,
            total=len(events),
            has_more=len(events) == limit,
        )

    def list_events_for_project(
        self,
        company_id: str,
        project_id: str,
        limit: int = 50,
        before: datetime | None = None,
    ) -> ActivityStreamResponse:
        """List audit events for a project, aggregating across child entities.

        Includes events emitted directly on the Project AND events on its
        WorkItems, Inspections, Incidents, DailyLogs, and ToolboxTalks. Child
        relationships that don't exist in the graph simply return no rows —
        safe to keep the full UNION even before all services are instrumented.

        Args:
            company_id: Tenant scope.
            project_id: The project ID.
            limit: Maximum events to return.
            before: Cursor for pagination.

        Returns:
            ActivityStreamResponse with events sorted newest first.
        """
        where_extra = ""
        params: dict[str, Any] = {
            "company_id": company_id,
            "project_id": project_id,
            "limit": limit,
        }
        if before is not None:
            where_extra = " AND ev.occurred_at < $before"
            params["before"] = before.isoformat()

        cypher = f"""
            MATCH (c:Company {{id: $company_id}})-[:OWNS_PROJECT]->(p:Project {{id: $project_id}})
            CALL {{
                WITH p
                MATCH (p)-[:EMITTED]->(ev:AuditEvent)
                RETURN ev
                UNION
                WITH p
                MATCH (p)-[:HAS_WORK_ITEM]->(wi:WorkItem)-[:EMITTED]->(ev:AuditEvent)
                RETURN ev
                UNION
                WITH p
                MATCH (p)-[:HAS_INSPECTION]->(i:Inspection)-[:EMITTED]->(ev:AuditEvent)
                RETURN ev
                UNION
                WITH p
                MATCH (p)-[:HAS_INCIDENT]->(inc:Incident)-[:EMITTED]->(ev:AuditEvent)
                RETURN ev
                UNION
                WITH p
                MATCH (p)-[:HAS_DAILY_LOG]->(dl:DailyLog)-[:EMITTED]->(ev:AuditEvent)
                RETURN ev
                UNION
                WITH p
                MATCH (p)-[:HAS_TOOLBOX_TALK]->(tb:ToolboxTalk)-[:EMITTED]->(ev:AuditEvent)
                RETURN ev
                UNION
                WITH p
                MATCH (p)-[:HAS_HAZARD_REPORT]->(hr:HazardReport)-[:EMITTED]->(ev:AuditEvent)
                RETURN ev
            }}
            WITH ev
            WHERE ev.company_id = $company_id{where_extra}
            RETURN ev {{.*}} AS event
            ORDER BY ev.occurred_at DESC
            LIMIT $limit
        """
        results = self._read_tx(cypher, params)
        events = [self._row_to_event(r["event"]) for r in results]
        return ActivityStreamResponse(
            events=events,
            total=len(events),
            has_more=len(events) == limit,
        )

    def list_events_for_worker(
        self,
        company_id: str,
        worker_id: str,
        limit: int = 50,
        before: datetime | None = None,
    ) -> ActivityStreamResponse:
        """List audit events for a worker, aggregating across related entities.

        Includes events directly on the Worker + certifications added/expired +
        incidents involving the worker + inspections where they were the inspector
        or an attendee.
        """
        where_extra = ""
        params: dict[str, Any] = {
            "company_id": company_id,
            "worker_id": worker_id,
            "limit": limit,
        }
        if before is not None:
            where_extra = " AND ev.occurred_at < $before"
            params["before"] = before.isoformat()

        cypher = f"""
            MATCH (c:Company {{id: $company_id}})-[:HAS_WORKER]->(w:Worker {{id: $worker_id}})
            CALL {{
                WITH w
                MATCH (w)-[:EMITTED]->(ev:AuditEvent)
                RETURN ev
                UNION
                WITH w
                MATCH (w)-[:HAS_CERTIFICATION]->(cert:Certification)-[:EMITTED]->(ev:AuditEvent)
                RETURN ev
            }}
            WITH ev
            WHERE ev.company_id = $company_id{where_extra}
            RETURN ev {{.*}} AS event
            ORDER BY ev.occurred_at DESC
            LIMIT $limit
        """
        results = self._read_tx(cypher, params)
        events = [self._row_to_event(r["event"]) for r in results]
        return ActivityStreamResponse(
            events=events,
            total=len(events),
            has_more=len(events) == limit,
        )

    def list_events_for_work_item(
        self,
        company_id: str,
        work_item_id: str,
        limit: int = 50,
        before: datetime | None = None,
    ) -> ActivityStreamResponse:
        """List audit events for a work item, including child Labour/Item events
        and TimeEntries logged against it.
        """
        where_extra = ""
        params: dict[str, Any] = {
            "company_id": company_id,
            "work_item_id": work_item_id,
            "limit": limit,
        }
        if before is not None:
            where_extra = " AND ev.occurred_at < $before"
            params["before"] = before.isoformat()

        cypher = f"""
            MATCH (wi:WorkItem {{id: $work_item_id}})
            CALL {{
                WITH wi
                MATCH (wi)-[:EMITTED]->(ev:AuditEvent)
                RETURN ev
                UNION
                WITH wi
                MATCH (wi)-[:HAS_LABOUR]->(lab:Labour)-[:EMITTED]->(ev:AuditEvent)
                RETURN ev
                UNION
                WITH wi
                MATCH (wi)-[:HAS_ITEM]->(item:Item)-[:EMITTED]->(ev:AuditEvent)
                RETURN ev
                UNION
                WITH wi
                MATCH (wi)-[:HAS_TIME_ENTRY]->(te:TimeEntry)-[:EMITTED]->(ev:AuditEvent)
                RETURN ev
            }}
            WITH ev
            WHERE ev.company_id = $company_id{where_extra}
            RETURN ev {{.*}} AS event
            ORDER BY ev.occurred_at DESC
            LIMIT $limit
        """
        results = self._read_tx(cypher, params)
        events = [self._row_to_event(r["event"]) for r in results]
        return ActivityStreamResponse(
            events=events,
            total=len(events),
            has_more=len(events) == limit,
        )

    def list_events_for_company(
        self,
        company_id: str,
        limit: int = 50,
        before: datetime | None = None,
    ) -> ActivityStreamResponse:
        """List all audit events for a company, company-wide timeline."""
        where_extra = ""
        params: dict[str, Any] = {
            "company_id": company_id,
            "limit": limit,
        }
        if before is not None:
            where_extra = " AND ev.occurred_at < $before"
            params["before"] = before.isoformat()

        cypher = f"""
            MATCH (ev:AuditEvent)
            WHERE ev.company_id = $company_id{where_extra}
            RETURN ev {{.*}} AS event
            ORDER BY ev.occurred_at DESC
            LIMIT $limit
        """
        results = self._read_tx(cypher, params)
        events = [self._row_to_event(r["event"]) for r in results]
        return ActivityStreamResponse(
            events=events,
            total=len(events),
            has_more=len(events) == limit,
        )
