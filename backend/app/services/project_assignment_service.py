"""Project assignment service (Neo4j-backed).

Manages worker and equipment assignments to projects.
"""

from datetime import datetime, timezone
from typing import Any

from app.exceptions import AssignmentNotFoundError, CompanyNotFoundError
from app.models.actor import Actor
from app.models.project_assignment import (
    AssignmentStatus,
    ProjectAssignment,
    ProjectAssignmentCreate,
    ProjectAssignmentUpdate,
    ResourceType,
)
from app.services.base_service import BaseService


class ProjectAssignmentService(BaseService):
    """Manages project resource assignments as Neo4j nodes.

    Assignments connect to companies via (Company)-[:HAS_ASSIGNMENT]->(ProjectAssignment).
    project_id and resource_id are stored as node properties for filtering.
    """

    def create(
        self, company_id: str, data: ProjectAssignmentCreate, user_id: str
    ) -> ProjectAssignment:
        """Create a new project assignment.

        Args:
            company_id: The owning company ID.
            data: Validated assignment creation data.
            user_id: Clerk user ID of the creating user.

        Returns:
            The created ProjectAssignment with all fields populated.

        Raises:
            CompanyNotFoundError: If the company does not exist.
        """
        actor = Actor.human(user_id)
        assignment_id = self._generate_id("asgn")

        props: dict[str, Any] = {
            "id": assignment_id,
            "resource_type": data.resource_type.value,
            "resource_id": data.resource_id,
            "project_id": data.project_id,
            "role": data.role,
            "start_date": data.start_date.isoformat(),
            "end_date": data.end_date.isoformat() if data.end_date else None,
            "status": data.status.value,
            "notes": data.notes,
            "deleted": False,
            **self._provenance_create(actor),
        }

        result = self._write_tx_single(
            """
            MATCH (c:Company {id: $company_id})
            CREATE (a:ProjectAssignment $props)
            CREATE (c)-[:HAS_ASSIGNMENT]->(a)
            RETURN a {.*, company_id: c.id} AS assignment
            """,
            {"company_id": company_id, "props": props},
        )
        if result is None:
            raise CompanyNotFoundError(company_id)
        return ProjectAssignment(**result["assignment"])

    def get(self, company_id: str, assignment_id: str) -> ProjectAssignment:
        """Fetch a single project assignment.

        Args:
            company_id: The owning company ID.
            assignment_id: The assignment ID to fetch.

        Returns:
            The ProjectAssignment model.

        Raises:
            AssignmentNotFoundError: If not found or soft-deleted.
        """
        result = self._read_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:HAS_ASSIGNMENT]->(a:ProjectAssignment {id: $id})
            WHERE a.deleted = false
            RETURN a {.*, company_id: c.id} AS assignment
            """,
            {"company_id": company_id, "id": assignment_id},
        )
        if result is None:
            raise AssignmentNotFoundError(assignment_id)
        return ProjectAssignment(**result["assignment"])

    def update(
        self,
        company_id: str,
        assignment_id: str,
        data: ProjectAssignmentUpdate,
        user_id: str,
    ) -> ProjectAssignment:
        """Update an existing project assignment.

        Args:
            company_id: The owning company ID.
            assignment_id: The assignment ID to update.
            data: Validated update data (only non-None fields are applied).
            user_id: Clerk user ID of the updating user.

        Returns:
            The updated ProjectAssignment.

        Raises:
            AssignmentNotFoundError: If not found or soft-deleted.
        """
        update_fields: dict[str, Any] = {}
        for field_name, value in data.model_dump(exclude_none=True).items():
            if field_name == "status" and value is not None:
                update_fields[field_name] = value.value if hasattr(value, "value") else value
            elif field_name in ("start_date", "end_date") and value is not None:
                update_fields[field_name] = value.isoformat() if hasattr(value, "isoformat") else value
            else:
                update_fields[field_name] = value

        actor = Actor.human(user_id)
        update_fields.update(self._provenance_update(actor))

        result = self._write_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:HAS_ASSIGNMENT]->(a:ProjectAssignment {id: $id})
            WHERE a.deleted = false
            SET a += $props
            RETURN a {.*, company_id: c.id} AS assignment
            """,
            {"company_id": company_id, "id": assignment_id, "props": update_fields},
        )
        if result is None:
            raise AssignmentNotFoundError(assignment_id)
        return ProjectAssignment(**result["assignment"])

    def delete(self, company_id: str, assignment_id: str) -> None:
        """Soft-delete a project assignment.

        Args:
            company_id: The owning company ID.
            assignment_id: The assignment ID to delete.

        Raises:
            AssignmentNotFoundError: If not found or already deleted.
        """
        result = self._write_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:HAS_ASSIGNMENT]->(a:ProjectAssignment {id: $id})
            WHERE a.deleted = false
            SET a.deleted = true, a.updated_at = $now
            RETURN a.id AS id
            """,
            {
                "company_id": company_id,
                "id": assignment_id,
                "now": datetime.now(timezone.utc).isoformat(),
            },
        )
        if result is None:
            raise AssignmentNotFoundError(assignment_id)

    def list_assignments(
        self,
        company_id: str,
        project_id: str | None = None,
        resource_type: ResourceType | None = None,
        resource_id: str | None = None,
        status: AssignmentStatus | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> dict:
        """List project assignments with optional filters.

        Args:
            company_id: The owning company ID.
            project_id: Filter by project.
            resource_type: Filter by worker or equipment.
            resource_id: Filter by specific resource.
            status: Filter by assignment status.
            limit: Max results to return.
            offset: Number of results to skip.

        Returns:
            Dict with 'assignments' list and 'total' count.
        """
        where_clauses = ["a.deleted = false"]
        params: dict[str, Any] = {
            "company_id": company_id,
            "limit": limit,
            "offset": offset,
        }

        if project_id:
            where_clauses.append("a.project_id = $project_id")
            params["project_id"] = project_id
        if resource_type:
            where_clauses.append("a.resource_type = $resource_type")
            params["resource_type"] = resource_type.value
        if resource_id:
            where_clauses.append("a.resource_id = $resource_id")
            params["resource_id"] = resource_id
        if status:
            where_clauses.append("a.status = $status")
            params["status"] = status.value

        where_str = " AND ".join(where_clauses)

        count_result = self._read_tx_single(
            f"""
            MATCH (c:Company {{id: $company_id}})-[:HAS_ASSIGNMENT]->(a:ProjectAssignment)
            WHERE {where_str}
            RETURN count(a) AS total
            """,
            params,
        )
        total = count_result["total"] if count_result else 0

        results = self._read_tx(
            f"""
            MATCH (c:Company {{id: $company_id}})-[:HAS_ASSIGNMENT]->(a:ProjectAssignment)
            WHERE {where_str}
            RETURN a {{.*, company_id: c.id}} AS assignment
            ORDER BY a.start_date DESC
            SKIP $offset LIMIT $limit
            """,
            params,
        )

        assignments = [ProjectAssignment(**r["assignment"]) for r in results]
        return {"assignments": assignments, "total": total}
