"""IndustryProductivityBaseline read-only lookup service.

IndustryProductivityBaseline nodes are shared across tenants (no company
scoping) and seeded, not user-mutable. This service provides read-only
traversal for the Layer 3 source cascade.
"""

from typing import Any

from app.services.base_service import BaseService


class IndustryBaselineService(BaseService):
    """Read-only lookups against IndustryProductivityBaseline nodes."""

    def get(self, baseline_id: str) -> dict[str, Any] | None:
        """Fetch a single baseline by ID.

        Args:
            baseline_id: The baseline ID.

        Returns:
            The baseline dict or None if not found.
        """
        result = self._read_tx_single(
            """
            MATCH (ipb:IndustryProductivityBaseline {id: $baseline_id})
            RETURN ipb {.*} AS baseline
            """,
            {"baseline_id": baseline_id},
        )
        return result["baseline"] if result else None

    def list_all(
        self, trade: str | None = None, limit: int = 200, offset: int = 0
    ) -> dict[str, Any]:
        """List industry baselines, optionally filtered by trade.

        Args:
            trade: Optional trade filter.
            limit: Page size.
            offset: Page offset.

        Returns:
            Dict with 'baselines' list and 'total' count.
        """
        where_clauses: list[str] = []
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        if trade is not None:
            where_clauses.append("ipb.trade = $trade")
            params["trade"] = trade
        where_str = (" WHERE " + " AND ".join(where_clauses)) if where_clauses else ""

        count_result = self._read_tx_single(
            f"""
            MATCH (ipb:IndustryProductivityBaseline)
            {where_str}
            RETURN count(ipb) AS total
            """,
            params,
        )
        total = count_result["total"] if count_result else 0

        results = self._read_tx(
            f"""
            MATCH (ipb:IndustryProductivityBaseline)
            {where_str}
            RETURN ipb {{.*}} AS baseline
            ORDER BY ipb.trade, ipb.work_description
            SKIP $offset LIMIT $limit
            """,
            params,
        )
        return {
            "baselines": [r["baseline"] for r in results],
            "total": total,
        }

    def find_by_trade_and_description(
        self,
        trade: str,
        description: str,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """Find baselines matching a trade and free-text description.

        Uses case-insensitive substring matching on work_description. Results
        are sorted with exact trade match first, then by descriptor similarity
        (longest token overlap as a proxy).

        Args:
            trade: Trade name (e.g. 'electrical').
            description: Work description to match.
            limit: Max rows to return.

        Returns:
            A list of baseline dicts.
        """
        needle = description.lower().strip()
        results = self._read_tx(
            """
            MATCH (ipb:IndustryProductivityBaseline)
            WHERE toLower(ipb.trade) = toLower($trade)
              AND (
                  toLower(ipb.work_description) CONTAINS $needle
                  OR $needle CONTAINS toLower(ipb.work_description)
              )
            RETURN ipb {.*} AS baseline
            ORDER BY size(ipb.work_description) ASC
            LIMIT $limit
            """,
            {
                "trade": trade,
                "needle": needle,
                "limit": limit,
            },
        )
        return [r["baseline"] for r in results]
