"""Agent administration router for managing AI agents.

Provides endpoints for registering, listing, updating, suspending,
and monitoring AI agents within a company.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.dependencies import (
    get_agent_identity_service,
    get_company_service,
    get_current_user,
)
from app.exceptions import AgentNotFoundError, CompanyNotFoundError
from app.models.agent_identity import (
    AgentIdentity,
    AgentIdentityCreate,
    AgentIdentityUpdate,
    AgentSpendReport,
)
from app.services.agent_identity_service import AgentIdentityService
from app.services.company_service import CompanyService

router = APIRouter(tags=["agents"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _resolve_company_id(user: dict, company_service: CompanyService) -> str:
    """Resolve the current user's company ID.

    Args:
        user: Decoded auth token dict.
        company_service: CompanyService instance.

    Returns:
        The company ID.

    Raises:
        HTTPException: 404 if no company is associated with the user.
    """
    company = company_service.get_by_user(user["uid"])
    if company is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No company found for current user",
        )
    return company.id


# ---------------------------------------------------------------------------
# Agent CRUD endpoints
# ---------------------------------------------------------------------------


@router.post("/me/agents", response_model=AgentIdentity, status_code=status.HTTP_201_CREATED)
async def register_agent(
    data: AgentIdentityCreate,
    user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    agent_service: Annotated[AgentIdentityService, Depends(get_agent_identity_service)],
) -> AgentIdentity:
    """Register a new AI agent for the current user's company.

    Only company owners/admins should call this. The agent is created
    in active status with the specified scopes and budget.
    """
    company_id = _resolve_company_id(user, company_service)
    try:
        return agent_service.register(company_id, data, user["uid"])
    except CompanyNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found",
        )


@router.get("/me/agents", response_model=list[AgentIdentity])
async def list_agents(
    user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    agent_service: Annotated[AgentIdentityService, Depends(get_agent_identity_service)],
) -> list[AgentIdentity]:
    """List all agents registered to the current user's company."""
    company_id = _resolve_company_id(user, company_service)
    return agent_service.list_for_company(company_id)


@router.get("/me/agents/{agent_id}", response_model=AgentIdentity)
async def get_agent(
    agent_id: str,
    user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    agent_service: Annotated[AgentIdentityService, Depends(get_agent_identity_service)],
) -> AgentIdentity:
    """Get details of a specific agent."""
    company_id = _resolve_company_id(user, company_service)
    try:
        return agent_service.get(agent_id, company_id)
    except AgentNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent not found: {agent_id}",
        )


@router.patch("/me/agents/{agent_id}", response_model=AgentIdentity)
async def update_agent(
    agent_id: str,
    data: AgentIdentityUpdate,
    user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    agent_service: Annotated[AgentIdentityService, Depends(get_agent_identity_service)],
) -> AgentIdentity:
    """Update an agent's configuration (name, scopes, budget, status)."""
    company_id = _resolve_company_id(user, company_service)
    try:
        return agent_service.update(agent_id, company_id, data)
    except AgentNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent not found: {agent_id}",
        )


@router.post("/me/agents/{agent_id}/suspend", response_model=AgentIdentity)
async def suspend_agent(
    agent_id: str,
    user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    agent_service: Annotated[AgentIdentityService, Depends(get_agent_identity_service)],
) -> AgentIdentity:
    """Suspend an agent immediately (kill switch).

    The agent will be unable to make any further API calls until reactivated.
    """
    company_id = _resolve_company_id(user, company_service)
    try:
        return agent_service.suspend(agent_id, company_id)
    except AgentNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent not found: {agent_id}",
        )


# ---------------------------------------------------------------------------
# Cost monitoring endpoints
# ---------------------------------------------------------------------------


@router.get("/me/agents/spend/report", response_model=list[AgentSpendReport])
async def get_spend_report(
    user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    agent_service: Annotated[AgentIdentityService, Depends(get_agent_identity_service)],
) -> list[AgentSpendReport]:
    """Get spend report for all agents in the company.

    Shows current daily spend, budget utilisation, and remaining budget
    for each agent.
    """
    company_id = _resolve_company_id(user, company_service)
    return agent_service.get_spend_report(company_id)


@router.post("/me/agents/spend/reset", status_code=status.HTTP_200_OK)
async def reset_daily_spend(
    user: Annotated[dict, Depends(get_current_user)],
    company_service: Annotated[CompanyService, Depends(get_company_service)],
    agent_service: Annotated[AgentIdentityService, Depends(get_agent_identity_service)],
) -> dict:
    """Reset daily spend counters for all agents in the company.

    Typically called by a scheduled job at midnight. Can also be
    triggered manually by company admins.
    """
    company_id = _resolve_company_id(user, company_service)
    count = agent_service.reset_daily_spend(company_id)
    return {"reset_count": count, "company_id": company_id}
