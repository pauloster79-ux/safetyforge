"""Condition management router — contract conditions and prerequisites."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.dependencies import (
    get_company_service,
    get_condition_service,
    get_current_user,
)
from app.exceptions import ConditionNotFoundError, ProjectNotFoundError
from app.models.condition import (
    Condition,
    ConditionCreate,
    ConditionListResponse,
    ConditionUpdate,
)
from app.services.company_service import CompanyService
from app.services.condition_service import ConditionService
from app.utils.async_helpers import run_sync

router = APIRouter(prefix="/me", tags=["conditions"])


async def _resolve_company(user: dict, company_service: CompanyService):
    """Resolve the current user's company or raise 404."""
    company = await run_sync(company_service.get_by_user, user["uid"])
    if company is None:
        raise HTTPException(status_code=404, detail="No company profile found for this user")
    return company


@router.post(
    "/projects/{project_id}/contract/conditions",
    response_model=Condition,
    status_code=status.HTTP_201_CREATED,
)
async def create_condition(
    project_id: str,
    data: ConditionCreate,
    current_user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    condition_service: Annotated[ConditionService, Depends(get_condition_service)],
) -> Condition:
    """Create a condition on a project's contract."""
    company = await _resolve_company(current_user, company_service)
    try:
        result = condition_service.create(
            company.id, project_id, data.model_dump(), current_user["uid"],
        )
        return Condition(**result)
    except ProjectNotFoundError:
        raise HTTPException(status_code=404, detail=f"Project not found: {project_id}")


@router.get(
    "/projects/{project_id}/contract/conditions",
    response_model=ConditionListResponse,
)
async def list_conditions(
    project_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    condition_service: Annotated[ConditionService, Depends(get_condition_service)],
) -> ConditionListResponse:
    """List conditions for a project's contract."""
    company = await _resolve_company(current_user, company_service)
    result = condition_service.list_by_contract(company.id, project_id)
    return ConditionListResponse(
        conditions=[Condition(**r) for r in result["conditions"]],
        total=result["total"],
    )


@router.get(
    "/projects/{project_id}/contract/conditions/{condition_id}",
    response_model=Condition,
)
async def get_condition(
    project_id: str,
    condition_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    condition_service: Annotated[ConditionService, Depends(get_condition_service)],
) -> Condition:
    """Get a specific condition."""
    company = await _resolve_company(current_user, company_service)
    try:
        return Condition(
            **condition_service.get(company.id, project_id, condition_id)
        )
    except ConditionNotFoundError:
        raise HTTPException(
            status_code=404, detail=f"Condition not found: {condition_id}"
        )


@router.patch(
    "/projects/{project_id}/contract/conditions/{condition_id}",
    response_model=Condition,
)
async def update_condition(
    project_id: str,
    condition_id: str,
    data: ConditionUpdate,
    current_user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    condition_service: Annotated[ConditionService, Depends(get_condition_service)],
) -> Condition:
    """Update a condition."""
    company = await _resolve_company(current_user, company_service)
    try:
        result = condition_service.update(
            company.id, project_id, condition_id,
            data.model_dump(exclude_none=True), current_user["uid"],
        )
        return Condition(**result)
    except ConditionNotFoundError:
        raise HTTPException(
            status_code=404, detail=f"Condition not found: {condition_id}"
        )


@router.delete(
    "/projects/{project_id}/contract/conditions/{condition_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_condition(
    project_id: str,
    condition_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    condition_service: Annotated[ConditionService, Depends(get_condition_service)],
) -> None:
    """Delete a condition."""
    company = await _resolve_company(current_user, company_service)
    try:
        condition_service.delete(company.id, project_id, condition_id)
    except ConditionNotFoundError:
        raise HTTPException(
            status_code=404, detail=f"Condition not found: {condition_id}"
        )
