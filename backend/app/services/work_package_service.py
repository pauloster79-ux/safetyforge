"""WorkPackage CRUD service (Neo4j-backed).

WorkPackages are optional groupings of WorkItems within a project,
useful for organising scope into logical phases or trades.
"""

from datetime import datetime, timezone
from typing import Any

from app.exceptions import ProjectNotFoundError
from app.models.actor import Actor
from app.services.base_service import BaseService


class WorkPackageNotFoundError(Exception):
    """Raised when a work package cannot be found."""

    def __init__(self, work_package_id: str) -> None:
        self.work_package_id = work_package_id
        super().__init__(f"Work package not found: {work_package_id}")


class WorkPackageService(BaseService):
    """Manages WorkPackage nodes in the Neo4j graph.

    WorkPackages connect to projects via (Project)-[:HAS_WORK_PACKAGE]->(WorkPackage)
    and group work items via (WorkPackage)-[:CONTAINS]->(WorkItem).
    """

    def create(
        self,
        company_id: str,
        project_id: str,
        data: dict[str, Any],
        user_id: str,
    ) -> dict[str, Any]:
        """Create a new work package on a project.

        Args:
            company_id: The owning company ID (used for access scope).
            project_id: The parent project ID.
            data: Work package fields — name, description, sort_order, status.
            user_id: Clerk user ID of the creating user.

        Returns:
            The created work package dict.

        Raises:
            ProjectNotFoundError: If the project does not exist under this company.
        """
        actor = Actor.human(user_id)
        wp_id = self._generate_id("wp")

        props: dict[str, Any] = {
            "id": wp_id,
            "name": data.get("name", ""),
            "description": data.get("description"),
            "sort_order": data.get("sort_order", 0),
            "status": data.get("status", "active"),
            "deleted": False,
            **self._provenance_create(actor),
        }

        result = self._write_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
            CREATE (wp:WorkPackage $props)
            CREATE (p)-[:HAS_WORK_PACKAGE]->(wp)
            RETURN wp {.*, project_id: p.id, company_id: c.id} AS work_package
            """,
            {"company_id": company_id, "project_id": project_id, "props": props},
        )
        if result is None:
            raise ProjectNotFoundError(project_id)
        self._emit_audit(
            event_type="entity.created",
            entity_id=wp_id,
            entity_type="WorkPackage",
            company_id=company_id,
            actor=actor,
            summary=f"Created work package '{data.get('name', '')}'",
            related_entity_ids=[project_id],
        )
        return result["work_package"]

    def get(
        self, company_id: str, project_id: str, work_package_id: str
    ) -> dict[str, Any]:
        """Fetch a single work package.

        Args:
            company_id: The owning company ID.
            project_id: The parent project ID.
            work_package_id: The work package ID to fetch.

        Returns:
            The work package dict.

        Raises:
            WorkPackageNotFoundError: If the work package does not exist or is soft-deleted.
        """
        result = self._read_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
                  -[:HAS_WORK_PACKAGE]->(wp:WorkPackage {id: $work_package_id})
            WHERE wp.deleted = false
            RETURN wp {.*, project_id: p.id, company_id: c.id} AS work_package
            """,
            {
                "company_id": company_id,
                "project_id": project_id,
                "work_package_id": work_package_id,
            },
        )
        if result is None:
            raise WorkPackageNotFoundError(work_package_id)
        return result["work_package"]

    def list_by_project(
        self,
        company_id: str,
        project_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> dict[str, Any]:
        """List work packages for a project, ordered by sort_order.

        Args:
            company_id: The owning company ID.
            project_id: The parent project ID.
            limit: Maximum number of packages to return.
            offset: Number of packages to skip.

        Returns:
            A dict with 'work_packages' list and 'total' count.
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
                  -[:HAS_WORK_PACKAGE]->(wp:WorkPackage)
            WHERE wp.deleted = false
            RETURN count(wp) AS total
            """,
            params,
        )
        total = count_result["total"] if count_result else 0

        results = self._read_tx(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
                  -[:HAS_WORK_PACKAGE]->(wp:WorkPackage)
            WHERE wp.deleted = false
            RETURN wp {.*, project_id: p.id, company_id: c.id} AS work_package
            ORDER BY wp.sort_order ASC, wp.created_at ASC
            SKIP $offset LIMIT $limit
            """,
            params,
        )

        return {"work_packages": [r["work_package"] for r in results], "total": total}

    def update(
        self,
        company_id: str,
        project_id: str,
        work_package_id: str,
        data: dict[str, Any],
        user_id: str,
    ) -> dict[str, Any]:
        """Update fields on an existing work package.

        Args:
            company_id: The owning company ID.
            project_id: The parent project ID.
            work_package_id: The work package ID to update.
            data: Fields to update (name, description, sort_order, status).
            user_id: Clerk user ID of the updating user.

        Returns:
            The updated work package dict.

        Raises:
            WorkPackageNotFoundError: If the work package does not exist or is soft-deleted.
        """
        actor = Actor.human(user_id)
        update_fields = {k: v for k, v in data.items() if v is not None}
        update_fields.update(self._provenance_update(actor))

        result = self._write_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
                  -[:HAS_WORK_PACKAGE]->(wp:WorkPackage {id: $work_package_id})
            WHERE wp.deleted = false
            SET wp += $props
            RETURN wp {.*, project_id: p.id, company_id: c.id} AS work_package
            """,
            {
                "company_id": company_id,
                "project_id": project_id,
                "work_package_id": work_package_id,
                "props": update_fields,
            },
        )
        if result is None:
            raise WorkPackageNotFoundError(work_package_id)
        self._emit_audit(
            event_type="entity.updated",
            entity_id=work_package_id,
            entity_type="WorkPackage",
            company_id=company_id,
            actor=actor,
            summary=f"Updated work package {work_package_id}",
        )
        return result["work_package"]

    def archive(
        self,
        company_id: str,
        project_id: str,
        work_package_id: str,
        user_id: str,
    ) -> None:
        """Soft-delete a work package.

        Does NOT cascade to contained WorkItems — they remain on the project.

        Args:
            company_id: The owning company ID.
            project_id: The parent project ID.
            work_package_id: The work package ID to archive.
            user_id: Clerk user ID of the deleting user.

        Raises:
            WorkPackageNotFoundError: If the work package does not exist.
        """
        result = self._write_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
                  -[:HAS_WORK_PACKAGE]->(wp:WorkPackage {id: $work_package_id})
            WHERE wp.deleted = false
            SET wp.deleted = true, wp.updated_at = $now
            RETURN wp.id AS id
            """,
            {
                "company_id": company_id,
                "project_id": project_id,
                "work_package_id": work_package_id,
                "now": datetime.now(timezone.utc).isoformat(),
            },
        )
        if result is None:
            raise WorkPackageNotFoundError(work_package_id)
        self._emit_audit(
            event_type="entity.archived",
            entity_id=work_package_id,
            entity_type="WorkPackage",
            company_id=company_id,
            actor=Actor.human(user_id),
            summary=f"Archived work package {work_package_id}",
        )
