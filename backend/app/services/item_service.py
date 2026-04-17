"""Item CRUD service (Neo4j-backed).

Item nodes are child nodes of WorkItems representing discrete non-labour costs
(materials, equipment, fixtures, rentals).
Graph model: (WorkItem)-[:HAS_ITEM]->(Item)
"""

from typing import Any

from app.exceptions import ItemNotFoundError
from app.models.actor import Actor
from app.services.base_service import BaseService
from app.services.work_item_service import WorkItemNotFoundError


class ItemService(BaseService):
    """Manages Item nodes under WorkItems in the Neo4j graph."""

    def create(
        self,
        company_id: str,
        project_id: str,
        work_item_id: str,
        data: dict[str, Any],
        user_id: str,
    ) -> dict[str, Any]:
        """Create an item on a work item.

        Computes total_cents as quantity * unit_cost_cents (rounded).

        Args:
            company_id: The owning company ID.
            project_id: The parent project ID.
            work_item_id: The parent work item ID.
            data: Item fields — description, product, quantity, unit, unit_cost_cents, notes.
            user_id: Clerk user ID of the creating user.

        Returns:
            The created item dict.

        Raises:
            WorkItemNotFoundError: If the work item does not exist.
        """
        actor = Actor.human(user_id)
        item_id = self._generate_id("item")

        quantity = data["quantity"]
        unit_cost_cents = data["unit_cost_cents"]
        total_cents = round(quantity * unit_cost_cents)

        # Normalise price_fetched_at if it came in as a datetime
        price_fetched_at = data.get("price_fetched_at")
        if price_fetched_at is not None and hasattr(price_fetched_at, "isoformat"):
            price_fetched_at = price_fetched_at.isoformat()

        props: dict[str, Any] = {
            "id": item_id,
            "description": data["description"],
            "product": data.get("product", ""),
            "quantity": quantity,
            "unit": data.get("unit", "EA"),
            "unit_cost_cents": unit_cost_cents,
            "total_cents": total_cents,
            "notes": data.get("notes", ""),
            # Source cascade provenance — optional at create time, set by MCP
            # tools / estimating agents.
            "price_source_id": data.get("price_source_id"),
            "price_source_type": data.get("price_source_type"),
            "source_reasoning": data.get("source_reasoning"),
            "source_url": data.get("source_url"),
            "price_fetched_at": price_fetched_at,
            **self._provenance_create(actor),
        }

        result = self._write_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
                  -[:HAS_WORK_ITEM]->(wi:WorkItem {id: $work_item_id})
            WHERE wi.deleted = false
            CREATE (item:Item $props)
            CREATE (wi)-[:HAS_ITEM]->(item)
            RETURN item {.*, work_item_id: wi.id} AS item
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
            entity_id=item_id,
            entity_type="Item",
            company_id=company_id,
            actor=actor,
            summary=f"Created item '{data['description']}' on work item {work_item_id}",
            related_entity_ids=[work_item_id],
        )
        return result["item"]

    def get(
        self,
        company_id: str,
        project_id: str,
        work_item_id: str,
        item_id: str,
    ) -> dict[str, Any]:
        """Fetch a single item.

        Args:
            company_id: The owning company ID.
            project_id: The parent project ID.
            work_item_id: The parent work item ID.
            item_id: The item ID to fetch.

        Returns:
            The item dict.

        Raises:
            ItemNotFoundError: If the item does not exist.
        """
        result = self._read_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
                  -[:HAS_WORK_ITEM]->(wi:WorkItem {id: $work_item_id})
                  -[:HAS_ITEM]->(item:Item {id: $item_id})
            RETURN item {.*, work_item_id: wi.id} AS item
            """,
            {
                "company_id": company_id,
                "project_id": project_id,
                "work_item_id": work_item_id,
                "item_id": item_id,
            },
        )
        if result is None:
            raise ItemNotFoundError(item_id)
        return result["item"]

    def list_by_work_item(
        self,
        company_id: str,
        project_id: str,
        work_item_id: str,
    ) -> dict[str, Any]:
        """List all items for a work item.

        Args:
            company_id: The owning company ID.
            project_id: The parent project ID.
            work_item_id: The parent work item ID.

        Returns:
            A dict with 'items' list and 'total' count.
        """
        results = self._read_tx(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
                  -[:HAS_WORK_ITEM]->(wi:WorkItem {id: $work_item_id})
                  -[:HAS_ITEM]->(item:Item)
            RETURN item {.*, work_item_id: wi.id} AS item
            ORDER BY item.created_at ASC
            """,
            {
                "company_id": company_id,
                "project_id": project_id,
                "work_item_id": work_item_id,
            },
        )
        items = [r["item"] for r in results]
        return {"items": items, "total": len(items)}

    def update(
        self,
        company_id: str,
        project_id: str,
        work_item_id: str,
        item_id: str,
        data: dict[str, Any],
        user_id: str,
    ) -> dict[str, Any]:
        """Update an item. Recomputes total_cents if quantity or unit_cost change.

        Args:
            company_id: The owning company ID.
            project_id: The parent project ID.
            work_item_id: The parent work item ID.
            item_id: The item ID to update.
            data: Fields to update (only non-None values applied).
            user_id: Clerk user ID of the updating user.

        Returns:
            The updated item dict.

        Raises:
            ItemNotFoundError: If the item does not exist.
        """
        actor = Actor.human(user_id)
        update_fields: dict[str, Any] = {}
        for field_name, value in data.items():
            if value is None:
                continue
            # Neo4j accepts ISO strings for datetime properties via `+=`
            if field_name == "price_fetched_at" and hasattr(value, "isoformat"):
                update_fields[field_name] = value.isoformat()
            else:
                update_fields[field_name] = value
        update_fields.update(self._provenance_update(actor))

        recompute = "quantity" in update_fields or "unit_cost_cents" in update_fields

        if recompute:
            result = self._write_tx_single(
                """
                MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
                      -[:HAS_WORK_ITEM]->(wi:WorkItem {id: $work_item_id})
                      -[:HAS_ITEM]->(item:Item {id: $item_id})
                SET item += $props
                WITH item, wi,
                     round(item.quantity * item.unit_cost_cents) AS new_total
                SET item.total_cents = new_total
                RETURN item {.*, work_item_id: wi.id} AS item
                """,
                {
                    "company_id": company_id,
                    "project_id": project_id,
                    "work_item_id": work_item_id,
                    "item_id": item_id,
                    "props": update_fields,
                },
            )
        else:
            result = self._write_tx_single(
                """
                MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
                      -[:HAS_WORK_ITEM]->(wi:WorkItem {id: $work_item_id})
                      -[:HAS_ITEM]->(item:Item {id: $item_id})
                SET item += $props
                RETURN item {.*, work_item_id: wi.id} AS item
                """,
                {
                    "company_id": company_id,
                    "project_id": project_id,
                    "work_item_id": work_item_id,
                    "item_id": item_id,
                    "props": update_fields,
                },
            )
        if result is None:
            raise ItemNotFoundError(item_id)
        self._emit_audit(
            event_type="entity.updated",
            entity_id=item_id,
            entity_type="Item",
            company_id=company_id,
            actor=actor,
            summary=f"Updated item {item_id}",
        )
        return result["item"]

    def delete(
        self,
        company_id: str,
        project_id: str,
        work_item_id: str,
        item_id: str,
    ) -> None:
        """Delete an item (hard delete — detail row, not top-level entity).

        Args:
            company_id: The owning company ID.
            project_id: The parent project ID.
            work_item_id: The parent work item ID.
            item_id: The item ID to delete.

        Raises:
            ItemNotFoundError: If the item does not exist.
        """
        result = self._write_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
                  -[:HAS_WORK_ITEM]->(wi:WorkItem {id: $work_item_id})
                  -[:HAS_ITEM]->(item:Item {id: $item_id})
            DETACH DELETE item
            RETURN wi.id AS work_item_id
            """,
            {
                "company_id": company_id,
                "project_id": project_id,
                "work_item_id": work_item_id,
                "item_id": item_id,
            },
        )
        if result is None:
            raise ItemNotFoundError(item_id)
