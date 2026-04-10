"""Incident CRUD service with OSHA recordability determination against Neo4j."""

import json
import logging
from datetime import datetime, timezone
from typing import Any

import anthropic

from app.config import Settings
from app.exceptions import GenerationError, IncidentNotFoundError, ProjectNotFoundError
from app.models.actor import Actor
from app.models.incident import (
    Incident,
    IncidentCreate,
    IncidentSeverity,
    IncidentStatus,
    IncidentUpdate,
)
from app.services.base_service import BaseService

logger = logging.getLogger(__name__)


class IncidentService(BaseService):
    """Manages incident reports in Neo4j with OSHA compliance features.

    Graph model:
        (Company)-[:OWNS_PROJECT]->(Project)-[:HAS_INCIDENT]->(Incident)
        Lists (photo_urls, involved_worker_ids) stored as JSON strings.

    Args:
        driver: Neo4j driver instance.
        settings: Application settings containing the Anthropic API key.
    """

    def __init__(self, driver: Any, settings: Settings) -> None:
        super().__init__(driver)
        self.settings = settings

    def _verify_project_exists(self, company_id: str, project_id: str) -> None:
        """Verify that the parent project exists and is not deleted.

        Args:
            company_id: The company ID.
            project_id: The project ID to check.

        Raises:
            ProjectNotFoundError: If the project does not exist or is soft-deleted.
        """
        result = self._read_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
            WHERE p.deleted = false
            RETURN p.id AS id
            """,
            {"company_id": company_id, "project_id": project_id},
        )
        if result is None:
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

    @staticmethod
    def _to_model(record: dict[str, Any]) -> Incident:
        """Convert a Neo4j record dict to an Incident model.

        Args:
            record: Dict with 'incident', 'company_id', 'project_id' keys.

        Returns:
            An Incident model instance.
        """
        data = record["incident"]
        # Deserialize JSON-encoded list fields
        photo_urls_json = data.pop("_photo_urls_json", "[]")
        data["photo_urls"] = json.loads(photo_urls_json) if photo_urls_json else []
        involved_json = data.pop("_involved_worker_ids_json", "[]")
        data["involved_worker_ids"] = json.loads(involved_json) if involved_json else []
        ai_json = data.pop("_ai_analysis_json", "{}")
        data["ai_analysis"] = json.loads(ai_json) if ai_json else {}
        data["company_id"] = record["company_id"]
        data["project_id"] = record["project_id"]
        return Incident(**data)

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
            user_id: UID of the creating user.

        Returns:
            The created Incident with all fields populated.

        Raises:
            ProjectNotFoundError: If the project does not exist.
        """
        self._verify_project_exists(company_id, project_id)

        actor = Actor.human(user_id)
        inc_id = self._generate_id("inc")
        recordability = self.determine_recordability(data.severity)

        props: dict[str, Any] = {
            "id": inc_id,
            "incident_date": data.incident_date.isoformat(),
            "incident_time": data.incident_time,
            "location": data.location,
            "severity": data.severity.value,
            "description": data.description,
            "persons_involved": data.persons_involved,
            "_involved_worker_ids_json": json.dumps(data.involved_worker_ids),
            "witnesses": data.witnesses,
            "immediate_actions_taken": data.immediate_actions_taken,
            "root_cause": data.root_cause,
            "corrective_actions": data.corrective_actions,
            "voice_transcript": data.voice_transcript,
            "_photo_urls_json": json.dumps(data.photo_urls),
            "status": IncidentStatus.REPORTED.value,
            "osha_recordable": recordability["osha_recordable"],
            "osha_reportable": recordability["osha_reportable"],
            "_ai_analysis_json": "{}",
            **self._provenance_create(actor),
        }

        result = self._write_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
            CREATE (i:Incident $props)
            CREATE (p)-[:HAS_INCIDENT]->(i)
            RETURN i {.*} AS incident, c.id AS company_id, p.id AS project_id
            """,
            {"company_id": company_id, "project_id": project_id, "props": props},
        )
        return self._to_model(result)

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
        result = self._read_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
                  -[:HAS_INCIDENT]->(i:Incident {id: $incident_id})
            RETURN i {.*} AS incident, c.id AS company_id, p.id AS project_id
            """,
            {
                "company_id": company_id,
                "project_id": project_id,
                "incident_id": incident_id,
            },
        )
        if result is None:
            raise IncidentNotFoundError(incident_id)
        return self._to_model(result)

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
        params: dict[str, Any] = {
            "company_id": company_id,
            "project_id": project_id,
            "limit": limit,
            "offset": offset,
        }

        count_result = self._read_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
                  -[:HAS_INCIDENT]->(i:Incident)
            RETURN count(i) AS total
            """,
            params,
        )
        total = count_result["total"] if count_result else 0

        results = self._read_tx(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
                  -[:HAS_INCIDENT]->(i:Incident)
            RETURN i {.*} AS incident, c.id AS company_id, p.id AS project_id
            ORDER BY i.created_at DESC
            SKIP $offset LIMIT $limit
            """,
            params,
        )

        incidents = [self._to_model(r) for r in results]
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
            user_id: UID of the updating user.

        Returns:
            The updated Incident model.

        Raises:
            IncidentNotFoundError: If the incident does not exist.
        """
        update_props: dict[str, Any] = {}
        for field_name, value in data.model_dump(exclude_none=True).items():
            if field_name == "incident_date" and value is not None:
                update_props[field_name] = (
                    value.isoformat() if hasattr(value, "isoformat") else value
                )
            elif field_name == "severity" and value is not None:
                update_props[field_name] = (
                    value.value if hasattr(value, "value") else value
                )
                recordability = self.determine_recordability(value)
                update_props["osha_recordable"] = recordability["osha_recordable"]
                update_props["osha_reportable"] = recordability["osha_reportable"]
            elif field_name == "status" and value is not None:
                update_props[field_name] = (
                    value.value if hasattr(value, "value") else value
                )
            elif field_name == "photo_urls" and value is not None:
                update_props["_photo_urls_json"] = json.dumps(value)
            elif field_name == "involved_worker_ids" and value is not None:
                update_props["_involved_worker_ids_json"] = json.dumps(value)
            else:
                update_props[field_name] = value

        if not update_props:
            return self.get(company_id, project_id, incident_id)

        actor = Actor.human(user_id)
        update_props.update(self._provenance_update(actor))

        result = self._write_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
                  -[:HAS_INCIDENT]->(i:Incident {id: $incident_id})
            SET i += $props
            RETURN i {.*} AS incident, c.id AS company_id, p.id AS project_id
            """,
            {
                "company_id": company_id,
                "project_id": project_id,
                "incident_id": incident_id,
                "props": update_props,
            },
        )
        if result is None:
            raise IncidentNotFoundError(incident_id)
        return self._to_model(result)

    def delete(
        self, company_id: str, project_id: str, incident_id: str
    ) -> None:
        """Permanently delete an incident report (DETACH DELETE).

        Args:
            company_id: The owning company ID.
            project_id: The parent project ID.
            incident_id: The incident ID to delete.

        Raises:
            IncidentNotFoundError: If the incident does not exist.
        """
        result = self._write_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
                  -[:HAS_INCIDENT]->(i:Incident {id: $incident_id})
            WITH i, i.id AS deleted_id
            DETACH DELETE i
            RETURN deleted_id AS id
            """,
            {
                "company_id": company_id,
                "project_id": project_id,
                "incident_id": incident_id,
            },
        )
        if result is None:
            raise IncidentNotFoundError(incident_id)

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
            user_id: UID of the requesting user.

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

        actor = Actor.human(user_id)
        update_props = {
            "_ai_analysis_json": json.dumps(analysis),
            "status": IncidentStatus.INVESTIGATING.value,
            **self._provenance_update(actor),
        }

        result = self._write_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
                  -[:HAS_INCIDENT]->(i:Incident {id: $incident_id})
            SET i += $props
            RETURN i {.*} AS incident, c.id AS company_id, p.id AS project_id
            """,
            {
                "company_id": company_id,
                "project_id": project_id,
                "incident_id": incident_id,
                "props": update_props,
            },
        )
        return self._to_model(result)
