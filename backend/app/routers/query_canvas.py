"""Query Canvas router — browse and execute registered graph queries.

Endpoints:
    GET  /me/queries              — list all registered queries (metadata only)
    GET  /me/queries/{query_id}/run — execute a query, return results
"""

import logging
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status

from app.dependencies import get_current_user
from app.services.company_service import CompanyService
from app.services.query_canvas_service import QueryCanvasService
from app.dependencies import get_neo4j_driver
from neo4j import Driver

logger = logging.getLogger(__name__)

router = APIRouter(tags=["queries"])


# ---------------------------------------------------------------------------
# Dependency providers
# ---------------------------------------------------------------------------


def _get_query_canvas_service(
    driver: Annotated[Driver, Depends(get_neo4j_driver)],
) -> QueryCanvasService:
    """Provide a QueryCanvasService instance."""
    return QueryCanvasService(driver)


def _get_company_service(
    driver: Annotated[Driver, Depends(get_neo4j_driver)],
) -> CompanyService:
    """Provide a CompanyService instance."""
    return CompanyService(driver)


async def _resolve_company_id(
    user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(_get_company_service)],
) -> str:
    """Resolve the current user's company ID.

    Returns:
        The company_id string.

    Raises:
        HTTPException: 404 if no company is found for the user.
    """
    company = company_service.get_by_user(user["uid"])
    if company is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No company found for current user",
        )
    return company.id


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("/me/queries")
async def list_queries(
    service: Annotated[QueryCanvasService, Depends(_get_query_canvas_service)],
    user: Annotated[dict, Depends(get_current_user)],
) -> dict[str, Any]:
    """Return metadata for all registered queries.

    Returns:
        A dict with 'queries' list and 'total' count.
    """
    queries = service.list_queries()
    return {"queries": queries, "total": len(queries)}


@router.get("/me/queries/{query_id}/run")
async def run_query(
    query_id: str,
    service: Annotated[QueryCanvasService, Depends(_get_query_canvas_service)],
    company_id: Annotated[str, Depends(_resolve_company_id)],
) -> dict[str, Any]:
    """Execute a registered query and return results.

    Args:
        query_id: Slug of the registered query to execute.

    Returns:
        A dict with query_id, name, columns, rows, and total.

    Raises:
        HTTPException: 404 if the query_id is not recognised.
    """
    try:
        return service.execute_query(query_id, company_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )
    except Exception as exc:
        logger.error("Query execution failed: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Query execution failed",
        )
