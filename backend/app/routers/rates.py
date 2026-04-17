"""Resource rate and productivity rate management router — company level."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.dependencies import (
    get_company_service,
    get_current_user,
    get_productivity_rate_service,
    get_resource_rate_service,
)
from app.exceptions import ProductivityRateNotFoundError, ResourceRateNotFoundError
from app.models.productivity_rate import (
    ProductivityRate,
    ProductivityRateCreate,
    ProductivityRateListResponse,
    ProductivityRateUpdate,
)
from app.models.resource_rate import (
    ResourceRate,
    ResourceRateCreate,
    ResourceRateListResponse,
    ResourceRateUpdate,
)
from app.services.company_service import CompanyService
from app.services.productivity_rate_service import ProductivityRateService
from app.services.resource_rate_service import ResourceRateService
from app.utils.async_helpers import run_sync

router = APIRouter(prefix="/me", tags=["rates"])


async def _resolve_company(user: dict, company_service: CompanyService):
    """Resolve the current user's company or raise 404."""
    company = await run_sync(company_service.get_by_user, user["uid"])
    if company is None:
        raise HTTPException(status_code=404, detail="No company profile found for this user")
    return company


# -- Resource Rates ----------------------------------------------------------------


@router.post(
    "/rates",
    response_model=ResourceRate,
    status_code=status.HTTP_201_CREATED,
)
async def create_resource_rate(
    data: ResourceRateCreate,
    current_user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    rate_service: Annotated[ResourceRateService, Depends(get_resource_rate_service)],
) -> ResourceRate:
    """Create a resource rate."""
    company = await _resolve_company(current_user, company_service)
    result = rate_service.create(company.id, data.model_dump(), current_user["uid"])
    return ResourceRate(**result)


@router.get("/rates", response_model=ResourceRateListResponse)
async def list_resource_rates(
    current_user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    rate_service: Annotated[ResourceRateService, Depends(get_resource_rate_service)],
    resource_type: str | None = Query(None),
    active_only: bool = Query(True),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> ResourceRateListResponse:
    """List resource rates for the company."""
    company = await _resolve_company(current_user, company_service)
    result = rate_service.list_rates(
        company.id, resource_type=resource_type, active_only=active_only,
        limit=limit, offset=offset,
    )
    return ResourceRateListResponse(
        rates=[ResourceRate(**r) for r in result["rates"]],
        total=result["total"],
    )


@router.get("/rates/{rate_id}", response_model=ResourceRate)
async def get_resource_rate(
    rate_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    rate_service: Annotated[ResourceRateService, Depends(get_resource_rate_service)],
) -> ResourceRate:
    """Get a specific resource rate."""
    company = await _resolve_company(current_user, company_service)
    try:
        return ResourceRate(**rate_service.get(company.id, rate_id))
    except ResourceRateNotFoundError:
        raise HTTPException(status_code=404, detail=f"Rate not found: {rate_id}")


@router.patch("/rates/{rate_id}", response_model=ResourceRate)
async def update_resource_rate(
    rate_id: str,
    data: ResourceRateUpdate,
    current_user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    rate_service: Annotated[ResourceRateService, Depends(get_resource_rate_service)],
) -> ResourceRate:
    """Update a resource rate."""
    company = await _resolve_company(current_user, company_service)
    try:
        result = rate_service.update(
            company.id, rate_id, data.model_dump(exclude_none=True), current_user["uid"],
        )
        return ResourceRate(**result)
    except ResourceRateNotFoundError:
        raise HTTPException(status_code=404, detail=f"Rate not found: {rate_id}")


@router.post("/rates/{rate_id}/deactivate", response_model=ResourceRate)
async def deactivate_resource_rate(
    rate_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    rate_service: Annotated[ResourceRateService, Depends(get_resource_rate_service)],
) -> ResourceRate:
    """Deactivate a resource rate."""
    company = await _resolve_company(current_user, company_service)
    try:
        return ResourceRate(**rate_service.deactivate(company.id, rate_id, current_user["uid"]))
    except ResourceRateNotFoundError:
        raise HTTPException(status_code=404, detail=f"Rate not found: {rate_id}")


@router.get("/rates/derive/{resource_type}")
async def derive_rate_from_actuals(
    resource_type: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    rate_service: Annotated[ResourceRateService, Depends(get_resource_rate_service)],
    description: str | None = Query(None),
    work_category_id: str | None = Query(None),
) -> dict:
    """Derive a rate from completed job actuals."""
    company = await _resolve_company(current_user, company_service)
    return rate_service.derive_from_actuals(
        company.id, resource_type, description, work_category_id,
    )


# -- Productivity Rates ------------------------------------------------------------


@router.post(
    "/productivity-rates",
    response_model=ProductivityRate,
    status_code=status.HTTP_201_CREATED,
)
async def create_productivity_rate(
    data: ProductivityRateCreate,
    current_user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    rate_service: Annotated[ProductivityRateService, Depends(get_productivity_rate_service)],
) -> ProductivityRate:
    """Create a productivity rate."""
    company = await _resolve_company(current_user, company_service)
    result = rate_service.create(company.id, data.model_dump(), current_user["uid"])
    return ProductivityRate(**result)


@router.get("/productivity-rates", response_model=ProductivityRateListResponse)
async def list_productivity_rates(
    current_user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    rate_service: Annotated[ProductivityRateService, Depends(get_productivity_rate_service)],
    active_only: bool = Query(True),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> ProductivityRateListResponse:
    """List productivity rates for the company."""
    company = await _resolve_company(current_user, company_service)
    result = rate_service.list_rates(
        company.id, active_only=active_only, limit=limit, offset=offset,
    )
    return ProductivityRateListResponse(
        rates=[ProductivityRate(**r) for r in result["rates"]],
        total=result["total"],
    )


@router.get("/productivity-rates/{rate_id}", response_model=ProductivityRate)
async def get_productivity_rate(
    rate_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    rate_service: Annotated[ProductivityRateService, Depends(get_productivity_rate_service)],
) -> ProductivityRate:
    """Get a specific productivity rate."""
    company = await _resolve_company(current_user, company_service)
    try:
        return ProductivityRate(**rate_service.get(company.id, rate_id))
    except ProductivityRateNotFoundError:
        raise HTTPException(status_code=404, detail=f"Rate not found: {rate_id}")


@router.patch("/productivity-rates/{rate_id}", response_model=ProductivityRate)
async def update_productivity_rate(
    rate_id: str,
    data: ProductivityRateUpdate,
    current_user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    rate_service: Annotated[ProductivityRateService, Depends(get_productivity_rate_service)],
) -> ProductivityRate:
    """Update a productivity rate."""
    company = await _resolve_company(current_user, company_service)
    try:
        result = rate_service.update(
            company.id, rate_id, data.model_dump(exclude_none=True), current_user["uid"],
        )
        return ProductivityRate(**result)
    except ProductivityRateNotFoundError:
        raise HTTPException(status_code=404, detail=f"Rate not found: {rate_id}")


@router.post("/productivity-rates/{rate_id}/deactivate", response_model=ProductivityRate)
async def deactivate_productivity_rate(
    rate_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    rate_service: Annotated[ProductivityRateService, Depends(get_productivity_rate_service)],
) -> ProductivityRate:
    """Deactivate a productivity rate."""
    company = await _resolve_company(current_user, company_service)
    try:
        return ProductivityRate(**rate_service.deactivate(company.id, rate_id, current_user["uid"]))
    except ProductivityRateNotFoundError:
        raise HTTPException(status_code=404, detail=f"Rate not found: {rate_id}")
