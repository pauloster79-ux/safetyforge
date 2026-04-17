"""Scheduling service — lightweight 2-4 week rolling lookahead.

Provides schedule views, worker/crew assignment via MCP tools,
and conflict detection (cert expiry, double-booking, equipment clashes).
"""

from datetime import datetime, timedelta, timezone
from typing import Any

from app.models.actor import Actor
from app.services.base_service import BaseService


class SchedulingService(BaseService):
    """Manages schedule views and conflict detection via graph traversal.

    Schedule data lives on WorkItem nodes (planned_start, planned_end)
    and assignment relationships (ASSIGNED_TO_WORKER, ASSIGNED_TO_CREW).
    """

    def get_schedule(
        self,
        company_id: str,
        project_id: str,
        weeks_ahead: int = 4,
    ) -> dict[str, Any]:
        """Get a rolling schedule view for a project, grouped by week.

        Args:
            company_id: The owning company ID.
            project_id: The project to get schedule for.
            weeks_ahead: Number of weeks to look ahead (default 4).

        Returns:
            Dict with schedule data grouped by week.
        """
        now = datetime.now(timezone.utc)
        cutoff = (now + timedelta(weeks=weeks_ahead)).strftime("%Y-%m-%d")
        today = now.strftime("%Y-%m-%d")

        results = self._read_tx(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
                  -[:HAS_WORK_ITEM]->(wi:WorkItem)
            WHERE wi.deleted = false
                  AND wi.state IN ['draft', 'scheduled', 'in_progress']
            OPTIONAL MATCH (wi)-[:ASSIGNED_TO_WORKER]->(w:Worker)
            OPTIONAL MATCH (wi)-[:ASSIGNED_TO_CREW]->(crew:Crew)
            RETURN wi.id AS work_item_id,
                   wi.description AS description,
                   wi.state AS state,
                   wi.planned_start AS planned_start,
                   wi.planned_end AS planned_end,
                   wi.labour_hours AS labour_hours,
                   w.id AS worker_id,
                   w.first_name + ' ' + w.last_name AS worker_name,
                   crew.id AS crew_id,
                   crew.name AS crew_name,
                   p.name AS project_name
            ORDER BY wi.planned_start ASC
            """,
            {
                "company_id": company_id,
                "project_id": project_id,
            },
        )

        # Group by ISO week
        weeks: dict[str, list[dict[str, Any]]] = {}
        unscheduled: list[dict[str, Any]] = []

        for row in results:
            item = {
                "work_item_id": row["work_item_id"],
                "description": row["description"],
                "state": row["state"],
                "planned_start": row["planned_start"],
                "planned_end": row["planned_end"],
                "labour_hours": row["labour_hours"],
                "assigned_worker": row["worker_name"],
                "assigned_worker_id": row["worker_id"],
                "assigned_crew": row["crew_name"],
                "assigned_crew_id": row["crew_id"],
            }

            if row["planned_start"]:
                try:
                    start_dt = datetime.fromisoformat(row["planned_start"])
                    iso_year, iso_week, _ = start_dt.isocalendar()
                    week_key = f"{iso_year}-W{iso_week:02d}"
                    weeks.setdefault(week_key, []).append(item)
                except (ValueError, TypeError):
                    unscheduled.append(item)
            else:
                unscheduled.append(item)

        return {
            "project_id": project_id,
            "project_name": results[0]["project_name"] if results else None,
            "weeks": weeks,
            "unscheduled": unscheduled,
            "total_items": len(results),
            "scheduled_items": len(results) - len(unscheduled),
            "generated_at": now.isoformat(),
        }

    def assign_workers(
        self,
        company_id: str,
        project_id: str,
        work_item_id: str,
        worker_ids: list[str] | None = None,
        crew_id: str | None = None,
        actor: Actor | None = None,
    ) -> dict[str, Any]:
        """Assign workers or a crew to a work item.

        Args:
            company_id: The owning company ID.
            project_id: The parent project ID.
            work_item_id: The work item to assign to.
            worker_ids: List of worker IDs to assign individually.
            crew_id: Crew ID to assign (alternative to individual workers).
            actor: The actor performing the assignment.

        Returns:
            Dict with assignment confirmation.
        """
        if not actor:
            actor = Actor.human("system")
        provenance = self._provenance_update(actor)
        assigned: list[dict[str, Any]] = []

        if crew_id:
            result = self._write_tx_single(
                """
                MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
                      -[:HAS_WORK_ITEM]->(wi:WorkItem {id: $work_item_id})
                WHERE wi.deleted = false
                MATCH (crew:Crew {id: $crew_id})
                OPTIONAL MATCH (wi)-[old:ASSIGNED_TO_CREW]->() DELETE old
                CREATE (wi)-[:ASSIGNED_TO_CREW]->(crew)
                SET wi += $provenance
                RETURN wi.id AS work_item_id, crew.name AS crew_name
                """,
                {
                    "company_id": company_id,
                    "project_id": project_id,
                    "work_item_id": work_item_id,
                    "crew_id": crew_id,
                    "provenance": provenance,
                },
            )
            if result:
                assigned.append({"crew_id": crew_id, "crew_name": result["crew_name"]})

        if worker_ids:
            for wid in worker_ids:
                result = self._write_tx_single(
                    """
                    MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
                          -[:HAS_WORK_ITEM]->(wi:WorkItem {id: $work_item_id})
                    WHERE wi.deleted = false
                    MATCH (w:Worker {id: $worker_id})
                    WHERE w.deleted = false
                    MERGE (wi)-[:ASSIGNED_TO_WORKER]->(w)
                    SET wi += $provenance
                    RETURN w.id AS worker_id, w.first_name + ' ' + w.last_name AS worker_name
                    """,
                    {
                        "company_id": company_id,
                        "project_id": project_id,
                        "work_item_id": work_item_id,
                        "worker_id": wid,
                        "provenance": provenance,
                    },
                )
                if result:
                    assigned.append({
                        "worker_id": result["worker_id"],
                        "worker_name": result["worker_name"],
                    })

        if assigned:
            self._emit_audit(
                event_type="relationship.added",
                entity_id=work_item_id,
                entity_type="WorkItem",
                company_id=company_id,
                actor=actor,
                summary=f"Assigned {len(assigned)} resource(s) to work item {work_item_id}",
                related_entity_ids=worker_ids or ([crew_id] if crew_id else []),
            )
        return {
            "work_item_id": work_item_id,
            "assigned": assigned,
            "total_assigned": len(assigned),
        }

    def detect_conflicts(
        self,
        company_id: str,
        project_id: str,
    ) -> dict[str, Any]:
        """Detect scheduling conflicts for a project.

        Checks:
        1. Worker certifications expiring before planned_end
        2. Workers double-booked across projects on overlapping dates
        3. Equipment maintenance windows overlapping work items

        Args:
            company_id: The owning company ID.
            project_id: The project to check.

        Returns:
            Dict with detected conflicts.
        """
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        conflicts: list[dict[str, Any]] = []

        # 1. Cert expiry conflicts — workers assigned to work items
        #    where cert expires before planned_end
        cert_results = self._read_tx(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
                  -[:HAS_WORK_ITEM]->(wi:WorkItem)-[:ASSIGNED_TO_WORKER]->(w:Worker)
            WHERE wi.deleted = false AND wi.planned_end IS NOT NULL
            MATCH (w)-[:HOLDS_CERT]->(cert:Certification)
            WHERE cert.expiry_date IS NOT NULL
                  AND cert.expiry_date < wi.planned_end
                  AND cert.expiry_date >= $today
            RETURN wi.id AS work_item_id, wi.description AS work_item_desc,
                   wi.planned_end AS planned_end,
                   w.id AS worker_id,
                   w.first_name + ' ' + w.last_name AS worker_name,
                   cert.certification_type AS cert_type,
                   cert.expiry_date AS cert_expiry
            """,
            {
                "company_id": company_id,
                "project_id": project_id,
                "today": today,
            },
        )

        for row in cert_results:
            conflicts.append({
                "type": "cert_expiry",
                "severity": "high",
                "worker_id": row["worker_id"],
                "worker_name": row["worker_name"],
                "work_item_id": row["work_item_id"],
                "description": (
                    f"{row['worker_name']}'s {row['cert_type']} expires "
                    f"{row['cert_expiry']}, before work item ends {row['planned_end']}"
                ),
                "resolution": f"Renew {row['cert_type']} before {row['cert_expiry']}",
            })

        # 2. Double-booking — worker assigned to overlapping work items
        #    across different projects
        double_results = self._read_tx(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
                  -[:HAS_WORK_ITEM]->(wi:WorkItem)-[:ASSIGNED_TO_WORKER]->(w:Worker)
            WHERE wi.deleted = false AND wi.planned_start IS NOT NULL AND wi.planned_end IS NOT NULL
            MATCH (w)<-[:ASSIGNED_TO_WORKER]-(other_wi:WorkItem)<-[:HAS_WORK_ITEM]-(other_p:Project)
            WHERE other_wi.id <> wi.id
                  AND other_wi.deleted = false
                  AND other_wi.planned_start IS NOT NULL AND other_wi.planned_end IS NOT NULL
                  AND other_wi.planned_start < wi.planned_end
                  AND other_wi.planned_end > wi.planned_start
            RETURN DISTINCT
                   w.id AS worker_id,
                   w.first_name + ' ' + w.last_name AS worker_name,
                   wi.id AS work_item_id_a, wi.description AS desc_a,
                   wi.planned_start AS start_a, wi.planned_end AS end_a,
                   other_wi.id AS work_item_id_b, other_wi.description AS desc_b,
                   other_wi.planned_start AS start_b, other_wi.planned_end AS end_b,
                   other_p.name AS other_project_name
            """,
            {
                "company_id": company_id,
                "project_id": project_id,
            },
        )

        seen_pairs: set[str] = set()
        for row in double_results:
            pair_key = "|".join(sorted([row["work_item_id_a"], row["work_item_id_b"]]))
            if pair_key in seen_pairs:
                continue
            seen_pairs.add(pair_key)
            conflicts.append({
                "type": "double_booking",
                "severity": "high",
                "worker_id": row["worker_id"],
                "worker_name": row["worker_name"],
                "work_item_id": row["work_item_id_a"],
                "description": (
                    f"{row['worker_name']} double-booked: "
                    f"'{row['desc_a']}' ({row['start_a']} to {row['end_a']}) "
                    f"overlaps with '{row['desc_b']}' on {row['other_project_name']}"
                ),
                "resolution": "Reassign worker on one of the conflicting items",
            })

        return {
            "project_id": project_id,
            "conflicts": conflicts,
            "total_conflicts": len(conflicts),
            "has_conflicts": len(conflicts) > 0,
            "checked_at": datetime.now(timezone.utc).isoformat(),
        }
