"""Hazard report CRUD service against Firestore."""

import secrets
from datetime import datetime, timezone
from typing import Any

from google.cloud import firestore

from app.exceptions import HazardReportNotFoundError, ProjectNotFoundError
from app.models.hazard_report import (
    HazardReport,
    HazardReportCreate,
    HazardReportStatusUpdate,
    HazardSeverity,
    HazardStatus,
    IdentifiedHazard,
    SEVERITY_RANK,
)
from app.services.hazard_analysis_service import HazardAnalysisService


class HazardReportService:
    """Manages photo-based hazard reports in Firestore.

    Args:
        db: Firestore client instance.
        analysis_service: HazardAnalysisService for AI photo analysis.
    """

    def __init__(
        self, db: firestore.Client, analysis_service: HazardAnalysisService
    ) -> None:
        self.db = db
        self.analysis_service = analysis_service

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
        """Return the hazard_reports subcollection for a project.

        Args:
            company_id: The parent company ID.
            project_id: The parent project ID.

        Returns:
            Firestore collection reference.
        """
        return self._project_ref(company_id, project_id).collection("hazard_reports")

    def _generate_id(self) -> str:
        """Generate a unique hazard report ID.

        Returns:
            A prefixed hex ID string.
        """
        return f"hzrd_{secrets.token_hex(8)}"

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
    def _strip_data_uri_prefix(photo_base64: str) -> str:
        """Strip data URI prefix if present (e.g. 'data:image/jpeg;base64,').

        Args:
            photo_base64: Raw base64 string, possibly with data URI prefix.

        Returns:
            Clean base64 string without prefix.
        """
        if photo_base64.startswith("data:"):
            # Format: data:image/jpeg;base64,/9j/4AAQ...
            comma_idx = photo_base64.index(",")
            return photo_base64[comma_idx + 1 :]
        return photo_base64

    @staticmethod
    def _parse_hazards(ai_analysis: dict) -> list[IdentifiedHazard]:
        """Parse identified hazards from AI analysis result.

        Args:
            ai_analysis: The raw AI analysis dict.

        Returns:
            List of validated IdentifiedHazard models.
        """
        raw_hazards = ai_analysis.get("identified_hazards", [])
        hazards: list[IdentifiedHazard] = []

        for i, raw in enumerate(raw_hazards):
            # Normalise severity to a valid enum value
            severity_str = raw.get("severity", "low").lower().replace(" ", "_")
            try:
                severity = HazardSeverity(severity_str)
            except ValueError:
                severity = HazardSeverity.LOW

            hazards.append(
                IdentifiedHazard(
                    hazard_id=raw.get("hazard_id", f"h_{i + 1}"),
                    description=raw.get("description", ""),
                    severity=severity,
                    osha_standard=raw.get("osha_standard", ""),
                    category=raw.get("category", "Other"),
                    recommended_action=raw.get("recommended_action", ""),
                    location_in_image=raw.get("location_in_image", ""),
                )
            )

        return hazards

    @staticmethod
    def _highest_severity(
        hazards: list[IdentifiedHazard],
    ) -> HazardSeverity | None:
        """Determine the highest severity among identified hazards.

        Args:
            hazards: List of identified hazards.

        Returns:
            The highest severity value, or None if no hazards.
        """
        if not hazards:
            return None
        return max(hazards, key=lambda h: SEVERITY_RANK.get(h.severity, 0)).severity

    def create_from_photo(
        self,
        company_id: str,
        project_id: str,
        data: HazardReportCreate,
        user_id: str,
    ) -> HazardReport:
        """Create a hazard report by analyzing a photo with AI.

        Args:
            company_id: The owning company ID.
            project_id: The parent project ID.
            data: Validated creation data including photo.
            user_id: Firebase UID of the creating user.

        Returns:
            The created HazardReport with AI analysis results.

        Raises:
            ProjectNotFoundError: If the project does not exist.
            GenerationError: If AI analysis fails.
        """
        self._verify_project_exists(company_id, project_id)

        clean_base64 = self._strip_data_uri_prefix(data.photo_base64)

        # Run AI analysis
        context = {
            "description": data.description,
            "location": data.location,
        }
        ai_analysis = self.analysis_service.analyze_photo(
            image_base64=clean_base64,
            image_media_type=data.media_type,
            context=context,
        )

        hazards = self._parse_hazards(ai_analysis)
        highest = self._highest_severity(hazards)

        now = datetime.now(timezone.utc)
        report_id = self._generate_id()

        # Store photo as data URI for MVP (Cloud Storage migration later)
        photo_url = f"data:{data.media_type};base64,{clean_base64[:50]}..."

        report_dict: dict[str, Any] = {
            "id": report_id,
            "company_id": company_id,
            "project_id": project_id,
            "photo_url": photo_url,
            "description": data.description,
            "location": data.location,
            "gps_latitude": data.gps_latitude,
            "gps_longitude": data.gps_longitude,
            "ai_analysis": ai_analysis,
            "identified_hazards": [h.model_dump() for h in hazards],
            "hazard_count": len(hazards),
            "highest_severity": highest.value if highest else None,
            "status": HazardStatus.OPEN.value,
            "corrective_action_taken": "",
            "corrected_at": None,
            "corrected_by": "",
            "created_at": now,
            "created_by": user_id,
            "updated_at": now,
            "updated_by": user_id,
        }

        self._collection(company_id, project_id).document(report_id).set(report_dict)
        return HazardReport(**report_dict)

    def get(
        self, company_id: str, project_id: str, report_id: str
    ) -> HazardReport:
        """Fetch a single hazard report.

        Args:
            company_id: The owning company ID.
            project_id: The parent project ID.
            report_id: The hazard report ID to fetch.

        Returns:
            The HazardReport model.

        Raises:
            HazardReportNotFoundError: If the report does not exist.
        """
        doc = (
            self._collection(company_id, project_id)
            .document(report_id)
            .get()
        )
        if not doc.exists:
            raise HazardReportNotFoundError(report_id)

        return HazardReport(**doc.to_dict())

    def list_reports(
        self,
        company_id: str,
        project_id: str,
        report_status: HazardStatus | None = None,
        severity: HazardSeverity | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> dict[str, Any]:
        """List hazard reports for a project with optional filters.

        Args:
            company_id: The owning company ID.
            project_id: The parent project ID.
            report_status: Optional status filter.
            severity: Optional highest_severity filter.
            limit: Maximum number of reports to return.
            offset: Number of reports to skip.

        Returns:
            Dict with 'reports' list and 'total' count.
        """
        query: firestore.Query = self._collection(company_id, project_id)

        if report_status is not None:
            query = query.where("status", "==", report_status.value)

        if severity is not None:
            query = query.where("highest_severity", "==", severity.value)

        query = query.order_by("created_at", direction=firestore.Query.DESCENDING)

        all_docs = list(query.stream())
        total = len(all_docs)

        page_docs = all_docs[offset : offset + limit]
        reports = [HazardReport(**doc.to_dict()) for doc in page_docs]

        return {"reports": reports, "total": total}

    def update_status(
        self,
        company_id: str,
        project_id: str,
        report_id: str,
        data: HazardReportStatusUpdate,
        user_id: str,
    ) -> HazardReport:
        """Update the status and corrective action of a hazard report.

        Args:
            company_id: The owning company ID.
            project_id: The parent project ID.
            report_id: The hazard report ID.
            data: Status update data.
            user_id: Firebase UID of the updating user.

        Returns:
            The updated HazardReport.

        Raises:
            HazardReportNotFoundError: If the report does not exist.
        """
        doc_ref = self._collection(company_id, project_id).document(report_id)
        doc = doc_ref.get()
        if not doc.exists:
            raise HazardReportNotFoundError(report_id)

        now = datetime.now(timezone.utc)
        update_dict: dict[str, Any] = {
            "status": data.status.value,
            "corrective_action_taken": data.corrective_action_taken,
            "updated_at": now,
            "updated_by": user_id,
        }

        if data.status in (HazardStatus.CORRECTED, HazardStatus.CLOSED):
            update_dict["corrected_at"] = now
            update_dict["corrected_by"] = user_id

        doc_ref.update(update_dict)

        updated = doc.to_dict()
        updated.update(update_dict)
        return HazardReport(**updated)

    def delete(
        self, company_id: str, project_id: str, report_id: str
    ) -> None:
        """Delete a hazard report.

        Args:
            company_id: The owning company ID.
            project_id: The parent project ID.
            report_id: The hazard report ID to delete.

        Raises:
            HazardReportNotFoundError: If the report does not exist.
        """
        doc_ref = self._collection(company_id, project_id).document(report_id)
        doc = doc_ref.get()
        if not doc.exists:
            raise HazardReportNotFoundError(report_id)

        doc_ref.delete()
