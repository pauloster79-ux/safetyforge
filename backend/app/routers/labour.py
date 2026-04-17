"""Labour management router — nested under work items."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.dependencies import get_company_service, get_current_user, get_labour_service
from app.exceptions import LabourNotFoundError
from app.models.labour import Labour, LabourCreate, LabourListResponse, LabourUpdate
from app.services.company_service import CompanyService
from app.services.labour_service import LabourService
from app.services.work_item_service import WorkItemNotFoundError
from app.utils.async_helpers import run_sync

router = APIRouter(prefix="/me", tags=["labour"])


async def _resolve_company(user: dict, company_service: CompanyService):
    """Resolve the current user's company or raise 404."""
    company = await run_sync(company_service.get_by_user, user["uid"])
    if company is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No company profile found for this user",
        )
    return company


@router.post(
    "/projects/{project_id}/work-items/{work_item_id}/labour",
    response_model=Labour,
    status_code=status.HTTP_201_CREATED,
)
async def create_labour(
    project_id: str,
    work_item_id: str,
    data: LabourCreate,
    current_user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    labour_service: Annotated[LabourService, Depends(get_labour_service)],
) -> Labour:
    """Create a labour task on a work item."""
    company = await _resolve_company(current_user, company_service)
    try:
        result = labour_service.create(
            company.id, project_id, work_item_id,
            data.model_dump(), current_user["uid"],
        )
        return Labour(**result)
    except WorkItemNotFoundError:
        raise HTTPException(status_code=404, detail=f"Work item not found: {work_item_id}")


@router.get(
    "/projects/{project_id}/work-items/{work_item_id}/labour",
    response_model=LabourListResponse,
)
async def list_labour(
    project_id: str,
    work_item_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    labour_service: Annotated[LabourService, Depends(get_labour_service)],
) -> LabourListResponse:
    """List all labour tasks for a work item."""
    company = await _resolve_company(current_user, company_service)
    result = labour_service.list_by_work_item(company.id, project_id, work_item_id)
    return LabourListResponse(
        labour=[Labour(**r) for r in result["labour"]],
        total=result["total"],
    )


@router.get(
    "/projects/{project_id}/work-items/{work_item_id}/labour/{labour_id}",
    response_model=Labour,
)
async def get_labour(
    project_id: str,
    work_item_id: str,
    labour_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    labour_service: Annotated[LabourService, Depends(get_labour_service)],
) -> Labour:
    """Get a specific labour task."""
    company = await _resolve_company(current_user, company_service)
    try:
        return Labour(**labour_service.get(company.id, project_id, work_item_id, labour_id))
    except LabourNotFoundError:
        raise HTTPException(status_code=404, detail=f"Labour not found: {labour_id}")


@router.patch(
    "/projects/{project_id}/work-items/{work_item_id}/labour/{labour_id}",
    response_model=Labour,
)
async def update_labour(
    project_id: str,
    work_item_id: str,
    labour_id: str,
    data: LabourUpdate,
    current_user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    labour_service: Annotated[LabourService, Depends(get_labour_service)],
) -> Labour:
    """Update a labour task."""
    company = await _resolve_company(current_user, company_service)
    try:
        result = labour_service.update(
            company.id, project_id, work_item_id, labour_id,
            data.model_dump(exclude_none=True), current_user["uid"],
        )
        return Labour(**result)
    except LabourNotFoundError:
        raise HTTPException(status_code=404, detail=f"Labour not found: {labour_id}")


@router.delete(
    "/projects/{project_id}/work-items/{work_item_id}/labour/{labour_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_labour(
    project_id: str,
    work_item_id: str,
    labour_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    labour_service: Annotated[LabourService, Depends(get_labour_service)],
) -> None:
    """Delete a labour task."""
    company = await _resolve_company(current_user, company_service)
    try:
        labour_service.delete(company.id, project_id, work_item_id, labour_id)
    except LabourNotFoundError:
        raise HTTPException(status_code=404, detail=f"Labour not found: {labour_id}")
