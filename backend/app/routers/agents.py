"""Agent administration router for managing AI agents.

Provides endpoints for registering, listing, updating, suspending,
and monitoring AI agents within a company.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from neo4j import Driver

from app.dependencies import (
    get_agent_identity_service,
    get_agent_orchestrator,
    get_company_service,
    get_current_user,
    get_neo4j_driver,
)
from app.exceptions import AgentNotFoundError, CompanyNotFoundError
from app.models.agent_identity import (
    AgentIdentity,
    AgentIdentityCreate,
    AgentIdentityUpdate,
    AgentSpendReport,
)
from app.services.agent_identity_service import AgentIdentityService
from app.services.agent_orchestrator import AgentOrchestrator
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


# ---------------------------------------------------------------------------
# Agent on-demand endpoints
# ---------------------------------------------------------------------------


@router.post("/me/agents/compliance/check")
async def run_compliance_check(
    project_id: str = Query(..., description="Project to check"),
    user: Annotated[dict, Depends(get_current_user)] = None,
    company_service: Annotated[CompanyService, Depends(get_company_service)] = None,
    orchestrator: Annotated[AgentOrchestrator, Depends(get_agent_orchestrator)] = None,
) -> dict:
    """Run an on-demand compliance check for a project.

    Args:
        project_id: The project ID to check compliance for.
        user: Authenticated user claims.
        company_service: CompanyService dependency.
        orchestrator: AgentOrchestrator dependency.

    Returns:
        A dict with alerts list and count.
    """
    company_id = _resolve_company_id(user, company_service)
    alerts = orchestrator.run_compliance_check(company_id, project_id)
    return {"alerts": alerts, "count": len(alerts)}


@router.get("/me/agents/compliance/alerts")
async def list_compliance_alerts(
    user: Annotated[dict, Depends(get_current_user)] = None,
    company_service: Annotated[CompanyService, Depends(get_company_service)] = None,
    driver: Annotated[Driver, Depends(get_neo4j_driver)] = None,
) -> dict:
    """List compliance alerts for the current user's company.

    Args:
        user: Authenticated user claims.
        company_service: CompanyService dependency.
        driver: Neo4j driver dependency.

    Returns:
        A dict with alerts list and count.
    """
    company_id = _resolve_company_id(user, company_service)
    with driver.session() as session:
        result = session.run(
            """
            MATCH (c:Company {id: $company_id})-[:HAS_COMPLIANCE_ALERT]->(a:ComplianceAlert)
            RETURN a ORDER BY a.created_at DESC LIMIT 50
            """,
            company_id=company_id,
        )
        alerts = [dict(record["a"]) for record in result]
    return {"alerts": alerts, "count": len(alerts)}


@router.post("/me/agents/briefing/generate")
async def generate_briefing(
    project_id: str = Query(..., description="Project to brief"),
    user: Annotated[dict, Depends(get_current_user)] = None,
    company_service: Annotated[CompanyService, Depends(get_company_service)] = None,
    orchestrator: Annotated[AgentOrchestrator, Depends(get_agent_orchestrator)] = None,
) -> dict:
    """Generate an on-demand morning briefing for a project.

    Args:
        project_id: The project ID to generate a briefing for.
        user: Authenticated user claims.
        company_service: CompanyService dependency.
        orchestrator: AgentOrchestrator dependency.

    Returns:
        A dict with the briefing data or a message if unavailable.
    """
    company_id = _resolve_company_id(user, company_service)
    briefing = orchestrator.run_briefing(company_id, project_id)
    if briefing is None:
        return {"briefing": None, "message": "No briefing agent registered or error occurred"}
    return {"briefing": briefing}


@router.get("/me/agents/briefings")
async def list_briefings(
    user: Annotated[dict, Depends(get_current_user)] = None,
    company_service: Annotated[CompanyService, Depends(get_company_service)] = None,
    driver: Annotated[Driver, Depends(get_neo4j_driver)] = None,
) -> dict:
    """List briefing summaries for the current user's company.

    Args:
        user: Authenticated user claims.
        company_service: CompanyService dependency.
        driver: Neo4j driver dependency.

    Returns:
        A dict with briefings list and count.
    """
    company_id = _resolve_company_id(user, company_service)
    with driver.session() as session:
        result = session.run(
            """
            MATCH (c:Company {id: $company_id})-[:HAS_BRIEFING]->(b:BriefingSummary)
            RETURN b ORDER BY b.created_at DESC LIMIT 20
            """,
            company_id=company_id,
        )
        briefings = [dict(record["b"]) for record in result]
    return {"briefings": briefings, "count": len(briefings)}
