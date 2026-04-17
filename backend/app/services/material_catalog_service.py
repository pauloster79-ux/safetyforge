"""MaterialCatalogEntry CRUD service (Neo4j-backed).

MaterialCatalogEntries are company-scoped price observations used by the
Layer 3 source cascade during estimating.

Graph model: (Company)-[:HAS_CATALOG_ENTRY]->(MaterialCatalogEntry)
"""

from datetime import datetime, timedelta, timezone
from typing import Any

from app.exceptions import (
    CompanyNotFoundError,
    MaterialCatalogEntryNotFoundError,
)
from app.models.actor import Actor
from app.services.base_service import BaseService


class MaterialCatalogService(BaseService):
    """Manages MaterialCatalogEntry nodes at the company level."""

    def create(
        self, company_id: str, data: dict[str, Any], user_id: str
    ) -> dict[str, Any]:
        """Create a material catalog entry.

        Args:
            company_id: The owning company ID.
            data: Entry fields.
            user_id: Clerk user ID.

        Returns:
            The created entry dict.

        Raises:
            CompanyNotFoundError: If the company does not exist.
        """
        actor = Actor.human(user_id)
        mce_id = self._generate_id("mce")
        now_iso = datetime.now(timezone.utc).isoformat()

        props: dict[str, Any] = {
            "id": mce_id,
            "description": data["description"],
            "product_code": data.get("product_code"),
            "unit": data["unit"],
            "unit_cost_cents": data["unit_cost_cents"],
            "supplier_name": data.get("supplier_name"),
            "source_url": data.get("source_url"),
            "location": data.get("location"),
            "fetched_at": now_iso,
            "last_verified_at": None,
            **self._provenance_create(actor),
        }

        result = self._write_tx_single(
            """
            MATCH (c:Company {id: $company_id})
            CREATE (mce:MaterialCatalogEntry $props)
            CREATE (c)-[:HAS_CATALOG_ENTRY]->(mce)
            RETURN mce {.*, company_id: c.id} AS entry
            """,
            {"company_id": company_id, "props": props},
        )
        if result is None:
            raise CompanyNotFoundError(company_id)

        self._emit_audit(
            event_type="entity.created",
            entity_id=mce_id,
            entity_type="MaterialCatalogEntry",
            company_id=company_id,
            actor=actor,
            summary=f"Created catalog entry: {data['description'][:80]}",
        )
        return result["entry"]

    def get(
        self, company_id: str, entry_id: str
    ) -> dict[str, Any]:
        """Fetch a single catalog entry.

        Args:
            company_id: The owning company ID.
            entry_id: The entry ID.

        Returns:
            The entry dict.

        Raises:
            MaterialCatalogEntryNotFoundError: If not found.
        """
        result = self._read_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:HAS_CATALOG_ENTRY]->(mce:MaterialCatalogEntry {id: $entry_id})
            RETURN mce {.*, company_id: c.id} AS entry
            """,
            {"company_id": company_id, "entry_id": entry_id},
        )
        if result is None:
            raise MaterialCatalogEntryNotFoundError(entry_id)
        return result["entry"]

    def list_by_company(
        self,
        company_id: str,
        location: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> dict[str, Any]:
        """List catalog entries for a company with optional location filter.

        Args:
            company_id: The owning company ID.
            location: Optional location filter (exact match).
            limit: Page size.
            offset: Page offset.

        Returns:
            Dict with 'entries' list and 'total' count.
        """
        where_clauses: list[str] = []
        params: dict[str, Any] = {
            "company_id": company_id,
            "limit": limit,
            "offset": offset,
        }
        if location is not None:
            where_clauses.append("mce.location = $location")
            params["location"] = location

        where_str = (" WHERE " + " AND ".join(where_clauses)) if where_clauses else ""

        count_result = self._read_tx_single(
            f"""
            MATCH (c:Company {{id: $company_id}})-[:HAS_CATALOG_ENTRY]->(mce:MaterialCatalogEntry)
            {where_str}
            RETURN count(mce) AS total
            """,
            params,
        )
        total = count_result["total"] if count_result else 0

        results = self._read_tx(
            f"""
            MATCH (c:Company {{id: $company_id}})-[:HAS_CATALOG_ENTRY]->(mce:MaterialCatalogEntry)
            {where_str}
            RETURN mce {{.*, company_id: c.id}} AS entry
            ORDER BY mce.fetched_at DESC
            SKIP $offset LIMIT $limit
            """,
            params,
        )
        return {
            "entries": [r["entry"] for r in results],
            "total": total,
        }

    def delete(self, company_id: str, entry_id: str) -> None:
        """Delete a catalog entry.

        Args:
            company_id: The owning company ID.
            entry_id: The entry ID.

        Raises:
            MaterialCatalogEntryNotFoundError: If not found.
        """
        result = self._write_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:HAS_CATALOG_ENTRY]->(mce:MaterialCatalogEntry {id: $entry_id})
            DETACH DELETE mce
            RETURN c.id AS company_id
            """,
            {"company_id": company_id, "entry_id": entry_id},
        )
        if result is None:
            raise MaterialCatalogEntryNotFoundError(entry_id)

    def find_by_description(
        self,
        company_id: str,
        description: str,
        location: str | None = None,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        """Find catalog entries matching a description (case-insensitive substring).

        Args:
            company_id: The owning company ID.
            description: Free text describing the material.
            location: Optional location filter.
            limit: Max rows to return.

        Returns:
            A list of entry dicts sorted by fetched_at DESC.
        """
        params: dict[str, Any] = {
            "company_id": company_id,
            "needle": description.lower(),
            "limit": limit,
        }
        where_extra = ""
        if location is not None:
            where_extra = " AND mce.location = $location"
            params["location"] = location

        results = self._read_tx(
            f"""
            MATCH (c:Company {{id: $company_id}})-[:HAS_CATALOG_ENTRY]->(mce:MaterialCatalogEntry)
            WHERE toLower(mce.description) CONTAINS $needle{where_extra}
            RETURN mce {{.*, company_id: c.id}} AS entry
            ORDER BY mce.fetched_at DESC
            LIMIT $limit
            """,
            params,
        )
        return [r["entry"] for r in results]

    def is_stale(
        self, entry: dict[str, Any], threshold_days: int = 60
    ) -> bool:
        """Return True if the entry's fetched_at is older than threshold_days.

        Args:
            entry: A catalog entry dict (or node with fetched_at property).
            threshold_days: Age threshold in days.

        Returns:
            True when the entry is stale and should be re-verified.
        """
        fetched_at_raw = entry.get("fetched_at")
        if fetched_at_raw is None:
            return True

        if isinstance(fetched_at_raw, datetime):
            fetched_at = fetched_at_raw
        else:
            # Neo4j returns ISO strings for datetime properties
            try:
                fetched_at = datetime.fromisoformat(
                    fetched_at_raw.replace("Z", "+00:00")
                    if isinstance(fetched_at_raw, str)
                    else fetched_at_raw
                )
            except (TypeError, ValueError):
                return True

        if fetched_at.tzinfo is None:
            fetched_at = fetched_at.replace(tzinfo=timezone.utc)

        age = datetime.now(timezone.utc) - fetched_at
        return age > timedelta(days=threshold_days)

    def find_from_history(
        self,
        company_id: str,
        description: str,
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        """Search the contractor's past Item nodes for matching descriptions.

        Looks at Items on WorkItems belonging to completed projects. Returns the
        most recent N matches.

        Args:
            company_id: The owning company ID.
            description: Free text describing the material.
            limit: Max rows to return (default 5).

        Returns:
            A list of dicts with project_name, supplier, unit_cost_cents, date.
        """
        results = self._read_tx(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project)
                  -[:HAS_WORK_ITEM]->(wi:WorkItem)-[:HAS_ITEM]->(item:Item)
            WHERE p.state = 'completed'
              AND toLower(item.description) CONTAINS $needle
            RETURN
                p.name AS project_name,
                coalesce(item.supplier, item.product, '') AS supplier,
                item.unit_cost_cents AS unit_cost_cents,
                item.created_at AS date
            ORDER BY item.created_at DESC
            LIMIT $limit
            """,
            {
                "company_id": company_id,
                "needle": description.lower(),
                "limit": limit,
            },
        )
        return [
            {
                "project_name": r["project_name"],
                "supplier": r["supplier"] or None,
                "unit_cost_cents": r["unit_cost_cents"],
                "date": r["date"],
            }
            for r in results
        ]
