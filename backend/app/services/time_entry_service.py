"""TimeEntry CRUD service (Neo4j-backed).

TimeEntries record worker clock-in/clock-out events against a WorkItem.
They support GPS capture, overtime tracking, and approval workflows.
"""

from datetime import datetime, timezone
from typing import Any

from app.models.actor import Actor
from app.services.base_service import BaseService


class TimeEntryNotFoundError(Exception):
    """Raised when a time entry cannot be found."""

    def __init__(self, time_entry_id: str) -> None:
        self.time_entry_id = time_entry_id
        super().__init__(f"Time entry not found: {time_entry_id}")


class TimeEntryService(BaseService):
    """Manages TimeEntry nodes in the Neo4j graph.

    TimeEntries connect to work items via (WorkItem)-[:HAS_TIME_ENTRY]->(TimeEntry),
    to workers via (TimeEntry)-[:LOGGED_BY]->(Worker),
    and to projects via (TimeEntry)-[:FOR_PROJECT]->(Project).
    """

    def create(
        self,
        company_id: str,
        work_item_id: str,
        worker_id: str,
        data: dict[str, Any],
        user_id: str,
    ) -> dict[str, Any]:
        """Create a new time entry (clock-in event).

        Args:
            company_id: The owning company ID (for access scope).
            work_item_id: The work item being logged against.
            worker_id: The worker clocking in.
            data: Entry fields — clock_in, source, notes, gps_lat, gps_lng,
                gps_accuracy, daily_log_id.
            user_id: Clerk user ID of the creating user.

        Returns:
            The created time entry dict.
        """
        actor = Actor.human(user_id)
        te_id = self._generate_id("te")
        now = datetime.now(timezone.utc).isoformat()

        props: dict[str, Any] = {
            "id": te_id,
            "clock_in": data.get("clock_in", now),
            "clock_out": None,
            "hours_regular": None,
            "hours_overtime": None,
            "break_minutes": data.get("break_minutes", 0),
            "source": data.get("source", "manual"),
            "status": "open",
            "gps_lat": data.get("gps_lat"),
            "gps_lng": data.get("gps_lng"),
            "gps_accuracy": data.get("gps_accuracy"),
            "notes": data.get("notes"),
            "deleted": False,
            **self._provenance_create(actor),
        }

        result = self._write_tx_single(
            """
            MATCH (wi:WorkItem {id: $work_item_id})
            MATCH (w:Worker {id: $worker_id})
            MATCH (p:Project)-[:HAS_WORK_ITEM]->(wi)
            CREATE (te:TimeEntry $props)
            CREATE (wi)-[:HAS_TIME_ENTRY]->(te)
            CREATE (te)-[:LOGGED_BY]->(w)
            CREATE (te)-[:FOR_PROJECT]->(p)
            RETURN te {.*, work_item_id: wi.id, worker_id: w.id, project_id: p.id} AS time_entry
            """,
            {
                "work_item_id": work_item_id,
                "worker_id": worker_id,
                "props": props,
            },
        )
        if result is None:
            raise TimeEntryNotFoundError(te_id)
        self._emit_audit(
            event_type="entity.created",
            entity_id=te_id,
            entity_type="TimeEntry",
            company_id=company_id,
            actor=actor,
            summary=f"Created time entry for worker {worker_id}",
            related_entity_ids=[work_item_id, worker_id],
        )
        return result["time_entry"]

    def update(
        self,
        company_id: str,
        time_entry_id: str,
        data: dict[str, Any],
        user_id: str,
    ) -> dict[str, Any]:
        """Update a time entry — typically used to clock out.

        Args:
            company_id: The owning company ID (for access scope).
            time_entry_id: The time entry ID to update.
            data: Fields to update — clock_out, hours_regular, hours_overtime,
                break_minutes, notes, status.
            user_id: Clerk user ID of the updating user.

        Returns:
            The updated time entry dict.

        Raises:
            TimeEntryNotFoundError: If the time entry does not exist.
        """
        actor = Actor.human(user_id)
        update_fields = {k: v for k, v in data.items() if v is not None}
        update_fields.update(self._provenance_update(actor))

        result = self._write_tx_single(
            """
            MATCH (te:TimeEntry {id: $time_entry_id})
            WHERE te.deleted = false
            SET te += $props
            WITH te
            OPTIONAL MATCH (te)-[:LOGGED_BY]->(w:Worker)
            OPTIONAL MATCH (te)-[:FOR_PROJECT]->(p:Project)
            OPTIONAL MATCH (wi:WorkItem)-[:HAS_TIME_ENTRY]->(te)
            RETURN te {
                .*,
                worker_id: w.id,
                project_id: p.id,
                work_item_id: wi.id
            } AS time_entry
            """,
            {"time_entry_id": time_entry_id, "props": update_fields},
        )
        if result is None:
            raise TimeEntryNotFoundError(time_entry_id)
        self._emit_audit(
            event_type="entity.updated",
            entity_id=time_entry_id,
            entity_type="TimeEntry",
            company_id=company_id,
            actor=actor,
            summary=f"Updated time entry {time_entry_id}",
        )
        return result["time_entry"]

    def get(self, company_id: str, time_entry_id: str) -> dict[str, Any]:
        """Fetch a single time entry.

        Args:
            company_id: The owning company ID (unused in traversal, reserved for
                future graph-native permission enforcement).
            time_entry_id: The time entry ID to fetch.

        Returns:
            The time entry dict.

        Raises:
            TimeEntryNotFoundError: If the time entry does not exist or is soft-deleted.
        """
        result = self._read_tx_single(
            """
            MATCH (te:TimeEntry {id: $time_entry_id})
            WHERE te.deleted = false
            OPTIONAL MATCH (te)-[:LOGGED_BY]->(w:Worker)
            OPTIONAL MATCH (te)-[:FOR_PROJECT]->(p:Project)
            OPTIONAL MATCH (wi:WorkItem)-[:HAS_TIME_ENTRY]->(te)
            RETURN te {
                .*,
                worker_id: w.id,
                project_id: p.id,
                work_item_id: wi.id
            } AS time_entry
            """,
            {"time_entry_id": time_entry_id},
        )
        if result is None:
            raise TimeEntryNotFoundError(time_entry_id)
        return result["time_entry"]

    def list_by_project(
        self,
        company_id: str,
        project_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> dict[str, Any]:
        """List all time entries for a project.

        Args:
            company_id: The owning company ID.
            project_id: The project ID.
            limit: Maximum number of entries to return.
            offset: Number of entries to skip.

        Returns:
            A dict with 'time_entries' list and 'total' count.
        """
        params: dict[str, Any] = {
            "company_id": company_id,
            "project_id": project_id,
            "limit": limit,
            "offset": offset,
        }

        count_result = self._read_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
            MATCH (te:TimeEntry)-[:FOR_PROJECT]->(p)
            WHERE te.deleted = false
            RETURN count(te) AS total
            """,
            params,
        )
        total = count_result["total"] if count_result else 0

        results = self._read_tx(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
            MATCH (te:TimeEntry)-[:FOR_PROJECT]->(p)
            WHERE te.deleted = false
            OPTIONAL MATCH (te)-[:LOGGED_BY]->(w:Worker)
            OPTIONAL MATCH (wi:WorkItem)-[:HAS_TIME_ENTRY]->(te)
            RETURN te {.*, worker_id: w.id, project_id: p.id, work_item_id: wi.id} AS time_entry
            ORDER BY te.clock_in DESC
            SKIP $offset LIMIT $limit
            """,
            params,
        )

        return {"time_entries": [r["time_entry"] for r in results], "total": total}

    def list_by_worker(
        self,
        company_id: str,
        worker_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> dict[str, Any]:
        """List all time entries for a specific worker.

        Args:
            company_id: The owning company ID.
            worker_id: The worker ID.
            limit: Maximum number of entries to return.
            offset: Number of entries to skip.

        Returns:
            A dict with 'time_entries' list and 'total' count.
        """
        params: dict[str, Any] = {
            "company_id": company_id,
            "worker_id": worker_id,
            "limit": limit,
            "offset": offset,
        }

        count_result = self._read_tx_single(
            """
            MATCH (c:Company {id: $company_id})
            MATCH (te:TimeEntry)-[:LOGGED_BY]->(w:Worker {id: $worker_id})
            WHERE te.deleted = false
            RETURN count(te) AS total
            """,
            params,
        )
        total = count_result["total"] if count_result else 0

        results = self._read_tx(
            """
            MATCH (c:Company {id: $company_id})
            MATCH (te:TimeEntry)-[:LOGGED_BY]->(w:Worker {id: $worker_id})
            WHERE te.deleted = false
            OPTIONAL MATCH (te)-[:FOR_PROJECT]->(p:Project)
            OPTIONAL MATCH (wi:WorkItem)-[:HAS_TIME_ENTRY]->(te)
            RETURN te {.*, worker_id: w.id, project_id: p.id, work_item_id: wi.id} AS time_entry
            ORDER BY te.clock_in DESC
            SKIP $offset LIMIT $limit
            """,
            params,
        )

        return {"time_entries": [r["time_entry"] for r in results], "total": total}

    def approve(
        self,
        company_id: str,
        time_entry_id: str,
        user_id: str,
    ) -> dict[str, Any]:
        """Approve a time entry, locking it for payroll.

        Args:
            company_id: The owning company ID.
            time_entry_id: The time entry ID to approve.
            user_id: Clerk user ID of the approving user.

        Returns:
            The updated time entry dict.

        Raises:
            TimeEntryNotFoundError: If the time entry does not exist.
        """
        actor = Actor.human(user_id)
        result = self._write_tx_single(
            """
            MATCH (te:TimeEntry {id: $time_entry_id})
            WHERE te.deleted = false
            SET te.status = 'approved', te += $provenance
            WITH te
            OPTIONAL MATCH (te)-[:LOGGED_BY]->(w:Worker)
            OPTIONAL MATCH (te)-[:FOR_PROJECT]->(p:Project)
            OPTIONAL MATCH (wi:WorkItem)-[:HAS_TIME_ENTRY]->(te)
            RETURN te {.*, worker_id: w.id, project_id: p.id, work_item_id: wi.id} AS time_entry
            """,
            {
                "time_entry_id": time_entry_id,
                "provenance": self._provenance_update(actor),
            },
        )
        if result is None:
            raise TimeEntryNotFoundError(time_entry_id)
        self._emit_audit(
            event_type="state.transitioned",
            entity_id=time_entry_id,
            entity_type="TimeEntry",
            company_id=company_id,
            actor=actor,
            summary=f"Approved time entry {time_entry_id}",
            new_state="approved",
        )
        return result["time_entry"]

    def get_timesheet_summary(
        self,
        company_id: str,
        project_id: str,
        worker_id: str | None = None,
        from_date: str | None = None,
        to_date: str | None = None,
    ) -> dict[str, Any]:
        """Aggregate hours and costs for a project (optionally filtered by worker and date).

        Args:
            company_id: The owning company ID.
            project_id: The project ID.
            worker_id: Optional worker ID to filter by.
            from_date: Optional ISO date string — entries with clock_in >= from_date.
            to_date: Optional ISO date string — entries with clock_in <= to_date.

        Returns:
            Dict with total_regular_hours, total_overtime_hours, entry_count, status_breakdown.
        """
        where_clauses = ["te.deleted = false"]
        params: dict[str, Any] = {
            "company_id": company_id,
            "project_id": project_id,
        }

        if worker_id:
            where_clauses.append("w.id = $worker_id")
            params["worker_id"] = worker_id
        if from_date:
            where_clauses.append("te.clock_in >= $from_date")
            params["from_date"] = from_date
        if to_date:
            where_clauses.append("te.clock_in <= $to_date")
            params["to_date"] = to_date

        where_str = " AND ".join(where_clauses)

        result = self._read_tx_single(
            f"""
            MATCH (c:Company {{id: $company_id}})-[:OWNS_PROJECT]->(p:Project {{id: $project_id}})
            MATCH (te:TimeEntry)-[:FOR_PROJECT]->(p)
            OPTIONAL MATCH (te)-[:LOGGED_BY]->(w:Worker)
            WHERE {where_str}
            RETURN {{
                total_regular_hours: sum(coalesce(te.hours_regular, 0)),
                total_overtime_hours: sum(coalesce(te.hours_overtime, 0)),
                entry_count: count(te),
                open_count: sum(CASE WHEN te.status = 'open' THEN 1 ELSE 0 END),
                approved_count: sum(CASE WHEN te.status = 'approved' THEN 1 ELSE 0 END)
            }} AS summary
            """,
            params,
        )
        return result["summary"] if result else {}
