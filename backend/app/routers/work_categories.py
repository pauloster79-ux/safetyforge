"""Work category router — canonical + extension model.

Exposes:
* ``GET /me/work-categories/canonical`` — list canonical tree for a jurisdiction
* ``GET /me/work-categories`` — merged view for the current company (canonical +
  extensions + aliases applied)
* ``POST /me/work-categories/aliases`` — add a display-name alias for a canonical
* ``POST /me/work-categories/extensions`` — add a company-scoped leaf extension
* ``GET /me/work-categories/{id}`` — resolve a single category (canonical OR
  extension), with access-scope check

See docs/design/canonical-work-categories.md for the two-tier model.
"""

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.dependencies import (
    get_company_service,
    get_current_user,
    get_work_category_service,
)
from app.services.company_service import CompanyService
from app.services.work_category_service import WorkCategoryService
from app.utils.async_helpers import run_sync


router = APIRouter(prefix="/me/work-categories", tags=["work-categories"])


async def _resolve_company(user: dict, company_service: CompanyService):
    """Resolve the current user's company or raise 404."""
    company = await run_sync(company_service.get_by_user, user["uid"])
    if company is None:
        raise HTTPException(status_code=404, detail="No company profile found for this user")
    return company


# ---------------------------------------------------------------------------
# Request / response models
# ---------------------------------------------------------------------------


class AliasCreate(BaseModel):
    """Input for creating a company alias on a canonical category."""

    canonical_id: str = Field(..., description="ID of the canonical category to alias")
    display_name: str = Field(..., min_length=1, max_length=128)


class ExtensionCreate(BaseModel):
    """Input for creating a company extension under a canonical parent."""

    parent_canonical_id: str = Field(..., description="ID of the canonical parent")
    name: str = Field(..., min_length=1, max_length=128)
    description: str | None = Field(None, max_length=500)


class CanonicalListResponse(BaseModel):
    """List of canonical categories for a jurisdiction."""

    jurisdiction_code: str
    categories: list[dict[str, Any]]
    total: int


class CompanyCategoriesResponse(BaseModel):
    """Merged category view for a company — canonical, extensions, aliases."""

    jurisdiction_code: str
    canonical: list[dict[str, Any]]
    extensions: list[dict[str, Any]]
    aliases: list[dict[str, Any]]


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("/canonical", response_model=CanonicalListResponse)
async def list_canonical_categories(
    current_user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    service: Annotated[WorkCategoryService, Depends(get_work_category_service)],
    jurisdiction_code: str | None = Query(
        None,
        description="Jurisdiction code (us, ca, uk, ie, au, nz). Defaults to the "
                    "company's jurisdiction if not provided.",
    ),
    level: int | None = Query(None, ge=1, le=4),
    parent_code: str | None = Query(None),
    search: str | None = Query(None, min_length=1, max_length=100),
    limit: int = Query(200, ge=1, le=500),
) -> CanonicalListResponse:
    """List canonical categories for a jurisdiction.

    Search is case-insensitive and matches on name or code. Combine with
    ``parent_code`` to drill into a subtree.
    """
    if jurisdiction_code is None:
        company = await _resolve_company(current_user, company_service)
        jurisdiction_code = (company.jurisdiction_code or "us").lower()

    categories = await run_sync(
        service.list_canonical,
        jurisdiction_code=jurisdiction_code,
        level=level,
        parent_code=parent_code,
        search=search,
        limit=limit,
    )
    return CanonicalListResponse(
        jurisdiction_code=jurisdiction_code,
        categories=categories,
        total=len(categories),
    )


@router.get("", response_model=CompanyCategoriesResponse)
async def list_company_categories(
    current_user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    service: Annotated[WorkCategoryService, Depends(get_work_category_service)],
    search: str | None = Query(None, min_length=1, max_length=100),
    limit: int = Query(200, ge=1, le=500),
) -> CompanyCategoriesResponse:
    """Merged category view for the current company.

    Returns the canonical tree for the company's jurisdiction, plus any
    company-scoped extensions and aliases.
    """
    company = await _resolve_company(current_user, company_service)
    jurisdiction_code = (company.jurisdiction_code or "us").lower()

    merged = await run_sync(
        service.list_for_company,
        company_id=company.id,
        jurisdiction_code=jurisdiction_code,
        search=search,
        limit=limit,
    )
    return CompanyCategoriesResponse(
        jurisdiction_code=jurisdiction_code,
        canonical=merged["canonical"],
        extensions=merged["extensions"],
        aliases=merged["aliases"],
    )


@router.post(
    "/aliases",
    status_code=status.HTTP_201_CREATED,
)
async def create_alias(
    data: AliasCreate,
    current_user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    service: Annotated[WorkCategoryService, Depends(get_work_category_service)],
) -> dict[str, Any]:
    """Add a display-name alias for a canonical category."""
    company = await _resolve_company(current_user, company_service)
    try:
        return await run_sync(
            service.add_alias,
            company_id=company.id,
            canonical_id=data.canonical_id,
            display_name=data.display_name,
            user_id=current_user["uid"],
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post(
    "/extensions",
    status_code=status.HTTP_201_CREATED,
)
async def create_extension(
    data: ExtensionCreate,
    current_user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    service: Annotated[WorkCategoryService, Depends(get_work_category_service)],
) -> dict[str, Any]:
    """Add a company extension leaf under a canonical parent."""
    company = await _resolve_company(current_user, company_service)
    try:
        return await run_sync(
            service.add_extension,
            company_id=company.id,
            parent_canonical_id=data.parent_canonical_id,
            name=data.name,
            description=data.description,
            user_id=current_user["uid"],
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/{category_id}")
async def resolve_category(
    category_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    service: Annotated[WorkCategoryService, Depends(get_work_category_service)],
) -> dict[str, Any]:
    """Resolve a category by ID (canonical or company extension).

    Used by the WorkItem creation flow to validate ``work_category_id`` before
    writing ``CATEGORISED_AS``. Extensions are scope-checked against the current
    company so one tenant cannot reference another tenant's extension.
    """
    company = await _resolve_company(current_user, company_service)
    result = await run_sync(
        service.resolve_for_work_item,
        company_id=company.id,
        category_id=category_id,
    )
    if result is None:
        raise HTTPException(
            status_code=404,
            detail=f"Category {category_id} not found or not accessible to this company",
        )
    return result
