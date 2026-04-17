"""Variation (change order) CRUD service (Neo4j-backed).

Variations capture approved or pending changes to project scope and value.
Each variation is assigned a sequential number per project.
"""

from datetime import datetime, timezone
from typing import Any

from app.exceptions import ProjectNotFoundError
from app.models.actor import Actor
from app.services.base_service import BaseService


class VariationNotFoundError(Exception):
    """Raised when a variation cannot be found."""

    def __init__(self, variation_id: str) -> None:
        self.variation_id = variation_id
        super().__init__(f"Variation not found: {variation_id}")


VALID_VARIATION_STATUSES = frozenset(
    {"draft", "submitted", "approved", "rejected", "withdrawn"}
)


class VariationService(BaseService):
    """Manages Variation nodes in the Neo4j graph.

    Variations connect to projects via (Project)-[:HAS_VARIATION]->(Variation).
    They can vary specific WorkItems via (Variation)-[:VARIES]->(WorkItem)
    and link to evidence via (Variation)-[:EVIDENCED_BY]->(DailyLog|TimeEntry|Document).
    """

    def _next_variation_number(self, project_id: str) -> int:
        """Calculate the next sequential variation number for a project.

        Args:
            project_id: The project ID.

        Returns:
            The next variation number (1-based).
        """
        result = self._read_tx_single(
            """
            MATCH (p:Project {id: $project_id})-[:HAS_VARIATION]->(v:Variation)
            RETURN coalesce(max(v.number), 0) + 1 AS next_number
            """,
            {"project_id": project_id},
        )
        return result["next_number"] if result else 1

    def create(
        self,
        company_id: str,
        project_id: str,
        data: dict[str, Any],
        user_id: str,
    ) -> dict[str, Any]:
        """Create a new variation on a project.

        The variation number is assigned automatically as the next sequential
        number for the project.

        Args:
            company_id: The owning company ID (used for access scope).
            project_id: The parent project ID.
            data: Variation fields — description, status, amount.
            user_id: Clerk user ID of the creating user.

        Returns:
            The created variation dict.

        Raises:
            ProjectNotFoundError: If the project does not exist under this company.
        """
        actor = Actor.human(user_id)
        var_id = self._generate_id("var")
        number = self._next_variation_number(project_id)

        props: dict[str, Any] = {
            "id": var_id,
            "number": number,
            "description": data.get("description", ""),
            "status": data.get("status", "draft"),
            "amount": data.get("amount"),
            "deleted": False,
            **self._provenance_create(actor),
        }

        result = self._write_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
            CREATE (v:Variation $props)
            CREATE (p)-[:HAS_VARIATION]->(v)
            RETURN v {.*, project_id: p.id, company_id: c.id} AS variation
            """,
            {"company_id": company_id, "project_id": project_id, "props": props},
        )
        if result is None:
            raise ProjectNotFoundError(project_id)
        self._emit_audit(
            event_type="entity.created",
            entity_id=var_id,
            entity_type="Variation",
            company_id=company_id,
            actor=actor,
            summary=f"Created variation #{number} on project {project_id}",
            related_entity_ids=[project_id],
        )
        return result["variation"]

    def get(
        self, company_id: str, project_id: str, variation_id: str
    ) -> dict[str, Any]:
        """Fetch a single variation.

        Args:
            company_id: The owning company ID.
            project_id: The parent project ID.
            variation_id: The variation ID to fetch.

        Returns:
            The variation dict.

        Raises:
            VariationNotFoundError: If the variation does not exist or is soft-deleted.
        """
        result = self._read_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
                  -[:HAS_VARIATION]->(v:Variation {id: $variation_id})
            WHERE v.deleted = false
            RETURN v {.*, project_id: p.id, company_id: c.id} AS variation
            """,
            {
                "company_id": company_id,
                "project_id": project_id,
                "variation_id": variation_id,
            },
        )
        if result is None:
            raise VariationNotFoundError(variation_id)
        return result["variation"]

    def list_by_project(
        self,
        company_id: str,
        project_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> dict[str, Any]:
        """List variations for a project, ordered by variation number.

        Args:
            company_id: The owning company ID.
            project_id: The parent project ID.
            limit: Maximum number of variations to return.
            offset: Number of variations to skip.

        Returns:
            A dict with 'variations' list and 'total' count.
        """
        params: dict[str, Any] = {
            "company_id": company_id,
            "project_id": project_id,
            "limit": limit,
            "offset": offset,
        }

        count_result = self._read_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
                  -[:HAS_VARIATION]->(v:Variation)
            WHERE v.deleted = false
            RETURN count(v) AS total
            """,
            params,
        )
        total = count_result["total"] if count_result else 0

        results = self._read_tx(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
                  -[:HAS_VARIATION]->(v:Variation)
            WHERE v.deleted = false
            RETURN v {.*, project_id: p.id, company_id: c.id} AS variation
            ORDER BY v.number ASC
            SKIP $offset LIMIT $limit
            """,
            params,
        )

        return {"variations": [r["variation"] for r in results], "total": total}

    def update_status(
        self,
        company_id: str,
        project_id: str,
        variation_id: str,
        new_status: str,
        user_id: str,
    ) -> dict[str, Any]:
        """Transition a variation to a new status.

        Args:
            company_id: The owning company ID.
            project_id: The parent project ID.
            variation_id: The variation ID.
            new_status: Target status — one of: draft, submitted, approved,
                rejected, withdrawn.
            user_id: Clerk user ID of the updating user.

        Returns:
            The updated variation dict.

        Raises:
            ValueError: If new_status is not a valid status.
            VariationNotFoundError: If the variation does not exist or is soft-deleted.
        """
        if new_status not in VALID_VARIATION_STATUSES:
            raise ValueError(
                f"Invalid status '{new_status}'. Must be one of: {sorted(VALID_VARIATION_STATUSES)}"
            )

        actor = Actor.human(user_id)
        result = self._write_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
                  -[:HAS_VARIATION]->(v:Variation {id: $variation_id})
            WHERE v.deleted = false
            SET v.status = $new_status, v += $provenance
            RETURN v {.*, project_id: p.id, company_id: c.id} AS variation
            """,
            {
                "company_id": company_id,
                "project_id": project_id,
                "variation_id": variation_id,
                "new_status": new_status,
                "provenance": self._provenance_update(actor),
            },
        )
        if result is None:
            raise VariationNotFoundError(variation_id)
        self._emit_audit(
            event_type="state.transitioned",
            entity_id=variation_id,
            entity_type="Variation",
            company_id=company_id,
            actor=actor,
            summary=f"Variation {variation_id} status changed to {new_status}",
            new_state=new_status,
        )
        return result["variation"]

    def link_evidence(
        self,
        company_id: str,
        project_id: str,
        variation_id: str,
        evidence_id: str,
        evidence_type: str,
        user_id: str,
    ) -> dict[str, Any]:
        """Link an evidence node to a variation.

        Creates a (Variation)-[:EVIDENCED_BY]->(evidence) relationship.
        Supported evidence types: DailyLog, TimeEntry, Document.

        Args:
            company_id: The owning company ID.
            project_id: The parent project ID.
            variation_id: The variation ID.
            evidence_id: The ID of the evidence node.
            evidence_type: The label of the evidence node (DailyLog, TimeEntry, Document).
            user_id: Clerk user ID performing the action.

        Returns:
            Dict with variation_id and evidence_id.

        Raises:
            ValueError: If evidence_type is not supported.
            VariationNotFoundError: If the variation does not exist.
        """
        allowed_types = {"DailyLog", "TimeEntry", "Document"}
        if evidence_type not in allowed_types:
            raise ValueError(
                f"Unsupported evidence_type '{evidence_type}'. Must be one of: {sorted(allowed_types)}"
            )

        result = self._write_tx_single(
            f"""
            MATCH (c:Company {{id: $company_id}})-[:OWNS_PROJECT]->(p:Project {{id: $project_id}})
                  -[:HAS_VARIATION]->(v:Variation {{id: $variation_id}})
            WHERE v.deleted = false
            MATCH (ev:{evidence_type} {{id: $evidence_id}})
            MERGE (v)-[:EVIDENCED_BY]->(ev)
            RETURN v.id AS variation_id, ev.id AS evidence_id
            """,
            {
                "company_id": company_id,
                "project_id": project_id,
                "variation_id": variation_id,
                "evidence_id": evidence_id,
            },
        )
        if result is None:
            raise VariationNotFoundError(variation_id)
        self._emit_audit(
            event_type="relationship.added",
            entity_id=variation_id,
            entity_type="Variation",
            company_id=company_id,
            actor=Actor.human(user_id),
            summary=f"Linked {evidence_type} evidence {evidence_id} to variation",
            related_entity_ids=[evidence_id],
        )
        return result

    def detect_variations(
        self,
        company_id: str,
        project_id: str,
    ) -> dict[str, Any]:
        """Detect potential variations by comparing daily log narratives to WorkItem scope.

        Fetches recent daily logs and work items. Flags work descriptions that
        don't match any known WorkItem scope as potential out-of-scope work.

        Uses keyword overlap as a deterministic heuristic pre-filter.

        Args:
            company_id: Tenant scope.
            project_id: The project to check.

        Returns:
            Dict with flagged potential variations and their evidence.
        """
        from datetime import timedelta

        results = self._read_tx(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
            MATCH (p)-[:HAS_DAILY_LOG]->(dl:DailyLog)
            WHERE dl.deleted = false AND dl.log_date >= $cutoff
            OPTIONAL MATCH (p)-[:HAS_WORK_ITEM]->(wi:WorkItem)
            WHERE wi.deleted = false
            RETURN dl.id AS log_id,
                   dl.log_date AS log_date,
                   dl.work_performed AS work_performed,
                   dl.notes AS notes,
                   collect(DISTINCT {
                       id: wi.id,
                       description: wi.description,
                       state: wi.state
                   }) AS work_items,
                   p.id AS project_id,
                   p.name AS project_name
            ORDER BY dl.log_date DESC
            LIMIT 14
            """,
            {
                "company_id": company_id,
                "project_id": project_id,
                "cutoff": (
                    datetime.now(timezone.utc) - timedelta(days=14)
                ).strftime("%Y-%m-%d"),
            },
        )

        if not results:
            return {
                "project_id": project_id,
                "flags": [],
                "flag_count": 0,
                "message": "No recent daily logs to analyse",
            }

        stop_words = {
            "the", "a", "an", "and", "or", "in", "on", "at", "to",
            "for", "of", "with", "is", "was", "are", "were", "been",
            "be", "have", "has", "had", "do", "does", "did", "will",
            "would", "could", "should", "may", "might", "can", "this",
            "that", "these", "those", "it", "its", "not", "no", "all",
        }

        # Build scope vocabulary from all work items (deduplicated)
        all_scope_words: set[str] = set()
        first_row_items = [wi for wi in results[0]["work_items"] if wi.get("id")]
        for wi in first_row_items:
            all_scope_words.update((wi.get("description") or "").lower().split())

        flags: list[dict[str, Any]] = []
        for row in results:
            log_text = " ".join(
                filter(None, [row.get("work_performed"), row.get("notes")])
            ).lower()
            if not log_text.strip():
                continue

            log_words = set(log_text.split()) - stop_words
            if not log_words:
                continue

            log_unique = log_words - all_scope_words
            overlap_ratio = 1.0 - (len(log_unique) / max(len(log_words), 1))

            if overlap_ratio < 0.4 and len(log_unique) > 3:
                flags.append({
                    "log_id": row["log_id"],
                    "log_date": row["log_date"],
                    "work_performed": row.get("work_performed", ""),
                    "overlap_ratio": round(overlap_ratio, 2),
                    "unmatched_keywords": sorted(list(log_unique))[:10],
                    "reason": "Daily log describes work not matching any work item scope",
                })

        return {
            "project_id": results[0]["project_id"] if results else project_id,
            "project_name": results[0].get("project_name", "") if results else "",
            "flags": flags,
            "flag_count": len(flags),
            "logs_analysed": len(results),
        }

    def archive(
        self,
        company_id: str,
        project_id: str,
        variation_id: str,
        user_id: str,
    ) -> None:
        """Soft-delete a variation.

        Args:
            company_id: The owning company ID.
            project_id: The parent project ID.
            variation_id: The variation ID to archive.
            user_id: Clerk user ID of the deleting user.

        Raises:
            VariationNotFoundError: If the variation does not exist.
        """
        result = self._write_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
                  -[:HAS_VARIATION]->(v:Variation {id: $variation_id})
            WHERE v.deleted = false
            SET v.deleted = true, v.updated_at = $now
            RETURN v.id AS id
            """,
            {
                "company_id": company_id,
                "project_id": project_id,
                "variation_id": variation_id,
                "now": datetime.now(timezone.utc).isoformat(),
            },
        )
        if result is None:
            raise VariationNotFoundError(variation_id)
        self._emit_audit(
            event_type="entity.archived",
            entity_id=variation_id,
            entity_type="Variation",
            company_id=company_id,
            actor=Actor.human(user_id),
            summary=f"Archived variation {variation_id}",
        )
