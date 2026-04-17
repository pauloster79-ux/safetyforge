"""Toolbox talk CRUD service against Neo4j."""

import json
from datetime import datetime, timezone
from typing import Any

from app.exceptions import ProjectNotFoundError, ToolboxTalkNotFoundError
from app.models.actor import Actor
from app.models.toolbox_talk import (
    Attendee,
    AttendeeCreate,
    ToolboxTalk,
    ToolboxTalkCreate,
    ToolboxTalkStatus,
    ToolboxTalkUpdate,
)
from app.services.base_service import BaseService


class ToolboxTalkService(BaseService):
    """Manages toolbox talks in Neo4j.

    Graph model:
        (Company)-[:OWNS_PROJECT]->(Project)-[:HAS_TOOLBOX_TALK]->(ToolboxTalk)
        Content dicts and attendees stored as JSON strings.
    """

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
    def _to_model(record: dict[str, Any]) -> ToolboxTalk:
        """Convert a Neo4j record dict to a ToolboxTalk model.

        Args:
            record: Dict with 'talk', 'company_id', 'project_id' keys.

        Returns:
            A ToolboxTalk model instance.
        """
        data = record["talk"]
        # Deserialize JSON-encoded fields
        content_en_json = data.pop("_content_en_json", "{}")
        data["content_en"] = json.loads(content_en_json) if content_en_json else {}
        content_es_json = data.pop("_content_es_json", "{}")
        data["content_es"] = json.loads(content_es_json) if content_es_json else {}
        attendees_json = data.pop("_attendees_json", "[]")
        data["attendees"] = json.loads(attendees_json) if attendees_json else []
        custom_points_json = data.pop("_custom_points_json", "[]")
        custom_points_val = json.loads(custom_points_json) if custom_points_json else []
        if isinstance(custom_points_val, list):
            data["custom_points"] = "\n".join(str(p) for p in custom_points_val)
        else:
            data["custom_points"] = str(custom_points_val)
        data["company_id"] = record["company_id"]
        data["project_id"] = record["project_id"]
        return ToolboxTalk(**data)

    def create(
        self,
        company_id: str,
        project_id: str,
        data: ToolboxTalkCreate,
        user_id: str,
    ) -> ToolboxTalk:
        """Create a new toolbox talk.

        Args:
            company_id: The owning company ID.
            project_id: The parent project ID.
            data: Validated toolbox talk creation data.
            user_id: UID of the creating user.

        Returns:
            The created ToolboxTalk with all fields populated.

        Raises:
            ProjectNotFoundError: If the project does not exist.
        """
        self._verify_project_exists(company_id, project_id)

        actor = Actor.human(user_id)
        talk_id = self._generate_id("talk")

        props: dict[str, Any] = {
            "id": talk_id,
            "topic": data.topic,
            "scheduled_date": data.scheduled_date.isoformat(),
            "target_audience": data.target_audience,
            "target_trade": data.target_trade,
            "duration_minutes": data.duration_minutes,
            "_custom_points_json": json.dumps(data.custom_points),
            "_content_en_json": "{}",
            "_content_es_json": "{}",
            "status": ToolboxTalkStatus.SCHEDULED.value,
            "_attendees_json": "[]",
            "overall_notes": "",
            "presented_at": None,
            "presented_by": "",
            "deleted": False,
            **self._provenance_create(actor),
        }

        result = self._write_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
            CREATE (t:ToolboxTalk $props)
            CREATE (p)-[:HAS_TOOLBOX_TALK]->(t)
            RETURN t {.*} AS talk, c.id AS company_id, p.id AS project_id
            """,
            {"company_id": company_id, "project_id": project_id, "props": props},
        )

        self._emit_audit(
            event_type="entity.created",
            entity_id=talk_id,
            entity_type="ToolboxTalk",
            company_id=company_id,
            actor=actor,
            summary=f"Scheduled toolbox talk: {data.topic}",
            related_entity_ids=[project_id],
        )

        return self._to_model(result)

    def get(
        self, company_id: str, project_id: str, talk_id: str
    ) -> ToolboxTalk:
        """Fetch a single toolbox talk.

        Args:
            company_id: The owning company ID.
            project_id: The parent project ID.
            talk_id: The toolbox talk ID to fetch.

        Returns:
            The ToolboxTalk model.

        Raises:
            ToolboxTalkNotFoundError: If the talk does not exist or is soft-deleted.
        """
        result = self._read_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
                  -[:HAS_TOOLBOX_TALK]->(t:ToolboxTalk {id: $talk_id})
            WHERE t.deleted = false
            RETURN t {.*} AS talk, c.id AS company_id, p.id AS project_id
            """,
            {
                "company_id": company_id,
                "project_id": project_id,
                "talk_id": talk_id,
            },
        )
        if result is None:
            raise ToolboxTalkNotFoundError(talk_id)
        return self._to_model(result)

    def list_talks(
        self,
        company_id: str,
        project_id: str,
        status: ToolboxTalkStatus | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> dict:
        """List toolbox talks for a project with optional filters and pagination.

        Args:
            company_id: The owning company ID.
            project_id: The parent project ID.
            status: Filter by talk status.
            limit: Maximum number of talks to return.
            offset: Number of talks to skip.

        Returns:
            A dict with 'toolbox_talks' list and 'total' count.
        """
        where_clauses = ["t.deleted = false"]
        params: dict[str, Any] = {
            "company_id": company_id,
            "project_id": project_id,
            "limit": limit,
            "offset": offset,
        }

        if status is not None:
            where_clauses.append("t.status = $status")
            params["status"] = status.value

        where_str = " AND ".join(where_clauses)

        count_result = self._read_tx_single(
            f"""
            MATCH (c:Company {{id: $company_id}})-[:OWNS_PROJECT]->(p:Project {{id: $project_id}})
                  -[:HAS_TOOLBOX_TALK]->(t:ToolboxTalk)
            WHERE {where_str}
            RETURN count(t) AS total
            """,
            params,
        )
        total = count_result["total"] if count_result else 0

        results = self._read_tx(
            f"""
            MATCH (c:Company {{id: $company_id}})-[:OWNS_PROJECT]->(p:Project {{id: $project_id}})
                  -[:HAS_TOOLBOX_TALK]->(t:ToolboxTalk)
            WHERE {where_str}
            RETURN t {{.*}} AS talk, c.id AS company_id, p.id AS project_id
            ORDER BY t.created_at DESC
            SKIP $offset LIMIT $limit
            """,
            params,
        )

        toolbox_talks = [self._to_model(r) for r in results]
        return {"toolbox_talks": toolbox_talks, "total": total}

    def update(
        self,
        company_id: str,
        project_id: str,
        talk_id: str,
        data: ToolboxTalkUpdate,
        user_id: str,
    ) -> ToolboxTalk:
        """Update an existing toolbox talk.

        Args:
            company_id: The owning company ID.
            project_id: The parent project ID.
            talk_id: The toolbox talk ID to update.
            data: Fields to update (only non-None fields are applied).
            user_id: UID of the updating user.

        Returns:
            The updated ToolboxTalk model.

        Raises:
            ToolboxTalkNotFoundError: If the talk does not exist or is soft-deleted.
        """
        update_props: dict[str, Any] = {}
        for field_name, value in data.model_dump(exclude_none=True).items():
            if field_name == "status" and value is not None:
                update_props[field_name] = (
                    value.value if hasattr(value, "value") else value
                )
            elif field_name == "content_en" and value is not None:
                update_props["_content_en_json"] = json.dumps(value)
            elif field_name == "content_es" and value is not None:
                update_props["_content_es_json"] = json.dumps(value)
            else:
                update_props[field_name] = value

        if not update_props:
            return self.get(company_id, project_id, talk_id)

        actor = Actor.human(user_id)
        update_props.update(self._provenance_update(actor))

        result = self._write_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
                  -[:HAS_TOOLBOX_TALK]->(t:ToolboxTalk {id: $talk_id})
            WHERE t.deleted = false
            SET t += $props
            RETURN t {.*} AS talk, c.id AS company_id, p.id AS project_id
            """,
            {
                "company_id": company_id,
                "project_id": project_id,
                "talk_id": talk_id,
                "props": update_props,
            },
        )
        if result is None:
            raise ToolboxTalkNotFoundError(talk_id)

        self._emit_audit(
            event_type="entity.updated",
            entity_id=talk_id,
            entity_type="ToolboxTalk",
            company_id=company_id,
            actor=actor,
            summary="Updated toolbox talk",
            related_entity_ids=[project_id],
        )

        return self._to_model(result)

    def delete(
        self, company_id: str, project_id: str, talk_id: str
    ) -> None:
        """Soft-delete a toolbox talk by setting the deleted flag.

        Args:
            company_id: The owning company ID.
            project_id: The parent project ID.
            talk_id: The toolbox talk ID to delete.

        Raises:
            ToolboxTalkNotFoundError: If the talk does not exist.
        """
        result = self._write_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
                  -[:HAS_TOOLBOX_TALK]->(t:ToolboxTalk {id: $talk_id})
            WHERE t.deleted = false
            SET t.deleted = true, t.updated_at = $now
            RETURN t.id AS id
            """,
            {
                "company_id": company_id,
                "project_id": project_id,
                "talk_id": talk_id,
                "now": datetime.now(timezone.utc).isoformat(),
            },
        )
        if result is None:
            raise ToolboxTalkNotFoundError(talk_id)

        self._emit_audit(
            event_type="entity.archived",
            entity_id=talk_id,
            entity_type="ToolboxTalk",
            company_id=company_id,
            actor=Actor.human("system"),
            summary="Deleted toolbox talk",
            related_entity_ids=[project_id],
        )

    def add_attendee(
        self,
        company_id: str,
        project_id: str,
        talk_id: str,
        attendee_data: AttendeeCreate,
    ) -> ToolboxTalk:
        """Add a signed attendee to a toolbox talk.

        Args:
            company_id: The owning company ID.
            project_id: The parent project ID.
            talk_id: The toolbox talk ID.
            attendee_data: Attendee information.

        Returns:
            The updated ToolboxTalk with the new attendee.

        Raises:
            ToolboxTalkNotFoundError: If the talk does not exist or is soft-deleted.
        """
        # Read current attendees
        current = self._read_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
                  -[:HAS_TOOLBOX_TALK]->(t:ToolboxTalk {id: $talk_id})
            WHERE t.deleted = false
            RETURN t._attendees_json AS attendees_json
            """,
            {
                "company_id": company_id,
                "project_id": project_id,
                "talk_id": talk_id,
            },
        )
        if current is None:
            raise ToolboxTalkNotFoundError(talk_id)

        now = datetime.now(timezone.utc)
        attendee = Attendee(
            worker_name=attendee_data.worker_name,
            signature_data=attendee_data.signature_data,
            signed_at=now,
            language_preference=attendee_data.language_preference,
        )

        existing = json.loads(current["attendees_json"] or "[]")
        existing.append(attendee.model_dump(mode="json"))
        new_json = json.dumps(existing)

        result = self._write_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
                  -[:HAS_TOOLBOX_TALK]->(t:ToolboxTalk {id: $talk_id})
            WHERE t.deleted = false
            SET t._attendees_json = $attendees_json, t.updated_at = $now
            RETURN t {.*} AS talk, c.id AS company_id, p.id AS project_id
            """,
            {
                "company_id": company_id,
                "project_id": project_id,
                "talk_id": talk_id,
                "attendees_json": new_json,
                "now": now.isoformat(),
            },
        )

        self._emit_audit(
            event_type="relationship.added",
            entity_id=talk_id,
            entity_type="ToolboxTalk",
            company_id=company_id,
            actor=Actor.human("system"),
            summary=f"Attendee signed: {attendee_data.worker_name}",
            related_entity_ids=[project_id],
        )

        return self._to_model(result)

    def complete_talk(
        self,
        company_id: str,
        project_id: str,
        talk_id: str,
        presented_by: str,
        notes: str = "",
    ) -> ToolboxTalk:
        """Mark a toolbox talk as completed with timestamp.

        Args:
            company_id: The owning company ID.
            project_id: The parent project ID.
            talk_id: The toolbox talk ID.
            presented_by: Name of the presenter.
            notes: Optional overall notes from the talk.

        Returns:
            The updated ToolboxTalk marked as completed.

        Raises:
            ToolboxTalkNotFoundError: If the talk does not exist or is soft-deleted.
        """
        now = datetime.now(timezone.utc).isoformat()

        result = self._write_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
                  -[:HAS_TOOLBOX_TALK]->(t:ToolboxTalk {id: $talk_id})
            WHERE t.deleted = false
            SET t.status = $status, t.presented_at = $now, t.presented_by = $presented_by,
                t.overall_notes = $notes, t.updated_at = $now
            RETURN t {.*} AS talk, c.id AS company_id, p.id AS project_id
            """,
            {
                "company_id": company_id,
                "project_id": project_id,
                "talk_id": talk_id,
                "status": ToolboxTalkStatus.COMPLETED.value,
                "now": now,
                "presented_by": presented_by,
                "notes": notes,
            },
        )
        if result is None:
            raise ToolboxTalkNotFoundError(talk_id)

        self._emit_audit(
            event_type="state.transitioned",
            entity_id=talk_id,
            entity_type="ToolboxTalk",
            company_id=company_id,
            actor=Actor.human("system"),
            summary=f"Toolbox talk completed, presented by {presented_by}",
            prev_state=ToolboxTalkStatus.SCHEDULED.value,
            new_state=ToolboxTalkStatus.COMPLETED.value,
            related_entity_ids=[project_id],
        )

        return self._to_model(result)

    def set_generated_content(
        self,
        company_id: str,
        project_id: str,
        talk_id: str,
        content_en: dict | None = None,
        content_es: dict | None = None,
        user_id: str = "",
    ) -> ToolboxTalk:
        """Store AI-generated content on a toolbox talk.

        Args:
            company_id: The owning company ID.
            project_id: The parent project ID.
            talk_id: The toolbox talk ID.
            content_en: English content dict.
            content_es: Spanish content dict.
            user_id: UID of the user.

        Returns:
            The updated ToolboxTalk with generated content.

        Raises:
            ToolboxTalkNotFoundError: If the talk does not exist or is soft-deleted.
        """
        update_props: dict[str, Any] = {
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        if user_id:
            update_props["updated_by"] = user_id
        if content_en is not None:
            update_props["_content_en_json"] = json.dumps(content_en)
        if content_es is not None:
            update_props["_content_es_json"] = json.dumps(content_es)

        result = self._write_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project {id: $project_id})
                  -[:HAS_TOOLBOX_TALK]->(t:ToolboxTalk {id: $talk_id})
            WHERE t.deleted = false
            SET t += $props
            RETURN t {.*} AS talk, c.id AS company_id, p.id AS project_id
            """,
            {
                "company_id": company_id,
                "project_id": project_id,
                "talk_id": talk_id,
                "props": update_props,
            },
        )
        if result is None:
            raise ToolboxTalkNotFoundError(talk_id)

        self._emit_audit(
            event_type="entity.updated",
            entity_id=talk_id,
            entity_type="ToolboxTalk",
            company_id=company_id,
            actor=Actor.human(user_id) if user_id else Actor.human("system"),
            summary="AI-generated content added to toolbox talk",
            related_entity_ids=[project_id],
        )

        return self._to_model(result)
