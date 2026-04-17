"""Exclusion management router — project-scoped and company templates."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.dependencies import get_company_service, get_current_user, get_exclusion_service
from app.exceptions import ExclusionNotFoundError, ProjectNotFoundError
from app.models.exclusion import (
    Exclusion,
    ExclusionCreate,
    ExclusionListResponse,
    ExclusionTemplate,
    ExclusionTemplateListResponse,
    ExclusionUpdate,
)
from app.services.company_service import CompanyService
from app.services.exclusion_service import ExclusionService
from app.utils.async_helpers import run_sync

router = APIRouter(prefix="/me", tags=["exclusions"])


async def _resolve_company(user: dict, company_service: CompanyService):
    """Resolve the current user's company or raise 404."""
    company = await run_sync(company_service.get_by_user, user["uid"])
    if company is None:
        raise HTTPException(status_code=404, detail="No company profile found for this user")
    return company


# -- Project exclusions ------------------------------------------------------------


@router.post(
    "/projects/{project_id}/exclusions",
    response_model=Exclusion,
    status_code=status.HTTP_201_CREATED,
)
async def create_exclusion(
    project_id: str,
    data: ExclusionCreate,
    current_user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    exclusion_service: Annotated[ExclusionService, Depends(get_exclusion_service)],
) -> Exclusion:
    """Create an exclusion on a project."""
    company = await _resolve_company(current_user, company_service)
    try:
        result = exclusion_service.create(
            company.id, project_id, data.model_dump(), current_user["uid"],
        )
        return Exclusion(**result)
    except ProjectNotFoundError:
        raise HTTPException(status_code=404, detail=f"Project not found: {project_id}")


@router.get(
    "/projects/{project_id}/exclusions",
    response_model=ExclusionListResponse,
)
async def list_exclusions(
    project_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    exclusion_service: Annotated[ExclusionService, Depends(get_exclusion_service)],
    category: str | None = Query(None),
) -> ExclusionListResponse:
    """List exclusions for a project."""
    company = await _resolve_company(current_user, company_service)
    result = exclusion_service.list_by_project(company.id, project_id, category)
    return ExclusionListResponse(
        exclusions=[Exclusion(**r) for r in result["exclusions"]],
        total=result["total"],
    )


@router.get(
    "/projects/{project_id}/exclusions/{exclusion_id}",
    response_model=Exclusion,
)
async def get_exclusion(
    project_id: str,
    exclusion_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    exclusion_service: Annotated[ExclusionService, Depends(get_exclusion_service)],
) -> Exclusion:
    """Get a specific exclusion."""
    company = await _resolve_company(current_user, company_service)
    try:
        return Exclusion(**exclusion_service.get(company.id, project_id, exclusion_id))
    except ExclusionNotFoundError:
        raise HTTPException(status_code=404, detail=f"Exclusion not found: {exclusion_id}")


@router.patch(
    "/projects/{project_id}/exclusions/{exclusion_id}",
    response_model=Exclusion,
)
async def update_exclusion(
    project_id: str,
    exclusion_id: str,
    data: ExclusionUpdate,
    current_user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    exclusion_service: Annotated[ExclusionService, Depends(get_exclusion_service)],
) -> Exclusion:
    """Update an exclusion."""
    company = await _resolve_company(current_user, company_service)
    try:
        result = exclusion_service.update(
            company.id, project_id, exclusion_id,
            data.model_dump(exclude_none=True), current_user["uid"],
        )
        return Exclusion(**result)
    except ExclusionNotFoundError:
        raise HTTPException(status_code=404, detail=f"Exclusion not found: {exclusion_id}")


@router.delete(
    "/projects/{project_id}/exclusions/{exclusion_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_exclusion(
    project_id: str,
    exclusion_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    exclusion_service: Annotated[ExclusionService, Depends(get_exclusion_service)],
) -> None:
    """Delete an exclusion."""
    company = await _resolve_company(current_user, company_service)
    try:
        exclusion_service.delete(company.id, project_id, exclusion_id)
    except ExclusionNotFoundError:
        raise HTTPException(status_code=404, detail=f"Exclusion not found: {exclusion_id}")


# -- Company templates -------------------------------------------------------------


@router.post(
    "/exclusion-templates",
    response_model=ExclusionTemplate,
    status_code=status.HTTP_201_CREATED,
)
async def create_exclusion_template(
    data: ExclusionCreate,
    current_user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    exclusion_service: Annotated[ExclusionService, Depends(get_exclusion_service)],
) -> ExclusionTemplate:
    """Create a company-level exclusion template."""
    company = await _resolve_company(current_user, company_service)
    result = exclusion_service.create_template(
        company.id, data.model_dump(), current_user["uid"],
    )
    return ExclusionTemplate(**result)


@router.get(
    "/exclusion-templates",
    response_model=ExclusionTemplateListResponse,
)
async def list_exclusion_templates(
    current_user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    exclusion_service: Annotated[ExclusionService, Depends(get_exclusion_service)],
    trade_type: str | None = Query(None),
) -> ExclusionTemplateListResponse:
    """List company exclusion templates."""
    company = await _resolve_company(current_user, company_service)
    result = exclusion_service.list_templates(company.id, trade_type)
    return ExclusionTemplateListResponse(
        templates=[ExclusionTemplate(**r) for r in result["templates"]],
        total=result["total"],
    )


@router.post(
    "/projects/{project_id}/exclusions/from-template/{template_id}",
    response_model=Exclusion,
    status_code=status.HTTP_201_CREATED,
)
async def copy_exclusion_from_template(
    project_id: str,
    template_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    exclusion_service: Annotated[ExclusionService, Depends(get_exclusion_service)],
) -> Exclusion:
    """Copy a company template as a project exclusion."""
    company = await _resolve_company(current_user, company_service)
    try:
        result = exclusion_service.copy_template_to_project(
            company.id, project_id, template_id, current_user["uid"],
        )
        return Exclusion(**result)
    except ExclusionNotFoundError:
        raise HTTPException(status_code=404, detail=f"Template not found: {template_id}")
