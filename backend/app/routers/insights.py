"""Insight management router — company-level CRUD + knowledge summary.

Also exposes ``GET /me/knowledge/summary`` — an aggregated view of the
contractor's learned knowledge (insights, resource rates, productivity
rates, material catalog entries, and completed project count). Powers the
Layer 4 "My Knowledge" canvas page.
"""

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from neo4j import Driver

from app.dependencies import (
    get_company_service,
    get_current_user,
    get_insight_service,
    get_material_catalog_service,
    get_neo4j_driver,
    get_productivity_rate_service,
    get_resource_rate_service,
)
from app.exceptions import CompanyNotFoundError, InsightNotFoundError
from app.models.insight import (
    Insight,
    InsightCreate,
    InsightListResponse,
    InsightUpdate,
)
from app.services.company_service import CompanyService
from app.services.insight_service import InsightService
from app.services.material_catalog_service import MaterialCatalogService
from app.services.productivity_rate_service import ProductivityRateService
from app.services.resource_rate_service import ResourceRateService
from app.utils.async_helpers import run_sync

router = APIRouter(prefix="/me", tags=["insights"])


async def _resolve_company(user: dict, company_service: CompanyService):
    """Resolve the current user's company or raise 404."""
    company = await run_sync(company_service.get_by_user, user["uid"])
    if company is None:
        raise HTTPException(status_code=404, detail="No company profile found for this user")
    return company


@router.post(
    "/insights",
    response_model=Insight,
    status_code=status.HTTP_201_CREATED,
)
async def create_insight(
    data: InsightCreate,
    current_user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    insight_service: Annotated[InsightService, Depends(get_insight_service)],
) -> Insight:
    """Create an insight for the current company."""
    company = await _resolve_company(current_user, company_service)
    try:
        result = insight_service.create(
            company.id, data.model_dump(), current_user["uid"],
        )
        return Insight(**result)
    except CompanyNotFoundError:
        raise HTTPException(status_code=404, detail=f"Company not found: {company.id}")


