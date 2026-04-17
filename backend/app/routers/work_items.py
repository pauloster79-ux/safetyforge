"""Work item management router — nested under projects."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.dependencies import get_company_service, get_current_user, get_work_item_service
from app.models.work_item import WorkItem, WorkItemUpdate
from app.services.company_service import CompanyService
from app.services.work_item_service import WorkItemNotFoundError, WorkItemService
from app.utils.async_helpers import run_sync

router = APIRouter(prefix="/me", tags=["work-items"])


async def _resolve_company(user: dict, company_service: CompanyService):
    """Resolve the current user's company or raise 404."""
    company = await run_sync(company_service.get_by_user, user["uid"])
    if company is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No company profile found for this user",
        )
    return company


@router.get(
    "/projects/{project_id}/work-items/{work_item_id}",
    response_model=WorkItem,
)
async def get_work_item(
    project_id: str,
    work_item_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    work_item_service: Annotated[WorkItemService, Depends(get_work_item_service)],
) -> WorkItem:
    """Get a specific work item."""
    company = await _resolve_company(current_user, company_service)
    try:
        return WorkItem(**work_item_service.get(company.id, project_id, work_item_id))
    except WorkItemNotFoundError:
        raise HTTPException(status_code=404, detail=f"Work item not found: {work_item_id}")


@router.patch(
    "/projects/{project_id}/work-items/{work_item_id}",
    response_model=WorkItem,
)
async def update_work_item(
    project_id: str,
    work_item_id: str,
    data: WorkItemUpdate,
    current_user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    work_item_service: Annotated[WorkItemService, Depends(get_work_item_service)],
) -> WorkItem:
    """Update a work item. Recalculates sell_price if margin_pct changes."""
    company = await _resolve_company(current_user, company_service)
    try:
        result = work_item_service.update(
            company.id, project_id, work_item_id,
            data.model_dump(exclude_none=True), current_user["uid"],
        )
        return WorkItem(**result)
    except WorkItemNotFoundError:
        raise HTTPException(status_code=404, detail=f"Work item not found: {work_item_id}")


@router.delete(
    "/projects/{project_id}/work-items/{work_item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def archive_work_item(
    project_id: str,
    work_item_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    work_item_service: Annotated[WorkItemService, Depends(get_work_item_service)],
) -> None:
    """Soft-delete (archive) a work item."""
    company = await _resolve_company(current_user, company_service)
    try:
        work_item_service.archive(company.id, project_id, work_item_id, current_user["uid"])
    except WorkItemNotFoundError:
        raise HTTPException(status_code=404, detail=f"Work item not found: {work_item_id}")


@router.post(
    "/projects/{project_id}/work-items/{work_item_id}/restore",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def restore_work_item(
    project_id: str,
    work_item_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    work_item_service: Annotated[WorkItemService, Depends(get_work_item_service)],
) -> None:
    """Restore a previously archived work item (undo delete)."""
    company = await _resolve_company(current_user, company_service)
    try:
        work_item_service.restore(company.id, project_id, work_item_id, current_user["uid"])
    except WorkItemNotFoundError:
        raise HTTPException(status_code=404, detail=f"Work item not found: {work_item_id}")
