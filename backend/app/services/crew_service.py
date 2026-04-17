"""Crew CRUD service (Neo4j-backed).

Crews are named groups of workers that can be assigned to work items as a unit.
"""

from datetime import datetime, timezone
from typing import Any

from app.exceptions import CompanyNotFoundError, WorkerNotFoundError
from app.models.actor import Actor
from app.services.base_service import BaseService


class CrewNotFoundError(Exception):
    """Raised when a crew cannot be found."""

    def __init__(self, crew_id: str) -> None:
        self.crew_id = crew_id
        super().__init__(f"Crew not found: {crew_id}")


class CrewService(BaseService):
    """Manages Crew nodes in the Neo4j graph.

    Workers join crews via (Worker)-[:MEMBER_OF]->(Crew).
    A lead is designated via (Crew)-[:LED_BY]->(Worker).
    Crews are scoped to a company (implicitly via their members' company relationships).
    """

    def create(
        self,
        company_id: str,
        data: dict[str, Any],
        user_id: str,
    ) -> dict[str, Any]:
        """Create a new crew for a company.

        Args:
            company_id: The owning company ID.
            data: Crew fields — name, status.
            user_id: Clerk user ID of the creating user.

        Returns:
            The created crew dict.

        Raises:
            CompanyNotFoundError: If the company does not exist.
        """
        actor = Actor.human(user_id)
        crew_id = self._generate_id("crew")

        props: dict[str, Any] = {
            "id": crew_id,
            "name": data.get("name", ""),
            "status": data.get("status", "active"),
            "company_id": company_id,
            "deleted": False,
            **self._provenance_create(actor),
        }

        result = self._write_tx_single(
            """
            MATCH (c:Company {id: $company_id})
            CREATE (crew:Crew $props)
            RETURN crew {.*} AS crew
            """,
            {"company_id": company_id, "props": props},
        )
        if result is None:
            raise CompanyNotFoundError(company_id)
        self._emit_audit(
            event_type="entity.created",
            entity_id=crew_id,
            entity_type="Crew",
            company_id=company_id,
            actor=actor,
            summary=f"Created crew '{data.get('name', '')}'",
        )
        return result["crew"]

    def get(self, company_id: str, crew_id: str) -> dict[str, Any]:
        """Fetch a single crew with its members.

        Args:
            company_id: The owning company ID.
            crew_id: The crew ID to fetch.

        Returns:
            The crew dict including 'members' list and optional 'lead'.

        Raises:
            CrewNotFoundError: If the crew does not exist or is soft-deleted.
        """
        result = self._read_tx_single(
            """
            MATCH (crew:Crew {id: $crew_id, company_id: $company_id})
            WHERE crew.deleted = false
            OPTIONAL MATCH (w:Worker)-[:MEMBER_OF]->(crew)
            OPTIONAL MATCH (crew)-[:LED_BY]->(lead:Worker)
            WITH crew, collect(w {.id, .name, .trade}) AS members, lead
            RETURN crew {.*, members: members, lead_id: lead.id} AS crew
            """,
            {"company_id": company_id, "crew_id": crew_id},
        )
        if result is None:
            raise CrewNotFoundError(crew_id)
        return result["crew"]

    def list_by_company(
        self,
        company_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> dict[str, Any]:
        """List all crews for a company.

        Args:
            company_id: The owning company ID.
            limit: Maximum number of crews to return.
            offset: Number of crews to skip.

        Returns:
            A dict with 'crews' list and 'total' count.
        """
        params: dict[str, Any] = {
            "company_id": company_id,
            "limit": limit,
            "offset": offset,
        }

        count_result = self._read_tx_single(
            """
            MATCH (crew:Crew {company_id: $company_id})
            WHERE crew.deleted = false
            RETURN count(crew) AS total
            """,
            params,
        )
        total = count_result["total"] if count_result else 0

        results = self._read_tx(
            """
            MATCH (crew:Crew {company_id: $company_id})
            WHERE crew.deleted = false
            OPTIONAL MATCH (crew)-[:LED_BY]->(lead:Worker)
            RETURN crew {.*, lead_id: lead.id} AS crew
            ORDER BY crew.name ASC
            SKIP $offset LIMIT $limit
            """,
            params,
        )

        return {"crews": [r["crew"] for r in results], "total": total}

    def add_member(
        self,
        company_id: str,
        crew_id: str,
        worker_id: str,
        user_id: str,
    ) -> dict[str, Any]:
        """Add a worker to a crew.

        Uses MERGE so that duplicate additions are idempotent.

        Args:
            company_id: The owning company ID.
            crew_id: The crew ID.
            worker_id: The worker ID to add.
            user_id: Clerk user ID performing the action.

        Returns:
            The updated crew dict.

        Raises:
            CrewNotFoundError: If the crew does not exist.
            WorkerNotFoundError: If the worker does not exist.
        """
        actor = Actor.human(user_id)
        result = self._write_tx_single(
            """
            MATCH (crew:Crew {id: $crew_id, company_id: $company_id})
            WHERE crew.deleted = false
            MATCH (w:Worker {id: $worker_id})
            MERGE (w)-[:MEMBER_OF]->(crew)
            SET crew += $provenance
            RETURN crew {.*, member_id: w.id} AS crew
            """,
            {
                "company_id": company_id,
                "crew_id": crew_id,
                "worker_id": worker_id,
                "provenance": self._provenance_update(actor),
            },
        )
        if result is None:
            raise CrewNotFoundError(crew_id)
        self._emit_audit(
            event_type="relationship.added",
            entity_id=crew_id,
            entity_type="Crew",
            company_id=company_id,
            actor=actor,
            summary=f"Added worker {worker_id} to crew",
            related_entity_ids=[worker_id],
        )
        return result["crew"]

    def remove_member(
        self,
        company_id: str,
        crew_id: str,
        worker_id: str,
        user_id: str,
    ) -> None:
        """Remove a worker from a crew.

        Args:
            company_id: The owning company ID.
            crew_id: The crew ID.
            worker_id: The worker ID to remove.
            user_id: Clerk user ID performing the action.

        Raises:
            CrewNotFoundError: If the crew does not exist.
        """
        actor = Actor.human(user_id)
        result = self._write_tx_single(
            """
            MATCH (crew:Crew {id: $crew_id, company_id: $company_id})
            WHERE crew.deleted = false
            MATCH (w:Worker {id: $worker_id})-[r:MEMBER_OF]->(crew)
            DELETE r
            SET crew += $provenance
            RETURN crew.id AS id
            """,
            {
                "company_id": company_id,
                "crew_id": crew_id,
                "worker_id": worker_id,
                "provenance": self._provenance_update(actor),
            },
        )
        if result is None:
            raise CrewNotFoundError(crew_id)
        self._emit_audit(
            event_type="relationship.removed",
            entity_id=crew_id,
            entity_type="Crew",
            company_id=company_id,
            actor=actor,
            summary=f"Removed worker {worker_id} from crew",
            related_entity_ids=[worker_id],
        )

    def set_lead(
        self,
        company_id: str,
        crew_id: str,
        worker_id: str,
        user_id: str,
    ) -> dict[str, Any]:
        """Set or replace the crew lead.

        Removes any existing LED_BY relationship before creating the new one.

        Args:
            company_id: The owning company ID.
            crew_id: The crew ID.
            worker_id: The worker ID to designate as lead.
            user_id: Clerk user ID performing the action.

        Returns:
            The updated crew dict.

        Raises:
            CrewNotFoundError: If the crew does not exist.
        """
        actor = Actor.human(user_id)
        result = self._write_tx_single(
            """
            MATCH (crew:Crew {id: $crew_id, company_id: $company_id})
            WHERE crew.deleted = false
            MATCH (w:Worker {id: $worker_id})
            OPTIONAL MATCH (crew)-[old:LED_BY]->() DELETE old
            CREATE (crew)-[:LED_BY]->(w)
            SET crew += $provenance
            RETURN crew {.*, lead_id: w.id} AS crew
            """,
            {
                "company_id": company_id,
                "crew_id": crew_id,
                "worker_id": worker_id,
                "provenance": self._provenance_update(actor),
            },
        )
        if result is None:
            raise CrewNotFoundError(crew_id)
        self._emit_audit(
            event_type="entity.updated",
            entity_id=crew_id,
            entity_type="Crew",
            company_id=company_id,
            actor=actor,
            summary=f"Set crew lead to worker {worker_id}",
            related_entity_ids=[worker_id],
        )
        return result["crew"]

    def archive(self, company_id: str, crew_id: str, user_id: str) -> None:
        """Soft-delete a crew.

        Does NOT remove member relationships — those persist for history.

        Args:
            company_id: The owning company ID.
            crew_id: The crew ID to archive.
            user_id: Clerk user ID of the deleting user.

        Raises:
            CrewNotFoundError: If the crew does not exist.
        """
        result = self._write_tx_single(
            """
            MATCH (crew:Crew {id: $crew_id, company_id: $company_id})
            WHERE crew.deleted = false
            SET crew.deleted = true, crew.updated_at = $now
            RETURN crew.id AS id
            """,
            {
                "company_id": company_id,
                "crew_id": crew_id,
                "now": datetime.now(timezone.utc).isoformat(),
            },
        )
        if result is None:
            raise CrewNotFoundError(crew_id)
        self._emit_audit(
            event_type="entity.archived",
            entity_id=crew_id,
            entity_type="Crew",
            company_id=company_id,
            actor=Actor.human(user_id),
            summary=f"Archived crew {crew_id}",
        )
