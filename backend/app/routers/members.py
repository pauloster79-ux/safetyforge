"""Members and invitations router for multi-user RBAC."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.dependencies import (
    get_company_service,
    get_current_user,
    get_invitation_service,
    get_member_service,
)
from app.exceptions import (
    CompanyNotFoundError,
    DuplicateMemberError,
    InsufficientPermissionError,
    InvitationExpiredError,
    InvitationNotFoundError,
    MemberNotFoundError,
)
from app.models.member import (
    Invitation,
    InvitationCreate,
    Member,
    MemberRole,
    MemberUpdate,
)
from app.services.company_service import CompanyService
from app.services.invitation_service import InvitationService
from app.services.member_service import MemberService

router = APIRouter(tags=["members"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _resolve_company_id(user: dict, company_service: CompanyService) -> str:
    """Resolve the current user's company ID.

    Args:
        user: Decoded Firebase token dict.
        company_service: CompanyService instance.

    Returns:
        The company ID.

    Raises:
        HTTPException: 404 if no company is associated with the user.
    """
    company = company_service.get_by_user(user["uid"])
    if company is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No company found for current user",
        )
    return company.id


# ---------------------------------------------------------------------------
# Member endpoints (scoped to /me/members)
# ---------------------------------------------------------------------------


@router.get("/me/members", response_model=list[Member])
async def list_members(
    user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    member_service: Annotated[MemberService, Depends(get_member_service)],
) -> list[Member]:
    """List all members of the current user's company.

    Any member can see the member list.
    """
    company_id = _resolve_company_id(user, company_service)
    try:
        member_service.check_permission(company_id, user["uid"], MemberRole.VIEWER)
    except InsufficientPermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this company",
        )
    return member_service.get_members(company_id)


@router.post("/me/members/invite", response_model=Invitation, status_code=status.HTTP_201_CREATED)
async def invite_member(
    data: InvitationCreate,
    user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    member_service: Annotated[MemberService, Depends(get_member_service)],
    invitation_service: Annotated[InvitationService, Depends(get_invitation_service)],
) -> Invitation:
    """Send a member invitation. Requires admin role or higher."""
    company_id = _resolve_company_id(user, company_service)
    try:
        member_service.check_permission(company_id, user["uid"], MemberRole.ADMIN)
    except InsufficientPermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin role or higher required to invite members",
        )

    # Check for existing member with this email
    try:
        member_service.check_duplicate(company_id, data.email)
    except DuplicateMemberError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A member with email {data.email} already exists",
        )

    company = company_service.get(company_id)
    return invitation_service.create_invitation(
        company_id=company_id,
        company_name=company.name,
        data=data,
        invited_by_uid=user["uid"],
        invited_by_email=user["email"],
    )


@router.get("/me/members/invitations", response_model=list[Invitation])
async def list_invitations(
    user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    member_service: Annotated[MemberService, Depends(get_member_service)],
    invitation_service: Annotated[InvitationService, Depends(get_invitation_service)],
) -> list[Invitation]:
    """List all invitations for the current user's company. Requires admin role or higher."""
    company_id = _resolve_company_id(user, company_service)
    try:
        member_service.check_permission(company_id, user["uid"], MemberRole.ADMIN)
    except InsufficientPermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin role or higher required to view invitations",
        )
    return invitation_service.list_invitations(company_id)


@router.patch("/me/members/{member_id}", response_model=Member)
async def update_member(
    member_id: str,
    data: MemberUpdate,
    user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    member_service: Annotated[MemberService, Depends(get_member_service)],
) -> Member:
    """Update a member's role or display name. Requires owner role."""
    company_id = _resolve_company_id(user, company_service)
    try:
        member_service.check_permission(company_id, user["uid"], MemberRole.OWNER)
    except InsufficientPermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Owner role required to update member roles",
        )

    try:
        return member_service.update_member(company_id, member_id, data, user["uid"])
    except MemberNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Member not found: {member_id}",
        )


@router.delete("/me/members/{member_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_member(
    member_id: str,
    user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    member_service: Annotated[MemberService, Depends(get_member_service)],
) -> None:
    """Remove a member from the company. Requires admin role or higher. Cannot remove the owner."""
    company_id = _resolve_company_id(user, company_service)
    try:
        member_service.check_permission(company_id, user["uid"], MemberRole.ADMIN)
    except InsufficientPermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin role or higher required to remove members",
        )

    # Check that we're not removing the owner
    try:
        members = member_service.get_members(company_id)
        target = next((m for m in members if m.id == member_id), None)
        if target is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Member not found: {member_id}",
            )
        if target.role == MemberRole.OWNER:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot remove the company owner",
            )
        member_service.remove_member(company_id, member_id)
    except MemberNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Member not found: {member_id}",
        )


@router.delete(
    "/me/members/invitations/{invitation_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def revoke_invitation(
    invitation_id: str,
    user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    member_service: Annotated[MemberService, Depends(get_member_service)],
    invitation_service: Annotated[InvitationService, Depends(get_invitation_service)],
) -> None:
    """Revoke a pending invitation. Requires admin role or higher."""
    company_id = _resolve_company_id(user, company_service)
    try:
        member_service.check_permission(company_id, user["uid"], MemberRole.ADMIN)
    except InsufficientPermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin role or higher required to revoke invitations",
        )

    try:
        invitation_service.revoke_invitation(invitation_id, company_id)
    except InvitationNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Invitation not found: {invitation_id}",
        )


# ---------------------------------------------------------------------------
# Public invitation endpoints
# ---------------------------------------------------------------------------


@router.get("/invitations/{token}", response_model=Invitation)
async def get_invitation(
    token: str,
    invitation_service: Annotated[InvitationService, Depends(get_invitation_service)],
) -> Invitation:
    """View invitation details by token. No authentication required.

    This endpoint is intentionally unauthenticated so invitation links
    can be previewed before the user signs in.
    """
    try:
        return invitation_service.get_invitation_by_token(token)
    except InvitationNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invitation not found or invalid token",
        )


class AcceptInvitationRequest(BaseModel):
    """Request body for accepting an invitation."""

    token: str


@router.post("/invitations/accept", response_model=Member, status_code=status.HTTP_201_CREATED)
async def accept_invitation(
    data: AcceptInvitationRequest,
    user: Annotated[dict, Depends(get_current_user)],
    invitation_service: Annotated[InvitationService, Depends(get_invitation_service)],
) -> Member:
    """Accept an invitation and join the company."""
    try:
        invitation, member = invitation_service.accept_invitation(
            token=data.token,
            uid=user["uid"],
            email=user["email"],
        )
        return member
    except InvitationNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invitation not found or invalid token",
        )
    except InvitationExpiredError:
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="Invitation has expired or is no longer pending",
        )
    except DuplicateMemberError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You are already a member of this company",
        )