@router.get("/insights", response_model=InsightListResponse)
async def list_insights(
    current_user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    insight_service: Annotated[InsightService, Depends(get_insight_service)],
    scope: str | None = Query(None, description="Filter by scope (e.g. 'work_type')"),
    scope_value: str | None = Query(None, description="Filter by scope_value"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
) -> InsightListResponse:
    """List insights for the current company."""
    company = await _resolve_company(current_user, company_service)
    result = insight_service.list_by_company(
        company.id, scope=scope, scope_value=scope_value, limit=limit, offset=offset,
    )
    return InsightListResponse(
        insights=[Insight(**r) for r in result["insights"]],
        total=result["total"],
    )


@router.get("/insights/{insight_id}", response_model=Insight)
async def get_insight(
    insight_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    insight_service: Annotated[InsightService, Depends(get_insight_service)],
) -> Insight:
    """Get a specific insight."""
    company = await _resolve_company(current_user, company_service)
    try:
        return Insight(**insight_service.get(company.id, insight_id))
    except InsightNotFoundError:
        raise HTTPException(status_code=404, detail=f"Insight not found: {insight_id}")


@router.patch("/insights/{insight_id}", response_model=Insight)
async def update_insight(
    insight_id: str,
    data: InsightUpdate,
    current_user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    insight_service: Annotated[InsightService, Depends(get_insight_service)],
) -> Insight:
    """Update an insight."""
    company = await _resolve_company(current_user, company_service)
    try:
        result = insight_service.update(
            company.id, insight_id,
            data.model_dump(exclude_none=True), current_user["uid"],
        )
        return Insight(**result)
    except InsightNotFoundError:
        raise HTTPException(status_code=404, detail=f"Insight not found: {insight_id}")


@router.delete(
    "/insights/{insight_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_insight(
    insight_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    insight_service: Annotated[InsightService, Depends(get_insight_service)],
) -> None:
    """Delete an insight."""
    company = await _resolve_company(current_user, company_service)
    try:
        insight_service.delete(company.id, insight_id)
    except InsightNotFoundError:
        raise HTTPException(status_code=404, detail=f"Insight not found: {insight_id}")


@router.post(
    "/insights/{insight_id}/validate",
    response_model=Insight,
)
async def validate_insight(
    insight_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    insight_service: Annotated[InsightService, Depends(get_insight_service)],
) -> Insight:
    """Record a successful application of the insight.

    Increments validation_count, bumps confidence by 0.05 (capped at 0.95),
    and sets last_applied_at to now.
    """
    company = await _resolve_company(current_user, company_service)
    try:
        result = insight_service.increment_validation(
            company.id, insight_id, current_user["uid"],
        )
        return Insight(**result)
    except InsightNotFoundError:
        raise HTTPException(status_code=404, detail=f"Insight not found: {insight_id}")


# ---------------------------------------------------------------------------
# Knowledge summary — aggregated Layer 4 view for the "My Knowledge" canvas.
# ---------------------------------------------------------------------------
#
# This endpoint returns a single denormalised payload that the frontend can
# render without making four separate round trips. It's intentionally
# co-located with the Insight CRUD because insights are the primary inhabitant
# of the knowledge page, and Paul's build note asked us to add it here.
#
# The mcp_tools.list_contractor_knowledge counterpart exists for agent tool
# calls. This HTTP endpoint shares the same underlying services but returns a
# shape tuned for UI rendering (full lists, not LLM-readable summaries).


def _count_completed_projects(driver: Driver, company_id: str) -> int:
    """Count projects in the completed state for a company.

    Separate query because none of the three rate/insight/material services own
    the concept of 'completed project' — they only produce knowledge derived
    from them. Graph-native: if no path exists through OWNS_PROJECT, the caller
    sees zero.
    """
    with driver.session() as session:
        record = session.run(
            """
            MATCH (c:Company {id: $company_id})-[:OWNS_PROJECT]->(p:Project)
            WHERE p.state = 'completed'
            RETURN count(p) AS n
            """,
            company_id=company_id,
        ).single()
    return int(record["n"]) if record else 0


@router.get("/knowledge/summary")
async def get_knowledge_summary(
    current_user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    insight_service: Annotated[InsightService, Depends(get_insight_service)],
    resource_rate_service: Annotated[
        ResourceRateService, Depends(get_resource_rate_service)
    ],
    productivity_rate_service: Annotated[
        ProductivityRateService, Depends(get_productivity_rate_service)
    ],
    material_catalog_service: Annotated[
        MaterialCatalogService, Depends(get_material_catalog_service)
    ],
    driver: Annotated[Driver, Depends(get_neo4j_driver)],
    rate_limit: int = Query(200, ge=1, le=500, description="Max rates to return"),
    insight_limit: int = Query(
        200, ge=1, le=500, description="Max insights to return",
    ),
) -> dict[str, Any]:
    """Aggregate learned knowledge for the current company's "My Knowledge" page.

    Returns the full lists of ResourceRates (active only), ProductivityRates
    (active only), and Insights, plus a count of MaterialCatalogEntries and
    completed projects. The frontend uses these to render Layer 4 panels
    (labour rates, productivity patterns, lessons learned, material catalog).

    Rates and insights are page-capped (rate_limit / insight_limit) to keep
    the payload bounded. In the common case the contractor has <50 of each
    and the caps don't bite.
    """
    company = await _resolve_company(current_user, company_service)

    # Parallel reads would be nice but these are cheap and Neo4j sessions are
    # not trivially poolable from async — keep them sequential and simple.
    resource_rates = resource_rate_service.list_rates(
        company.id, active_only=True, limit=rate_limit, offset=0,
    )
    productivity_rates = productivity_rate_service.list_rates(
        company.id, active_only=True, limit=rate_limit, offset=0,
    )
    insights = insight_service.list_by_company(
        company.id, limit=insight_limit, offset=0,
    )
    material_catalog = material_catalog_service.list_by_company(
        company.id, limit=1, offset=0,  # we only need the total
    )
    completed_project_count = _count_completed_projects(driver, company.id)

    return {
        "company_id": company.id,
        "resource_rates": {
            "items": resource_rates["rates"],
            "total": resource_rates["total"],
        },
        "productivity_rates": {
            "items": productivity_rates["rates"],
            "total": productivity_rates["total"],
        },
        "insights": {
            "items": insights["insights"],
            "total": insights["total"],
        },
        "material_catalog": {
            "total": material_catalog["total"],
        },
        "completed_projects": {
            "total": completed_project_count,
        },
    }
