"""Invitation management service for company member invites."""

import secrets
from datetime import datetime, timedelta, timezone

from google.cloud import firestore

from app.exceptions import (
    DuplicateMemberError,
    InvitationExpiredError,
    InvitationNotFoundError,
    MemberNotFoundError,
)
from app.models.member import (
    Invitation,
    InvitationCreate,
    InvitationStatus,
    Member,
    MemberRole,
)
from app.services.member_service import MemberService

_INVITATION_EXPIRY_DAYS = 7


class InvitationService:
    """Manages member invitations in Firestore.

    Invitations are stored in a top-level 'invitations' collection.

    Args:
        db: Firestore client instance.
    """

    def __init__(self, db: firestore.Client) -> None:
        self.db = db

    def _collection(self) -> firestore.CollectionReference:
        """Return the invitations collection reference.

        Returns:
            A Firestore collection reference.
        """
        return self.db.collection("invitations")

    def _generate_id(self) -> str:
        """Generate a unique invitation ID.

        Returns:
            A prefixed hex ID string.
        """
        return f"inv_{secrets.token_hex(8)}"

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
            company_id: The company document ID.
            company_name: Display name of the company.
            data: Validated invitation creation data.
            invited_by_uid: Firebase UID of the inviting user.
            invited_by_email: Email of the inviting user.

        Returns:
            The created Invitation.
        """
        now = datetime.now(timezone.utc)
        invitation_id = self._generate_id()
        token = self._generate_token()

        invitation_dict = {
            "id": invitation_id,
            "company_id": company_id,
            "company_name": company_name,
            "email": data.email,
            "role": data.role.value,
            "status": InvitationStatus.PENDING.value,
            "invited_by": invited_by_uid,
            "invited_by_email": invited_by_email,
            "token": token,
            "expires_at": now + timedelta(days=_INVITATION_EXPIRY_DAYS),
            "created_at": now,
            "accepted_at": None,
        }

        self._collection().document(invitation_id).set(invitation_dict)
        return Invitation(**invitation_dict)

    def get_invitation_by_token(self, token: str) -> Invitation:
        """Look up an invitation by its token.

        Args:
            token: The invitation token.

        Returns:
            The Invitation model.

        Raises:
            InvitationNotFoundError: If no invitation with this token exists.
        """
        query = self._collection().where("token", "==", token).limit(1)
        docs = list(query.stream())
        if not docs:
            raise InvitationNotFoundError(token)
        return Invitation(**docs[0].to_dict())

    def accept_invitation(
        self, token: str, uid: str, email: str
    ) -> tuple[Invitation, Member]:
        """Accept an invitation and create the member record.

        Args:
            token: The invitation token.
            uid: Firebase UID of the accepting user.
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
            # Mark as expired
            self._collection().document(invitation.id).update({
                "status": InvitationStatus.EXPIRED.value,
            })
            raise InvitationExpiredError(invitation.id)

        # Check for duplicate membership
        member_service = MemberService(self.db)
        member_service.check_duplicate(invitation.company_id, email)

        # Create the member
        member_id = f"mem_{secrets.token_hex(8)}"
        member_dict = {
            "id": member_id,
            "company_id": invitation.company_id,
            "uid": uid,
            "email": email,
            "display_name": email.split("@")[0],
            "role": invitation.role.value,
            "invited_by": invitation.invited_by,
            "joined_at": now,
            "created_at": now,
            "updated_at": now,
        }

        self.db.collection("companies").document(invitation.company_id).collection(
            "members"
        ).document(member_id).set(member_dict)

        # Update invitation status
        self._collection().document(invitation.id).update({
            "status": InvitationStatus.ACCEPTED.value,
            "accepted_at": now,
        })

        updated_invitation = Invitation(
            **{**invitation.model_dump(), "status": InvitationStatus.ACCEPTED, "accepted_at": now}
        )
        member = Member(**member_dict)

        return updated_invitation, member

    def list_invitations(self, company_id: str) -> list[Invitation]:
        """List all invitations for a company.

        Args:
            company_id: The company document ID.

        Returns:
            A list of Invitation models.
        """
        query = self._collection().where("company_id", "==", company_id)
        docs = list(query.stream())
        return [Invitation(**doc.to_dict()) for doc in docs]

    def revoke_invitation(self, invitation_id: str, company_id: str) -> None:
        """Revoke a pending invitation.

        Args:
            invitation_id: The invitation document ID.
            company_id: The company document ID (for verification).

        Raises:
            InvitationNotFoundError: If the invitation does not exist.
        """
        doc_ref = self._collection().document(invitation_id)
        doc = doc_ref.get()
        if not doc.exists:
            raise InvitationNotFoundError(invitation_id)

        data = doc.to_dict()
        if data.get("company_id") != company_id:
            raise InvitationNotFoundError(invitation_id)

        doc_ref.update({
            "status": InvitationStatus.REVOKED.value,
        })
