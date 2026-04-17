"""ProductivityRate CRUD service (Neo4j-backed).

ProductivityRates capture how fast a crew produces output for a specific
type of work — company-specific and condition-specific.
Graph model: (Company)-[:HAS_PRODUCTIVITY]->(ProductivityRate)
"""

from typing import Any

from app.exceptions import ProductivityRateNotFoundError
from app.models.actor import Actor
from app.services.base_service import BaseService


class ProductivityRateService(BaseService):
    """Manages ProductivityRate nodes at the company level."""

    def create(
        self, company_id: str, data: dict[str, Any], user_id: str
    ) -> dict[str, Any]:
        """Create a productivity rate.

        Args:
            company_id: The owning company ID.
            data: Rate fields.
            user_id: Clerk user ID.

        Returns:
            The created rate dict.
        """
        actor = Actor.human(user_id)
        pr_id = self._generate_id("pr")

        props: dict[str, Any] = {
            "id": pr_id,
            "description": data["description"],
            "rate": data["rate"],
            "rate_unit": data["rate_unit"],
            "time_unit": data["time_unit"],
            "crew_composition": data.get("crew_composition", ""),
            "conditions": data.get("conditions", ""),
            "source": data.get("source", "manual_entry"),
            "sample_size": None,
            "std_deviation": None,
            "includes_non_productive": data.get("includes_non_productive", False),
            "last_derived_at": None,
            "active": True,
            **self._provenance_create(actor),
        }

        result = self._write_tx_single(
            """
            MATCH (c:Company {id: $company_id})
            CREATE (pr:ProductivityRate $props)
            CREATE (c)-[:HAS_PRODUCTIVITY]->(pr)
            RETURN pr {.*, company_id: c.id} AS rate
            """,
            {"company_id": company_id, "props": props},
        )
        self._emit_audit(
            event_type="entity.created",
            entity_id=pr_id,
            entity_type="ProductivityRate",
            company_id=company_id,
            actor=actor,
            summary=f"Created productivity rate '{data['description']}'",
        )
        return result["rate"]

    def get(self, company_id: str, rate_id: str) -> dict[str, Any]:
        """Fetch a single productivity rate.

        Args:
            company_id: The owning company ID.
            rate_id: The rate ID.

        Returns:
            The rate dict.

        Raises:
            ProductivityRateNotFoundError: If not found.
        """
        result = self._read_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:HAS_PRODUCTIVITY]->(pr:ProductivityRate {id: $rate_id})
            RETURN pr {.*, company_id: c.id} AS rate
            """,
            {"company_id": company_id, "rate_id": rate_id},
        )
        if result is None:
            raise ProductivityRateNotFoundError(rate_id)
        return result["rate"]

    def list_rates(
        self,
        company_id: str,
        active_only: bool = True,
        limit: int = 50,
        offset: int = 0,
    ) -> dict[str, Any]:
        """List productivity rates for a company.

        Args:
            company_id: The owning company ID.
            active_only: Whether to filter to active rates only.
            limit: Maximum number of rates to return.
            offset: Number of rates to skip.

        Returns:
            A dict with 'rates' list and 'total' count.
        """
        where_clauses: list[str] = []
        params: dict[str, Any] = {
            "company_id": company_id,
            "limit": limit,
            "offset": offset,
        }

        if active_only:
            where_clauses.append("pr.active = true")

        where_str = (" WHERE " + " AND ".join(where_clauses)) if where_clauses else ""

        count_result = self._read_tx_single(
            f"""
            MATCH (c:Company {{id: $company_id}})-[:HAS_PRODUCTIVITY]->(pr:ProductivityRate)
            {where_str}
            RETURN count(pr) AS total
            """,
            params,
        )
        total = count_result["total"] if count_result else 0

        results = self._read_tx(
            f"""
            MATCH (c:Company {{id: $company_id}})-[:HAS_PRODUCTIVITY]->(pr:ProductivityRate)
            {where_str}
            RETURN pr {{.*, company_id: c.id}} AS rate
            ORDER BY pr.description ASC
            SKIP $offset LIMIT $limit
            """,
            params,
        )

        return {"rates": [r["rate"] for r in results], "total": total}

    def update(
        self, company_id: str, rate_id: str, data: dict[str, Any], user_id: str
    ) -> dict[str, Any]:
        """Update a productivity rate.

        Args:
            company_id: The owning company ID.
            rate_id: The rate ID.
            data: Fields to update.
            user_id: Clerk user ID.

        Returns:
            The updated rate dict.

        Raises:
            ProductivityRateNotFoundError: If not found.
        """
        actor = Actor.human(user_id)
        update_fields = {k: v for k, v in data.items() if v is not None}
        update_fields.update(self._provenance_update(actor))

        result = self._write_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:HAS_PRODUCTIVITY]->(pr:ProductivityRate {id: $rate_id})
            SET pr += $props
            RETURN pr {.*, company_id: c.id} AS rate
            """,
            {
                "company_id": company_id,
                "rate_id": rate_id,
                "props": update_fields,
            },
        )
        if result is None:
            raise ProductivityRateNotFoundError(rate_id)
        self._emit_audit(
            event_type="entity.updated",
            entity_id=rate_id,
            entity_type="ProductivityRate",
            company_id=company_id,
            actor=actor,
            summary=f"Updated productivity rate {rate_id}",
        )
        return result["rate"]

    def deactivate(
        self, company_id: str, rate_id: str, user_id: str
    ) -> dict[str, Any]:
        """Deactivate a productivity rate.

        Args:
            company_id: The owning company ID.
            rate_id: The rate ID.
            user_id: Clerk user ID.

        Returns:
            The deactivated rate dict.

        Raises:
            ProductivityRateNotFoundError: If not found.
        """
        actor = Actor.human(user_id)
        result = self._write_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:HAS_PRODUCTIVITY]->(pr:ProductivityRate {id: $rate_id})
            SET pr.active = false, pr += $provenance
            RETURN pr {.*, company_id: c.id} AS rate
            """,
            {
                "company_id": company_id,
                "rate_id": rate_id,
                "provenance": self._provenance_update(actor),
            },
        )
        if result is None:
            raise ProductivityRateNotFoundError(rate_id)
        self._emit_audit(
            event_type="entity.archived",
            entity_id=rate_id,
            entity_type="ProductivityRate",
            company_id=company_id,
            actor=actor,
            summary=f"Deactivated productivity rate {rate_id}",
        )
        return result["rate"]
