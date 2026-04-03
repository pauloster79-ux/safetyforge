"""FastAPI application entry point for SafetyForge backend."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routers import auth, billing, companies, documents, pdf, templates

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup/shutdown events."""
    settings = get_settings()
    logger.info(
        "SafetyForge backend starting (environment=%s, project=%s)",
        settings.environment,
        settings.google_cloud_project,
    )
    yield
    logger.info("SafetyForge backend shutting down")


app = FastAPI(
    title="SafetyForge API",
    description="AI-powered safety compliance document generator for construction contractors",
    version="1.0.0",
    lifespan=lifespan,
)

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


@app.get("/health", tags=["health"])
async def health_check() -> dict:
    """Health check endpoint for load balancers and monitoring.

    Returns:
        A dict with status and version information.
    """
    return {
        "status": "healthy",
        "version": "1.0.0",
        "service": "safetyforge-api",
    }
