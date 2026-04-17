"""Labour CRUD service (Neo4j-backed).

Labour nodes are child nodes of WorkItems representing discrete labour tasks.
Graph model: (WorkItem)-[:HAS_LABOUR]->(Labour)
"""

from typing import Any

from app.exceptions import LabourNotFoundError, ProjectNotFoundError
from app.models.actor import Actor
from app.services.base_service import BaseService
from app.services.work_item_service import WorkItemNotFoundError


class LabourService(BaseService):
    """Manages Labour nodes under WorkItems in the Neo4j graph."""

    def create(
        self,
        company_id: str,
        project_id: str,
        work_item_id: str,
        data: dict[str, Any],
        user_id: str,
    ) -> dict[str, Any]:
        """Create a labour task on a work item.

        Computes cost_cents as rate_cents * hours (rounded to nearest cent).

        Args:
            company_id: The owning company ID.
            project_id: The parent project ID.
            work_item_id: The parent work item ID.
            data: Labour fields — task, rate_cents, hours, notes.
            user_id: Clerk user ID of the creating user.

        Returns:
            The created labour dict.

        Raises:
            WorkItemNotFoundError: If the work item does not exist.
        """
        actor = Actor.human(user_id)
        lab_id = self._generate_id("lab")

        rate_cents = data["rate_cents"]
        hours = data["hours"]
        cost_cents = round(rate_cents * hours)

        props: dict[str, Any] = {
            "id": lab_id,
            "task": data["task"],
            "rate_cents": rate_cents,
            "hours": hours,
            "cost_cents": cost_cents,
            "notes": data.get("notes", ""),
            # Source cascade provenance — optional at create time, set by MCP
            # tools / estimating agents.
            "rate_source_id": data.get("rate_source_id"),
            "rate_source_type": data.get("rate_source_type"),
            "productivity_source_id": data.get("productivity_source_id"),
            "productivity_source_type": data.get("productivity_source_type"),
            "source_reasoning": data.get("source_reasoning"),
            **self._provenance_create(actor),
        }

        result = self._write_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
                  -[:HAS_WORK_ITEM]->(wi:WorkItem {id: $work_item_id})
            WHERE wi.deleted = false
            CREATE (lab:Labour $props)
            CREATE (wi)-[:HAS_LABOUR]->(lab)
            RETURN lab {.*, work_item_id: wi.id} AS labour
            """,
            {
                "company_id": company_id,
                "project_id": project_id,
                "work_item_id": work_item_id,
                "props": props,
            },
        )
        if result is None:
            raise WorkItemNotFoundError(work_item_id)
        self._emit_audit(
            event_type="entity.created",
            entity_id=lab_id,
            entity_type="Labour",
            company_id=company_id,
            actor=actor,
            summary=f"Created labour task '{data['task']}' on work item {work_item_id}",
            related_entity_ids=[work_item_id],
        )
        return result["labour"]

    def get(
        self,
        company_id: str,
        project_id: str,
        work_item_id: str,
        labour_id: str,
    ) -> dict[str, Any]:
        """Fetch a single labour task.

        Args:
            company_id: The owning company ID.
            project_id: The parent project ID.
            work_item_id: The parent work item ID.
            labour_id: The labour ID to fetch.

        Returns:
            The labour dict.

        Raises:
            LabourNotFoundError: If the labour task does not exist.
        """
        result = self._read_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
                  -[:HAS_WORK_ITEM]->(wi:WorkItem {id: $work_item_id})
                  -[:HAS_LABOUR]->(lab:Labour {id: $labour_id})
            RETURN lab {.*, work_item_id: wi.id} AS labour
            """,
            {
                "company_id": company_id,
                "project_id": project_id,
                "work_item_id": work_item_id,
                "labour_id": labour_id,
            },
        )
        if result is None:
            raise LabourNotFoundError(labour_id)
        return result["labour"]

    def list_by_work_item(
        self,
        company_id: str,
        project_id: str,
        work_item_id: str,
    ) -> dict[str, Any]:
        """List all labour tasks for a work item.

        Args:
            company_id: The owning company ID.
            project_id: The parent project ID.
            work_item_id: The parent work item ID.

        Returns:
            A dict with 'labour' list and 'total' count.
        """
        results = self._read_tx(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
                  -[:HAS_WORK_ITEM]->(wi:WorkItem {id: $work_item_id})
                  -[:HAS_LABOUR]->(lab:Labour)
            RETURN lab {.*, work_item_id: wi.id} AS labour
            ORDER BY lab.created_at ASC
            """,
            {
                "company_id": company_id,
                "project_id": project_id,
                "work_item_id": work_item_id,
            },
        )
        labour = [r["labour"] for r in results]
        return {"labour": labour, "total": len(labour)}

    def update(
        self,
        company_id: str,
        project_id: str,
        work_item_id: str,
        labour_id: str,
        data: dict[str, Any],
        user_id: str,
    ) -> dict[str, Any]:
        """Update a labour task. Recomputes cost_cents if rate or hours change.

        Args:
            company_id: The owning company ID.
            project_id: The parent project ID.
            work_item_id: The parent work item ID.
            labour_id: The labour ID to update.
            data: Fields to update (only non-None values applied).
            user_id: Clerk user ID of the updating user.

        Returns:
            The updated labour dict.

        Raises:
            LabourNotFoundError: If the labour task does not exist.
        """
        actor = Actor.human(user_id)
        update_fields = {k: v for k, v in data.items() if v is not None}
        update_fields.update(self._provenance_update(actor))

        # Recompute cost if rate or hours are changing
        recompute = "rate_cents" in update_fields or "hours" in update_fields

        if recompute:
            result = self._write_tx_single(
                """
                MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
                      -[:HAS_WORK_ITEM]->(wi:WorkItem {id: $work_item_id})
                      -[:HAS_LABOUR]->(lab:Labour {id: $labour_id})
                SET lab += $props
                WITH lab, wi,
                     round(lab.rate_cents * lab.hours) AS new_cost
                SET lab.cost_cents = new_cost
                RETURN lab {.*, work_item_id: wi.id} AS labour
                """,
                {
                    "company_id": company_id,
                    "project_id": project_id,
                    "work_item_id": work_item_id,
                    "labour_id": labour_id,
                    "props": update_fields,
                },
            )
        else:
            result = self._write_tx_single(
                """
                MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
                      -[:HAS_WORK_ITEM]->(wi:WorkItem {id: $work_item_id})
                      -[:HAS_LABOUR]->(lab:Labour {id: $labour_id})
                SET lab += $props
                RETURN lab {.*, work_item_id: wi.id} AS labour
                """,
                {
                    "company_id": company_id,
                    "project_id": project_id,
                    "work_item_id": work_item_id,
                    "labour_id": labour_id,
                    "props": update_fields,
                },
            )
        if result is None:
            raise LabourNotFoundError(labour_id)
        self._emit_audit(
            event_type="entity.updated",
            entity_id=labour_id,
            entity_type="Labour",
            company_id=company_id,
            actor=actor,
            summary=f"Updated labour task {labour_id}",
        )
        return result["labour"]

    def delete(
        self,
        company_id: str,
        project_id: str,
        work_item_id: str,
        labour_id: str,
    ) -> None:
        """Delete a labour task (hard delete — these are detail rows, not top-level entities).

        Args:
            company_id: The owning company ID.
            project_id: The parent project ID.
            work_item_id: The parent work item ID.
            labour_id: The labour ID to delete.

        Raises:
            LabourNotFoundError: If the labour task does not exist.
        """
        result = self._write_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
                  -[:HAS_WORK_ITEM]->(wi:WorkItem {id: $work_item_id})
                  -[:HAS_LABOUR]->(lab:Labour {id: $labour_id})
            DETACH DELETE lab
            RETURN wi.id AS work_item_id
            """,
            {
                "company_id": company_id,
                "project_id": project_id,
                "work_item_id": work_item_id,
                "labour_id": labour_id,
            },
        )
        if result is None:
            raise LabourNotFoundError(labour_id)
