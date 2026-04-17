"""Estimating service — historical rate lookup and estimate assembly.

Searches past completed projects for similar WorkItems to suggest
labour hours and rates. Now queries Labour/Item children and
ResourceRate/ProductivityRate nodes for rate intelligence.
"""

from typing import Any

from app.services.base_service import BaseService


class EstimatingService(BaseService):
    """Provides estimating intelligence by querying historical project data.

    Traverses the graph across completed projects to find similar WorkItems
    with their Labour and Item breakdowns, and queries ResourceRate and
    ProductivityRate nodes for company rate knowledge.
    """

    def search_historical_rates(
        self,
        company_id: str,
        description: str | None = None,
        work_category_id: str | None = None,
        limit: int = 10,
    ) -> dict[str, Any]:
        """Search past completed projects for similar work items.

        Now traverses Labour and Item children instead of flat properties.
        Also includes matching ResourceRates and ProductivityRates.

        Args:
            company_id: Tenant scope — only searches this company's projects.
            description: Optional text to match against work item descriptions.
            work_category_id: Optional WorkCategory ID to filter by.
            limit: Maximum number of historical items to return.

        Returns:
            Dict with historical_items, resource_rates, productivity_rates,
            and aggregated statistics.
        """
        where_clauses = [
            "p.deleted = false",
            "wi.deleted = false",
            "p.state IN ['completed', 'closed']",
        ]
        params: dict[str, Any] = {
            "company_id": company_id,
            "limit": limit,
        }

        if work_category_id:
            where_clauses.append("cat.id = $work_category_id")
            params["work_category_id"] = work_category_id

        if description:
            where_clauses.append("toLower(wi.description) CONTAINS toLower($description)")
            params["description"] = description

        where_str = " AND ".join(where_clauses)

        # Query work items with Labour/Item rollups
        results = self._read_tx(
            f"""
            MATCH (c:Company {{id: $company_id}})-[:OWNS_PROJECT]->(p:Project)
                  -[:HAS_WORK_ITEM]->(wi:WorkItem)
            OPTIONAL MATCH (wi)-[:CATEGORISED_AS]->(cat:WorkCategory)
            WHERE {where_str}
            OPTIONAL MATCH (wi)-[:HAS_LABOUR]->(lab:Labour)
            OPTIONAL MATCH (wi)-[:HAS_ITEM]->(item:Item)
            WITH wi, p, cat,
                 coalesce(sum(DISTINCT lab.cost_cents), 0) AS labour_total_cents,
                 coalesce(sum(DISTINCT item.total_cents), 0) AS items_total_cents,
                 count(DISTINCT lab) AS labour_count,
                 count(DISTINCT item) AS item_count
            RETURN wi.id AS work_item_id,
                   wi.description AS description,
                   wi.quantity AS quantity,
                   wi.unit AS unit,
                   wi.margin_pct AS margin_pct,
                   wi.state AS state,
                   labour_total_cents,
                   items_total_cents,
                   labour_count,
                   item_count,
                   p.id AS project_id,
                   p.name AS project_name,
                   p.state AS project_state,
                   cat.id AS category_id,
                   cat.name AS category_name
            ORDER BY p.created_at DESC
            LIMIT $limit
            """,
            params,
        )

        items = [dict(r) for r in results]

        # Calculate aggregated statistics from Labour children
        labour_costs = [i["labour_total_cents"] for i in items if i["labour_total_cents"] > 0]
        items_costs = [i["items_total_cents"] for i in items if i["items_total_cents"] > 0]

        stats: dict[str, Any] = {}
        if labour_costs:
            stats["labour_total_cents"] = {
                "min": min(labour_costs),
                "max": max(labour_costs),
                "avg": round(sum(labour_costs) / len(labour_costs)),
                "sample_count": len(labour_costs),
            }
        if items_costs:
            stats["items_total_cents"] = {
                "min": min(items_costs),
                "max": max(items_costs),
                "avg": round(sum(items_costs) / len(items_costs)),
                "sample_count": len(items_costs),
            }

        # Fetch matching resource rates
        resource_rates = self._fetch_matching_rates(company_id, description)

        # Fetch matching productivity rates
        productivity_rates = self._fetch_matching_productivity(company_id, description)

        return {
            "historical_items": items,
            "resource_rates": resource_rates,
            "productivity_rates": productivity_rates,
            "statistics": stats,
            "total_found": len(items),
            "search_criteria": {
                "description": description,
                "work_category_id": work_category_id,
            },
        }

    def _fetch_matching_rates(
        self, company_id: str, description: str | None
    ) -> list[dict[str, Any]]:
        """Fetch ResourceRates matching a description.

        Args:
            company_id: Tenant scope.
            description: Optional text filter.

        Returns:
            List of matching rate dicts.
        """
        params: dict[str, Any] = {"company_id": company_id}
        desc_filter = ""
        if description:
            desc_filter = " AND toLower(rr.description) CONTAINS toLower($description)"
            params["description"] = description

        results = self._read_tx(
            f"""
            MATCH (c:Company {{id: $company_id}})-[:HAS_RATE]->(rr:ResourceRate)
            WHERE rr.active = true{desc_filter}
            RETURN rr {{.*}} AS rate
            ORDER BY rr.resource_type ASC, rr.description ASC
            LIMIT 20
            """,
            params,
        )
        return [r["rate"] for r in results]

    def _fetch_matching_productivity(
        self, company_id: str, description: str | None
    ) -> list[dict[str, Any]]:
        """Fetch ProductivityRates matching a description.

        Args:
            company_id: Tenant scope.
            description: Optional text filter.

        Returns:
            List of matching productivity rate dicts.
        """
        params: dict[str, Any] = {"company_id": company_id}
        desc_filter = ""
        if description:
            desc_filter = " AND toLower(pr.description) CONTAINS toLower($description)"
            params["description"] = description

        results = self._read_tx(
            f"""
            MATCH (c:Company {{id: $company_id}})-[:HAS_PRODUCTIVITY]->(pr:ProductivityRate)
            WHERE pr.active = true{desc_filter}
            RETURN pr {{.*}} AS rate
            ORDER BY pr.description ASC
            LIMIT 20
            """,
            params,
        )
        return [r["rate"] for r in results]

    def get_estimate_summary(
        self, company_id: str, project_id: str
    ) -> dict[str, Any]:
        """Calculate a full estimate summary for a project.

        Traverses Project -> WorkItems -> Labour/Item children to build
        the estimate with correct cost rollup.

        Args:
            company_id: Tenant scope.
            project_id: The project to summarise.

        Returns:
            Dict with itemised breakdown and totals.
        """
        result = self._read_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
            WHERE p.deleted = false

            CALL {
                WITH p
                OPTIONAL MATCH (p)-[:HAS_WORK_ITEM]->(wi:WorkItem)
                WHERE wi.deleted = false
                OPTIONAL MATCH (wi)-[:HAS_LABOUR]->(lab:Labour)
                OPTIONAL MATCH (wi)-[:HAS_ITEM]->(item:Item)
                WITH wi,
                     coalesce(sum(DISTINCT lab.cost_cents), 0) AS labour_cost,
                     coalesce(sum(DISTINCT item.total_cents), 0) AS items_cost,
                     coalesce(wi.margin_pct, 0) AS margin_pct
                WITH wi, labour_cost, items_cost, margin_pct,
                     round((labour_cost + items_cost)
                           * (1 + margin_pct / 100.0)) AS line_total
                RETURN collect({
                    id: wi.id,
                    description: wi.description,
                    state: wi.state,
                    quantity: wi.quantity,
                    unit: wi.unit,
                    labour_cost_cents: labour_cost,
                    items_cost_cents: items_cost,
                    margin_pct: margin_pct,
                    sell_price_cents: line_total,
                    is_alternate: wi.is_alternate
                }) AS items,
                sum(labour_cost) AS total_labour,
                sum(items_cost) AS total_items,
                sum(line_total) AS grand_total,
                count(wi) AS item_count
            }

            RETURN p.id AS project_id,
                   p.name AS project_name,
                   p.state AS project_state,
                   p.estimate_confidence AS estimate_confidence,
                   p.target_margin_percent AS target_margin_percent,
                   items, total_labour, total_items, grand_total, item_count
            """,
            {"company_id": company_id, "project_id": project_id},
        )

        if result is None:
            return {"error": f"Project {project_id} not found"}

        # Filter out null items from collect
        items = [i for i in result["items"] if i.get("id")]

        return {
            "project_id": result["project_id"],
            "project_name": result["project_name"],
            "project_state": result["project_state"],
            "estimate_confidence": result["estimate_confidence"],
            "target_margin_percent": result["target_margin_percent"],
            "items": items,
            "item_count": result["item_count"] or 0,
            "total_labour_cents": result["total_labour"] or 0,
            "total_items_cents": result["total_items"] or 0,
            "grand_total_cents": result["grand_total"] or 0,
            "currency": "USD",
        }
