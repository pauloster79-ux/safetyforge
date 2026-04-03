"""GC/Sub Portal router for managing GC-Sub relationships and compliance visibility."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.dependencies import (
    get_company_service,
    get_current_user,
    get_gc_portal_service,
)
from app.exceptions import (
    CompanyNotFoundError,
    GcInvitationNotFoundError,
    GcRelationshipNotFoundError,
)
from app.models.gc_portal import (
    GcInvitation,
    GcRelationship,
    GcRelationshipCreate,
    GcRelationshipListResponse,
    InviteSubRequest,
    SubComplianceDashboard,
    SubComplianceSummary,
)
from app.services.company_service import CompanyService
from app.services.gc_portal_service import GcPortalService

router = APIRouter(prefix="/gc-portal", tags=["gc-portal"])


def _resolve_company(user: dict, company_service: CompanyService):
    """Resolve the current user's company or raise 404.

    Args:
        user: The current user claims dict.
        company_service: CompanyService instance.

    Returns:
        The user's Company.

    Raises:
        HTTPException: 404 if no company found.
    """
    company = company_service.get_by_user(user["uid"])
    if company is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No company profile found for this user",
        )
    return company


@router.post("/relationships", response_model=GcRelationship)
async def create_relationship(
    data: GcRelationshipCreate,
    current_user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    gc_service: Annotated[GcPortalService, Depends(get_gc_portal_service)],
) -> GcRelationship:
    """Create a new GC/Sub relationship.

    The current user's company is the GC in the relationship.

    Args:
        data: Relationship creation data including sub company ID.
        current_user: Authenticated user claims.
        company_service: CompanyService dependency.
        gc_service: GcPortalService dependency.

    Returns:
        The created GcRelationship.
    """
    company = _resolve_company(current_user, company_service)
    try:
        return gc_service.create_relationship(
            gc_company_id=company.id,
            data=data,
        )
    except CompanyNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )


@router.get("/my-subs", response_model=GcRelationshipListResponse)
async def list_my_subs(
    current_user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    gc_service: Annotated[GcPortalService, Depends(get_gc_portal_service)],
) -> GcRelationshipListResponse:
    """List all sub-contractors for the current user's company (as GC).

    Args:
        current_user: Authenticated user claims.
        company_service: CompanyService dependency.
        gc_service: GcPortalService dependency.

    Returns:
        A GcRelationshipListResponse with sub relationships.
    """
    company = _resolve_company(current_user, company_service)
    result = gc_service.get_relationships_as_gc(company.id)
    return GcRelationshipListResponse(**result)


@router.get("/my-gcs", response_model=GcRelationshipListResponse)
async def list_my_gcs(
    current_user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    gc_service: Annotated[GcPortalService, Depends(get_gc_portal_service)],
) -> GcRelationshipListResponse:
    """List all GCs for the current user's company (as sub-contractor).

    Args:
        current_user: Authenticated user claims.
        company_service: CompanyService dependency.
        gc_service: GcPortalService dependency.

    Returns:
        A GcRelationshipListResponse with GC relationships.
    """
    company = _resolve_company(current_user, company_service)
    result = gc_service.get_relationships_as_sub(company.id)
    return GcRelationshipListResponse(**result)


@router.get("/subs/{sub_id}/compliance", response_model=SubComplianceSummary)
async def get_sub_compliance(
    sub_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    gc_service: Annotated[GcPortalService, Depends(get_gc_portal_service)],
) -> SubComplianceSummary:
    """Get compliance summary for a specific sub-contractor.

    Requires an active GC/Sub relationship.

    Args:
        sub_id: The sub-contractor's company ID.
        current_user: Authenticated user claims.
        company_service: CompanyService dependency.
        gc_service: GcPortalService dependency.

    Returns:
        A SubComplianceSummary with live compliance data.
    """
    company = _resolve_company(current_user, company_service)
    try:
        return gc_service.get_sub_compliance_summary(company.id, sub_id)
    except GcRelationshipNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No active relationship with sub-contractor: {sub_id}",
        )
    except CompanyNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sub-contractor company not found: {sub_id}",
        )


@router.get("/dashboard", response_model=SubComplianceDashboard)
async def get_gc_dashboard(
    current_user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    gc_service: Annotated[GcPortalService, Depends(get_gc_portal_service)],
) -> SubComplianceDashboard:
    """Get compliance dashboard with all sub-contractor summaries.

    Args:
        current_user: Authenticated user claims.
        company_service: CompanyService dependency.
        gc_service: GcPortalService dependency.

    Returns:
        A SubComplianceDashboard with all sub summaries.
    """
    company = _resolve_company(current_user, company_service)
    result = gc_service.get_all_sub_summaries(company.id)
    return SubComplianceDashboard(**result)


@router.post("/invite", response_model=GcInvitation)
async def invite_sub(
    data: InviteSubRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    gc_service: Annotated[GcPortalService, Depends(get_gc_portal_service)],
) -> GcInvitation:
    """Invite a sub-contractor to connect via email.

    Args:
        data: Invitation data with sub email and optional project name.
        current_user: Authenticated user claims.
        company_service: CompanyService dependency.
        gc_service: GcPortalService dependency.

    Returns:
        The created GcInvitation.
    """
    company = _resolve_company(current_user, company_service)
    return gc_service.invite_sub(
        gc_company_id=company.id,
        sub_email=data.sub_email,
        project_name=data.project_name,
    )


@router.post("/accept/{invitation_id}", response_model=GcRelationship)
async def accept_invitation(
    invitation_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    gc_service: Annotated[GcPortalService, Depends(get_gc_portal_service)],
) -> GcRelationship:
    """Accept a GC invitation and create the relationship.

    The current user's company becomes the sub-contractor in the relationship.

    Args:
        invitation_id: The invitation ID to accept.
        current_user: Authenticated user claims.
        company_service: CompanyService dependency.
        gc_service: GcPortalService dependency.

    Returns:
        The created GcRelationship.
    """
    company = _resolve_company(current_user, company_service)
    try:
        return gc_service.accept_invitation(invitation_id, company.id)
    except GcInvitationNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Invitation not found or already accepted: {invitation_id}",
        )
    except CompanyNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )
