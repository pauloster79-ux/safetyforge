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

    Two-tier model (see docs/design/canonical-work-categories.md):

    * **Canonical** categories (:WorkCategory:Canonical) — shared system-maintained
      trees per jurisdiction, loaded from YAML seeds. Contractors cannot create or
      modify these; they are the authoritative taxonomy (MasterFormat for US/CA,
      NRM 2 for UK/IE, NATSPEC for AU/NZ).

    * **Extension** categories (:WorkCategory:Extension) — company-scoped leaves
      under a Canonical parent. Contractors create these via ``add_extension`` for
      specialisations that don't warrant a canonical entry.

    Additionally, companies may alias canonical categories via ``add_alias`` — a
    display-name override that does not fork the tree.

    Hierarchical relationships use (WorkCategory)-[:PARENT_CATEGORY]->(WorkCategory)
    with Extensions always pointing at a Canonical parent.

    Regulatory links use (:WorkCategory:Canonical)-[:LINKS_TO_ACTIVITY]->(Activity)
    — attached to Canonical nodes only; Extensions inherit regulatory context by
    traversing through their canonical parent.
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

    # ------------------------------------------------------------------
    # Canonical category operations (two-tier model)
    # ------------------------------------------------------------------

    def list_canonical(
        self,
        jurisdiction_code: str,
        level: int | None = None,
        parent_code: str | None = None,
        search: str | None = None,
        limit: int = 200,
    ) -> list[dict[str, Any]]:
        """List canonical WorkCategories for a jurisdiction.

        Args:
            jurisdiction_code: ISO-style code ('us', 'uk', 'ca', 'ie', 'au', 'nz').
            level: Optional filter to a specific hierarchy level (1, 2, or 3).
            parent_code: Optional filter to children of a given parent code.
            search: Optional case-insensitive substring match on name or code.
            limit: Maximum rows to return (default 200).

        Returns:
            List of canonical category dicts ordered by code.
        """
        where_clauses = ["c.jurisdiction_code = $jurisdiction_code"]
        params: dict[str, Any] = {
            "jurisdiction_code": jurisdiction_code,
            "limit": limit,
        }
        if level is not None:
            where_clauses.append("c.level = $level")
            params["level"] = level
        if search:
            where_clauses.append(
                "(toLower(c.name) CONTAINS toLower($search) "
                "OR toLower(c.code) CONTAINS toLower($search))"
            )
            params["search"] = search

        where_str = " AND ".join(where_clauses)

        if parent_code is not None:
            params["parent_code"] = parent_code
            query = f"""
            MATCH (c:WorkCategory:Canonical)-[:PARENT_CATEGORY]->(parent:WorkCategory:Canonical)
            WHERE {where_str}
              AND parent.code = $parent_code
              AND parent.jurisdiction_code = $jurisdiction_code
            RETURN c {{.*, parent_code: parent.code}} AS category
            ORDER BY c.code
            LIMIT $limit
            """
        else:
            query = f"""
            MATCH (c:WorkCategory:Canonical)
            WHERE {where_str}
            OPTIONAL MATCH (c)-[:PARENT_CATEGORY]->(parent:WorkCategory:Canonical)
            RETURN c {{.*, parent_code: parent.code}} AS category
            ORDER BY c.code
            LIMIT $limit
            """

        results = self._read_tx(query, params)
        return [r["category"] for r in results]

    def list_for_company(
        self,
        company_id: str,
        jurisdiction_code: str,
        search: str | None = None,
        limit: int = 200,
    ) -> dict[str, Any]:
        """List the effective category set for a company.

        Merges:
        * All Canonical categories for the jurisdiction
        * Company Extensions (leaves under canonical parents)
        * Company aliases (display-name overrides for canonical nodes)

        Args:
            company_id: The owning company ID.
            jurisdiction_code: Jurisdiction to scope canonical tree.
            search: Optional case-insensitive substring filter.
            limit: Maximum rows to return.

        Returns:
            Dict with ``canonical``, ``extensions``, and ``aliases`` keys.
        """
        params: dict[str, Any] = {
            "company_id": company_id,
            "jurisdiction_code": jurisdiction_code,
            "limit": limit,
        }
        search_filter = ""
        if search:
            search_filter = (
                " AND (toLower(c.name) CONTAINS toLower($search) "
                "OR toLower(c.code) CONTAINS toLower($search))"
            )
            params["search"] = search

        canonical = self._read_tx(
            f"""
            MATCH (c:WorkCategory:Canonical)
            WHERE c.jurisdiction_code = $jurisdiction_code{search_filter}
            OPTIONAL MATCH (c)-[:PARENT_CATEGORY]->(parent:WorkCategory:Canonical)
            RETURN c {{.*, parent_code: parent.code}} AS category
            ORDER BY c.code
            LIMIT $limit
            """,
            params,
        )

        extensions = self._read_tx(
            """
            MATCH (co:Company {id: $company_id})-[:HAS_EXTENSION]->(ext:WorkCategory:Extension)
            OPTIONAL MATCH (ext)-[:PARENT_CATEGORY]->(parent:WorkCategory:Canonical)
            WHERE parent.jurisdiction_code = $jurisdiction_code
            RETURN ext {.*, parent_code: parent.code, parent_id: parent.id} AS extension
            ORDER BY parent.code, ext.name
            """,
            params,
        )

        aliases = self._read_tx(
            """
            MATCH (co:Company {id: $company_id})-[a:HAS_ALIAS]->(c:WorkCategory:Canonical)
            WHERE c.jurisdiction_code = $jurisdiction_code
            RETURN {
                canonical_id: c.id,
                canonical_code: c.code,
                canonical_name: c.name,
                display_name: a.display_name,
                added_at: a.added_at
            } AS alias
            """,
            params,
        )

        return {
            "canonical": [r["category"] for r in canonical],
            "extensions": [r["extension"] for r in extensions],
            "aliases": [r["alias"] for r in aliases],
        }

    def add_alias(
        self,
        company_id: str,
        canonical_id: str,
        display_name: str,
        user_id: str,
    ) -> dict[str, Any]:
        """Add a display-name alias for a canonical category.

        The company's contractors see ``display_name`` throughout the UI in place
        of the canonical name. The alias is a relationship property, not a node
        copy — the canonical tree is not forked.

        Args:
            company_id: The owning company ID.
            canonical_id: The canonical category ID to alias.
            display_name: The contractor-preferred display name.
            user_id: Clerk user ID performing the action.

        Returns:
            Dict with alias metadata.

        Raises:
            ValueError: If the target is not a Canonical category or the
                company does not exist.
        """
        actor = Actor.human(user_id)
        now = datetime.now(timezone.utc).isoformat()
        result = self._write_tx_single(
            """
            MATCH (co:Company {id: $company_id})
            MATCH (c:WorkCategory:Canonical {id: $canonical_id})
            MERGE (co)-[a:HAS_ALIAS]->(c)
            SET a.display_name = $display_name,
                a.added_at = $now,
                a.added_by = $actor_id
            RETURN {
                canonical_id: c.id,
                canonical_code: c.code,
                canonical_name: c.name,
                display_name: a.display_name,
                added_at: a.added_at
            } AS alias
            """,
            {
                "company_id": company_id,
                "canonical_id": canonical_id,
                "display_name": display_name,
                "now": now,
                "actor_id": actor.id,
            },
        )
        if result is None:
            raise ValueError(
                f"Cannot alias: company '{company_id}' or canonical category "
                f"'{canonical_id}' not found"
            )
        self._emit_audit(
            event_type="relationship.added",
            entity_id=canonical_id,
            entity_type="WorkCategory",
            company_id=company_id,
            actor=actor,
            summary=f"Aliased canonical category {canonical_id} to '{display_name}'",
        )
        return result["alias"]

    def add_extension(
        self,
        company_id: str,
        parent_canonical_id: str,
        name: str,
        description: str | None,
        user_id: str,
    ) -> dict[str, Any]:
        """Add a company Extension under a Canonical parent.

        Extensions are company-scoped leaf categories that do not exist in the
        canonical tree. Guarded so the parent MUST be a Canonical node — you
        cannot extend an Extension (keeping the tree shallow and predictable).

        Args:
            company_id: The owning company ID.
            parent_canonical_id: Parent canonical node ID.
            name: Extension display name.
            description: Optional description.
            user_id: Clerk user ID performing the action.

        Returns:
            The created extension dict.

        Raises:
            ValueError: If the parent is not Canonical or does not exist.
        """
        actor = Actor.human(user_id)
        ext_id = self._generate_id("wcat")
        props = {
            "id": ext_id,
            "name": name,
            "description": description,
            "deleted": False,
            **self._provenance_create(actor),
        }

        result = self._write_tx_single(
            """
            MATCH (co:Company {id: $company_id})
            MATCH (parent:WorkCategory:Canonical {id: $parent_id})
            CREATE (ext:WorkCategory:Extension $props)
            SET ext.level = parent.level + 1
            CREATE (co)-[:HAS_EXTENSION]->(ext)
            CREATE (ext)-[:PARENT_CATEGORY]->(parent)
            RETURN ext {
                .*,
                company_id: co.id,
                parent_code: parent.code,
                parent_id: parent.id
            } AS extension
            """,
            {
                "company_id": company_id,
                "parent_id": parent_canonical_id,
                "props": props,
            },
        )
        if result is None:
            raise ValueError(
                f"Cannot extend: company '{company_id}' not found or parent "
                f"'{parent_canonical_id}' is not a Canonical category"
            )
        self._emit_audit(
            event_type="entity.created",
            entity_id=ext_id,
            entity_type="WorkCategory",
            company_id=company_id,
            actor=actor,
            summary=f"Created extension category '{name}' under canonical {parent_canonical_id}",
        )
        return result["extension"]

    def resolve_for_work_item(
        self,
        company_id: str,
        category_id: str,
    ) -> dict[str, Any] | None:
        """Resolve a category by ID for use on a WorkItem (CATEGORISED_AS target).

        Accepts either a Canonical ID or a company-scoped Extension ID.
        Validates that if Extension, it belongs to this company.

        Args:
            company_id: The owning company ID for access-scope check.
            category_id: Canonical or Extension category ID.

        Returns:
            Dict with id, name, code, jurisdiction, level, and is_canonical flag,
            or None if not found / not accessible.
        """
        result = self._read_tx_single(
            """
            MATCH (cat:WorkCategory {id: $category_id})
            WHERE cat:Canonical
               OR EXISTS {
                   MATCH (co:Company {id: $company_id})-[:HAS_EXTENSION]->(cat)
               }
            OPTIONAL MATCH (cat)-[:PARENT_CATEGORY]->(parent:WorkCategory:Canonical)
            RETURN cat {
                .*,
                is_canonical: cat:Canonical,
                parent_code: parent.code,
                parent_id: parent.id
            } AS category
            """,
            {"company_id": company_id, "category_id": category_id},
        )
        return result["category"] if result else None
