"""Item management router — nested under work items."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.dependencies import get_company_service, get_current_user, get_item_service
from app.exceptions import ItemNotFoundError
from app.models.item import Item, ItemCreate, ItemListResponse, ItemUpdate
from app.services.company_service import CompanyService
from app.services.item_service import ItemService
from app.services.work_item_service import WorkItemNotFoundError
from app.utils.async_helpers import run_sync

router = APIRouter(prefix="/me", tags=["items"])


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
    "/projects/{project_id}/work-items/{work_item_id}/items",
    response_model=Item,
    status_code=status.HTTP_201_CREATED,
)
async def create_item(
    project_id: str,
    work_item_id: str,
    data: ItemCreate,
    current_user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    item_service: Annotated[ItemService, Depends(get_item_service)],
) -> Item:
    """Create an item on a work item."""
    company = await _resolve_company(current_user, company_service)
    try:
        result = item_service.create(
            company.id, project_id, work_item_id,
            data.model_dump(), current_user["uid"],
        )
        return Item(**result)
    except WorkItemNotFoundError:
        raise HTTPException(status_code=404, detail=f"Work item not found: {work_item_id}")


@router.get(
    "/projects/{project_id}/work-items/{work_item_id}/items",
    response_model=ItemListResponse,
)
async def list_items(
    project_id: str,
    work_item_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    item_service: Annotated[ItemService, Depends(get_item_service)],
) -> ItemListResponse:
    """List all items for a work item."""
    company = await _resolve_company(current_user, company_service)
    result = item_service.list_by_work_item(company.id, project_id, work_item_id)
    return ItemListResponse(
        items=[Item(**r) for r in result["items"]],
        total=result["total"],
    )


@router.get(
    "/projects/{project_id}/work-items/{work_item_id}/items/{item_id}",
    response_model=Item,
)
async def get_item(
    project_id: str,
    work_item_id: str,
    item_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    item_service: Annotated[ItemService, Depends(get_item_service)],
) -> Item:
    """Get a specific item."""
    company = await _resolve_company(current_user, company_service)
    try:
        return Item(**item_service.get(company.id, project_id, work_item_id, item_id))
    except ItemNotFoundError:
        raise HTTPException(status_code=404, detail=f"Item not found: {item_id}")


@router.patch(
    "/projects/{project_id}/work-items/{work_item_id}/items/{item_id}",
    response_model=Item,
)
async def update_item(
    project_id: str,
    work_item_id: str,
    item_id: str,
    data: ItemUpdate,
    current_user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    item_service: Annotated[ItemService, Depends(get_item_service)],
) -> Item:
    """Update an item."""
    company = await _resolve_company(current_user, company_service)
    try:
        result = item_service.update(
            company.id, project_id, work_item_id, item_id,
            data.model_dump(exclude_none=True), current_user["uid"],
        )
        return Item(**result)
    except ItemNotFoundError:
        raise HTTPException(status_code=404, detail=f"Item not found: {item_id}")


@router.delete(
    "/projects/{project_id}/work-items/{work_item_id}/items/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_item(
    project_id: str,
    work_item_id: str,
    item_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    item_service: Annotated[ItemService, Depends(get_item_service)],
) -> None:
    """Delete an item."""
    company = await _resolve_company(current_user, company_service)
    try:
        item_service.delete(company.id, project_id, work_item_id, item_id)
    except ItemNotFoundError:
        raise HTTPException(status_code=404, detail=f"Item not found: {item_id}")
