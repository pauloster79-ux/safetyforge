"""FastAPI application entry point for Kerf backend."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.config import get_settings
from app.middleware.rate_limit import limiter
from app.services.neo4j_client import (
    check_neo4j_health,
    close_async_driver,
    close_sync_driver,
    get_sync_driver,
)
from app.routers import (
    agents,
    auth,
    billing,
    companies,
    documents,
    gc_portal,
    jurisdictions,
    me,
    members,
    pdf,
    templates,
    voice,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


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
app.include_router(jurisdictions.router, prefix="/api/v1")
app.include_router(members.router, prefix="/api/v1")
app.include_router(gc_portal.router, prefix="/api/v1")
app.include_router(voice.router, prefix="/api/v1")
app.include_router(agents.router, prefix="/api/v1")


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
