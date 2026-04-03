"""Inspection CRUD service against Firestore."""

import secrets
from datetime import date, datetime, timezone
from typing import Any

from google.cloud import firestore

from app.exceptions import InspectionNotFoundError, ProjectNotFoundError
from app.models.inspection import (
    Inspection,
    InspectionCreate,
    InspectionItem,
    InspectionStatus,
    InspectionType,
    InspectionUpdate,
)


class InspectionService:
    """Manages daily inspection logs in Firestore.

    Args:
        db: Firestore client instance.
    """

    def __init__(self, db: firestore.Client) -> None:
        self.db = db

    def _project_ref(
        self, company_id: str, project_id: str
    ) -> firestore.DocumentReference:
        """Return a reference to the project document."""
        return (
            self.db.collection("companies")
            .document(company_id)
            .collection("projects")
            .document(project_id)
        )

    def _collection(
        self, company_id: str, project_id: str
    ) -> firestore.CollectionReference:
        """Return the inspections subcollection for a project.

        Args:
            company_id: The parent company ID.
            project_id: The parent project ID.

        Returns:
            Firestore collection reference.
        """
        return self._project_ref(company_id, project_id).collection("inspections")

    def _generate_id(self) -> str:
        """Generate a unique inspection ID.

        Returns:
            A prefixed hex ID string.
        """
        return f"insp_{secrets.token_hex(8)}"

    def _verify_project_exists(self, company_id: str, project_id: str) -> None:
        """Verify that the parent project exists and is not deleted.

        Args:
            company_id: The company ID.
            project_id: The project ID to check.

        Raises:
            ProjectNotFoundError: If the project does not exist or is soft-deleted.
        """
        doc = self._project_ref(company_id, project_id).get()
        if not doc.exists:
            raise ProjectNotFoundError(project_id)
        if doc.to_dict().get("deleted", False):
            raise ProjectNotFoundError(project_id)

    @staticmethod
    def calculate_overall_status(items: list[InspectionItem]) -> InspectionStatus:
        """Calculate the overall inspection status from checklist items.

        Rules:
        - If any item has status 'fail', overall is FAIL.
        - If all items are 'pass' or 'na', overall is PASS.
        - Otherwise, overall is PARTIAL.
        - If no items, default to PASS.

        Args:
            items: List of inspection checklist items.

        Returns:
            The calculated InspectionStatus.
        """
        if not items:
            return InspectionStatus.PASS

        statuses = [item.status for item in items]

        if any(s == "fail" for s in statuses):
            return InspectionStatus.FAIL

        if all(s in ("pass", "na") for s in statuses):
            return InspectionStatus.PASS

        return InspectionStatus.PARTIAL

    def create(
        self,
        company_id: str,
        project_id: str,
        data: InspectionCreate,
        user_id: str,
    ) -> Inspection:
        """Create a new inspection.

        Args:
            company_id: The owning company ID.
            project_id: The parent project ID.
            data: Validated inspection creation data.
            user_id: Firebase UID of the creating user.

        Returns:
            The created Inspection with all fields populated.

        Raises:
            ProjectNotFoundError: If the project does not exist.
        """
        self._verify_project_exists(company_id, project_id)

        now = datetime.now(timezone.utc)
        insp_id = self._generate_id()
        overall_status = self.calculate_overall_status(data.items)

        insp_dict: dict[str, Any] = {
            "id": insp_id,
            "company_id": company_id,
            "project_id": project_id,
            "inspection_type": data.inspection_type.value,
            "inspection_date": data.inspection_date.isoformat(),
            "inspector_name": data.inspector_name,
            "weather_conditions": data.weather_conditions,
            "temperature": data.temperature,
            "wind_conditions": data.wind_conditions,
            "workers_on_site": data.workers_on_site,
            "items": [item.model_dump() for item in data.items],
            "overall_notes": data.overall_notes,
            "corrective_actions_needed": data.corrective_actions_needed,
            "gps_latitude": data.gps_latitude,
            "gps_longitude": data.gps_longitude,
            "overall_status": overall_status.value,
            "created_at": now,
            "created_by": user_id,
            "updated_at": now,
            "updated_by": user_id,
            "deleted": False,
        }

        self._collection(company_id, project_id).document(insp_id).set(insp_dict)
        return Inspection(**insp_dict)

    def get(
        self, company_id: str, project_id: str, inspection_id: str
    ) -> Inspection:
        """Fetch a single inspection.

        Args:
            company_id: The owning company ID.
            project_id: The parent project ID.
            inspection_id: The inspection ID to fetch.

        Returns:
            The Inspection model.

        Raises:
            InspectionNotFoundError: If the inspection does not exist or is soft-deleted.
        """
        doc = (
            self._collection(company_id, project_id)
            .document(inspection_id)
            .get()
        )
        if not doc.exists:
            raise InspectionNotFoundError(inspection_id)

        data = doc.to_dict()
        if data.get("deleted", False):
            raise InspectionNotFoundError(inspection_id)

        return Inspection(**data)

    def list_inspections(
        self,
        company_id: str,
        project_id: str,
        inspection_type: InspectionType | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> dict:
        """List inspections for a project with optional filters and pagination.

        Args:
            company_id: The owning company ID.
            project_id: The parent project ID.
            inspection_type: Filter by inspection type.
            date_from: Filter inspections on or after this date.
            date_to: Filter inspections on or before this date.
            limit: Maximum number of inspections to return.
            offset: Number of inspections to skip.

        Returns:
            A dict with 'inspections' list and 'total' count.
        """
        base_query: firestore.Query = self._collection(
            company_id, project_id
        ).where("deleted", "==", False)

        if inspection_type is not None:
            base_query = base_query.where(
                "inspection_type", "==", inspection_type.value
            )

        if date_from is not None:
            base_query = base_query.where(
                "inspection_date", ">=", date_from.isoformat()
            )

        if date_to is not None:
            base_query = base_query.where(
                "inspection_date", "<=", date_to.isoformat()
            )

        # Count total matching inspections
        all_docs = [Inspection(**doc.to_dict()) for doc in base_query.stream()]
        total = len(all_docs)

        # Apply sorting, offset, and limit
        paginated_query = base_query.order_by(
            "created_at", direction=firestore.Query.DESCENDING
        )
        paginated_query = paginated_query.offset(offset).limit(limit)

        inspections = [
            Inspection(**doc.to_dict()) for doc in paginated_query.stream()
        ]

        return {"inspections": inspections, "total": total}

    def update(
        self,
        company_id: str,
        project_id: str,
        inspection_id: str,
        data: InspectionUpdate,
        user_id: str,
    ) -> Inspection:
        """Update an existing inspection.

        Args:
            company_id: The owning company ID.
            project_id: The parent project ID.
            inspection_id: The inspection ID to update.
            data: Fields to update (only non-None fields are applied).
            user_id: Firebase UID of the updating user.

        Returns:
            The updated Inspection model.

        Raises:
            InspectionNotFoundError: If the inspection does not exist or is soft-deleted.
        """
        doc_ref = self._collection(company_id, project_id).document(inspection_id)
        doc = doc_ref.get()

        if not doc.exists or doc.to_dict().get("deleted", False):
            raise InspectionNotFoundError(inspection_id)

        update_data: dict[str, Any] = {}
        for field_name, value in data.model_dump(exclude_none=True).items():
            if field_name == "inspection_type" and value is not None:
                update_data[field_name] = (
                    value.value if hasattr(value, "value") else value
                )
            elif field_name == "inspection_date" and value is not None:
                update_data[field_name] = (
                    value.isoformat() if hasattr(value, "isoformat") else value
                )
            elif field_name == "items" and value is not None:
                update_data[field_name] = [
                    item.model_dump() if hasattr(item, "model_dump") else item
                    for item in value
                ]
            else:
                update_data[field_name] = value

        if not update_data:
            return Inspection(**doc.to_dict())

        # Recalculate overall status if items were updated
        if "items" in update_data:
            items = [
                InspectionItem(**item) if isinstance(item, dict) else item
                for item in update_data["items"]
            ]
            update_data["overall_status"] = self.calculate_overall_status(
                items
            ).value

        update_data["updated_at"] = datetime.now(timezone.utc)
        update_data["updated_by"] = user_id

        doc_ref.update(update_data)

        updated_doc = doc_ref.get()
        return Inspection(**updated_doc.to_dict())

    def delete(
        self, company_id: str, project_id: str, inspection_id: str
    ) -> None:
        """Soft-delete an inspection by setting the deleted flag.

        Args:
            company_id: The owning company ID.
            project_id: The parent project ID.
            inspection_id: The inspection ID to delete.

        Raises:
            InspectionNotFoundError: If the inspection does not exist.
        """
        doc_ref = self._collection(company_id, project_id).document(inspection_id)
        doc = doc_ref.get()

        if not doc.exists or doc.to_dict().get("deleted", False):
            raise InspectionNotFoundError(inspection_id)

        doc_ref.update(
            {
                "deleted": True,
                "updated_at": datetime.now(timezone.utc),
            }
        )
