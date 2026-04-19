"""FastAPI application entry point for Kerf backend."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.config import get_settings
from app.middleware.rate_limit import limiter
from app.services.agent_identity_service import AgentIdentityService
from app.services.agent_orchestrator import AgentOrchestrator
from app.services.event_bus import EventBus
from app.services.guardrails_service import GuardrailsService
from app.services.llm_service import LLMService
from app.services.mcp_tools import MCPToolService
from app.services.neo4j_client import (
    check_neo4j_health,
    close_async_driver,
    close_sync_driver,
    get_sync_driver,
)
from app.routers import (
    agents,
    assumptions,
    audit,
    auth,
    billing,
    chat,
    companies,
    conditions,
    conversations,
    daily_logs,
    documents,
    estimates,
    exclusions,
    gc_portal,
    insights,
    items,
    jurisdictions,
    knowledge,
    labour,
    me,
    members,
    payment_milestones,
    pdf,
    query_canvas,
    rates,
    templates,
    voice,
    warranties,
    work_categories,
    work_items,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def _ensure_system_agents(driver) -> None:
    """Create system-level AgentIdentity nodes if they don't already exist.

    System agents (like the memory extractor) are not tied to a company.
    Uses MERGE to be idempotent across restarts.

    Args:
        driver: Neo4j driver instance.
    """
    system_agents = [
        {
            "id": "agent_memory_extractor",
            "name": "Memory Extractor",
            "agent_type": "system",
            "status": "active",
            "model_tier": "fast",
            "daily_budget_cents": 500,
            "daily_spend_cents": 0,
        },
    ]
    try:
        with driver.session() as session:
            for agent in system_agents:
                session.run(
                    """
                    MERGE (a:AgentIdentity {id: $id})
                    ON CREATE SET
                        a.name = $name,
                        a.agent_type = $agent_type,
                        a.status = $status,
                        a.model_tier = $model_tier,
                        a.daily_budget_cents = $daily_budget_cents,
                        a.daily_spend_cents = $daily_spend_cents,
                        a.created_at = datetime(),
                        a.created_by = 'system'
                    """,
                    agent,
                )
            logger.info("System agents ensured: %s", [a["id"] for a in system_agents])
    except Exception as exc:
        logger.warning("Failed to ensure system agents: %s", exc)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup/shutdown events.

    On startup: initialises the Neo4j driver and verifies connectivity.
    On shutdown: closes all Neo4j connections cleanly.
    """
    settings = get_settings()
    logger.info(
        "Kerf backend starting (environment=%s, neo4j=%s)",
        settings.environment,
        settings.neo4j_uri,
    )

    # Eagerly create the driver and verify connectivity
    try:
        driver = get_sync_driver()
        driver.verify_connectivity()
        logger.info("Neo4j connectivity verified")
    except Exception as exc:
        logger.error("Neo4j connectivity check failed: %s", exc)
        # Don't prevent startup — the driver will retry on first query

    # Agentic infrastructure
    try:
        event_bus = EventBus()
        agent_identity_service = AgentIdentityService(driver)
        guardrails = GuardrailsService(driver)
        mcp_tools = MCPToolService(driver, guardrails, event_bus)
        llm_service = LLMService(settings, agent_identity_service)
        orchestrator = AgentOrchestrator(
            driver, agent_identity_service, mcp_tools, llm_service, event_bus
        )
        orchestrator.wire_subscriptions()

        # Ensure system agents exist (idempotent MERGE)
        _ensure_system_agents(driver)

        # Store on app.state for DI
        app.state.event_bus = event_bus
        app.state.mcp_tools = mcp_tools
        app.state.agent_orchestrator = orchestrator
        app.state.llm_service = llm_service
        logger.info("Agentic infrastructure initialised")
    except Exception as exc:
        logger.error("Agentic infrastructure init failed: %s", exc)
        # Don't prevent startup — agentic features will be unavailable

    yield

    # Shutdown: close all drivers
    close_sync_driver()
    await close_async_driver()
    logger.info("Kerf backend shut down — all connections closed")


app = FastAPI(
    title="Kerf API",
    description="AI-powered construction operations platform",
    version="1.1.0",
    lifespan=lifespan,
)

# Rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS middleware
settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers under /api/v1 prefix
app.include_router(auth.router, prefix="/api/v1")
app.include_router(companies.router, prefix="/api/v1")
app.include_router(documents.router, prefix="/api/v1")
app.include_router(templates.router, prefix="/api/v1")
app.include_router(billing.router, prefix="/api/v1")
app.include_router(pdf.router, prefix="/api/v1")
app.include_router(me.router, prefix="/api/v1")
app.include_router(daily_logs.router, prefix="/api/v1")
app.include_router(audit.router, prefix="/api/v1")
app.include_router(jurisdictions.router, prefix="/api/v1")
app.include_router(members.router, prefix="/api/v1")
app.include_router(gc_portal.router, prefix="/api/v1")
app.include_router(voice.router, prefix="/api/v1")
app.include_router(chat.router, prefix="/api/v1")
app.include_router(conversations.router, prefix="/api/v1")
app.include_router(knowledge.router, prefix="/api/v1")
app.include_router(agents.router, prefix="/api/v1")
app.include_router(labour.router, prefix="/api/v1")
app.include_router(items.router, prefix="/api/v1")
app.include_router(work_items.router, prefix="/api/v1")
app.include_router(work_categories.router, prefix="/api/v1")
app.include_router(assumptions.router, prefix="/api/v1")
app.include_router(estimates.router, prefix="/api/v1")
app.include_router(exclusions.router, prefix="/api/v1")
app.include_router(payment_milestones.router, prefix="/api/v1")
app.include_router(conditions.router, prefix="/api/v1")
app.include_router(warranties.router, prefix="/api/v1")
app.include_router(query_canvas.router, prefix="/api/v1")
app.include_router(rates.router, prefix="/api/v1")
app.include_router(insights.router, prefix="/api/v1")


@app.get("/health", tags=["health"])
async def health_check() -> dict:
    """Health check endpoint for load balancers and monitoring.

    Checks Neo4j connectivity and returns server info.

    Returns:
        A dict with status, version, and database health information.
    """
    neo4j_health = await check_neo4j_health()
    overall_status = "healthy" if neo4j_health["status"] == "healthy" else "degraded"

    return {
        "status": overall_status,
        "version": "1.1.0",
        "service": "kerf-api",
        "database": neo4j_health,
    }
