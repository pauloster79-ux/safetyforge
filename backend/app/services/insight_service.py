"""Insight CRUD service (Neo4j-backed).

Insights capture contractor-specific learned adjustments that feed Layer 3
of the source cascade during estimating. They are company-scoped.

Graph model: (Company)-[:HAS_INSIGHT]->(Insight)
"""

from datetime import datetime, timezone
from typing import Any

from app.exceptions import InsightNotFoundError
from app.models.actor import Actor
from app.services.base_service import BaseService


class InsightService(BaseService):
    """Manages Insight nodes at the company level."""

    def create(
        self, company_id: str, data: dict[str, Any], user_id: str
    ) -> dict[str, Any]:
        """Create an insight for the company.

        Args:
            company_id: The owning company ID.
            data: Insight fields (scope, scope_value, statement, adjustment_type,
                adjustment_value, confidence, source_context).
            user_id: Clerk user ID of the creating user.

        Returns:
            The created insight dict.
        """
        actor = Actor.human(user_id)
        ins_id = self._generate_id("ins")

        scope = data["scope"]
        scope_value = data["scope"].value if hasattr(data["scope"], "value") else data["scope"]

        # NB: ``confidence`` is a domain field on Insight (0-1) — we spread
        # ``_provenance_create`` first (which sets ``confidence`` from actor
        # self-confidence, typically None for humans) and then overwrite with
        # the domain value so the insight's confidence survives.
        props: dict[str, Any] = {
            "id": ins_id,
            "scope": scope_value,
            "scope_value": data["scope_value"],
            "statement": data["statement"],
            "adjustment_type": data["adjustment_type"],
            "adjustment_value": data.get("adjustment_value"),
            "source_context": data.get("source_context"),
            "validation_count": 0,
            "last_applied_at": None,
            **self._provenance_create(actor),
            # Overwrite provenance's `confidence` key with the domain value
            "confidence": data.get("confidence", 0.5),
        }

        result = self._write_tx_single(
            """
            MATCH (c:Company {id: $company_id})
            CREATE (ins:Insight $props)
            CREATE (c)-[:HAS_INSIGHT]->(ins)
            RETURN ins {.*, company_id: c.id} AS insight
            """,
            {"company_id": company_id, "props": props},
        )
        if result is None:
            from app.exceptions import CompanyNotFoundError
            raise CompanyNotFoundError(company_id)

        self._emit_audit(
            event_type="entity.created",
            entity_id=ins_id,
            entity_type="Insight",
            company_id=company_id,
            actor=actor,
            summary=f"Created insight for {scope_value}: '{data['statement'][:80]}'",
        )
        return result["insight"]

    def get(self, company_id: str, insight_id: str) -> dict[str, Any]:
        """Fetch a single insight.

        Args:
            company_id: The owning company ID.
            insight_id: The insight ID.

        Returns:
            The insight dict.

        Raises:
            InsightNotFoundError: If not found.
        """
        result = self._read_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:HAS_INSIGHT]->(ins:Insight {id: $insight_id})
            RETURN ins {.*, company_id: c.id} AS insight
            """,
            {"company_id": company_id, "insight_id": insight_id},
        )
        if result is None:
            raise InsightNotFoundError(insight_id)
        return result["insight"]

    def list_by_company(
        self,
        company_id: str,
        scope: str | None = None,
        scope_value: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> dict[str, Any]:
        """List insights for a company with optional scope filters.

        Args:
            company_id: The owning company ID.
            scope: Optional filter on scope (e.g. 'work_type').
            scope_value: Optional filter on scope_value.
            limit: Page size.
            offset: Page offset.

        Returns:
            A dict with 'insights' list and 'total' count.
        """
        where_clauses: list[str] = []
        params: dict[str, Any] = {
            "company_id": company_id,
            "limit": limit,
            "offset": offset,
        }
        if scope is not None:
            where_clauses.append("ins.scope = $scope")
            params["scope"] = scope
        if scope_value is not None:
            where_clauses.append("ins.scope_value = $scope_value")
            params["scope_value"] = scope_value

        where_str = (" WHERE " + " AND ".join(where_clauses)) if where_clauses else ""

        count_result = self._read_tx_single(
            f"""
            MATCH (c:Company {{id: $company_id}})-[:HAS_INSIGHT]->(ins:Insight)
            {where_str}
            RETURN count(ins) AS total
            """,
            params,
        )
        total = count_result["total"] if count_result else 0

        results = self._read_tx(
            f"""
            MATCH (c:Company {{id: $company_id}})-[:HAS_INSIGHT]->(ins:Insight)
            {where_str}
            RETURN ins {{.*, company_id: c.id}} AS insight
            ORDER BY ins.confidence DESC, ins.created_at DESC
            SKIP $offset LIMIT $limit
            """,
            params,
        )
        return {
            "insights": [r["insight"] for r in results],
            "total": total,
        }

    def find_applicable(
        self,
        company_id: str,
        work_type: str | None = None,
        trade: str | None = None,
        jurisdiction: str | None = None,
        client_type: str | None = None,
        project_size: str | None = None,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        """Return insights applicable to the given project context.

        Matches Insights whose (scope, scope_value) match any of the provided
        dimensions. Sorted by confidence DESC so the strongest insights surface
        first.

        Args:
            company_id: The owning company ID.
            work_type: Optional work_type tag to match.
            trade: Optional trade to match.
            jurisdiction: Optional jurisdiction code.
            client_type: Optional client type tag.
            project_size: Optional project size bucket.
            limit: Maximum number of insights to return.

        Returns:
            A list of insight dicts sorted by confidence DESC.
        """
        # Build the list of (scope, scope_value) pairs to match.
        # scope_value matching uses token overlap — 'warehouse_conversion'
        # should match 'renovation_electrical' if any significant tokens
        # (renovation|conversion|electrical) overlap.
        pairs: list[dict[str, str]] = []
        if work_type:
            pairs.append({"scope": "work_type", "scope_value": work_type})
        if trade:
            pairs.append({"scope": "trade", "scope_value": trade})
        if jurisdiction:
            pairs.append({"scope": "jurisdiction", "scope_value": jurisdiction})
        if client_type:
            pairs.append({"scope": "client_type", "scope_value": client_type})
        if project_size:
            pairs.append({"scope": "project_size", "scope_value": project_size})

        if not pairs:
            return []

        # Fetch ALL active insights for the company. We score by token
        # overlap regardless of scope dimension — the scope tags are
        # agent-chosen and inconsistent (work_type vs project_size vs
        # trade for essentially the same pattern). This ensures an
        # Insight saved with scope=project_size/pre_2000_residential
        # still surfaces when querying for work_type=panel_upgrade.
        raw = self._read_tx(
            """
            MATCH (c:Company {id: $company_id})-[:HAS_INSIGHT]->(ins:Insight)
            WHERE coalesce(ins.active, true) = true
              AND coalesce(ins.deprecated, false) = false
            RETURN ins {.*, company_id: c.id} AS insight
            """,
            {"company_id": company_id},
        )

        # Semantic equivalences — lets "conversion" match "renovation",
        # "refurb" match "renovation", etc. Kept small and pragmatic.
        _EQUIVALENCES = {
            "renovation": {"renovation", "conversion", "refurb", "refurbishment", "remodel", "retrofit"},
            "conversion": {"renovation", "conversion", "refurb", "refurbishment", "remodel", "retrofit"},
            "refurb": {"renovation", "conversion", "refurb", "refurbishment", "remodel", "retrofit"},
            "remodel": {"renovation", "conversion", "refurb", "refurbishment", "remodel", "retrofit"},
            "retrofit": {"renovation", "conversion", "refurb", "refurbishment", "remodel", "retrofit"},
            "commercial": {"commercial", "office", "retail", "cafe", "restaurant", "warehouse", "industrial"},
            "office": {"commercial", "office"},
            "retail": {"commercial", "retail", "shop"},
            "warehouse": {"commercial", "warehouse", "industrial"},
            "residential": {"residential", "home", "house", "apartment", "loft", "flat"},
            "old": {"old", "renovation", "conversion", "heritage", "existing"},
        }

        def _expand(tokens: set[str]) -> set[str]:
            expanded = set(tokens)
            for t in tokens:
                if t in _EQUIVALENCES:
                    expanded |= _EQUIVALENCES[t]
            return expanded

        def _tokens(value: str | None) -> set[str]:
            if not value:
                return set()
            return {
                t for t in value.lower().replace("-", " ").replace("_", " ").split()
                if len(t) >= 3
            }

        # Score each candidate by token overlap with ANY pair, regardless
        # of scope dimension. The scope_value tokens are what matter —
        # whether the Insight was tagged as trade, work_type, or
        # project_size, if the tokens overlap with the current context,
        # it's relevant.
        scored: list[tuple[int, dict[str, Any]]] = []
        for row in raw:
            ins = row["insight"]
            ins_tokens = _expand(_tokens(ins.get("scope_value")))
            best_score = 0
            for pair in pairs:
                pair_tokens = _expand(_tokens(pair["scope_value"]))
                overlap = len(ins_tokens & pair_tokens)
                if overlap > best_score:
                    best_score = overlap
            if best_score >= 1:
                scored.append((best_score, ins))

        # Sort by score DESC, then by confidence DESC
        scored.sort(
            key=lambda x: (x[0], x[1].get("confidence") or 0, x[1].get("validation_count") or 0),
            reverse=True,
        )
        return [ins for _, ins in scored[:limit]]

    def update(
        self,
        company_id: str,
        insight_id: str,
        data: dict[str, Any],
        user_id: str,
    ) -> dict[str, Any]:
        """Update an insight.

        Args:
            company_id: The owning company ID.
            insight_id: The insight ID.
            data: Fields to update (only non-None values applied).
            user_id: Clerk user ID.

        Returns:
            The updated insight dict.

        Raises:
            InsightNotFoundError: If not found.
        """
        actor = Actor.human(user_id)
        update_fields: dict[str, Any] = {}
        for field_name, value in data.items():
            if value is None:
                continue
            if field_name == "scope" and hasattr(value, "value"):
                update_fields[field_name] = value.value
            elif field_name == "last_applied_at" and hasattr(value, "isoformat"):
                update_fields[field_name] = value.isoformat()
            else:
                update_fields[field_name] = value
        update_fields.update(self._provenance_update(actor))

        result = self._write_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:HAS_INSIGHT]->(ins:Insight {id: $insight_id})
            SET ins += $props
            RETURN ins {.*, company_id: c.id} AS insight
            """,
            {
                "company_id": company_id,
                "insight_id": insight_id,
                "props": update_fields,
            },
        )
        if result is None:
            raise InsightNotFoundError(insight_id)

        self._emit_audit(
            event_type="entity.updated",
            entity_id=insight_id,
            entity_type="Insight",
            company_id=company_id,
            actor=actor,
            summary=f"Updated insight {insight_id}",
        )
        return result["insight"]

    def delete(self, company_id: str, insight_id: str) -> None:
        """Delete an insight (hard delete).

        Args:
            company_id: The owning company ID.
            insight_id: The insight ID.

        Raises:
            InsightNotFoundError: If not found.
        """
        result = self._write_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:HAS_INSIGHT]->(ins:Insight {id: $insight_id})
            DETACH DELETE ins
            RETURN c.id AS company_id
            """,
            {"company_id": company_id, "insight_id": insight_id},
        )
        if result is None:
            raise InsightNotFoundError(insight_id)

    def increment_validation(
        self, company_id: str, insight_id: str, user_id: str
    ) -> dict[str, Any]:
        """Increment validation_count, bump confidence, and record last_applied_at.

        Used when an insight is applied to an estimate and the contractor
        accepts it (explicit or implicit validation). Confidence is raised by
        0.05, capped at 0.95.

        Args:
            company_id: The owning company ID.
            insight_id: The insight ID.
            user_id: Clerk user ID.

        Returns:
            The updated insight dict.

        Raises:
            InsightNotFoundError: If not found.
        """
        actor = Actor.human(user_id)
        now_iso = datetime.now(timezone.utc).isoformat()
        provenance = self._provenance_update(actor)

        result = self._write_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:HAS_INSIGHT]->(ins:Insight {id: $insight_id})
            SET ins.validation_count = coalesce(ins.validation_count, 0) + 1,
                ins.confidence = CASE
                    WHEN coalesce(ins.confidence, 0.5) + 0.05 > 0.95 THEN 0.95
                    ELSE coalesce(ins.confidence, 0.5) + 0.05
                END,
                ins.last_applied_at = $now_iso,
                ins += $provenance
            RETURN ins {.*, company_id: c.id} AS insight
            """,
            {
                "company_id": company_id,
                "insight_id": insight_id,
                "now_iso": now_iso,
                "provenance": provenance,
            },
        )
        if result is None:
            raise InsightNotFoundError(insight_id)

        self._emit_audit(
            event_type="entity.updated",
            entity_id=insight_id,
            entity_type="Insight",
            company_id=company_id,
            actor=actor,
            summary=f"Validated insight {insight_id} (confidence raised)",
        )
        return result["insight"]

    def decrement_validation(
        self,
        company_id: str,
        insight_id: str,
        user_id: str,
        reason: str,
    ) -> dict[str, Any]:
        """Decrement confidence and append the correction reason.

        Used when the contractor rejects or corrects an applied insight.
        Confidence is reduced by 0.10 (floor 0.0). The reason is appended
        to ``source_context`` with a timestamp so the rejection history is
        preserved. If confidence drops below 0.2 the insight is marked
        ``active = false`` (and ``deprecated = true`` for back-compat) so
        future surfacing skips it.

        Args:
            company_id: The owning company ID.
            insight_id: The insight ID being rejected.
            user_id: Clerk user ID.
            reason: Why the contractor pushed back.

        Returns:
            The updated insight dict (includes ``deactivated`` flag).

        Raises:
            InsightNotFoundError: If not found.
        """
        actor = Actor.human(user_id)
        now_iso = datetime.now(timezone.utc).isoformat()
        rejection_line = f"[{now_iso}] rejected: {reason}"
        provenance = self._provenance_update(actor)

        result = self._write_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:HAS_INSIGHT]->(ins:Insight {id: $insight_id})
            SET ins.confidence = CASE
                    WHEN coalesce(ins.confidence, 0.5) - 0.10 < 0.0 THEN 0.0
                    ELSE coalesce(ins.confidence, 0.5) - 0.10
                END,
                ins.source_context = CASE
                    WHEN ins.source_context IS NULL OR ins.source_context = ''
                        THEN $rejection_line
                    ELSE ins.source_context + '\n' + $rejection_line
                END,
                ins += $provenance
            WITH ins
            SET ins.active = (ins.confidence >= 0.2),
                ins.deprecated = (ins.confidence < 0.2)
            RETURN ins {.*, company_id: c.id} AS insight,
                   (ins.confidence < 0.2) AS deactivated
            """,
            {
                "company_id": company_id,
                "insight_id": insight_id,
                "rejection_line": rejection_line,
                "provenance": provenance,
            },
        )
        if result is None:
            raise InsightNotFoundError(insight_id)

        self._emit_audit(
            event_type="entity.updated",
            entity_id=insight_id,
            entity_type="Insight",
            company_id=company_id,
            actor=actor,
            summary=(
                f"Rejected insight — confidence reduced by 0.10"
                + (" (deactivated)" if result["deactivated"] else "")
                + f" — {reason[:80]}"
            ),
        )
        insight = result["insight"]
        insight["deactivated"] = bool(result["deactivated"])
        return insight
