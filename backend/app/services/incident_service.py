"""Incident CRUD service with OSHA recordability determination against Firestore."""

import json
import logging
import secrets
from datetime import datetime, timezone
from typing import Any

import anthropic
from google.cloud import firestore

from app.config import Settings
from app.exceptions import GenerationError, IncidentNotFoundError, ProjectNotFoundError
from app.models.incident import (
    Incident,
    IncidentCreate,
    IncidentSeverity,
    IncidentStatus,
    IncidentUpdate,
)

logger = logging.getLogger(__name__)


class IncidentService:
    """Manages incident reports in Firestore with OSHA compliance features.

    Args:
        db: Firestore client instance.
        settings: Application settings containing the Anthropic API key.
    """

    def __init__(self, db: firestore.Client, settings: Settings) -> None:
        self.db = db
        self.settings = settings

    def _project_ref(
        self, company_id: str, project_id: str
    ) -> firestore.DocumentReference:
        """Return a reference to the project document.

        Args:
            company_id: The parent company ID.
            project_id: The project ID.

        Returns:
            Firestore document reference.
        """
        return (
            self.db.collection("companies")
            .document(company_id)
            .collection("projects")
            .document(project_id)
        )

    def _collection(
        self, company_id: str, project_id: str
    ) -> firestore.CollectionReference:
        """Return the incidents subcollection for a project.

        Args:
            company_id: The parent company ID.
            project_id: The parent project ID.

        Returns:
            Firestore collection reference.
        """
        return self._project_ref(company_id, project_id).collection("incidents")

    def _generate_id(self) -> str:
        """Generate a unique incident ID.

        Returns:
            A prefixed hex ID string.
        """
        return f"inc_{secrets.token_hex(8)}"

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
    def determine_recordability(severity: IncidentSeverity) -> dict[str, bool]:
        """Determine OSHA recordability and reportability based on severity.

        Per 29 CFR 1904.7 and 29 CFR 1904.39:
        - Fatality: recordable + reportable within 8 hours
        - Hospitalization/amputation/eye loss: recordable + reportable within 24 hours
        - Medical treatment: recordable
        - First aid / near miss / property damage: not recordable

        Args:
            severity: The incident severity classification.

        Returns:
            A dict with 'osha_recordable' and 'osha_reportable' booleans.
        """
        if severity == IncidentSeverity.FATALITY:
            return {"osha_recordable": True, "osha_reportable": True}
        if severity == IncidentSeverity.HOSPITALIZATION:
            return {"osha_recordable": True, "osha_reportable": True}
        if severity == IncidentSeverity.MEDICAL_TREATMENT:
            return {"osha_recordable": True, "osha_reportable": False}
        return {"osha_recordable": False, "osha_reportable": False}

    def create(
        self,
        company_id: str,
        project_id: str,
        data: IncidentCreate,
        user_id: str,
    ) -> Incident:
        """Create a new incident report.

        Automatically determines OSHA recordability based on severity.

        Args:
            company_id: The owning company ID.
            project_id: The parent project ID.
            data: Validated incident creation data.
            user_id: Firebase UID of the creating user.

        Returns:
            The created Incident with all fields populated.

        Raises:
            ProjectNotFoundError: If the project does not exist.
        """
        self._verify_project_exists(company_id, project_id)

        now = datetime.now(timezone.utc)
        inc_id = self._generate_id()
        recordability = self.determine_recordability(data.severity)

        inc_dict: dict[str, Any] = {
            "id": inc_id,
            "company_id": company_id,
            "project_id": project_id,
            "incident_date": data.incident_date.isoformat(),
            "incident_time": data.incident_time,
            "location": data.location,
            "severity": data.severity.value,
            "description": data.description,
            "persons_involved": data.persons_involved,
            "witnesses": data.witnesses,
            "immediate_actions_taken": data.immediate_actions_taken,
            "root_cause": data.root_cause,
            "corrective_actions": data.corrective_actions,
            "voice_transcript": data.voice_transcript,
            "photo_urls": data.photo_urls,
            "status": IncidentStatus.REPORTED.value,
            "osha_recordable": recordability["osha_recordable"],
            "osha_reportable": recordability["osha_reportable"],
            "ai_analysis": {},
            "created_at": now,
            "created_by": user_id,
            "updated_at": now,
            "updated_by": user_id,
        }

        self._collection(company_id, project_id).document(inc_id).set(inc_dict)
        return Incident(**inc_dict)

    def get(
        self, company_id: str, project_id: str, incident_id: str
    ) -> Incident:
        """Fetch a single incident.

        Args:
            company_id: The owning company ID.
            project_id: The parent project ID.
            incident_id: The incident ID to fetch.

        Returns:
            The Incident model.

        Raises:
            IncidentNotFoundError: If the incident does not exist.
        """
        doc = (
            self._collection(company_id, project_id)
            .document(incident_id)
            .get()
        )
        if not doc.exists:
            raise IncidentNotFoundError(incident_id)
        return Incident(**doc.to_dict())

    def list_incidents(
        self,
        company_id: str,
        project_id: str,
        limit: int = 20,
        offset: int = 0,
    ) -> dict:
        """List incidents for a project with pagination.

        Args:
            company_id: The owning company ID.
            project_id: The parent project ID.
            limit: Maximum number of incidents to return.
            offset: Number of incidents to skip.

        Returns:
            A dict with 'incidents' list and 'total' count.
        """
        base_query: firestore.Query = self._collection(company_id, project_id)

        all_docs = list(base_query.stream())
        total = len(all_docs)

        # Sort by created_at descending, then paginate
        all_docs_data = [doc.to_dict() for doc in all_docs]
        all_docs_data.sort(key=lambda d: d.get("created_at", ""), reverse=True)
        paginated = all_docs_data[offset: offset + limit]

        incidents = [Incident(**d) for d in paginated]
        return {"incidents": incidents, "total": total}

    def update(
        self,
        company_id: str,
        project_id: str,
        incident_id: str,
        data: IncidentUpdate,
        user_id: str,
    ) -> Incident:
        """Update an existing incident.

        Args:
            company_id: The owning company ID.
            project_id: The parent project ID.
            incident_id: The incident ID to update.
            data: Fields to update (only non-None fields are applied).
            user_id: Firebase UID of the updating user.

        Returns:
            The updated Incident model.

        Raises:
            IncidentNotFoundError: If the incident does not exist.
        """
        doc_ref = self._collection(company_id, project_id).document(incident_id)
        doc = doc_ref.get()

        if not doc.exists:
            raise IncidentNotFoundError(incident_id)

        update_data: dict[str, Any] = {}
        for field_name, value in data.model_dump(exclude_none=True).items():
            if field_name == "incident_date" and value is not None:
                update_data[field_name] = (
                    value.isoformat() if hasattr(value, "isoformat") else value
                )
            elif field_name == "severity" and value is not None:
                update_data[field_name] = (
                    value.value if hasattr(value, "value") else value
                )
                # Recalculate recordability if severity changes
                recordability = self.determine_recordability(value)
                update_data["osha_recordable"] = recordability["osha_recordable"]
                update_data["osha_reportable"] = recordability["osha_reportable"]
            elif field_name == "status" and value is not None:
                update_data[field_name] = (
                    value.value if hasattr(value, "value") else value
                )
            else:
                update_data[field_name] = value

        if not update_data:
            return Incident(**doc.to_dict())

        update_data["updated_at"] = datetime.now(timezone.utc)
        update_data["updated_by"] = user_id

        doc_ref.update(update_data)

        updated_doc = doc_ref.get()
        return Incident(**updated_doc.to_dict())

    def delete(
        self, company_id: str, project_id: str, incident_id: str
    ) -> None:
        """Permanently delete an incident report.

        Args:
            company_id: The owning company ID.
            project_id: The parent project ID.
            incident_id: The incident ID to delete.

        Raises:
            IncidentNotFoundError: If the incident does not exist.
        """
        doc_ref = self._collection(company_id, project_id).document(incident_id)
        doc = doc_ref.get()

        if not doc.exists:
            raise IncidentNotFoundError(incident_id)

        doc_ref.delete()

    def generate_investigation(
        self,
        company_id: str,
        project_id: str,
        incident_id: str,
        user_id: str,
    ) -> Incident:
        """Generate AI-assisted root cause analysis for an incident.

        Args:
            company_id: The owning company ID.
            project_id: The parent project ID.
            incident_id: The incident ID to analyze.
            user_id: Firebase UID of the requesting user.

        Returns:
            The Incident with ai_analysis populated.

        Raises:
            IncidentNotFoundError: If the incident does not exist.
            GenerationError: If the AI call fails.
        """
        incident = self.get(company_id, project_id, incident_id)

        prompt = f"""Analyze this construction site incident and provide a root cause analysis.

INCIDENT DETAILS:
- Date: {incident.incident_date}
- Location: {incident.location}
- Severity: {incident.severity.value}
- Description: {incident.description}
- Persons involved: {incident.persons_involved}
- Witnesses: {incident.witnesses}
- Immediate actions taken: {incident.immediate_actions_taken}
- Root cause (if identified): {incident.root_cause}

Provide your analysis as a JSON object with these keys:
- "immediate_cause": string describing the direct cause
- "contributing_factors": array of 3-5 contributing factors
- "root_causes": array of 2-3 systemic root causes
- "corrective_actions": array of objects with "action", "type" (Immediate/Short-Term/Long-Term), "responsible_role"
- "preventive_measures": array of recommendations to prevent recurrence
- "osha_standards_applicable": array of relevant OSHA CFR references

Return ONLY valid JSON."""

        try:
            client = anthropic.Anthropic(api_key=self.settings.anthropic_api_key)
            response = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=4096,
                system=(
                    "You are an expert construction safety investigator. "
                    "Provide thorough, professional root cause analyses "
                    "following OSHA investigation methodologies."
                ),
                messages=[{"role": "user", "content": prompt}],
            )
        except anthropic.APIError as exc:
            logger.error("Anthropic API error during investigation: %s", exc)
            raise GenerationError(
                "AI investigation service encountered an error",
                detail=str(exc),
            )

        raw_text = response.content[0].text.strip()

        # Strip markdown code fences if present
        if raw_text.startswith("```"):
            first_newline = raw_text.index("\n")
            raw_text = raw_text[first_newline + 1:]
        if raw_text.endswith("```"):
            raw_text = raw_text[:-3].rstrip()

        try:
            analysis = json.loads(raw_text)
        except json.JSONDecodeError as exc:
            logger.error("Failed to parse AI investigation response: %s", exc)
            raise GenerationError(
                "AI investigation response could not be parsed. Please try again.",
                detail=f"JSON parse error: {exc}",
            )

        # Store the analysis on the incident
        doc_ref = self._collection(company_id, project_id).document(incident_id)
        now = datetime.now(timezone.utc)
        doc_ref.update({
            "ai_analysis": analysis,
            "status": IncidentStatus.INVESTIGATING.value,
            "updated_at": now,
            "updated_by": user_id,
        })

        updated_doc = doc_ref.get()
        return Incident(**updated_doc.to_dict())
