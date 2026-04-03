"""Company member management service."""

import secrets
from datetime import datetime, timezone

from google.cloud import firestore

from app.exceptions import (
    DuplicateMemberError,
    InsufficientPermissionError,
    MemberNotFoundError,
)
from app.models.member import Member, MemberRole, MemberUpdate


# Role hierarchy: lower index = higher privilege
_ROLE_HIERARCHY = [MemberRole.OWNER, MemberRole.ADMIN, MemberRole.EDITOR, MemberRole.VIEWER]


class MemberService:
    """Manages company members in Firestore.

    Members are stored as a subcollection: companies/{company_id}/members/{member_id}

    Args:
        db: Firestore client instance.
    """

    def __init__(self, db: firestore.Client) -> None:
        self.db = db

    def _collection(self, company_id: str) -> firestore.CollectionReference:
        """Return the members subcollection for a company.

        Args:
            company_id: The parent company document ID.

        Returns:
            A Firestore collection reference.
        """
        return self.db.collection("companies").document(company_id).collection("members")

    def _generate_id(self) -> str:
        """Generate a unique member ID.

        Returns:
            A prefixed hex ID string.
        """
        return f"mem_{secrets.token_hex(8)}"

    def create_owner_member(self, company_id: str, uid: str, email: str) -> Member:
        """Auto-create the owner member when a company is created.

        Args:
            company_id: The company document ID.
            uid: Firebase UID of the owner.
            email: Email address of the owner.

        Returns:
            The created Member with owner role.
        """
        now = datetime.now(timezone.utc)
        member_id = self._generate_id()

        member_dict = {
            "id": member_id,
            "company_id": company_id,
            "uid": uid,
            "email": email,
            "display_name": email.split("@")[0],
            "role": MemberRole.OWNER.value,
            "invited_by": None,
            "joined_at": now,
            "created_at": now,
            "updated_at": now,
        }

        self._collection(company_id).document(member_id).set(member_dict)
        return Member(**member_dict)

    def get_members(self, company_id: str) -> list[Member]:
        """List all members for a company.

        Args:
            company_id: The company document ID.

        Returns:
            A list of Member models.
        """
        docs = self._collection(company_id).stream()
        return [Member(**doc.to_dict()) for doc in docs]

    def get_member_by_uid(self, company_id: str, uid: str) -> Member | None:
        """Find a member by Firebase UID within a company.

        Args:
            company_id: The company document ID.
            uid: Firebase UID to look up.

        Returns:
            The Member if found, None otherwise.
        """
        query = self._collection(company_id).where("uid", "==", uid).limit(1)
        docs = list(query.stream())
        if not docs:
            return None
        return Member(**docs[0].to_dict())

    def update_member(
        self, company_id: str, member_id: str, data: MemberUpdate, updated_by: str
    ) -> Member:
        """Update a member's role or display name.

        Args:
            company_id: The company document ID.
            member_id: The member document ID.
            data: Fields to update (only non-None fields are applied).
            updated_by: Firebase UID of the user performing the update.

        Returns:
            The updated Member model.

        Raises:
            MemberNotFoundError: If the member does not exist.
        """
        doc_ref = self._collection(company_id).document(member_id)
        doc = doc_ref.get()
        if not doc.exists:
            raise MemberNotFoundError(member_id)

        update_data: dict = {}
        for field_name, value in data.model_dump(exclude_none=True).items():
            if field_name == "role" and value is not None:
                update_data[field_name] = value.value if hasattr(value, "value") else value
            else:
                update_data[field_name] = value

        if not update_data:
            return Member(**doc.to_dict())

        update_data["updated_at"] = datetime.now(timezone.utc)

        doc_ref.update(update_data)

        updated_doc = doc_ref.get()
        return Member(**updated_doc.to_dict())

    def remove_member(self, company_id: str, member_id: str) -> None:
        """Delete a member document.

        Args:
            company_id: The company document ID.
            member_id: The member document ID.

        Raises:
            MemberNotFoundError: If the member does not exist.
        """
        doc_ref = self._collection(company_id).document(member_id)
        doc = doc_ref.get()
        if not doc.exists:
            raise MemberNotFoundError(member_id)
        doc_ref.delete()

    def get_user_companies(self, uid: str) -> list[dict]:
        """Query all companies where a user is a member.

        Uses a collection_group query on the 'members' subcollection.

        Args:
            uid: Firebase UID to look up.

        Returns:
            A list of dicts with company_id and role for each membership.
        """
        query = self.db.collection_group("members").where("uid", "==", uid)
        docs = list(query.stream())
        return [
            {"company_id": doc.to_dict()["company_id"], "role": doc.to_dict()["role"]}
            for doc in docs
        ]

    def check_permission(
        self, company_id: str, uid: str, minimum_role: MemberRole
    ) -> Member:
        """Check that a user has at least the minimum role in a company.

        Args:
            company_id: The company document ID.
            uid: Firebase UID of the user to check.
            minimum_role: The minimum role required.

        Returns:
            The Member model if permission is granted.

        Raises:
            InsufficientPermissionError: If user is not a member or lacks the role.
        """
        member = self.get_member_by_uid(company_id, uid)
        if member is None:
            raise InsufficientPermissionError(
                f"User {uid} is not a member of company {company_id}"
            )

        user_level = _ROLE_HIERARCHY.index(member.role)
        required_level = _ROLE_HIERARCHY.index(minimum_role)

        if user_level > required_level:
            raise InsufficientPermissionError(
                f"Requires {minimum_role.value} role or higher"
            )

        return member

    def check_duplicate(self, company_id: str, email: str) -> None:
        """Check that no existing member has this email.

        Args:
            company_id: The company document ID.
            email: Email address to check.

        Raises:
            DuplicateMemberError: If a member with this email already exists.
        """
        query = self._collection(company_id).where("email", "==", email).limit(1)
        docs = list(query.stream())
        if docs:
            raise DuplicateMemberError(email)
