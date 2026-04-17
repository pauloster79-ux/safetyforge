"""Company member management service (Neo4j-backed)."""

from typing import Any

from app.exceptions import (
    DuplicateMemberError,
    InsufficientPermissionError,
    MemberNotFoundError,
)
from app.models.actor import Actor
from app.models.member import Member, MemberRole, MemberUpdate
from app.services.base_service import BaseService


# Role hierarchy: lower index = higher privilege
_ROLE_HIERARCHY = [MemberRole.OWNER, MemberRole.ADMIN, MemberRole.EDITOR, MemberRole.VIEWER]


class MemberService(BaseService):
    """Manages company members as Neo4j nodes.

    Members connect to companies via (Member)-[:MEMBER_OF]->(Company).
    """

    def create_owner_member(self, company_id: str, uid: str, email: str) -> Member:
        """Auto-create the owner member when a company is created.

        Args:
            company_id: The company ID.
            uid: Clerk user ID of the owner.
            email: Email address of the owner.

        Returns:
            The created Member with owner role.
        """
        actor = Actor.human(uid)
        member_id = self._generate_id("mem")

        props: dict[str, Any] = {
            "id": member_id,
            "uid": uid,
            "email": email,
            "display_name": email.split("@")[0],
            "role": MemberRole.OWNER.value,
            "invited_by": None,
            "joined_at": self._provenance_create(actor)["created_at"],
            **self._provenance_create(actor),
        }

        result = self._write_tx_single(
            """
            MATCH (c:Company {id: $company_id})
            CREATE (m:Member $props)
            CREATE (m)-[:MEMBER_OF]->(c)
            RETURN m {.*, company_id: c.id} AS member
            """,
            {"company_id": company_id, "props": props},
        )
        self._emit_audit(
            event_type="entity.created",
            entity_id=member_id,
            entity_type="Member",
            company_id=company_id,
            actor=actor,
            summary=f"Created owner member for company {company_id}",
        )
        return Member(**result["member"])

    def get_members(self, company_id: str) -> list[Member]:
        """List all members for a company.

        Args:
            company_id: The company ID.

        Returns:
            A list of Member models.
        """
        results = self._read_tx(
            """
            MATCH (m:Member)-[:MEMBER_OF]->(c:Company {id: $company_id})
            RETURN m {.*, company_id: c.id} AS member
            ORDER BY m.created_at
            """,
            {"company_id": company_id},
        )
        return [Member(**r["member"]) for r in results]

    def get_member_by_uid(self, company_id: str, uid: str) -> Member | None:
        """Find a member by Clerk user ID within a company.

        Args:
            company_id: The company ID.
            uid: Clerk user ID to look up.

        Returns:
            The Member if found, None otherwise.
        """
        result = self._read_tx_single(
            """
            MATCH (m:Member {uid: $uid})-[:MEMBER_OF]->(c:Company {id: $company_id})
            RETURN m {.*, company_id: c.id} AS member
            """,
            {"company_id": company_id, "uid": uid},
        )
        if result is None:
            return None
        return Member(**result["member"])

    def update_member(
        self, company_id: str, member_id: str, data: MemberUpdate, updated_by: str
    ) -> Member:
        """Update a member's role or display name.

        Args:
            company_id: The company ID.
            member_id: The member ID.
            data: Fields to update (only non-None fields are applied).
            updated_by: Clerk user ID of the user performing the update.

        Returns:
            The updated Member model.

        Raises:
            MemberNotFoundError: If the member does not exist.
        """
        update_fields: dict[str, Any] = {}
        for field_name, value in data.model_dump(exclude_none=True).items():
            if field_name == "role" and value is not None:
                update_fields[field_name] = value.value if hasattr(value, "value") else value
            else:
                update_fields[field_name] = value

        actor = Actor.human(updated_by)
        update_fields.update(self._provenance_update(actor))

        result = self._write_tx_single(
            """
            MATCH (m:Member {id: $member_id})-[:MEMBER_OF]->(c:Company {id: $company_id})
            SET m += $props
            RETURN m {.*, company_id: c.id} AS member
            """,
            {"company_id": company_id, "member_id": member_id, "props": update_fields},
        )
        if result is None:
            raise MemberNotFoundError(member_id)
        self._emit_audit(
            event_type="entity.updated",
            entity_id=member_id,
            entity_type="Member",
            company_id=company_id,
            actor=actor,
            summary=f"Updated member {member_id}",
        )
        return Member(**result["member"])

    def remove_member(self, company_id: str, member_id: str) -> None:
        """Delete a member node and its relationships.

        Args:
            company_id: The company ID.
            member_id: The member ID.

        Raises:
            MemberNotFoundError: If the member does not exist.
        """
        result = self._read_tx_single(
            """
            MATCH (m:Member {id: $member_id})-[:MEMBER_OF]->(c:Company {id: $company_id})
            RETURN m.id AS id
            """,
            {"company_id": company_id, "member_id": member_id},
        )
        if result is None:
            raise MemberNotFoundError(member_id)

        self._write_tx(
            """
            MATCH (m:Member {id: $member_id})
            DETACH DELETE m
            """,
            {"member_id": member_id},
        )

    def get_user_companies(self, uid: str) -> list[dict]:
        """Query all companies where a user is a member.

        Args:
            uid: Clerk user ID to look up.

        Returns:
            A list of dicts with company_id and role for each membership.
        """
        results = self._read_tx(
            """
            MATCH (m:Member {uid: $uid})-[:MEMBER_OF]->(c:Company)
            RETURN c.id AS company_id, m.role AS role
            """,
            {"uid": uid},
        )
        return [{"company_id": r["company_id"], "role": r["role"]} for r in results]

    def check_permission(
        self, company_id: str, uid: str, minimum_role: MemberRole
    ) -> Member:
        """Check that a user has at least the minimum role in a company.

        Args:
            company_id: The company ID.
            uid: Clerk user ID of the user to check.
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
            company_id: The company ID.
            email: Email address to check.

        Raises:
            DuplicateMemberError: If a member with this email already exists.
        """
        result = self._read_tx_single(
            """
            MATCH (m:Member {email: $email})-[:MEMBER_OF]->(c:Company {id: $company_id})
            RETURN m.id AS id
            """,
            {"company_id": company_id, "email": email},
        )
        if result is not None:
            raise DuplicateMemberError(email)
