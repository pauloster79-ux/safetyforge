"""Invitation management service for company member invites (Neo4j-backed)."""

import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

from app.exceptions import (
    DuplicateMemberError,
    InvitationExpiredError,
    InvitationNotFoundError,
)
from app.models.actor import Actor
from app.models.member import (
    Invitation,
    InvitationCreate,
    InvitationStatus,
    Member,
)
from app.services.base_service import BaseService

_INVITATION_EXPIRY_DAYS = 7


class InvitationService(BaseService):
    """Manages member invitations as Neo4j nodes.

    Invitations connect to companies via (Invitation)-[:FOR_COMPANY]->(Company).
    """

    def _generate_token(self) -> str:
        """Generate a secure URL-safe invitation token.

        Returns:
            A URL-safe token string.
        """
        return secrets.token_urlsafe(32)

    def create_invitation(
        self,
        company_id: str,
        company_name: str,
        data: InvitationCreate,
        invited_by_uid: str,
        invited_by_email: str,
    ) -> Invitation:
        """Create a new member invitation.

        Args:
            company_id: The company ID.
            company_name: Display name of the company.
            data: Validated invitation creation data.
            invited_by_uid: Clerk user ID of the inviting user.
            invited_by_email: Email of the inviting user.

        Returns:
            The created Invitation.
        """
        actor = Actor.human(invited_by_uid)
        now = datetime.now(timezone.utc)
        invitation_id = self._generate_id("inv")
        token = self._generate_token()

        props: dict[str, Any] = {
            "id": invitation_id,
            "company_name": company_name,
            "email": data.email,
            "role": data.role.value,
            "status": InvitationStatus.PENDING.value,
            "invited_by": invited_by_uid,
            "invited_by_email": invited_by_email,
            "token": token,
            "expires_at": (now + timedelta(days=_INVITATION_EXPIRY_DAYS)).isoformat(),
            "accepted_at": None,
            **self._provenance_create(actor),
        }

        result = self._write_tx_single(
            """
            MATCH (c:Company {id: $company_id})
            CREATE (inv:Invitation $props)
            CREATE (inv)-[:FOR_COMPANY]->(c)
            RETURN inv {.*, company_id: c.id} AS invitation
            """,
            {"company_id": company_id, "props": props},
        )
        self._emit_audit(
            event_type="entity.created",
            entity_id=invitation_id,
            entity_type="Invitation",
            company_id=company_id,
            actor=actor,
            summary=f"Created invitation for {data.email} as {data.role.value}",
        )
        return Invitation(**result["invitation"])

    def get_invitation_by_token(self, token: str) -> Invitation:
        """Look up an invitation by its token.

        Args:
            token: The invitation token.

        Returns:
            The Invitation model.

        Raises:
            InvitationNotFoundError: If no invitation with this token exists.
        """
        result = self._read_tx_single(
            """
            MATCH (inv:Invitation {token: $token})-[:FOR_COMPANY]->(c:Company)
            RETURN inv {.*, company_id: c.id} AS invitation
            """,
            {"token": token},
        )
        if result is None:
            raise InvitationNotFoundError(token)
        return Invitation(**result["invitation"])

    def accept_invitation(
        self, token: str, uid: str, email: str
    ) -> tuple[Invitation, Member]:
        """Accept an invitation and create the member record.

        Args:
            token: The invitation token.
            uid: Clerk user ID of the accepting user.
            email: Email of the accepting user.

        Returns:
            A tuple of (updated Invitation, created Member).

        Raises:
            InvitationNotFoundError: If no invitation with this token exists.
            InvitationExpiredError: If the invitation has expired or is not pending.
            DuplicateMemberError: If user is already a member.
        """
        invitation = self.get_invitation_by_token(token)

        if invitation.status != InvitationStatus.PENDING:
            raise InvitationExpiredError(invitation.id)

        now = datetime.now(timezone.utc)
        if invitation.expires_at < now:
            self._write_tx(
                """
                MATCH (inv:Invitation {id: $id})
                SET inv.status = $status
                """,
                {"id": invitation.id, "status": InvitationStatus.EXPIRED.value},
            )
            raise InvitationExpiredError(invitation.id)

        # Check for duplicate membership
        dup_check = self._read_tx_single(
            """
            MATCH (m:Member {email: $email})-[:MEMBER_OF]->(c:Company {id: $company_id})
            RETURN m.id AS id
            """,
            {"email": email, "company_id": invitation.company_id},
        )
        if dup_check is not None:
            raise DuplicateMemberError(email)

        actor = Actor.human(uid)
        member_id = self._generate_id("mem")
        now_iso = now.isoformat()

        member_props: dict[str, Any] = {
            "id": member_id,
            "uid": uid,
            "email": email,
            "display_name": email.split("@")[0],
            "role": invitation.role.value,
            "invited_by": invitation.invited_by,
            "joined_at": now_iso,
            **self._provenance_create(actor),
        }

        result = self._write_tx_single(
            """
            MATCH (inv:Invitation {id: $inv_id})-[:FOR_COMPANY]->(c:Company)
            SET inv.status = $accepted_status, inv.accepted_at = $now
            CREATE (m:Member $member_props)
            CREATE (m)-[:MEMBER_OF]->(c)
            RETURN inv {.*, company_id: c.id} AS invitation,
                   m {.*, company_id: c.id} AS member
            """,
            {
                "inv_id": invitation.id,
                "accepted_status": InvitationStatus.ACCEPTED.value,
                "now": now_iso,
                "member_props": member_props,
            },
        )

        updated_invitation = Invitation(**result["invitation"])
        member = Member(**result["member"])
        self._emit_audit(
            event_type="state.transitioned",
            entity_id=invitation.id,
            entity_type="Invitation",
            company_id=invitation.company_id,
            actor=actor,
            summary=f"Invitation accepted by {email}",
            prev_state="pending",
            new_state="accepted",
        )
        self._emit_audit(
            event_type="entity.created",
            entity_id=member_id,
            entity_type="Member",
            company_id=invitation.company_id,
            actor=actor,
            summary=f"Member {email} joined via invitation",
        )
        return updated_invitation, member

    def list_invitations(self, company_id: str) -> list[Invitation]:
        """List all invitations for a company.

        Args:
            company_id: The company ID.

        Returns:
            A list of Invitation models.
        """
        results = self._read_tx(
            """
            MATCH (inv:Invitation)-[:FOR_COMPANY]->(c:Company {id: $company_id})
            RETURN inv {.*, company_id: c.id} AS invitation
            ORDER BY inv.created_at DESC
            """,
            {"company_id": company_id},
        )
        return [Invitation(**r["invitation"]) for r in results]

    def revoke_invitation(self, invitation_id: str, company_id: str) -> None:
        """Revoke a pending invitation.

        Args:
            invitation_id: The invitation ID.
            company_id: The company ID (for verification).

        Raises:
            InvitationNotFoundError: If the invitation does not exist.
        """
        result = self._write_tx_single(
            """
            MATCH (inv:Invitation {id: $id})-[:FOR_COMPANY]->(c:Company {id: $company_id})
            SET inv.status = $status
            RETURN inv.id AS id
            """,
            {
                "id": invitation_id,
                "company_id": company_id,
                "status": InvitationStatus.REVOKED.value,
            },
        )
        if result is None:
            raise InvitationNotFoundError(invitation_id)
        self._emit_audit(
            event_type="state.transitioned",
            entity_id=invitation_id,
            entity_type="Invitation",
            company_id=company_id,
            actor=Actor.human("system"),
            summary=f"Revoked invitation {invitation_id}",
            new_state="revoked",
        )
