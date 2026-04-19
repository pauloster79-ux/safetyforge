"""WorkItem CRUD service (Neo4j-backed).

WorkItems are the atomic unit of the platform — a discrete scope of work
that can be estimated, scheduled, assigned, and invoiced. Cost is built
up from Labour and Item child nodes, not flat properties.
"""

from datetime import datetime, timezone
from typing import Any

from app.exceptions import ProjectNotFoundError
from app.models.actor import Actor
from app.services.base_service import BaseService


class WorkItemNotFoundError(Exception):
    """Raised when a work item cannot be found."""

    def __init__(self, work_item_id: str) -> None:
        self.work_item_id = work_item_id
        super().__init__(f"Work item not found: {work_item_id}")


VALID_STATES = frozenset(
    {
        "draft",
        "scheduled",
        "in_progress",
        "complete",
        "invoiced",
        "on_hold",
        "cancelled",
        "superseded",
    }
)


class WorkItemService(BaseService):
    """Manages WorkItem nodes in the Neo4j graph.

    WorkItems connect to projects via (Project)-[:HAS_WORK_ITEM]->(WorkItem).
    They may optionally belong to a WorkPackage via (WorkPackage)-[:CONTAINS]->(WorkItem).
    Cost is derived from child Labour and Item nodes.
    """

    def create(
        self,
        company_id: str,
        project_id: str,
        data: dict[str, Any],
        user_id: str,
        work_package_id: str | None = None,
        work_category_id: str | None = None,
    ) -> dict[str, Any]:
        """Create a new work item on a project.

        Args:
            company_id: The owning company ID (used for access scope).
            project_id: The parent project ID.
            data: Work item fields — description, quantity, unit, margin_pct,
                is_alternate, alternate_label, planned_start, planned_end, notes, etc.
            user_id: Clerk user ID of the creating user.
            work_package_id: Optional work package to group this item under.
            work_category_id: Optional canonical or extension category ID. When
                supplied, the service writes `(wi)-[:CATEGORISED_AS]->(cat)` atomically
                with the node creation. The caller is responsible for validating
                access scope for Extensions (see
                ``WorkCategoryService.resolve_for_work_item``). Canonicals are
                globally accessible.

        Returns:
            The created work item dict.

        Raises:
            ProjectNotFoundError: If the project does not exist under this company.
            ValueError: If ``work_category_id`` is supplied but does not reference
                an accessible WorkCategory.
        """
        actor = Actor.human(user_id)
        wi_id = self._generate_id("wi")

        props: dict[str, Any] = {
            "id": wi_id,
            "description": data.get("description", ""),
            "state": "draft",
            "quantity": data.get("quantity"),
            "unit": data.get("unit"),
            "labour_total_cents": 0,
            "items_total_cents": 0,
            "margin_pct": data.get("margin_pct"),
            "sell_price_cents": 0,
            "is_alternate": data.get("is_alternate", False),
            "alternate_label": data.get("alternate_label"),
            "alternate_description": data.get("alternate_description"),
            "alternate_price_adjustment_cents": data.get("alternate_price_adjustment_cents"),
            "planned_start": data.get("planned_start"),
            "planned_end": data.get("planned_end"),
            "actual_start": None,
            "actual_end": None,
            "notes": data.get("notes"),
            "deleted": False,
            **self._provenance_create(actor),
        }

        # Compose Cypher based on whether package and/or category are supplied.
        # All four combinations share the core pattern; we MATCH the optional
        # targets first, then CREATE the WorkItem + relationships in one tx.
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
            package_match = "MATCH (wp:WorkPackage {id: $work_package_id})\n            "
            package_link = "CREATE (wp)-[:CONTAINS]->(wi)\n            "
            params["work_package_id"] = work_package_id

        if work_category_id:
            # Accept both Canonical (shared) and Extension (scoped to this company).
            # The Canonical match is unscoped; Extensions must be owned by this company.
            category_match = (
                "MATCH (cat:WorkCategory {id: $work_category_id})\n            "
                "WHERE cat:Canonical OR EXISTS { "
                "MATCH (c)-[:HAS_EXTENSION]->(cat) }\n            "
            )
            category_link = "CREATE (wi)-[:CATEGORISED_AS]->(cat)\n            "
            params["work_category_id"] = work_category_id

        cypher = f"""
            MATCH (c:Company {{id: $company_id}})-[:OWNS_PROJECT]->(p:Project {{id: $project_id}})
            {package_match}{category_match}CREATE (wi:WorkItem $props)
            CREATE (p)-[:HAS_WORK_ITEM]->(wi)
            {package_link}{category_link}RETURN wi {{.*, project_id: p.id, company_id: c.id}} AS work_item
        """

        result = self._write_tx_single(cypher, params)
        if result is None:
            raise ProjectNotFoundError(project_id)

        self._emit_audit(
            event_type="entity.created",
            entity_id=wi_id,
            entity_type="WorkItem",
            company_id=company_id,
            actor=actor,
            summary=f"Created work item '{data.get('description', '')}' (draft)",
            related_entity_ids=[work_package_id] if work_package_id else None,
        )
        return result["work_item"]

    def get(self, company_id: str, project_id: str, work_item_id: str) -> dict[str, Any]:
        """Fetch a single work item with computed cost totals from children.

        Args:
            company_id: The owning company ID.
            project_id: The parent project ID.
            work_item_id: The work item ID to fetch.

        Returns:
            The work item dict with labour_total_cents and items_total_cents.

        Raises:
            WorkItemNotFoundError: If the work item does not exist or is soft-deleted.
        """
        result = self._read_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
                  -[:HAS_WORK_ITEM]->(wi:WorkItem {id: $work_item_id})
            WHERE wi.deleted = false
            OPTIONAL MATCH (wi)-[:HAS_LABOUR]->(lab:Labour)
            OPTIONAL MATCH (wi)-[:HAS_ITEM]->(item:Item)
            WITH wi, p, c,
                 coalesce(sum(lab.cost_cents), 0) AS labour_total,
                 coalesce(sum(item.total_cents), 0) AS items_total
            RETURN wi {.*,
                labour_total_cents: labour_total,
                items_total_cents: items_total,
                sell_price_cents: round((labour_total + items_total)
                    * (1 + coalesce(wi.margin_pct, 0) / 100.0)),
                project_id: p.id,
                company_id: c.id
            } AS work_item
            """,
            {
                "company_id": company_id,
                "project_id": project_id,
                "work_item_id": work_item_id,
            },
        )
        if result is None:
            raise WorkItemNotFoundError(work_item_id)
        return result["work_item"]

    def list_by_project(
        self,
        company_id: str,
        project_id: str,
        state: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> dict[str, Any]:
        """List work items for a project with optional state filter.

        Args:
            company_id: The owning company ID.
            project_id: The parent project ID.
            state: Optional state filter (draft, scheduled, in_progress, etc.).
            limit: Maximum number of items to return.
            offset: Number of items to skip.

        Returns:
            A dict with 'work_items' list and 'total' count.
        """
        where_clauses = ["wi.deleted = false"]
        params: dict[str, Any] = {
            "company_id": company_id,
            "project_id": project_id,
            "limit": limit,
            "offset": offset,
        }

        if state is not None:
            where_clauses.append("wi.state = $state")
            params["state"] = state

        where_str = " AND ".join(where_clauses)

        count_result = self._read_tx_single(
            f"""
            MATCH (c:Company {{id: $company_id}})-[:OWNS_PROJECT]->(p:Project {{id: $project_id}})
                  -[:HAS_WORK_ITEM]->(wi:WorkItem)
            WHERE {where_str}
            RETURN count(wi) AS total
            """,
            params,
        )
        total = count_result["total"] if count_result else 0

        results = self._read_tx(
            f"""
            MATCH (c:Company {{id: $company_id}})-[:OWNS_PROJECT]->(p:Project {{id: $project_id}})
                  -[:HAS_WORK_ITEM]->(wi:WorkItem)
            WHERE {where_str}
            OPTIONAL MATCH (wi)-[:HAS_LABOUR]->(lab:Labour)
            OPTIONAL MATCH (wi)-[:HAS_ITEM]->(item:Item)
            WITH wi, p, c,
                 coalesce(sum(lab.cost_cents), 0) AS labour_total,
                 coalesce(sum(item.total_cents), 0) AS items_total
            RETURN wi {{.*,
                labour_total_cents: labour_total,
                items_total_cents: items_total,
                sell_price_cents: round((labour_total + items_total)
                    * (1 + coalesce(wi.margin_pct, 0) / 100.0)),
                project_id: p.id,
                company_id: c.id
            }} AS work_item
            ORDER BY wi.created_at DESC
            SKIP $offset LIMIT $limit
            """,
            params,
        )

        return {"work_items": [r["work_item"] for r in results], "total": total}

    def update(
        self,
        company_id: str,
        project_id: str,
        work_item_id: str,
        data: dict[str, Any],
        user_id: str,
    ) -> dict[str, Any]:
        """Update fields on an existing work item.

        Args:
            company_id: The owning company ID.
            project_id: The parent project ID.
            work_item_id: The work item ID to update.
            data: Fields to update (only non-None values applied).
            user_id: Clerk user ID of the updating user.

        Returns:
            The updated work item dict.

        Raises:
            WorkItemNotFoundError: If the work item does not exist or is soft-deleted.
        """
        actor = Actor.human(user_id)
        update_fields = {k: v for k, v in data.items() if v is not None}
        update_fields.update(self._provenance_update(actor))

        # If margin_pct changed, recalculate sell_price_cents from existing totals
        recalc_sell_price = "margin_pct" in update_fields

        result = self._write_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
                  -[:HAS_WORK_ITEM]->(wi:WorkItem {id: $work_item_id})
            WHERE wi.deleted = false
            SET wi += $props
            WITH c, p, wi
            // Recalculate sell_price_cents if margin changed
            SET wi.sell_price_cents = CASE
                WHEN $recalc
                THEN round((coalesce(wi.labour_total_cents, 0) + coalesce(wi.items_total_cents, 0))
                     * (1 + coalesce(wi.margin_pct, 0) / 100.0))
                ELSE wi.sell_price_cents
            END
            RETURN wi {.*, project_id: p.id, company_id: c.id} AS work_item
            """,
            {
                "company_id": company_id,
                "project_id": project_id,
                "work_item_id": work_item_id,
                "props": update_fields,
                "recalc": recalc_sell_price,
            },
        )
        if result is None:
            raise WorkItemNotFoundError(work_item_id)

        changed = [
            k for k in update_fields
            if k not in ("updated_by", "updated_actor_type", "updated_at")
        ]
        suffix = f" ({', '.join(changed)})" if changed else ""
        self._emit_audit(
            event_type="entity.updated",
            entity_id=work_item_id,
            entity_type="WorkItem",
            company_id=company_id,
            actor=actor,
            summary=f"Updated work item '{result['work_item'].get('description', '')}'{suffix}",
        )
        return result["work_item"]

    def update_state(
        self,
        company_id: str,
        project_id: str,
        work_item_id: str,
        new_state: str,
        user_id: str,
    ) -> dict[str, Any]:
        """Transition a work item to a new lifecycle state.

        Args:
            company_id: The owning company ID.
            project_id: The parent project ID.
            work_item_id: The work item ID.
            new_state: Target state. Must be one of: draft, scheduled, in_progress,
                complete, invoiced, on_hold, cancelled, superseded.
            user_id: Clerk user ID of the updating user.

        Returns:
            The updated work item dict.

        Raises:
            ValueError: If new_state is not a valid state.
            WorkItemNotFoundError: If the work item does not exist or is soft-deleted.
        """
        if new_state not in VALID_STATES:
            raise ValueError(f"Invalid state '{new_state}'. Must be one of: {sorted(VALID_STATES)}")

        actor = Actor.human(user_id)
        now = datetime.now(timezone.utc).isoformat()
        extra: dict[str, Any] = {"actual_start": now} if new_state == "in_progress" else {}
        if new_state == "complete":
            extra["actual_end"] = now

        result = self._write_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
                  -[:HAS_WORK_ITEM]->(wi:WorkItem {id: $work_item_id})
            WHERE wi.deleted = false
            WITH wi, p, c, wi.state AS prev_state, wi.description AS wi_desc
            SET wi.state = $new_state, wi += $extra, wi.updated_by = $updated_by,
                wi.updated_at = $updated_at, wi.updated_actor_type = $updated_actor_type
            RETURN wi {.*, project_id: p.id, company_id: c.id} AS work_item,
                   prev_state, wi_desc
            """,
            {
                "company_id": company_id,
                "project_id": project_id,
                "work_item_id": work_item_id,
                "new_state": new_state,
                "extra": extra,
                **self._provenance_update(actor),
            },
        )
        if result is None:
            raise WorkItemNotFoundError(work_item_id)

        self._emit_audit(
            event_type="state.transitioned",
            entity_id=work_item_id,
            entity_type="WorkItem",
            company_id=company_id,
            actor=actor,
            summary=f"Work item '{result['wi_desc']}': {result['prev_state']} → {new_state}",
            prev_state=result["prev_state"],
            new_state=new_state,
        )
        return result["work_item"]

    def archive(
        self, company_id: str, project_id: str, work_item_id: str, user_id: str
    ) -> None:
        """Soft-delete a work item and cascade to its Labour/Item children.

        Children are marked deleted so they stop contributing to estimate
        rollups. Restoration reverses this.

        Args:
            company_id: The owning company ID.
            project_id: The parent project ID.
            work_item_id: The work item ID to archive.
            user_id: Clerk user ID of the deleting user.

        Raises:
            WorkItemNotFoundError: If the work item does not exist.
        """
        result = self._write_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
                  -[:HAS_WORK_ITEM]->(wi:WorkItem {id: $work_item_id})
            WHERE coalesce(wi.deleted, false) = false
            SET wi.deleted = true, wi.updated_at = $now
            WITH wi
            OPTIONAL MATCH (wi)-[:HAS_LABOUR]->(lab:Labour)
            OPTIONAL MATCH (wi)-[:HAS_ITEM]->(item:Item)
            WITH wi, collect(DISTINCT lab) AS labs, collect(DISTINCT item) AS items
            FOREACH (lab IN labs | SET lab.deleted = true)
            FOREACH (item IN items | SET item.deleted = true)
            RETURN wi.id AS id, wi.description AS description
            """,
            {
                "company_id": company_id,
                "project_id": project_id,
                "work_item_id": work_item_id,
                "now": datetime.now(timezone.utc).isoformat(),
            },
        )
        if result is None:
            raise WorkItemNotFoundError(work_item_id)

        self._emit_audit(
            event_type="entity.archived",
            entity_id=work_item_id,
            entity_type="WorkItem",
            company_id=company_id,
            actor=Actor.human(user_id),
            summary=f"Archived work item '{result['description']}'",
        )

    def restore(
        self, company_id: str, project_id: str, work_item_id: str, user_id: str
    ) -> None:
        """Restore a soft-deleted work item and its Labour/Item children.

        Args:
            company_id: The owning company ID.
            project_id: The parent project ID.
            work_item_id: The work item ID to restore.
            user_id: Clerk user ID of the restoring user.

        Raises:
            WorkItemNotFoundError: If the work item does not exist.
        """
        result = self._write_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
                  -[:HAS_WORK_ITEM]->(wi:WorkItem {id: $work_item_id})
            WHERE wi.deleted = true
            SET wi.deleted = false, wi.updated_at = $now
            WITH wi
            OPTIONAL MATCH (wi)-[:HAS_LABOUR]->(lab:Labour)
            OPTIONAL MATCH (wi)-[:HAS_ITEM]->(item:Item)
            WITH wi, collect(DISTINCT lab) AS labs, collect(DISTINCT item) AS items
            FOREACH (lab IN labs | SET lab.deleted = false)
            FOREACH (item IN items | SET item.deleted = false)
            RETURN wi.id AS id, wi.description AS description
            """,
            {
                "company_id": company_id,
                "project_id": project_id,
                "work_item_id": work_item_id,
                "now": datetime.now(timezone.utc).isoformat(),
            },
        )
        if result is None:
            raise WorkItemNotFoundError(work_item_id)

        self._emit_audit(
            event_type="entity.restored",
            entity_id=work_item_id,
            entity_type="WorkItem",
            company_id=company_id,
            actor=Actor.human(user_id),
            summary=f"Restored work item '{result['description']}'",
        )

    def create_alternate(
        self,
        company_id: str,
        project_id: str,
        base_work_item_id: str,
        data: dict[str, Any],
        user_id: str,
    ) -> dict[str, Any]:
        """Create an alternate (VE) version of an existing work item.

        The alternate is linked to the base via ALTERNATE_TO relationship.

        Args:
            company_id: The owning company ID.
            project_id: The parent project ID.
            base_work_item_id: The base work item this is an alternate for.
            data: Alternate work item fields.
            user_id: Clerk user ID of the creating user.

        Returns:
            The created alternate work item dict.

        Raises:
            WorkItemNotFoundError: If the base work item does not exist.
        """
        actor = Actor.human(user_id)
        wi_id = self._generate_id("wi")

        props: dict[str, Any] = {
            "id": wi_id,
            "description": data.get("description", ""),
            "state": "draft",
            "quantity": data.get("quantity"),
            "unit": data.get("unit"),
            "labour_total_cents": 0,
            "items_total_cents": 0,
            "margin_pct": data.get("margin_pct"),
            "sell_price_cents": 0,
            "is_alternate": True,
            "alternate_label": data.get("alternate_label", ""),
            "alternate_description": data.get("alternate_description", ""),
            "alternate_price_adjustment_cents": data.get("alternate_price_adjustment_cents"),
            "planned_start": data.get("planned_start"),
            "planned_end": data.get("planned_end"),
            "notes": data.get("notes"),
            "deleted": False,
            **self._provenance_create(actor),
        }

        result = self._write_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
                  -[:HAS_WORK_ITEM]->(base:WorkItem {id: $base_id})
            WHERE base.deleted = false
            CREATE (alt:WorkItem $props)
            CREATE (p)-[:HAS_WORK_ITEM]->(alt)
            CREATE (alt)-[:ALTERNATE_TO]->(base)
            RETURN alt {.*, project_id: p.id, company_id: c.id} AS work_item,
                   base.description AS base_desc
            """,
            {
                "company_id": company_id,
                "project_id": project_id,
                "base_id": base_work_item_id,
                "props": props,
            },
        )
        if result is None:
            raise WorkItemNotFoundError(base_work_item_id)

        self._emit_audit(
            event_type="entity.created",
            entity_id=wi_id,
            entity_type="WorkItem",
            company_id=company_id,
            actor=actor,
            summary=(
                f"Created alternate '{data.get('alternate_label', '')}' "
                f"for '{result['base_desc']}'"
            ),
            related_entity_ids=[base_work_item_id],
        )
        return result["work_item"]

    def assign_worker(
        self,
        company_id: str,
        project_id: str,
        work_item_id: str,
        worker_id: str,
        user_id: str,
    ) -> dict[str, Any]:
        """Assign a worker to a work item.

        Creates an (WorkItem)-[:ASSIGNED_TO_WORKER]->(Worker) relationship.
        Any previous worker assignment is replaced.

        Args:
            company_id: The owning company ID.
            project_id: The parent project ID.
            work_item_id: The work item ID.
            worker_id: The worker ID to assign.
            user_id: Clerk user ID of the updating user.

        Returns:
            The updated work item dict.

        Raises:
            WorkItemNotFoundError: If the work item does not exist.
        """
        actor = Actor.human(user_id)
        result = self._write_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
                  -[:HAS_WORK_ITEM]->(wi:WorkItem {id: $work_item_id})
            WHERE wi.deleted = false
            MATCH (w:Worker {id: $worker_id})
            OPTIONAL MATCH (wi)-[old:ASSIGNED_TO_WORKER]->()
            DELETE old
            CREATE (wi)-[:ASSIGNED_TO_WORKER]->(w)
            SET wi += $provenance
            RETURN wi {.*, project_id: p.id, company_id: c.id} AS work_item,
                   w.name AS worker_name
            """,
            {
                "company_id": company_id,
                "project_id": project_id,
                "work_item_id": work_item_id,
                "worker_id": worker_id,
                "provenance": self._provenance_update(actor),
            },
        )
        if result is None:
            raise WorkItemNotFoundError(work_item_id)

        self._emit_audit(
            event_type="relationship.added",
            entity_id=work_item_id,
            entity_type="WorkItem",
            company_id=company_id,
            actor=actor,
            summary=(
                f"Assigned {result['worker_name']} to work item "
                f"'{result['work_item'].get('description', '')}'"
            ),
            related_entity_ids=[worker_id],
        )
        return result["work_item"]

    def assign_crew(
        self,
        company_id: str,
        project_id: str,
        work_item_id: str,
        crew_id: str,
        user_id: str,
    ) -> dict[str, Any]:
        """Assign a crew to a work item.

        Creates an (WorkItem)-[:ASSIGNED_TO_CREW]->(Crew) relationship.
        Any previous crew assignment is replaced.

        Args:
            company_id: The owning company ID.
            project_id: The parent project ID.
            work_item_id: The work item ID.
            crew_id: The crew ID to assign.
            user_id: Clerk user ID of the updating user.

        Returns:
            The updated work item dict.

        Raises:
            WorkItemNotFoundError: If the work item does not exist.
        """
        actor = Actor.human(user_id)
        result = self._write_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
                  -[:HAS_WORK_ITEM]->(wi:WorkItem {id: $work_item_id})
            WHERE wi.deleted = false
            MATCH (crew:Crew {id: $crew_id})
            OPTIONAL MATCH (wi)-[old:ASSIGNED_TO_CREW]->()
            DELETE old
            CREATE (wi)-[:ASSIGNED_TO_CREW]->(crew)
            SET wi += $provenance
            RETURN wi {.*, project_id: p.id, company_id: c.id} AS work_item,
                   crew.name AS crew_name
            """,
            {
                "company_id": company_id,
                "project_id": project_id,
                "work_item_id": work_item_id,
                "crew_id": crew_id,
                "provenance": self._provenance_update(actor),
            },
        )
        if result is None:
            raise WorkItemNotFoundError(work_item_id)

        self._emit_audit(
            event_type="relationship.added",
            entity_id=work_item_id,
            entity_type="WorkItem",
            company_id=company_id,
            actor=actor,
            summary=(
                f"Assigned crew '{result['crew_name']}' to work item "
                f"'{result['work_item'].get('description', '')}'"
            ),
            related_entity_ids=[crew_id],
        )
        return result["work_item"]

    def recalculate_totals(
        self, company_id: str, project_id: str, work_item_id: str
    ) -> dict[str, Any]:
        """Recalculate labour_total_cents, items_total_cents, and sell_price_cents from children.

        Args:
            company_id: The owning company ID.
            project_id: The parent project ID.
            work_item_id: The work item ID.

        Returns:
            The updated work item dict with recalculated totals.

        Raises:
            WorkItemNotFoundError: If the work item does not exist.
        """
        result = self._write_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
                  -[:HAS_WORK_ITEM]->(wi:WorkItem {id: $work_item_id})
            WHERE wi.deleted = false
            OPTIONAL MATCH (wi)-[:HAS_LABOUR]->(lab:Labour)
            OPTIONAL MATCH (wi)-[:HAS_ITEM]->(item:Item)
            WITH wi, p, c,
                 coalesce(sum(DISTINCT lab.cost_cents), 0) AS labour_total,
                 coalesce(sum(DISTINCT item.total_cents), 0) AS items_total
            SET wi.labour_total_cents = labour_total,
                wi.items_total_cents = items_total,
                wi.sell_price_cents = round((labour_total + items_total)
                    * (1 + coalesce(wi.margin_pct, 0) / 100.0)),
                wi.updated_at = $now
            RETURN wi {.*, project_id: p.id, company_id: c.id} AS work_item
            """,
            {
                "company_id": company_id,
                "project_id": project_id,
                "work_item_id": work_item_id,
                "now": datetime.now(timezone.utc).isoformat(),
            },
        )
        if result is None:
            raise WorkItemNotFoundError(work_item_id)
        return result["work_item"]

    def get_estimate_summary(
        self, company_id: str, project_id: str, work_item_id: str
    ) -> dict[str, Any]:
        """Calculate cost estimates from Labour and Item children.

        Args:
            company_id: The owning company ID.
            project_id: The parent project ID.
            work_item_id: The work item ID.

        Returns:
            Dict with labour_cost, materials_cost, margin_amount, total, and currency.

        Raises:
            WorkItemNotFoundError: If the work item does not exist.
        """
        result = self._read_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
                  -[:HAS_WORK_ITEM]->(wi:WorkItem {id: $work_item_id})
            WHERE wi.deleted = false
            OPTIONAL MATCH (wi)-[:HAS_LABOUR]->(lab:Labour)
            OPTIONAL MATCH (wi)-[:HAS_ITEM]->(item:Item)
            WITH wi,
                 coalesce(sum(DISTINCT lab.cost_cents), 0) AS labour_cost,
                 coalesce(sum(DISTINCT item.total_cents), 0) AS items_cost
            RETURN {
                labour_cost_cents: labour_cost,
                items_cost_cents: items_cost,
                margin_pct: coalesce(wi.margin_pct, 0),
                sell_price_cents: round((labour_cost + items_cost)
                    * (1 + coalesce(wi.margin_pct, 0) / 100.0)),
                currency: 'USD'
            } AS summary
            """,
            {
                "company_id": company_id,
                "project_id": project_id,
                "work_item_id": work_item_id,
            },
        )
        if result is None:
            raise WorkItemNotFoundError(work_item_id)
        return result["summary"]
