"""ResourceRate CRUD service (Neo4j-backed).

ResourceRates capture company-level rate knowledge for labour, materials,
and equipment — either manually entered or derived from completed job actuals.
Graph model: (Company)-[:HAS_RATE]->(ResourceRate)
"""

from datetime import datetime, timezone
from typing import Any

from app.exceptions import ResourceRateNotFoundError
from app.models.actor import Actor
from app.services.base_service import BaseService


class ResourceRateService(BaseService):
    """Manages ResourceRate nodes at the company level."""

    def create(
        self, company_id: str, data: dict[str, Any], user_id: str
    ) -> dict[str, Any]:
        """Create a resource rate.

        Args:
            company_id: The owning company ID.
            data: Rate fields.
            user_id: Clerk user ID.

        Returns:
            The created rate dict.
        """
        actor = Actor.human(user_id)
        rr_id = self._generate_id("rr")

        props: dict[str, Any] = {
            "id": rr_id,
            "resource_type": data["resource_type"],
            "description": data["description"],
            "rate_cents": data["rate_cents"],
            "unit": data["unit"],
            "source": data.get("source", "manual_entry"),
            "base_rate_cents": data.get("base_rate_cents"),
            "burden_percent": data.get("burden_percent"),
            "non_productive_percent": data.get("non_productive_percent"),
            "supplier_name": data.get("supplier_name", ""),
            "quote_valid_until": (
                data["quote_valid_until"].isoformat()
                if data.get("quote_valid_until")
                else None
            ),
            "sample_size": None,
            "std_deviation_cents": None,
            "last_derived_at": None,
            "active": True,
            **self._provenance_create(actor),
        }

        result = self._write_tx_single(
            """
            MATCH (c:Company {id: $company_id})
            CREATE (rr:ResourceRate $props)
            CREATE (c)-[:HAS_RATE]->(rr)
            RETURN rr {.*, company_id: c.id} AS rate
            """,
            {"company_id": company_id, "props": props},
        )
        self._emit_audit(
            event_type="entity.created",
            entity_id=rr_id,
            entity_type="ResourceRate",
            company_id=company_id,
            actor=actor,
            summary=f"Created resource rate '{data['description']}'",
        )
        return result["rate"]

    def get(self, company_id: str, rate_id: str) -> dict[str, Any]:
        """Fetch a single resource rate.

        Args:
            company_id: The owning company ID.
            rate_id: The rate ID.

        Returns:
            The rate dict.

        Raises:
            ResourceRateNotFoundError: If not found.
        """
        result = self._read_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:HAS_RATE]->(rr:ResourceRate {id: $rate_id})
            RETURN rr {.*, company_id: c.id} AS rate
            """,
            {"company_id": company_id, "rate_id": rate_id},
        )
        if result is None:
            raise ResourceRateNotFoundError(rate_id)
        return result["rate"]

    def list_rates(
        self,
        company_id: str,
        resource_type: str | None = None,
        active_only: bool = True,
        limit: int = 50,
        offset: int = 0,
    ) -> dict[str, Any]:
        """List resource rates for a company.

        Args:
            company_id: The owning company ID.
            resource_type: Optional filter (labour, material, equipment).
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
            where_clauses.append("rr.active = true")
        if resource_type:
            where_clauses.append("rr.resource_type = $resource_type")
            params["resource_type"] = resource_type

        where_str = (" WHERE " + " AND ".join(where_clauses)) if where_clauses else ""

        count_result = self._read_tx_single(
            f"""
            MATCH (c:Company {{id: $company_id}})-[:HAS_RATE]->(rr:ResourceRate)
            {where_str}
            RETURN count(rr) AS total
            """,
            params,
        )
        total = count_result["total"] if count_result else 0

        results = self._read_tx(
            f"""
            MATCH (c:Company {{id: $company_id}})-[:HAS_RATE]->(rr:ResourceRate)
            {where_str}
            RETURN rr {{.*, company_id: c.id}} AS rate
            ORDER BY rr.resource_type ASC, rr.description ASC
            SKIP $offset LIMIT $limit
            """,
            params,
        )

        return {"rates": [r["rate"] for r in results], "total": total}

    def update(
        self, company_id: str, rate_id: str, data: dict[str, Any], user_id: str
    ) -> dict[str, Any]:
        """Update a resource rate.

        Args:
            company_id: The owning company ID.
            rate_id: The rate ID.
            data: Fields to update.
            user_id: Clerk user ID.

        Returns:
            The updated rate dict.

        Raises:
            ResourceRateNotFoundError: If not found.
        """
        actor = Actor.human(user_id)
        update_fields = {k: v for k, v in data.items() if v is not None}

        # Serialize date fields
        if "quote_valid_until" in update_fields and update_fields["quote_valid_until"] is not None:
            update_fields["quote_valid_until"] = update_fields["quote_valid_until"].isoformat()

        update_fields.update(self._provenance_update(actor))

        result = self._write_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:HAS_RATE]->(rr:ResourceRate {id: $rate_id})
            SET rr += $props
            RETURN rr {.*, company_id: c.id} AS rate
            """,
            {
                "company_id": company_id,
                "rate_id": rate_id,
                "props": update_fields,
            },
        )
        if result is None:
            raise ResourceRateNotFoundError(rate_id)
        self._emit_audit(
            event_type="entity.updated",
            entity_id=rate_id,
            entity_type="ResourceRate",
            company_id=company_id,
            actor=actor,
            summary=f"Updated resource rate {rate_id}",
        )
        return result["rate"]

    def deactivate(
        self, company_id: str, rate_id: str, user_id: str
    ) -> dict[str, Any]:
        """Deactivate a resource rate (soft archive).

        Args:
            company_id: The owning company ID.
            rate_id: The rate ID.
            user_id: Clerk user ID.

        Returns:
            The deactivated rate dict.

        Raises:
            ResourceRateNotFoundError: If not found.
        """
        actor = Actor.human(user_id)
        result = self._write_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:HAS_RATE]->(rr:ResourceRate {id: $rate_id})
            SET rr.active = false, rr += $provenance
            RETURN rr {.*, company_id: c.id} AS rate
            """,
            {
                "company_id": company_id,
                "rate_id": rate_id,
                "provenance": self._provenance_update(actor),
            },
        )
        if result is None:
            raise ResourceRateNotFoundError(rate_id)
        self._emit_audit(
            event_type="entity.archived",
            entity_id=rate_id,
            entity_type="ResourceRate",
            company_id=company_id,
            actor=actor,
            summary=f"Deactivated resource rate {rate_id}",
        )
        return result["rate"]

    def derive_from_actuals(
        self,
        company_id: str,
        resource_type: str,
        description_filter: str | None = None,
        work_category_id: str | None = None,
    ) -> dict[str, Any]:
        """Derive a rate from completed job actuals.

        Queries Labour or Item nodes on completed projects to calculate
        statistical rate data.

        Args:
            company_id: Tenant scope.
            resource_type: Type of resource (labour, material, equipment).
            description_filter: Optional text filter on descriptions.
            work_category_id: Optional work category to filter by.

        Returns:
            Dict with derived rate statistics.
        """
        if resource_type == "labour":
            return self._derive_labour_rate(
                company_id, description_filter, work_category_id
            )
        return self._derive_item_rate(
            company_id, resource_type, description_filter, work_category_id
        )

    def _derive_labour_rate(
        self,
        company_id: str,
        description_filter: str | None,
        work_category_id: str | None,
    ) -> dict[str, Any]:
        """Derive labour rates from completed Labour nodes.

        Args:
            company_id: Tenant scope.
            description_filter: Optional text filter.
            work_category_id: Optional category filter.

        Returns:
            Dict with avg_rate_cents, sample_size, std_deviation_cents.
        """
        where_clauses = [
            "p.deleted = false",
            "wi.deleted = false",
            "p.state IN ['completed', 'closed']",
        ]
        params: dict[str, Any] = {"company_id": company_id}

        if description_filter:
            where_clauses.append("toLower(lab.task) CONTAINS toLower($desc)")
            params["desc"] = description_filter
        if work_category_id:
            where_clauses.append("cat.id = $wcat_id")
            params["wcat_id"] = work_category_id

        where_str = " AND ".join(where_clauses)

        result = self._read_tx_single(
            f"""
            MATCH (c:Company {{id: $company_id}})-[:OWNS_PROJECT]->(p:Project)
                  -[:HAS_WORK_ITEM]->(wi:WorkItem)-[:HAS_LABOUR]->(lab:Labour)
            OPTIONAL MATCH (wi)-[:CATEGORISED_AS]->(cat:WorkCategory)
            WHERE {where_str}
            WITH collect(lab.rate_cents) AS rates
            RETURN size(rates) AS sample_size,
                   CASE WHEN size(rates) > 0
                        THEN reduce(s = 0, x IN rates | s + x) / size(rates)
                        ELSE 0 END AS avg_rate_cents,
                   CASE WHEN size(rates) > 1
                        THEN reduce(s = 0.0, x IN rates |
                            s + (x - reduce(s2 = 0, y IN rates | s2 + y) / size(rates))
                            * (x - reduce(s2 = 0, y IN rates | s2 + y) / size(rates))
                        ) / (size(rates) - 1)
                        ELSE 0 END AS variance
            """,
            params,
        )

        if result is None or result["sample_size"] == 0:
            return {"sample_size": 0, "avg_rate_cents": 0, "std_deviation_cents": 0}

        import math
        std_dev = round(math.sqrt(max(result["variance"], 0)))

        return {
            "sample_size": result["sample_size"],
            "avg_rate_cents": round(result["avg_rate_cents"]),
            "std_deviation_cents": std_dev,
        }

    def _derive_item_rate(
        self,
        company_id: str,
        resource_type: str,
        description_filter: str | None,
        work_category_id: str | None,
    ) -> dict[str, Any]:
        """Derive material/equipment rates from completed Item nodes.

        Args:
            company_id: Tenant scope.
            resource_type: material or equipment.
            description_filter: Optional text filter.
            work_category_id: Optional category filter.

        Returns:
            Dict with avg_unit_cost_cents, sample_size, std_deviation_cents.
        """
        where_clauses = [
            "p.deleted = false",
            "wi.deleted = false",
            "p.state IN ['completed', 'closed']",
        ]
        params: dict[str, Any] = {"company_id": company_id}

        if description_filter:
            where_clauses.append("toLower(item.description) CONTAINS toLower($desc)")
            params["desc"] = description_filter
        if work_category_id:
            where_clauses.append("cat.id = $wcat_id")
            params["wcat_id"] = work_category_id

        where_str = " AND ".join(where_clauses)

        result = self._read_tx_single(
            f"""
            MATCH (c:Company {{id: $company_id}})-[:OWNS_PROJECT]->(p:Project)
                  -[:HAS_WORK_ITEM]->(wi:WorkItem)-[:HAS_ITEM]->(item:Item)
            OPTIONAL MATCH (wi)-[:CATEGORISED_AS]->(cat:WorkCategory)
            WHERE {where_str}
            RETURN count(item) AS sample_size,
                   CASE WHEN count(item) > 0
                        THEN avg(item.unit_cost_cents) ELSE 0 END AS avg_unit_cost_cents,
                   CASE WHEN count(item) > 1
                        THEN stDev(item.unit_cost_cents) ELSE 0 END AS std_deviation_cents
            """,
            params,
        )

        if result is None or result["sample_size"] == 0:
            return {"sample_size": 0, "avg_unit_cost_cents": 0, "std_deviation_cents": 0}

        return {
            "sample_size": result["sample_size"],
            "avg_unit_cost_cents": round(result["avg_unit_cost_cents"]),
            "std_deviation_cents": round(result["std_deviation_cents"]),
        }
