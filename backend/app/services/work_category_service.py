"""WorkCategory CRUD service (Neo4j-backed).

WorkCategories form a hierarchical taxonomy for classifying WorkItems.
Companies can customise their own category tree, optionally linking categories
to regulatory Activity nodes in the knowledge graph.
"""

from datetime import datetime, timezone
from typing import Any

from app.exceptions import CompanyNotFoundError
from app.models.actor import Actor
from app.services.base_service import BaseService


class WorkCategoryNotFoundError(Exception):
    """Raised when a work category cannot be found."""

    def __init__(self, category_id: str) -> None:
        self.category_id = category_id
        super().__init__(f"Work category not found: {category_id}")


class WorkCategoryService(BaseService):
    """Manages WorkCategory nodes in the Neo4j graph.

    Categories connect to companies via (Company)-[:HAS_WORK_CATEGORY]->(WorkCategory).
    Hierarchical relationships use (WorkCategory)-[:PARENT_CATEGORY]->(WorkCategory).
    Regulatory links use (WorkCategory)-[:LINKS_TO_ACTIVITY]->(Activity).
    """

    def create(
        self,
        company_id: str,
        data: dict[str, Any],
        user_id: str,
    ) -> dict[str, Any]:
        """Create a new work category for a company.

        Args:
            company_id: The owning company ID.
            data: Category fields — name, description, level, parent_id (optional).
            user_id: Clerk user ID of the creating user.

        Returns:
            The created work category dict.

        Raises:
            CompanyNotFoundError: If the company does not exist.
        """
        actor = Actor.human(user_id)
        cat_id = self._generate_id("wcat")
        parent_id = data.get("parent_id")

        props: dict[str, Any] = {
            "id": cat_id,
            "name": data.get("name", ""),
            "description": data.get("description"),
            "level": data.get("level", 1),
            "deleted": False,
            **self._provenance_create(actor),
        }

        if parent_id:
            result = self._write_tx_single(
                """
                MATCH (c:Company {id: $company_id})
                MATCH (parent:WorkCategory {id: $parent_id})
                CREATE (cat:WorkCategory $props)
                CREATE (c)-[:HAS_WORK_CATEGORY]->(cat)
                CREATE (cat)-[:PARENT_CATEGORY]->(parent)
                RETURN cat {.*, company_id: c.id, parent_id: parent.id} AS category
                """,
                {"company_id": company_id, "props": props, "parent_id": parent_id},
            )
        else:
            result = self._write_tx_single(
                """
                MATCH (c:Company {id: $company_id})
                CREATE (cat:WorkCategory $props)
                CREATE (c)-[:HAS_WORK_CATEGORY]->(cat)
                RETURN cat {.*, company_id: c.id} AS category
                """,
                {"company_id": company_id, "props": props},
            )

        if result is None:
            raise CompanyNotFoundError(company_id)
        self._emit_audit(
            event_type="entity.created",
            entity_id=cat_id,
            entity_type="WorkCategory",
            company_id=company_id,
            actor=actor,
            summary=f"Created work category '{data.get('name', '')}'",
        )
        return result["category"]

    def get(self, company_id: str, category_id: str) -> dict[str, Any]:
        """Fetch a single work category.

        Args:
            company_id: The owning company ID.
            category_id: The category ID to fetch.

        Returns:
            The category dict.

        Raises:
            WorkCategoryNotFoundError: If the category does not exist or is soft-deleted.
        """
        result = self._read_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:HAS_WORK_CATEGORY]
                  ->(cat:WorkCategory {id: $category_id})
            WHERE cat.deleted = false
            OPTIONAL MATCH (cat)-[:PARENT_CATEGORY]->(parent:WorkCategory)
            OPTIONAL MATCH (cat)-[:LINKS_TO_ACTIVITY]->(act)
            RETURN cat {
                .*,
                company_id: c.id,
                parent_id: parent.id,
                activity_id: act.id
            } AS category
            """,
            {"company_id": company_id, "category_id": category_id},
        )
        if result is None:
            raise WorkCategoryNotFoundError(category_id)
        return result["category"]

    def list_by_company(
        self,
        company_id: str,
        limit: int = 100,
        offset: int = 0,
    ) -> dict[str, Any]:
        """List all work categories for a company (flat list).

        Args:
            company_id: The owning company ID.
            limit: Maximum number of categories to return.
            offset: Number of categories to skip.

        Returns:
            A dict with 'categories' list and 'total' count.
        """
        params: dict[str, Any] = {
            "company_id": company_id,
            "limit": limit,
            "offset": offset,
        }

        count_result = self._read_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:HAS_WORK_CATEGORY]->(cat:WorkCategory)
            WHERE cat.deleted = false
            RETURN count(cat) AS total
            """,
            params,
        )
        total = count_result["total"] if count_result else 0

        results = self._read_tx(
            """
            MATCH (c:Company {id: $company_id})-[:HAS_WORK_CATEGORY]->(cat:WorkCategory)
            WHERE cat.deleted = false
            OPTIONAL MATCH (cat)-[:PARENT_CATEGORY]->(parent:WorkCategory)
            RETURN cat {.*, company_id: c.id, parent_id: parent.id} AS category
            ORDER BY cat.level ASC, cat.name ASC
            SKIP $offset LIMIT $limit
            """,
            params,
        )

        return {"categories": [r["category"] for r in results], "total": total}

    def get_tree(self, company_id: str) -> list[dict[str, Any]]:
        """Return the full category tree for a company as a nested structure.

        Fetches all non-deleted categories and assembles them into a tree
        by following PARENT_CATEGORY relationships. Root nodes have no parent.

        Args:
            company_id: The owning company ID.

        Returns:
            List of root-level category dicts, each with a 'children' list.
        """
        results = self._read_tx(
            """
            MATCH (c:Company {id: $company_id})-[:HAS_WORK_CATEGORY]->(cat:WorkCategory)
            WHERE cat.deleted = false
            OPTIONAL MATCH (cat)-[:PARENT_CATEGORY]->(parent:WorkCategory)
            RETURN cat {.*, company_id: c.id, parent_id: parent.id} AS category
            ORDER BY cat.level ASC, cat.name ASC
            """,
            {"company_id": company_id},
        )

        categories = [r["category"] for r in results]

        # Build tree in Python — more efficient than recursive Cypher for
        # shallow hierarchies (typically 2-3 levels).
        cat_map = {cat["id"]: {**cat, "children": []} for cat in categories}
        roots: list[dict[str, Any]] = []

        for cat in cat_map.values():
            parent_id = cat.get("parent_id")
            if parent_id and parent_id in cat_map:
                cat_map[parent_id]["children"].append(cat)
            else:
                roots.append(cat)

        return roots

    def update(
        self,
        company_id: str,
        category_id: str,
        data: dict[str, Any],
        user_id: str,
    ) -> dict[str, Any]:
        """Update fields on an existing work category.

        Args:
            company_id: The owning company ID.
            category_id: The category ID to update.
            data: Fields to update (name, description, level).
            user_id: Clerk user ID of the updating user.

        Returns:
            The updated category dict.

        Raises:
            WorkCategoryNotFoundError: If the category does not exist or is soft-deleted.
        """
        actor = Actor.human(user_id)
        update_fields = {k: v for k, v in data.items() if v is not None and k not in ("parent_id",)}
        update_fields.update(self._provenance_update(actor))

        result = self._write_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:HAS_WORK_CATEGORY]
                  ->(cat:WorkCategory {id: $category_id})
            WHERE cat.deleted = false
            SET cat += $props
            OPTIONAL MATCH (cat)-[:PARENT_CATEGORY]->(parent:WorkCategory)
            RETURN cat {.*, company_id: c.id, parent_id: parent.id} AS category
            """,
            {
                "company_id": company_id,
                "category_id": category_id,
                "props": update_fields,
            },
        )
        if result is None:
            raise WorkCategoryNotFoundError(category_id)
        self._emit_audit(
            event_type="entity.updated",
            entity_id=category_id,
            entity_type="WorkCategory",
            company_id=company_id,
            actor=actor,
            summary=f"Updated work category {category_id}",
        )
        return result["category"]

    def link_activity(
        self,
        company_id: str,
        category_id: str,
        activity_id: str,
        user_id: str,
    ) -> dict[str, Any]:
        """Link a work category to a regulatory Activity node.

        Creates a (WorkCategory)-[:LINKS_TO_ACTIVITY]->(Activity) relationship.
        Uses MERGE so duplicate links are idempotent.

        Args:
            company_id: The owning company ID.
            category_id: The category ID.
            activity_id: The Activity node ID in the knowledge graph.
            user_id: Clerk user ID performing the action.

        Returns:
            The updated category dict.

        Raises:
            WorkCategoryNotFoundError: If the category does not exist.
        """
        actor = Actor.human(user_id)
        result = self._write_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:HAS_WORK_CATEGORY]
                  ->(cat:WorkCategory {id: $category_id})
            WHERE cat.deleted = false
            MATCH (act:Activity {id: $activity_id})
            MERGE (cat)-[:LINKS_TO_ACTIVITY]->(act)
            SET cat += $provenance
            RETURN cat {.*, company_id: c.id, activity_id: act.id} AS category
            """,
            {
                "company_id": company_id,
                "category_id": category_id,
                "activity_id": activity_id,
                "provenance": self._provenance_update(actor),
            },
        )
        if result is None:
            raise WorkCategoryNotFoundError(category_id)
        self._emit_audit(
            event_type="relationship.added",
            entity_id=category_id,
            entity_type="WorkCategory",
            company_id=company_id,
            actor=actor,
            summary=f"Linked category {category_id} to activity {activity_id}",
            related_entity_ids=[activity_id],
        )
        return result["category"]

    def archive(self, company_id: str, category_id: str, user_id: str) -> None:
        """Soft-delete a work category.

        Does NOT cascade to child categories.

        Args:
            company_id: The owning company ID.
            category_id: The category ID to archive.
            user_id: Clerk user ID of the deleting user.

        Raises:
            WorkCategoryNotFoundError: If the category does not exist.
        """
        result = self._write_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:HAS_WORK_CATEGORY]
                  ->(cat:WorkCategory {id: $category_id})
            WHERE cat.deleted = false
            SET cat.deleted = true, cat.updated_at = $now
            RETURN cat.id AS id
            """,
            {
                "company_id": company_id,
                "category_id": category_id,
                "now": datetime.now(timezone.utc).isoformat(),
            },
        )
        if result is None:
            raise WorkCategoryNotFoundError(category_id)
        self._emit_audit(
            event_type="entity.archived",
            entity_id=category_id,
            entity_type="WorkCategory",
            company_id=company_id,
            actor=Actor.human(user_id),
            summary=f"Archived work category {category_id}",
        )
