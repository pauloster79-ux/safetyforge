"""Toolbox talk CRUD service against Firestore."""

import secrets
from datetime import datetime, timezone
from typing import Any

from google.cloud import firestore

from app.exceptions import ProjectNotFoundError, ToolboxTalkNotFoundError
from app.models.toolbox_talk import (
    Attendee,
    AttendeeCreate,
    ToolboxTalk,
    ToolboxTalkCreate,
    ToolboxTalkStatus,
    ToolboxTalkUpdate,
)


class ToolboxTalkService:
    """Manages toolbox talks in Firestore.

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
        """Return the toolbox_talks subcollection for a project.

        Args:
            company_id: The parent company ID.
            project_id: The parent project ID.

        Returns:
            Firestore collection reference.
        """
        return self._project_ref(company_id, project_id).collection("toolbox_talks")

    def _generate_id(self) -> str:
        """Generate a unique toolbox talk ID.

        Returns:
            A prefixed hex ID string.
        """
        return f"talk_{secrets.token_hex(8)}"

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
            user_id: Firebase UID of the creating user.

        Returns:
            The created ToolboxTalk with all fields populated.

        Raises:
            ProjectNotFoundError: If the project does not exist.
        """
        self._verify_project_exists(company_id, project_id)

        now = datetime.now(timezone.utc)
        talk_id = self._generate_id()

        talk_dict: dict[str, Any] = {
            "id": talk_id,
            "company_id": company_id,
            "project_id": project_id,
            "topic": data.topic,
            "scheduled_date": data.scheduled_date.isoformat(),
            "target_audience": data.target_audience,
            "target_trade": data.target_trade,
            "duration_minutes": data.duration_minutes,
            "custom_points": data.custom_points,
            "content_en": {},
            "content_es": {},
            "status": ToolboxTalkStatus.SCHEDULED.value,
            "attendees": [],
            "overall_notes": "",
            "presented_at": None,
            "presented_by": "",
            "created_at": now,
            "created_by": user_id,
            "updated_at": now,
            "updated_by": user_id,
            "deleted": False,
        }

        self._collection(company_id, project_id).document(talk_id).set(talk_dict)
        return ToolboxTalk(**talk_dict)

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
        doc = (
            self._collection(company_id, project_id)
            .document(talk_id)
            .get()
        )
        if not doc.exists:
            raise ToolboxTalkNotFoundError(talk_id)

        data = doc.to_dict()
        if data.get("deleted", False):
            raise ToolboxTalkNotFoundError(talk_id)

        return ToolboxTalk(**data)

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
        base_query: firestore.Query = self._collection(
            company_id, project_id
        ).where("deleted", "==", False)

        if status is not None:
            base_query = base_query.where("status", "==", status.value)

        # Count total matching talks
        all_docs = [ToolboxTalk(**doc.to_dict()) for doc in base_query.stream()]
        total = len(all_docs)

        # Apply sorting, offset, and limit
        paginated_query = base_query.order_by(
            "created_at", direction=firestore.Query.DESCENDING
        )
        paginated_query = paginated_query.offset(offset).limit(limit)

        toolbox_talks = [
            ToolboxTalk(**doc.to_dict()) for doc in paginated_query.stream()
        ]

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
            user_id: Firebase UID of the updating user.

        Returns:
            The updated ToolboxTalk model.

        Raises:
            ToolboxTalkNotFoundError: If the talk does not exist or is soft-deleted.
        """
        doc_ref = self._collection(company_id, project_id).document(talk_id)
        doc = doc_ref.get()

        if not doc.exists or doc.to_dict().get("deleted", False):
            raise ToolboxTalkNotFoundError(talk_id)

        update_data: dict[str, Any] = {}
        for field_name, value in data.model_dump(exclude_none=True).items():
            if field_name == "status" and value is not None:
                update_data[field_name] = (
                    value.value if hasattr(value, "value") else value
                )
            else:
                update_data[field_name] = value

        if not update_data:
            return ToolboxTalk(**doc.to_dict())

        update_data["updated_at"] = datetime.now(timezone.utc)
        update_data["updated_by"] = user_id

        doc_ref.update(update_data)

        updated_doc = doc_ref.get()
        return ToolboxTalk(**updated_doc.to_dict())

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
        doc_ref = self._collection(company_id, project_id).document(talk_id)
        doc = doc_ref.get()

        if not doc.exists or doc.to_dict().get("deleted", False):
            raise ToolboxTalkNotFoundError(talk_id)

        doc_ref.update(
            {
                "deleted": True,
                "updated_at": datetime.now(timezone.utc),
            }
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
        doc_ref = self._collection(company_id, project_id).document(talk_id)
        doc = doc_ref.get()

        if not doc.exists or doc.to_dict().get("deleted", False):
            raise ToolboxTalkNotFoundError(talk_id)

        now = datetime.now(timezone.utc)
        attendee = Attendee(
            worker_name=attendee_data.worker_name,
            signature_data=attendee_data.signature_data,
            signed_at=now,
            language_preference=attendee_data.language_preference,
        )

        doc_ref.update(
            {
                "attendees": firestore.ArrayUnion([attendee.model_dump()]),
                "updated_at": now,
            }
        )

        updated_doc = doc_ref.get()
        return ToolboxTalk(**updated_doc.to_dict())

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
        doc_ref = self._collection(company_id, project_id).document(talk_id)
        doc = doc_ref.get()

        if not doc.exists or doc.to_dict().get("deleted", False):
            raise ToolboxTalkNotFoundError(talk_id)

        now = datetime.now(timezone.utc)

        doc_ref.update(
            {
                "status": ToolboxTalkStatus.COMPLETED.value,
                "presented_at": now,
                "presented_by": presented_by,
                "overall_notes": notes,
                "updated_at": now,
            }
        )

        updated_doc = doc_ref.get()
        return ToolboxTalk(**updated_doc.to_dict())

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
            user_id: Firebase UID of the user.

        Returns:
            The updated ToolboxTalk with generated content.

        Raises:
            ToolboxTalkNotFoundError: If the talk does not exist or is soft-deleted.
        """
        doc_ref = self._collection(company_id, project_id).document(talk_id)
        doc = doc_ref.get()

        if not doc.exists or doc.to_dict().get("deleted", False):
            raise ToolboxTalkNotFoundError(talk_id)

        update_data: dict[str, Any] = {
            "updated_at": datetime.now(timezone.utc),
        }
        if user_id:
            update_data["updated_by"] = user_id
        if content_en is not None:
            update_data["content_en"] = content_en
        if content_es is not None:
            update_data["content_es"] = content_es

        doc_ref.update(update_data)

        updated_doc = doc_ref.get()
        return ToolboxTalk(**updated_doc.to_dict())
