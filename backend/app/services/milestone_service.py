"""Milestone CRUD service (Neo4j-backed).

Milestones mark significant dates or deliverables on a project
and can be tracked for on-time completion.
"""

from datetime import datetime, timezone
from typing import Any

from app.exceptions import ProjectNotFoundError
from app.models.actor import Actor
from app.services.base_service import BaseService


class MilestoneNotFoundError(Exception):
    """Raised when a milestone cannot be found."""

    def __init__(self, milestone_id: str) -> None:
        self.milestone_id = milestone_id
        super().__init__(f"Milestone not found: {milestone_id}")


VALID_MILESTONE_STATUSES = frozenset({"pending", "at_risk", "met", "missed"})


class MilestoneService(BaseService):
    """Manages Milestone nodes in the Neo4j graph.

    Milestones connect to projects via (Project)-[:HAS_MILESTONE]->(Milestone).
    """

    def create(
        self,
        company_id: str,
        project_id: str,
        data: dict[str, Any],
        user_id: str,
    ) -> dict[str, Any]:
        """Create a new milestone on a project.

        Args:
            company_id: The owning company ID (used for access scope).
            project_id: The parent project ID.
            data: Milestone fields — name, planned_date, status.
            user_id: Clerk user ID of the creating user.

        Returns:
            The created milestone dict.

        Raises:
            ProjectNotFoundError: If the project does not exist under this company.
        """
        actor = Actor.human(user_id)
        ms_id = self._generate_id("ms")

        props: dict[str, Any] = {
            "id": ms_id,
            "name": data.get("name", ""),
            "planned_date": data.get("planned_date"),
            "actual_date": None,
            "status": data.get("status", "pending"),
            "deleted": False,
            **self._provenance_create(actor),
        }

        result = self._write_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
            CREATE (ms:Milestone $props)
            CREATE (p)-[:HAS_MILESTONE]->(ms)
            RETURN ms {.*, project_id: p.id, company_id: c.id} AS milestone
            """,
            {"company_id": company_id, "project_id": project_id, "props": props},
        )
        if result is None:
            raise ProjectNotFoundError(project_id)
        self._emit_audit(
            event_type="entity.created",
            entity_id=ms_id,
            entity_type="Milestone",
            company_id=company_id,
            actor=actor,
            summary=f"Created milestone '{data.get('name', '')}' on project {project_id}",
            related_entity_ids=[project_id],
        )
        return result["milestone"]

    def get(
        self, company_id: str, project_id: str, milestone_id: str
    ) -> dict[str, Any]:
        """Fetch a single milestone.

        Args:
            company_id: The owning company ID.
            project_id: The parent project ID.
            milestone_id: The milestone ID to fetch.

        Returns:
            The milestone dict.

        Raises:
            MilestoneNotFoundError: If the milestone does not exist or is soft-deleted.
        """
        result = self._read_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
                  -[:HAS_MILESTONE]->(ms:Milestone {id: $milestone_id})
            WHERE ms.deleted = false
            RETURN ms {.*, project_id: p.id, company_id: c.id} AS milestone
            """,
            {
                "company_id": company_id,
                "project_id": project_id,
                "milestone_id": milestone_id,
            },
        )
        if result is None:
            raise MilestoneNotFoundError(milestone_id)
        return result["milestone"]

    def list_by_project(
        self,
        company_id: str,
        project_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> dict[str, Any]:
        """List milestones for a project, ordered by planned date.

        Args:
            company_id: The owning company ID.
            project_id: The parent project ID.
            limit: Maximum number of milestones to return.
            offset: Number of milestones to skip.

        Returns:
            A dict with 'milestones' list and 'total' count.
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
                  -[:HAS_MILESTONE]->(ms:Milestone)
            WHERE ms.deleted = false
            RETURN count(ms) AS total
            """,
            params,
        )
        total = count_result["total"] if count_result else 0

        results = self._read_tx(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
                  -[:HAS_MILESTONE]->(ms:Milestone)
            WHERE ms.deleted = false
            RETURN ms {.*, project_id: p.id, company_id: c.id} AS milestone
            ORDER BY ms.planned_date ASC
            SKIP $offset LIMIT $limit
            """,
            params,
        )

        return {"milestones": [r["milestone"] for r in results], "total": total}

    def update(
        self,
        company_id: str,
        project_id: str,
        milestone_id: str,
        data: dict[str, Any],
        user_id: str,
    ) -> dict[str, Any]:
        """Update fields on an existing milestone.

        Args:
            company_id: The owning company ID.
            project_id: The parent project ID.
            milestone_id: The milestone ID to update.
            data: Fields to update (only non-None values are applied).
            user_id: Clerk user ID of the updating user.

        Returns:
            The updated milestone dict.

        Raises:
            MilestoneNotFoundError: If the milestone does not exist or is soft-deleted.
        """
        actor = Actor.human(user_id)
        update_fields = {k: v for k, v in data.items() if v is not None}
        update_fields.update(self._provenance_update(actor))

        result = self._write_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
                  -[:HAS_MILESTONE]->(ms:Milestone {id: $milestone_id})
            WHERE ms.deleted = false
            SET ms += $props
            RETURN ms {.*, project_id: p.id, company_id: c.id} AS milestone
            """,
            {
                "company_id": company_id,
                "project_id": project_id,
                "milestone_id": milestone_id,
                "props": update_fields,
            },
        )
        if result is None:
            raise MilestoneNotFoundError(milestone_id)
        self._emit_audit(
            event_type="entity.updated",
            entity_id=milestone_id,
            entity_type="Milestone",
            company_id=company_id,
            actor=actor,
            summary=f"Updated milestone {milestone_id}",
        )
        return result["milestone"]

    def mark_met(
        self,
        company_id: str,
        project_id: str,
        milestone_id: str,
        actual_date: str,
        user_id: str,
    ) -> dict[str, Any]:
        """Mark a milestone as met and record the actual completion date.

        Args:
            company_id: The owning company ID.
            project_id: The parent project ID.
            milestone_id: The milestone ID.
            actual_date: ISO date string of when the milestone was actually met.
            user_id: Clerk user ID performing the action.

        Returns:
            The updated milestone dict.

        Raises:
            MilestoneNotFoundError: If the milestone does not exist.
        """
        actor = Actor.human(user_id)
        result = self._write_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
                  -[:HAS_MILESTONE]->(ms:Milestone {id: $milestone_id})
            WHERE ms.deleted = false
            SET ms.status = 'met', ms.actual_date = $actual_date, ms += $provenance
            RETURN ms {.*, project_id: p.id, company_id: c.id} AS milestone
            """,
            {
                "company_id": company_id,
                "project_id": project_id,
                "milestone_id": milestone_id,
                "actual_date": actual_date,
                "provenance": self._provenance_update(actor),
            },
        )
        if result is None:
            raise MilestoneNotFoundError(milestone_id)
        self._emit_audit(
            event_type="state.transitioned",
            entity_id=milestone_id,
            entity_type="Milestone",
            company_id=company_id,
            actor=actor,
            summary=f"Milestone {milestone_id} marked as met",
            new_state="met",
        )
        return result["milestone"]

    def archive(
        self,
        company_id: str,
        project_id: str,
        milestone_id: str,
        user_id: str,
    ) -> None:
        """Soft-delete a milestone.

        Args:
            company_id: The owning company ID.
            project_id: The parent project ID.
            milestone_id: The milestone ID to archive.
            user_id: Clerk user ID of the deleting user.

        Raises:
            MilestoneNotFoundError: If the milestone does not exist.
        """
        result = self._write_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
                  -[:HAS_MILESTONE]->(ms:Milestone {id: $milestone_id})
            WHERE ms.deleted = false
            SET ms.deleted = true, ms.updated_at = $now
            RETURN ms.id AS id
            """,
            {
                "company_id": company_id,
                "project_id": project_id,
                "milestone_id": milestone_id,
                "now": datetime.now(timezone.utc).isoformat(),
            },
        )
        if result is None:
            raise MilestoneNotFoundError(milestone_id)
        self._emit_audit(
            event_type="entity.archived",
            entity_id=milestone_id,
            entity_type="Milestone",
            company_id=company_id,
            actor=Actor.human(user_id),
            summary=f"Archived milestone {milestone_id}",
        )
