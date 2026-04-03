"""Project CRUD service against Firestore."""

import secrets
from datetime import datetime, timezone
from typing import Any

from google.cloud import firestore

from app.exceptions import CompanyNotFoundError, ProjectNotFoundError
from app.models.project import (
    Project,
    ProjectCreate,
    ProjectStatus,
    ProjectUpdate,
)


class ProjectService:
    """Manages construction projects in Firestore.

    Args:
        db: Firestore client instance.
    """

    def __init__(self, db: firestore.Client) -> None:
        self.db = db

    def _company_ref(self, company_id: str) -> firestore.DocumentReference:
        """Return a reference to the company document."""
        return self.db.collection("companies").document(company_id)

    def _collection(self, company_id: str) -> firestore.CollectionReference:
        """Return the projects subcollection for a company.

        Args:
            company_id: The parent company ID.

        Returns:
            Firestore collection reference.
        """
        return self._company_ref(company_id).collection("projects")

    def _generate_id(self) -> str:
        """Generate a unique project ID.

        Returns:
            A prefixed hex ID string.
        """
        return f"proj_{secrets.token_hex(8)}"

    def _verify_company_exists(self, company_id: str) -> None:
        """Verify that the parent company exists.

        Args:
            company_id: The company ID to check.

        Raises:
            CompanyNotFoundError: If the company does not exist.
        """
        if not self._company_ref(company_id).get().exists:
            raise CompanyNotFoundError(company_id)

    def create(self, company_id: str, data: ProjectCreate, user_id: str) -> Project:
        """Create a new project.

        Args:
            company_id: The owning company ID.
            data: Validated project creation data.
            user_id: Firebase UID of the creating user.

        Returns:
            The created Project with all fields populated.

        Raises:
            CompanyNotFoundError: If the company does not exist.
        """
        self._verify_company_exists(company_id)

        now = datetime.now(timezone.utc)
        project_id = self._generate_id()

        project_dict: dict[str, Any] = {
            "id": project_id,
            "company_id": company_id,
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
            "created_at": now,
            "created_by": user_id,
            "updated_at": now,
            "updated_by": user_id,
            "deleted": False,
        }

        self._collection(company_id).document(project_id).set(project_dict)
        return Project(**project_dict)

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
        doc = self._collection(company_id).document(project_id).get()
        if not doc.exists:
            raise ProjectNotFoundError(project_id)

        data = doc.to_dict()
        if data.get("deleted", False):
            raise ProjectNotFoundError(project_id)

        return Project(**data)

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
        base_query: firestore.Query = self._collection(company_id).where(
            "deleted", "==", False
        )

        if status is not None:
            base_query = base_query.where("status", "==", status.value)

        # Count total matching projects
        all_docs = [Project(**doc.to_dict()) for doc in base_query.stream()]
        total = len(all_docs)

        # Apply sorting, offset, and limit
        paginated_query = base_query.order_by(
            "created_at", direction=firestore.Query.DESCENDING
        )
        paginated_query = paginated_query.offset(offset).limit(limit)

        projects = [Project(**doc.to_dict()) for doc in paginated_query.stream()]

        return {"projects": projects, "total": total}

    def update(
        self, company_id: str, project_id: str, data: ProjectUpdate, user_id: str
    ) -> Project:
        """Update an existing project.

        Args:
            company_id: The owning company ID.
            project_id: The project ID to update.
            data: Fields to update (only non-None fields are applied).
            user_id: Firebase UID of the updating user.

        Returns:
            The updated Project model.

        Raises:
            ProjectNotFoundError: If the project does not exist or is soft-deleted.
        """
        doc_ref = self._collection(company_id).document(project_id)
        doc = doc_ref.get()

        if not doc.exists or doc.to_dict().get("deleted", False):
            raise ProjectNotFoundError(project_id)

        update_data: dict[str, Any] = {}
        for field_name, value in data.model_dump(exclude_none=True).items():
            if field_name == "status" and value is not None:
                update_data[field_name] = value.value if hasattr(value, "value") else value
            elif field_name in ("start_date", "end_date") and value is not None:
                update_data[field_name] = value.isoformat() if hasattr(value, "isoformat") else value
            else:
                update_data[field_name] = value

        if not update_data:
            return Project(**doc.to_dict())

        update_data["updated_at"] = datetime.now(timezone.utc)
        update_data["updated_by"] = user_id

        doc_ref.update(update_data)

        updated_doc = doc_ref.get()
        return Project(**updated_doc.to_dict())

    def delete(self, company_id: str, project_id: str) -> None:
        """Soft-delete a project by setting the deleted flag.

        Args:
            company_id: The owning company ID.
            project_id: The project ID to delete.

        Raises:
            ProjectNotFoundError: If the project does not exist.
        """
        doc_ref = self._collection(company_id).document(project_id)
        doc = doc_ref.get()

        if not doc.exists or doc.to_dict().get("deleted", False):
            raise ProjectNotFoundError(project_id)

        doc_ref.update(
            {
                "deleted": True,
                "updated_at": datetime.now(timezone.utc),
            }
        )

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
        from datetime import timedelta

        now = datetime.now(timezone.utc)
        seven_days_ago = now - timedelta(days=7)

        # Get recent inspections
        inspections_ref = (
            self._company_ref(company_id)
            .collection("projects")
            .document(project_id)
            .collection("inspections")
        )

        all_inspections = list(
            inspections_ref.where("deleted", "==", False).stream()
        )

        score = 0

        # Factor 1: Recent inspections (up to 40 points)
        recent_inspections = []
        for insp in all_inspections:
            data = insp.to_dict()
            created_at = data.get("created_at")
            if created_at is not None and created_at >= seven_days_ago:
                recent_inspections.append(data)

        if recent_inspections:
            # At least 1 recent inspection = 20 pts, 3+ = 40 pts
            if len(recent_inspections) >= 3:
                score += 40
            elif len(recent_inspections) >= 1:
                score += 20

        # Factor 2: Pass rate of all inspections (up to 40 points)
        if all_inspections:
            pass_count = sum(
                1
                for insp in all_inspections
                if insp.to_dict().get("overall_status") == "pass"
            )
            pass_rate = pass_count / len(all_inspections)
            score += int(pass_rate * 40)

        # Factor 3: Document completeness (up to 20 points)
        docs_ref = self._company_ref(company_id).collection("documents")
        doc_count = sum(
            1 for _ in docs_ref.where("deleted", "==", False).limit(5).stream()
        )
        if doc_count >= 3:
            score += 20
        elif doc_count >= 1:
            score += 10

        return min(score, 100)
