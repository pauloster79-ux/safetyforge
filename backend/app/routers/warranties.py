"""Warranty management router — single warranty per contract (upsert semantics)."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.dependencies import (
    get_company_service,
    get_current_user,
    get_warranty_service,
)
from app.exceptions import ProjectNotFoundError, WarrantyNotFoundError
from app.models.warranty import Warranty, WarrantyCreate
from app.services.company_service import CompanyService
from app.services.warranty_service import WarrantyService
from app.utils.async_helpers import run_sync

router = APIRouter(prefix="/me", tags=["warranties"])


async def _resolve_company(user: dict, company_service: CompanyService):
    """Resolve the current user's company or raise 404."""
    company = await run_sync(company_service.get_by_user, user["uid"])
    if company is None:
        raise HTTPException(status_code=404, detail="No company profile found for this user")
    return company


@router.put(
    "/projects/{project_id}/contract/warranty",
    response_model=Warranty,
)
async def set_warranty(
    project_id: str,
    data: WarrantyCreate,
    current_user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    warranty_service: Annotated[WarrantyService, Depends(get_warranty_service)],
) -> Warranty:
    """Set the warranty on a project's contract (upsert — replaces existing)."""
    company = await _resolve_company(current_user, company_service)
    try:
        result = warranty_service.set_warranty(
            company.id, project_id, data.model_dump(), current_user["uid"],
        )
        return Warranty(**result)
    except ProjectNotFoundError:
        raise HTTPException(status_code=404, detail=f"Project not found: {project_id}")


@router.get(
    "/projects/{project_id}/contract/warranty",
    response_model=Warranty,
)
async def get_warranty(
    project_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    warranty_service: Annotated[WarrantyService, Depends(get_warranty_service)],
) -> Warranty:
    """Get the warranty for a project's contract."""
    company = await _resolve_company(current_user, company_service)
    try:
        return Warranty(**warranty_service.get_by_contract(company.id, project_id))
    except WarrantyNotFoundError:
        raise HTTPException(
            status_code=404, detail=f"No warranty found for project: {project_id}"
        )


@router.delete(
    "/projects/{project_id}/contract/warranty",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_warranty(
    project_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    warranty_service: Annotated[WarrantyService, Depends(get_warranty_service)],
) -> None:
    """Delete the warranty on a project's contract."""
    company = await _resolve_company(current_user, company_service)
    try:
        warranty_service.delete(company.id, project_id)
    except WarrantyNotFoundError:
        raise HTTPException(
            status_code=404, detail=f"No warranty found for project: {project_id}"
        )
