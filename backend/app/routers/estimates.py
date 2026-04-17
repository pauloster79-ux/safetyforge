"""Estimate endpoints — direct REST access to estimate summary data.

Replaces the SSE/chat-based pattern for fetching estimate summaries,
providing a standard synchronous JSON endpoint.
"""

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status

from app.dependencies import (
    get_company_service,
    get_current_user,
    get_estimating_service,
)
from app.services.company_service import CompanyService
from app.services.estimating_service import EstimatingService
from app.utils.async_helpers import run_sync

router = APIRouter(prefix="/me", tags=["estimates"])


async def _resolve_company(
    user: dict, company_service: CompanyService
):
    """Resolve the current user's company or raise 404."""
    company = await run_sync(company_service.get_by_user, user["uid"])
    if company is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No company profile found for this user",
        )
    return company


@router.get("/projects/{project_id}/estimate-summary")
async def get_estimate_summary(
    project_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    estimating_service: Annotated[EstimatingService, Depends(get_estimating_service)],
) -> dict[str, Any]:
    """Return the full estimate summary for a project.

    Traverses Project -> WorkItems -> Labour/Item children to build
    the estimate with correct cost rollup.

    Args:
        project_id: The project to summarise.
        current_user: Authenticated user from Clerk JWT.
        company_service: For resolving the user's company.
        estimating_service: For computing the estimate summary.

    Returns:
        Dict with itemised breakdown and totals.
    """
    company = await _resolve_company(current_user, company_service)
    result = await run_sync(
        estimating_service.get_estimate_summary,
        company.id,
        project_id,
    )
    if "error" in result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=result["error"],
        )
    return result
