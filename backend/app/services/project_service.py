"""Project CRUD service (Neo4j-backed)."""

from datetime import datetime, timedelta, timezone
from typing import Any

from app.exceptions import CompanyNotFoundError, ProjectNotFoundError
from app.models.actor import Actor
from app.models.project import (
    Project,
    ProjectCreate,
    ProjectStatus,
    ProjectUpdate,
)
from app.services.base_service import BaseService


class ProjectService(BaseService):
    """Manages construction projects as Neo4j nodes.

    Projects connect to companies via (Company)-[:OWNS_PROJECT]->(Project).
    company_id is NOT stored on the node — it is derived from the relationship.
    """

    def _verify_company_exists(self, company_id: str) -> None:
        """Verify that the parent company exists.

        Args:
            company_id: The company ID to check.

        Raises:
            CompanyNotFoundError: If the company does not exist.
        """
        result = self._read_tx_single(
            "MATCH (c:Company {id: $id}) RETURN c.id AS id",
            {"id": company_id},
        )
        if result is None:
            raise CompanyNotFoundError(company_id)

    def create(self, company_id: str, data: ProjectCreate, user_id: str) -> Project:
        """Create a new project linked to a company.

        Args:
            company_id: The owning company ID.
            data: Validated project creation data.
            user_id: Clerk user ID of the creating user.

        Returns:
            The created Project with all fields populated.

        Raises:
            CompanyNotFoundError: If the company does not exist.
        """
        actor = Actor.human(user_id)
        project_id = self._generate_id("proj")

        props: dict[str, Any] = {
            "id": project_id,
            "name": data.name,
            "address": data.address,
            "client_name": data.client_name,
            "project_type": data.project_type,
            "trade_types": data.trade_types,
            "start_date": data.start_date.isoformat() if data.start_date else None,
            "end_date": data.end_date.isoformat() if data.end_date else None,
            "estimated_workers": data.estimated_workers,
            "description": data.description,
            "special_hazards": data.special_hazards,
            "nearest_hospital": data.nearest_hospital,
            "emergency_contact_name": data.emergency_contact_name,
            "emergency_contact_phone": data.emergency_contact_phone,
            "status": ProjectStatus.ACTIVE.value,
            "compliance_score": 0,
            "deleted": False,
            **self._provenance_create(actor),
        }

        result = self._write_tx_single(
            """
            MATCH (c:Company {id: $company_id})
            CREATE (p:Project $props)
            CREATE (c)-[:OWNS_PROJECT]->(p)
            RETURN p {.*, company_id: c.id} AS project
            """,
            {"company_id": company_id, "props": props},
        )
        if result is None:
            raise CompanyNotFoundError(company_id)
        return Project(**result["project"])

    def get(self, company_id: str, project_id: str) -> Project:
        """Fetch a single project.

        Args:
            company_id: The owning company ID.
            project_id: The project ID to fetch.

        Returns:
            The Project model.

        Raises:
            ProjectNotFoundError: If the project does not exist or is soft-deleted.
        """
        result = self._read_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
            WHERE p.deleted = false
            RETURN p {.*, company_id: c.id} AS project
            """,
            {"company_id": company_id, "project_id": project_id},
        )
        if result is None:
            raise ProjectNotFoundError(project_id)
        return Project(**result["project"])

    def list_projects(
        self,
        company_id: str,
        status: ProjectStatus | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> dict:
        """List projects for a company with optional filters and pagination.

        Args:
            company_id: The owning company ID.
            status: Filter by project status.
            limit: Maximum number of projects to return.
            offset: Number of projects to skip.

        Returns:
            A dict with 'projects' list and 'total' count.
        """
        where_clauses = ["p.deleted = false"]
        params: dict[str, Any] = {
            "company_id": company_id,
            "limit": limit,
            "offset": offset,
        }

        if status is not None:
            where_clauses.append("p.status = $status")
            params["status"] = status.value

        where_str = " AND ".join(where_clauses)

        count_result = self._read_tx_single(
            f"""
            MATCH (c:Company {{id: $company_id}})-[:OWNS_PROJECT]->(p:Project)
            WHERE {where_str}
            RETURN count(p) AS total
            """,
            params,
        )
        total = count_result["total"] if count_result else 0

        results = self._read_tx(
            f"""
            MATCH (c:Company {{id: $company_id}})-[:OWNS_PROJECT]->(p:Project)
            WHERE {where_str}
            RETURN p {{.*, company_id: c.id}} AS project
            ORDER BY p.created_at DESC
            SKIP $offset LIMIT $limit
            """,
            params,
        )

        projects = [Project(**r["project"]) for r in results]
        return {"projects": projects, "total": total}

    def update(
        self, company_id: str, project_id: str, data: ProjectUpdate, user_id: str
    ) -> Project:
        """Update an existing project.

        Args:
            company_id: The owning company ID.
            project_id: The project ID to update.
            data: Fields to update (only non-None fields are applied).
            user_id: Clerk user ID of the updating user.

        Returns:
            The updated Project model.

        Raises:
            ProjectNotFoundError: If the project does not exist or is soft-deleted.
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
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
            WHERE p.deleted = false
            SET p += $props
            RETURN p {.*, company_id: c.id} AS project
            """,
            {"company_id": company_id, "project_id": project_id, "props": update_fields},
        )
        if result is None:
            raise ProjectNotFoundError(project_id)
        return Project(**result["project"])

    def delete(self, company_id: str, project_id: str) -> None:
        """Soft-delete a project by setting the deleted flag.

        Args:
            company_id: The owning company ID.
            project_id: The project ID to delete.

        Raises:
            ProjectNotFoundError: If the project does not exist.
        """
        result = self._write_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
            WHERE p.deleted = false
            SET p.deleted = true, p.updated_at = $now
            RETURN p.id AS id
            """,
            {
                "company_id": company_id,
                "project_id": project_id,
                "now": datetime.now(timezone.utc).isoformat(),
            },
        )
        if result is None:
            raise ProjectNotFoundError(project_id)

    def get_compliance_score(self, company_id: str, project_id: str) -> int:
        """Calculate a compliance score (0-100) for a project.

        Factors:
        - Recent inspections (last 7 days) contribute up to 40 points
        - Inspection pass rate contributes up to 40 points
        - Document completeness contributes up to 20 points

        Args:
            company_id: The owning company ID.
            project_id: The project ID.

        Returns:
            An integer score from 0 to 100.
        """
        now = datetime.now(timezone.utc)
        seven_days_ago = (now - timedelta(days=7)).isoformat()

        result = self._read_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
            OPTIONAL MATCH (p)-[:HAS_INSPECTION]->(i:Inspection)
            WHERE i.deleted = false
            WITH c, p,
                 count(i) AS total_inspections,
                 sum(CASE WHEN i.created_at >= $cutoff THEN 1 ELSE 0 END) AS recent_count,
                 sum(CASE WHEN i.overall_status = 'pass' THEN 1 ELSE 0 END) AS pass_count
            OPTIONAL MATCH (c)-[:HAS_DOCUMENT]->(d:Document)
            WHERE d.deleted = false
            WITH total_inspections, recent_count, pass_count, count(d) AS doc_count
            RETURN total_inspections, recent_count, pass_count, doc_count
            """,
            {
                "company_id": company_id,
                "project_id": project_id,
                "cutoff": seven_days_ago,
            },
        )
        if result is None:
            return 0

        score = 0

        recent_count = result["recent_count"]
        if recent_count >= 3:
            score += 40
        elif recent_count >= 1:
            score += 20

        total_inspections = result["total_inspections"]
        if total_inspections > 0:
            pass_rate = result["pass_count"] / total_inspections
            score += int(pass_rate * 40)

        doc_count = result["doc_count"]
        if doc_count >= 3:
            score += 20
        elif doc_count >= 1:
            score += 10

        return min(score, 100)
