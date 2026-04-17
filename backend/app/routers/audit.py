"""Audit / activity stream router.

Exposes entity-scoped and company-scoped activity stream endpoints that
aggregate AuditEvent nodes from the graph. See docs/design/phase-0-foundations.md.
"""

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.dependencies import (
    get_audit_service,
    get_company_service,
    get_current_user,
)
from app.models.audit_event import ActivityStreamResponse
from app.services.audit_service import AuditService
from app.services.company_service import CompanyService
from app.utils.async_helpers import run_sync

router = APIRouter(prefix="/me", tags=["activity"])


# Entity types allowed for the generic fallback endpoint. Any type in this
# list must also have a corresponding service that emits AuditEvents for it.
_ALLOWED_ENTITY_TYPES: frozenset[str] = frozenset(
    {
        "Project",
        "WorkItem",
        "WorkPackage",
        "Worker",
        "Crew",
        "Inspection",
        "Incident",
        "HazardReport",
        "ToolboxTalk",
        "DailyLog",
        "Equipment",
        "Certification",
        "CorrectiveAction",
        "Contract",
        "Variation",
        "Invoice",
        "TimeEntry",
        "Document",
        "WorkCategory",
    }
)


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


@router.get("/activity", response_model=ActivityStreamResponse)
async def get_company_activity(
    current_user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    audit_service: Annotated[AuditService, Depends(get_audit_service)],
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    before: datetime | None = None,
) -> ActivityStreamResponse:
    """Company-wide audit timeline, newest first.

    Args:
        limit: Max events to return (1-200, default 50).
        before: Cursor — only return events strictly before this timestamp.
    """
    company = await _resolve_company(current_user, company_service)
    return await run_sync(
        audit_service.list_events_for_company,
        company.id,
        limit,
        before,
    )


@router.get(
    "/projects/{project_id}/activity",
    response_model=ActivityStreamResponse,
)
async def get_project_activity(
    project_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    audit_service: Annotated[AuditService, Depends(get_audit_service)],
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    before: datetime | None = None,
) -> ActivityStreamResponse:
    """Activity stream for a project, including events on child entities
    (WorkItems, Inspections, Incidents, DailyLogs, ToolboxTalks, HazardReports).
    """
    company = await _resolve_company(current_user, company_service)
    return await run_sync(
        audit_service.list_events_for_project,
        company.id,
        project_id,
        limit,
        before,
    )


@router.get(
    "/work-items/{work_item_id}/activity",
    response_model=ActivityStreamResponse,
)
async def get_work_item_activity(
    work_item_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    audit_service: Annotated[AuditService, Depends(get_audit_service)],
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    before: datetime | None = None,
) -> ActivityStreamResponse:
    """Activity stream for a work item, including child Labour/Item events
    and TimeEntries logged against it.
    """
    company = await _resolve_company(current_user, company_service)
    return await run_sync(
        audit_service.list_events_for_work_item,
        company.id,
        work_item_id,
        limit,
        before,
    )


@router.get(
    "/workers/{worker_id}/activity",
    response_model=ActivityStreamResponse,
)
async def get_worker_activity(
    worker_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    audit_service: Annotated[AuditService, Depends(get_audit_service)],
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    before: datetime | None = None,
) -> ActivityStreamResponse:
    """Activity stream for a worker, including certification events."""
    company = await _resolve_company(current_user, company_service)
    return await run_sync(
        audit_service.list_events_for_worker,
        company.id,
        worker_id,
        limit,
        before,
    )


@router.get(
    "/entities/{entity_type}/{entity_id}/activity",
    response_model=ActivityStreamResponse,
)
async def get_entity_activity(
    entity_type: str,
    entity_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    audit_service: Annotated[AuditService, Depends(get_audit_service)],
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    before: datetime | None = None,
) -> ActivityStreamResponse:
    """Generic fallback: activity stream for any entity by type and ID.

    Returns only events directly emitted by this entity (not child entities).
    For aggregated streams on Project / Worker / WorkItem, prefer the
    entity-specific endpoints above.
    """
    if entity_type not in _ALLOWED_ENTITY_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported entity type: {entity_type}",
        )
    company = await _resolve_company(current_user, company_service)
    return await run_sync(
        audit_service.list_events_for_entity,
        company.id,
        entity_type,
        entity_id,
        limit,
        before,
    )
