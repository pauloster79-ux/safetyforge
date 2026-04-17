"""Daily log CRUD service against Neo4j."""

import json
from datetime import date, datetime, timedelta, timezone
from typing import Any

from app.exceptions import DailyLogNotFoundError, ProjectNotFoundError
from app.models.actor import Actor
from app.models.daily_log import (
    DailyLog,
    DailyLogCreate,
    DailyLogStatus,
    DailyLogUpdate,
)
from app.services.base_service import BaseService


class DailyLogService(BaseService):
    """Manages construction daily logs in Neo4j.

    Graph model:
        (Company)-[:OWNS_PROJECT]->(Project)-[:HAS_DAILY_LOG]->(DailyLog)
        Complex fields stored as JSON strings on the DailyLog node:
            _weather_json, _materials_json, _delays_json, _visitors_json,
            _inspections_json, _talks_json, _incidents_json
    """

    def _verify_project_exists(self, company_id: str, project_id: str) -> None:
        """Verify that the parent project exists and is not deleted.

        Args:
            company_id: The company ID.
            project_id: The project ID to check.

        Raises:
            ProjectNotFoundError: If the project does not exist or is soft-deleted.
        """
        result = self._read_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
            WHERE p.deleted = false
            RETURN p.id AS id
            """,
            {"company_id": company_id, "project_id": project_id},
        )
        if result is None:
            raise ProjectNotFoundError(project_id)

    def _auto_populate_summaries(
        self, company_id: str, project_id: str, log_date: date
    ) -> dict[str, list[dict[str, Any]]]:
        """Auto-populate daily log summaries from existing safety data.

        Queries inspections, toolbox talks, and incidents for the given
        project and date to include in the daily log.

        Args:
            company_id: The company ID.
            project_id: The project ID.
            log_date: The date to query data for.

        Returns:
            A dict with inspections_summary, toolbox_talks_summary,
            and incidents_summary lists.
        """
        date_str = log_date.isoformat()

        # Query inspections for this date
        inspections = self._read_tx(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
                  -[:HAS_INSPECTION]->(i:Inspection)
            WHERE i.deleted = false AND i.inspection_date = $log_date
            RETURN i.id AS id, i.category AS type,
                   i.inspector_name AS inspector, i.overall_status AS status
            """,
            {"company_id": company_id, "project_id": project_id, "log_date": date_str},
        )
        inspections_summary = [dict(r) for r in inspections]

        # Query toolbox talks for this date
        talks = self._read_tx(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
                  -[:HAS_TOOLBOX_TALK]->(t:ToolboxTalk)
            WHERE t.deleted = false AND t.talk_date = $log_date
            RETURN t.id AS id, t.topic AS topic, t.presenter_name AS presenter,
                   t.status AS status
            """,
            {"company_id": company_id, "project_id": project_id, "log_date": date_str},
        )
        toolbox_talks_summary = [dict(r) for r in talks]

        # Query incidents for this date
        incidents = self._read_tx(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
                  -[:HAS_INCIDENT]->(inc:Incident)
            WHERE inc.deleted = false AND inc.incident_date = $log_date
            RETURN inc.id AS id, inc.incident_type AS type,
                   inc.severity AS severity, inc.description AS description
            """,
            {"company_id": company_id, "project_id": project_id, "log_date": date_str},
        )
        incidents_summary = [dict(r) for r in incidents]

        return {
            "inspections_summary": inspections_summary,
            "toolbox_talks_summary": toolbox_talks_summary,
            "incidents_summary": incidents_summary,
        }

    @staticmethod
    def _to_model(record: dict[str, Any]) -> DailyLog:
        """Convert a Neo4j record dict to a DailyLog model.

        Args:
            record: Dict with 'daily_log', 'company_id', and 'project_id' keys.

        Returns:
            A DailyLog model instance.
        """
        data = record["daily_log"]

        # Parse JSON fields
        weather_json = data.pop("_weather_json", "{}")
        data["weather"] = json.loads(weather_json) if weather_json else {}

        materials_json = data.pop("_materials_json", "[]")
        data["materials_delivered"] = json.loads(materials_json) if materials_json else []

        delays_json = data.pop("_delays_json", "[]")
        data["delays"] = json.loads(delays_json) if delays_json else []

        visitors_json = data.pop("_visitors_json", "[]")
        data["visitors"] = json.loads(visitors_json) if visitors_json else []

        inspections_json = data.pop("_inspections_json", "[]")
        data["inspections_summary"] = json.loads(inspections_json) if inspections_json else []

        talks_json = data.pop("_talks_json", "[]")
        data["toolbox_talks_summary"] = json.loads(talks_json) if talks_json else []

        incidents_json = data.pop("_incidents_json", "[]")
        data["incidents_summary"] = json.loads(incidents_json) if incidents_json else []

        data["company_id"] = record["company_id"]
        data["project_id"] = record["project_id"]
        return DailyLog(**data)

    def create(
        self,
        company_id: str,
        project_id: str,
        data: DailyLogCreate,
        user_id: str,
    ) -> DailyLog:
        """Create a new daily log draft with auto-populated summaries.

        Args:
            company_id: The owning company ID.
            project_id: The parent project ID.
            data: Validated daily log creation data.
            user_id: UID of the creating user.

        Returns:
            The created DailyLog with all fields populated.

        Raises:
            ProjectNotFoundError: If the project does not exist.
        """
        self._verify_project_exists(company_id, project_id)

        actor = Actor.human(user_id)
        dlog_id = self._generate_id("dlog")

        # Auto-populate summaries from existing safety data
        summaries = self._auto_populate_summaries(company_id, project_id, data.log_date)

        weather_json = json.dumps(data.weather.model_dump())
        materials_json = json.dumps(
            [m.model_dump() for m in data.materials_delivered]
        )
        delays_json = json.dumps([d.model_dump() for d in data.delays])
        visitors_json = json.dumps([v.model_dump() for v in data.visitors])
        inspections_json = json.dumps(summaries["inspections_summary"])
        talks_json = json.dumps(summaries["toolbox_talks_summary"])
        incidents_json = json.dumps(summaries["incidents_summary"])

        props: dict[str, Any] = {
            "id": dlog_id,
            "log_date": data.log_date.isoformat(),
            "superintendent_name": data.superintendent_name,
            "_weather_json": weather_json,
            "workers_on_site": data.workers_on_site,
            "work_performed": data.work_performed,
            "_materials_json": materials_json,
            "_delays_json": delays_json,
            "_visitors_json": visitors_json,
            "safety_incidents": data.safety_incidents,
            "equipment_used": data.equipment_used,
            "notes": data.notes,
            "status": DailyLogStatus.DRAFT.value,
            "_inspections_json": inspections_json,
            "_talks_json": talks_json,
            "_incidents_json": incidents_json,
            "submitted_at": None,
            "submitted_by": None,
            "approved_at": None,
            "approved_by": None,
            "deleted": False,
            **self._provenance_create(actor),
        }

        result = self._write_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
            CREATE (d:DailyLog $props)
            CREATE (p)-[:HAS_DAILY_LOG]->(d)
            RETURN d {.*} AS daily_log, c.id AS company_id, p.id AS project_id
            """,
            {"company_id": company_id, "project_id": project_id, "props": props},
        )

        self._emit_audit(
            event_type="entity.created",
            entity_id=dlog_id,
            entity_type="DailyLog",
            company_id=company_id,
            actor=actor,
            summary=f"Created daily log for {data.log_date.isoformat()}",
            related_entity_ids=[project_id],
        )

        return self._to_model(result)

    def get(
        self, company_id: str, project_id: str, daily_log_id: str
    ) -> DailyLog:
        """Fetch a single daily log.

        Args:
            company_id: The owning company ID.
            project_id: The parent project ID.
            daily_log_id: The daily log ID to fetch.

        Returns:
            The DailyLog model.

        Raises:
            DailyLogNotFoundError: If the daily log does not exist or is soft-deleted.
        """
        result = self._read_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
                  -[:HAS_DAILY_LOG]->(d:DailyLog {id: $daily_log_id})
            WHERE d.deleted = false
            RETURN d {.*} AS daily_log, c.id AS company_id, p.id AS project_id
            """,
            {
                "company_id": company_id,
                "project_id": project_id,
                "daily_log_id": daily_log_id,
            },
        )
        if result is None:
            raise DailyLogNotFoundError(daily_log_id)
        return self._to_model(result)

    def list_daily_logs(
        self,
        company_id: str,
        project_id: str,
        status_filter: DailyLogStatus | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> dict:
        """List daily logs for a project with optional filters and pagination.

        Args:
            company_id: The owning company ID.
            project_id: The parent project ID.
            status_filter: Filter by workflow status.
            date_from: Filter logs on or after this date.
            date_to: Filter logs on or before this date.
            limit: Maximum number of logs to return.
            offset: Number of logs to skip.

        Returns:
            A dict with 'daily_logs' list and 'total' count.
        """
        where_clauses = ["d.deleted = false"]
        params: dict[str, Any] = {
            "company_id": company_id,
            "project_id": project_id,
            "limit": limit,
            "offset": offset,
        }

        if status_filter is not None:
            where_clauses.append("d.status = $status_filter")
            params["status_filter"] = status_filter.value

        if date_from is not None:
            where_clauses.append("d.log_date >= $date_from")
            params["date_from"] = date_from.isoformat()

        if date_to is not None:
            where_clauses.append("d.log_date <= $date_to")
            params["date_to"] = date_to.isoformat()

        where_str = " AND ".join(where_clauses)

        # Count query
        count_result = self._read_tx_single(
            f"""
            MATCH (c:Company {{id: $company_id}})-[:OWNS_PROJECT]->(p:Project {{id: $project_id}})
                  -[:HAS_DAILY_LOG]->(d:DailyLog)
            WHERE {where_str}
            RETURN count(d) AS total
            """,
            params,
        )
        total = count_result["total"] if count_result else 0

        # Data query
        results = self._read_tx(
            f"""
            MATCH (c:Company {{id: $company_id}})-[:OWNS_PROJECT]->(p:Project {{id: $project_id}})
                  -[:HAS_DAILY_LOG]->(d:DailyLog)
            WHERE {where_str}
            RETURN d {{.*}} AS daily_log, c.id AS company_id, p.id AS project_id
            ORDER BY d.log_date DESC
            SKIP $offset LIMIT $limit
            """,
            params,
        )

        daily_logs = [self._to_model(r) for r in results]
        return {"daily_logs": daily_logs, "total": total}

    def update(
        self,
        company_id: str,
        project_id: str,
        daily_log_id: str,
        data: DailyLogUpdate,
        user_id: str,
    ) -> DailyLog:
        """Update an existing daily log (only allowed in draft status).

        Args:
            company_id: The owning company ID.
            project_id: The parent project ID.
            daily_log_id: The daily log ID to update.
            data: Fields to update (only non-None fields are applied).
            user_id: UID of the updating user.

        Returns:
            The updated DailyLog model.

        Raises:
            DailyLogNotFoundError: If the daily log does not exist or is soft-deleted.
        """
        update_props: dict[str, Any] = {}
        for field_name, value in data.model_dump(exclude_none=True).items():
            if field_name == "weather" and value is not None:
                update_props["_weather_json"] = json.dumps(value)
            elif field_name == "materials_delivered" and value is not None:
                update_props["_materials_json"] = json.dumps(value)
            elif field_name == "delays" and value is not None:
                update_props["_delays_json"] = json.dumps(value)
            elif field_name == "visitors" and value is not None:
                update_props["_visitors_json"] = json.dumps(value)
            else:
                update_props[field_name] = value

        if not update_props:
            return self.get(company_id, project_id, daily_log_id)

        actor = Actor.human(user_id)
        update_props.update(self._provenance_update(actor))

        result = self._write_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
                  -[:HAS_DAILY_LOG]->(d:DailyLog {id: $daily_log_id})
            WHERE d.deleted = false
            SET d += $props
            RETURN d {.*} AS daily_log, c.id AS company_id, p.id AS project_id
            """,
            {
                "company_id": company_id,
                "project_id": project_id,
                "daily_log_id": daily_log_id,
                "props": update_props,
            },
        )
        if result is None:
            raise DailyLogNotFoundError(daily_log_id)

        self._emit_audit(
            event_type="entity.updated",
            entity_id=daily_log_id,
            entity_type="DailyLog",
            company_id=company_id,
            actor=actor,
            summary="Updated daily log",
            related_entity_ids=[project_id],
        )

        return self._to_model(result)

    def submit(
        self, company_id: str, project_id: str, daily_log_id: str, user_id: str
    ) -> DailyLog:
        """Submit a daily log for approval (draft -> submitted).

        Args:
            company_id: The owning company ID.
            project_id: The parent project ID.
            daily_log_id: The daily log ID to submit.
            user_id: UID of the submitting user.

        Returns:
            The updated DailyLog model with submitted status.

        Raises:
            DailyLogNotFoundError: If the daily log does not exist.
        """
        now = datetime.now(timezone.utc).isoformat()
        result = self._write_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
                  -[:HAS_DAILY_LOG]->(d:DailyLog {id: $daily_log_id})
            WHERE d.deleted = false AND d.status = $draft_status
            SET d.status = $submitted_status,
                d.submitted_at = $now,
                d.submitted_by = $user_id,
                d.updated_at = $now,
                d.updated_by = $user_id
            RETURN d {.*} AS daily_log, c.id AS company_id, p.id AS project_id
            """,
            {
                "company_id": company_id,
                "project_id": project_id,
                "daily_log_id": daily_log_id,
                "draft_status": DailyLogStatus.DRAFT.value,
                "submitted_status": DailyLogStatus.SUBMITTED.value,
                "now": now,
                "user_id": user_id,
            },
        )
        if result is None:
            raise DailyLogNotFoundError(daily_log_id)

        self._emit_audit(
            event_type="state.transitioned",
            entity_id=daily_log_id,
            entity_type="DailyLog",
            company_id=company_id,
            actor=Actor.human(user_id),
            summary="Daily log submitted for approval",
            prev_state=DailyLogStatus.DRAFT.value,
            new_state=DailyLogStatus.SUBMITTED.value,
            related_entity_ids=[project_id],
        )

        return self._to_model(result)

    def approve(
        self, company_id: str, project_id: str, daily_log_id: str, user_id: str
    ) -> DailyLog:
        """Approve a submitted daily log (submitted -> approved).

        Args:
            company_id: The owning company ID.
            project_id: The parent project ID.
            daily_log_id: The daily log ID to approve.
            user_id: UID of the approving user.

        Returns:
            The updated DailyLog model with approved status.

        Raises:
            DailyLogNotFoundError: If the daily log does not exist.
        """
        now = datetime.now(timezone.utc).isoformat()
        result = self._write_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
                  -[:HAS_DAILY_LOG]->(d:DailyLog {id: $daily_log_id})
            WHERE d.deleted = false AND d.status = $submitted_status
            SET d.status = $approved_status,
                d.approved_at = $now,
                d.approved_by = $user_id,
                d.updated_at = $now,
                d.updated_by = $user_id
            RETURN d {.*} AS daily_log, c.id AS company_id, p.id AS project_id
            """,
            {
                "company_id": company_id,
                "project_id": project_id,
                "daily_log_id": daily_log_id,
                "submitted_status": DailyLogStatus.SUBMITTED.value,
                "approved_status": DailyLogStatus.APPROVED.value,
                "now": now,
                "user_id": user_id,
            },
        )
        if result is None:
            raise DailyLogNotFoundError(daily_log_id)

        self._emit_audit(
            event_type="state.transitioned",
            entity_id=daily_log_id,
            entity_type="DailyLog",
            company_id=company_id,
            actor=Actor.human(user_id),
            summary="Daily log approved",
            prev_state=DailyLogStatus.SUBMITTED.value,
            new_state=DailyLogStatus.APPROVED.value,
            related_entity_ids=[project_id],
        )

        return self._to_model(result)

    def delete(
        self, company_id: str, project_id: str, daily_log_id: str
    ) -> None:
        """Soft-delete a daily log by setting the deleted flag.

        Args:
            company_id: The owning company ID.
            project_id: The parent project ID.
            daily_log_id: The daily log ID to delete.

        Raises:
            DailyLogNotFoundError: If the daily log does not exist.
        """
        result = self._write_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
                  -[:HAS_DAILY_LOG]->(d:DailyLog {id: $daily_log_id})
            WHERE d.deleted = false
            SET d.deleted = true, d.updated_at = $now
            RETURN d.id AS id
            """,
            {
                "company_id": company_id,
                "project_id": project_id,
                "daily_log_id": daily_log_id,
                "now": datetime.now(timezone.utc).isoformat(),
            },
        )
        if result is None:
            raise DailyLogNotFoundError(daily_log_id)

        self._emit_audit(
            event_type="entity.archived",
            entity_id=daily_log_id,
            entity_type="DailyLog",
            company_id=company_id,
            actor=Actor.human("system"),
            summary="Deleted daily log",
            related_entity_ids=[project_id],
        )

    def get_missing_logs(
        self,
        company_id: str,
        project_id: str,
        date_from: date,
        date_to: date,
    ) -> list[str]:
        """Return dates within a range that don't have a daily log.

        Args:
            company_id: The owning company ID.
            project_id: The parent project ID.
            date_from: Start of the date range (inclusive).
            date_to: End of the date range (inclusive).

        Returns:
            A list of date strings (ISO format) that are missing logs.

        Raises:
            ProjectNotFoundError: If the project does not exist.
        """
        self._verify_project_exists(company_id, project_id)

        # Get all logged dates in the range
        results = self._read_tx(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
                  -[:HAS_DAILY_LOG]->(d:DailyLog)
            WHERE d.deleted = false
              AND d.log_date >= $date_from
              AND d.log_date <= $date_to
            RETURN d.log_date AS log_date
            """,
            {
                "company_id": company_id,
                "project_id": project_id,
                "date_from": date_from.isoformat(),
                "date_to": date_to.isoformat(),
            },
        )

        logged_dates = {r["log_date"] for r in results}

        # Generate all dates in range and find missing ones
        missing: list[str] = []
        current = date_from
        while current <= date_to:
            date_str = current.isoformat()
            if date_str not in logged_dates:
                missing.append(date_str)
            current += timedelta(days=1)

        return missing
