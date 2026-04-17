"""Daily log management router."""

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.dependencies import (
    get_company_service,
    get_current_user,
    get_daily_log_service,
    get_event_bus,
)
from app.exceptions import DailyLogNotFoundError, ProjectNotFoundError
from app.models.actor import Actor
from app.models.daily_log import (
    DailyLog,
    DailyLogCreate,
    DailyLogListResponse,
    DailyLogStatus,
    DailyLogUpdate,
)
from app.models.events import EventType
from app.services.company_service import CompanyService
from app.services.daily_log_service import DailyLogService
from app.services.event_bus import EventBus
from app.utils.async_helpers import run_sync

router = APIRouter(prefix="/me", tags=["daily-logs"])


async def _resolve_company(
    user: dict, company_service: CompanyService
) -> "Company":
    """Resolve the current user's company or raise 404.

    Args:
        user: The current user claims dict.
        company_service: CompanyService instance.

    Returns:
        The user's Company.

    Raises:
        HTTPException: 404 if no company found.
    """
    from app.models.company import Company

    company = await run_sync(company_service.get_by_user, user["uid"])
    if company is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No company profile found for this user",
        )
    return company


# -- Daily Log endpoints ---------------------------------------------------------


@router.post(
    "/projects/{project_id}/daily-logs",
    response_model=DailyLog,
    status_code=status.HTTP_201_CREATED,
)
async def create_daily_log(
    project_id: str,
    data: DailyLogCreate,
    current_user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    daily_log_service: Annotated[DailyLogService, Depends(get_daily_log_service)],
) -> DailyLog:
    """Create a new daily log draft with auto-populated safety summaries.

    Args:
        project_id: The parent project ID.
        data: Daily log creation data.
        current_user: Authenticated user claims.
        company_service: CompanyService dependency.
        daily_log_service: DailyLogService dependency.

    Returns:
        The created DailyLog.
    """
    company = await _resolve_company(current_user, company_service)
    try:
        return daily_log_service.create(
            company.id, project_id, data, current_user["uid"]
        )
    except ProjectNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project not found: {project_id}",
        )


@router.get(
    "/projects/{project_id}/daily-logs",
    response_model=DailyLogListResponse,
)
async def list_daily_logs(
    project_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    daily_log_service: Annotated[DailyLogService, Depends(get_daily_log_service)],
    status_filter: DailyLogStatus | None = Query(None, alias="status"),
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> DailyLogListResponse:
    """List daily logs for a project with optional filters.

    Args:
        project_id: The parent project ID.
        current_user: Authenticated user claims.
        company_service: CompanyService dependency.
        daily_log_service: DailyLogService dependency.
        status_filter: Filter by workflow status.
        date_from: Filter logs on or after this date.
        date_to: Filter logs on or before this date.
        limit: Maximum number of logs to return.
        offset: Number of logs to skip.

    Returns:
        DailyLogListResponse with logs and total count.
    """
    company = await _resolve_company(current_user, company_service)
    result = daily_log_service.list_daily_logs(
        company.id,
        project_id,
        status_filter=status_filter,
        date_from=date_from,
        date_to=date_to,
        limit=limit,
        offset=offset,
    )
    return DailyLogListResponse(**result)


@router.get(
    "/projects/{project_id}/daily-logs/missing",
)
async def get_missing_daily_logs(
    project_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    daily_log_service: Annotated[DailyLogService, Depends(get_daily_log_service)],
    date_from: date = Query(...),
    date_to: date = Query(...),
) -> list[str]:
    """Get dates within a range that are missing daily logs.

    Args:
        project_id: The parent project ID.
        current_user: Authenticated user claims.
        company_service: CompanyService dependency.
        daily_log_service: DailyLogService dependency.
        date_from: Start of the date range.
        date_to: End of the date range.

    Returns:
        List of ISO date strings that are missing logs.
    """
    company = await _resolve_company(current_user, company_service)
    try:
        return daily_log_service.get_missing_logs(
            company.id, project_id, date_from, date_to
        )
    except ProjectNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project not found: {project_id}",
        )


