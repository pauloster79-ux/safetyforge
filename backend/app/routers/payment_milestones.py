"""Payment milestone management router — contract payment schedule items."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.dependencies import (
    get_company_service,
    get_current_user,
    get_payment_milestone_service,
)
from app.exceptions import PaymentMilestoneNotFoundError, ProjectNotFoundError
from app.models.payment_milestone import (
    PaymentMilestone,
    PaymentMilestoneCreate,
    PaymentMilestoneListResponse,
    PaymentMilestoneUpdate,
)
from app.services.company_service import CompanyService
from app.services.payment_milestone_service import PaymentMilestoneService
from app.utils.async_helpers import run_sync

router = APIRouter(prefix="/me", tags=["payment-milestones"])


async def _resolve_company(user: dict, company_service: CompanyService):
    """Resolve the current user's company or raise 404."""
    company = await run_sync(company_service.get_by_user, user["uid"])
    if company is None:
        raise HTTPException(status_code=404, detail="No company profile found for this user")
    return company


@router.post(
    "/projects/{project_id}/contract/payment-milestones",
    response_model=PaymentMilestone,
    status_code=status.HTTP_201_CREATED,
)
async def create_payment_milestone(
    project_id: str,
    data: PaymentMilestoneCreate,
    current_user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    milestone_service: Annotated[PaymentMilestoneService, Depends(get_payment_milestone_service)],
) -> PaymentMilestone:
    """Create a payment milestone on a project's contract."""
    company = await _resolve_company(current_user, company_service)
    try:
        result = milestone_service.create(
            company.id, project_id, data.model_dump(), current_user["uid"],
        )
        return PaymentMilestone(**result)
    except ProjectNotFoundError:
        raise HTTPException(status_code=404, detail=f"Project not found: {project_id}")


@router.get(
    "/projects/{project_id}/contract/payment-milestones",
    response_model=PaymentMilestoneListResponse,
)
async def list_payment_milestones(
    project_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    milestone_service: Annotated[PaymentMilestoneService, Depends(get_payment_milestone_service)],
) -> PaymentMilestoneListResponse:
    """List payment milestones for a project's contract."""
    company = await _resolve_company(current_user, company_service)
    result = milestone_service.list_by_contract(company.id, project_id)
    return PaymentMilestoneListResponse(
        milestones=[PaymentMilestone(**r) for r in result["milestones"]],
        total=result["total"],
    )


@router.get(
    "/projects/{project_id}/contract/payment-milestones/{milestone_id}",
    response_model=PaymentMilestone,
)
async def get_payment_milestone(
    project_id: str,
    milestone_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    milestone_service: Annotated[PaymentMilestoneService, Depends(get_payment_milestone_service)],
) -> PaymentMilestone:
    """Get a specific payment milestone."""
    company = await _resolve_company(current_user, company_service)
    try:
        return PaymentMilestone(
            **milestone_service.get(company.id, project_id, milestone_id)
        )
    except PaymentMilestoneNotFoundError:
        raise HTTPException(
            status_code=404, detail=f"Payment milestone not found: {milestone_id}"
        )


@router.patch(
    "/projects/{project_id}/contract/payment-milestones/{milestone_id}",
    response_model=PaymentMilestone,
)
async def update_payment_milestone(
    project_id: str,
    milestone_id: str,
    data: PaymentMilestoneUpdate,
    current_user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    milestone_service: Annotated[PaymentMilestoneService, Depends(get_payment_milestone_service)],
) -> PaymentMilestone:
    """Update a payment milestone."""
    company = await _resolve_company(current_user, company_service)
    try:
        result = milestone_service.update(
            company.id, project_id, milestone_id,
            data.model_dump(exclude_none=True), current_user["uid"],
        )
        return PaymentMilestone(**result)
    except PaymentMilestoneNotFoundError:
        raise HTTPException(
            status_code=404, detail=f"Payment milestone not found: {milestone_id}"
        )


@router.delete(
    "/projects/{project_id}/contract/payment-milestones/{milestone_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_payment_milestone(
    project_id: str,
    milestone_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    milestone_service: Annotated[PaymentMilestoneService, Depends(get_payment_milestone_service)],
) -> None:
    """Delete a payment milestone."""
    company = await _resolve_company(current_user, company_service)
    try:
        milestone_service.delete(company.id, project_id, milestone_id)
    except PaymentMilestoneNotFoundError:
        raise HTTPException(
            status_code=404, detail=f"Payment milestone not found: {milestone_id}"
        )
