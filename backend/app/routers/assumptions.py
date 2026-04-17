"""Assumption management router — project-scoped and company templates."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.dependencies import get_assumption_service, get_company_service, get_current_user
from app.exceptions import AssumptionNotFoundError, ProjectNotFoundError
from app.models.assumption import (
    Assumption,
    AssumptionCreate,
    AssumptionListResponse,
    AssumptionTemplate,
    AssumptionTemplateListResponse,
    AssumptionUpdate,
)
from app.services.assumption_service import AssumptionService
from app.services.company_service import CompanyService
from app.utils.async_helpers import run_sync

router = APIRouter(prefix="/me", tags=["assumptions"])


async def _resolve_company(user: dict, company_service: CompanyService):
    """Resolve the current user's company or raise 404."""
    company = await run_sync(company_service.get_by_user, user["uid"])
    if company is None:
        raise HTTPException(status_code=404, detail="No company profile found for this user")
    return company


# -- Project assumptions -----------------------------------------------------------


@router.post(
    "/projects/{project_id}/assumptions",
    response_model=Assumption,
    status_code=status.HTTP_201_CREATED,
)
async def create_assumption(
    project_id: str,
    data: AssumptionCreate,
    current_user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    assumption_service: Annotated[AssumptionService, Depends(get_assumption_service)],
) -> Assumption:
    """Create an assumption on a project."""
    company = await _resolve_company(current_user, company_service)
    try:
        result = assumption_service.create(
            company.id, project_id, data.model_dump(), current_user["uid"],
        )
        return Assumption(**result)
    except ProjectNotFoundError:
        raise HTTPException(status_code=404, detail=f"Project not found: {project_id}")


@router.get(
    "/projects/{project_id}/assumptions",
    response_model=AssumptionListResponse,
)
async def list_assumptions(
    project_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    assumption_service: Annotated[AssumptionService, Depends(get_assumption_service)],
    category: str | None = Query(None),
) -> AssumptionListResponse:
    """List assumptions for a project."""
    company = await _resolve_company(current_user, company_service)
    result = assumption_service.list_by_project(company.id, project_id, category)
    return AssumptionListResponse(
        assumptions=[Assumption(**r) for r in result["assumptions"]],
        total=result["total"],
    )


@router.get(
    "/projects/{project_id}/assumptions/{assumption_id}",
    response_model=Assumption,
)
async def get_assumption(
    project_id: str,
    assumption_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    assumption_service: Annotated[AssumptionService, Depends(get_assumption_service)],
) -> Assumption:
    """Get a specific assumption."""
    company = await _resolve_company(current_user, company_service)
    try:
        return Assumption(**assumption_service.get(company.id, project_id, assumption_id))
    except AssumptionNotFoundError:
        raise HTTPException(status_code=404, detail=f"Assumption not found: {assumption_id}")


@router.patch(
    "/projects/{project_id}/assumptions/{assumption_id}",
    response_model=Assumption,
)
async def update_assumption(
    project_id: str,
    assumption_id: str,
    data: AssumptionUpdate,
    current_user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    assumption_service: Annotated[AssumptionService, Depends(get_assumption_service)],
) -> Assumption:
    """Update an assumption."""
    company = await _resolve_company(current_user, company_service)
    try:
        result = assumption_service.update(
            company.id, project_id, assumption_id,
            data.model_dump(exclude_none=True), current_user["uid"],
        )
        return Assumption(**result)
    except AssumptionNotFoundError:
        raise HTTPException(status_code=404, detail=f"Assumption not found: {assumption_id}")


@router.delete(
    "/projects/{project_id}/assumptions/{assumption_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_assumption(
    project_id: str,
    assumption_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    assumption_service: Annotated[AssumptionService, Depends(get_assumption_service)],
) -> None:
    """Delete an assumption."""
    company = await _resolve_company(current_user, company_service)
    try:
        assumption_service.delete(company.id, project_id, assumption_id)
    except AssumptionNotFoundError:
        raise HTTPException(status_code=404, detail=f"Assumption not found: {assumption_id}")


# -- Company templates -------------------------------------------------------------


@router.post(
    "/assumption-templates",
    response_model=AssumptionTemplate,
    status_code=status.HTTP_201_CREATED,
)
async def create_assumption_template(
    data: AssumptionCreate,
    current_user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    assumption_service: Annotated[AssumptionService, Depends(get_assumption_service)],
) -> AssumptionTemplate:
    """Create a company-level assumption template."""
    company = await _resolve_company(current_user, company_service)
    result = assumption_service.create_template(
        company.id, data.model_dump(), current_user["uid"],
    )
    return AssumptionTemplate(**result)


@router.get(
    "/assumption-templates",
    response_model=AssumptionTemplateListResponse,
)
async def list_assumption_templates(
    current_user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    assumption_service: Annotated[AssumptionService, Depends(get_assumption_service)],
    trade_type: str | None = Query(None),
) -> AssumptionTemplateListResponse:
    """List company assumption templates."""
    company = await _resolve_company(current_user, company_service)
    result = assumption_service.list_templates(company.id, trade_type)
    return AssumptionTemplateListResponse(
        templates=[AssumptionTemplate(**r) for r in result["templates"]],
        total=result["total"],
    )


@router.post(
    "/projects/{project_id}/assumptions/from-template/{template_id}",
    response_model=Assumption,
    status_code=status.HTTP_201_CREATED,
)
async def copy_assumption_from_template(
    project_id: str,
    template_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    assumption_service: Annotated[AssumptionService, Depends(get_assumption_service)],
) -> Assumption:
    """Copy a company template as a project assumption."""
    company = await _resolve_company(current_user, company_service)
    try:
        result = assumption_service.copy_template_to_project(
            company.id, project_id, template_id, current_user["uid"],
        )
        return Assumption(**result)
    except AssumptionNotFoundError:
        raise HTTPException(status_code=404, detail=f"Template not found: {template_id}")