@router.get(
    "/projects/{project_id}/daily-logs/{daily_log_id}",
    response_model=DailyLog,
)
async def get_daily_log(
    project_id: str,
    daily_log_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    daily_log_service: Annotated[DailyLogService, Depends(get_daily_log_service)],
) -> DailyLog:
    """Get a specific daily log by ID.

    Args:
        project_id: The parent project ID.
        daily_log_id: The daily log ID.
        current_user: Authenticated user claims.
        company_service: CompanyService dependency.
        daily_log_service: DailyLogService dependency.

    Returns:
        The DailyLog.
    """
    company = await _resolve_company(current_user, company_service)
    try:
        return daily_log_service.get(company.id, project_id, daily_log_id)
    except DailyLogNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Daily log not found: {daily_log_id}",
        )


@router.patch(
    "/projects/{project_id}/daily-logs/{daily_log_id}",
    response_model=DailyLog,
)
async def update_daily_log(
    project_id: str,
    daily_log_id: str,
    data: DailyLogUpdate,
    current_user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    daily_log_service: Annotated[DailyLogService, Depends(get_daily_log_service)],
) -> DailyLog:
    """Update a daily log.

    Args:
        project_id: The parent project ID.
        daily_log_id: The daily log ID.
        data: Fields to update.
        current_user: Authenticated user claims.
        company_service: CompanyService dependency.
        daily_log_service: DailyLogService dependency.

    Returns:
        The updated DailyLog.
    """
    company = await _resolve_company(current_user, company_service)
    try:
        return daily_log_service.update(
            company.id, project_id, daily_log_id, data, current_user["uid"]
        )
    except DailyLogNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Daily log not found: {daily_log_id}",
        )


@router.delete(
    "/projects/{project_id}/daily-logs/{daily_log_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_daily_log(
    project_id: str,
    daily_log_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    daily_log_service: Annotated[DailyLogService, Depends(get_daily_log_service)],
) -> None:
    """Soft-delete a daily log.

    Args:
        project_id: The parent project ID.
        daily_log_id: The daily log ID.
        current_user: Authenticated user claims.
        company_service: CompanyService dependency.
        daily_log_service: DailyLogService dependency.
    """
    company = await _resolve_company(current_user, company_service)
    try:
        daily_log_service.delete(company.id, project_id, daily_log_id)
    except DailyLogNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Daily log not found: {daily_log_id}",
        )


@router.post(
    "/projects/{project_id}/daily-logs/{daily_log_id}/submit",
    response_model=DailyLog,
)
async def submit_daily_log(
    project_id: str,
    daily_log_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    daily_log_service: Annotated[DailyLogService, Depends(get_daily_log_service)],
    event_bus: Annotated[EventBus, Depends(get_event_bus)],
) -> DailyLog:
    """Submit a daily log for approval (draft -> submitted).

    Args:
        project_id: The parent project ID.
        daily_log_id: The daily log ID.
        current_user: Authenticated user claims.
        company_service: CompanyService dependency.
        daily_log_service: DailyLogService dependency.
        event_bus: EventBus dependency for event emission.

    Returns:
        The submitted DailyLog.
    """
    company = await _resolve_company(current_user, company_service)
    try:
        result = daily_log_service.submit(
            company.id, project_id, daily_log_id, current_user["uid"]
        )
        event = event_bus.create_event(
            event_type=EventType.DAILY_LOG_SUBMITTED,
            entity_id=result.id,
            entity_type="DailyLog",
            company_id=company.id,
            actor=Actor.human(current_user["uid"]),
            project_id=project_id,
            summary={"log_date": result.log_date.isoformat(), "status": result.status.value},
        )
        event_bus.emit(event)
        return result
    except DailyLogNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Daily log not found: {daily_log_id}",
        )


@router.post(
    "/projects/{project_id}/daily-logs/{daily_log_id}/approve",
    response_model=DailyLog,
)
async def approve_daily_log(
    project_id: str,
    daily_log_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    daily_log_service: Annotated[DailyLogService, Depends(get_daily_log_service)],
) -> DailyLog:
    """Approve a submitted daily log (submitted -> approved).

    Args:
        project_id: The parent project ID.
        daily_log_id: The daily log ID.
        current_user: Authenticated user claims.
        company_service: CompanyService dependency.
        daily_log_service: DailyLogService dependency.

    Returns:
        The approved DailyLog.
    """
    company = await _resolve_company(current_user, company_service)
    try:
        return daily_log_service.approve(
            company.id, project_id, daily_log_id, current_user["uid"]
        )
    except DailyLogNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Daily log not found: {daily_log_id}",
        )
