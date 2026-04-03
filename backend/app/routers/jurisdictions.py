"""API endpoints for jurisdiction configuration."""

import logging

from fastapi import APIRouter, HTTPException, status

from app.jurisdiction.loader import JurisdictionLoader

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/jurisdictions", tags=["jurisdictions"])


@router.get("")
def list_jurisdictions() -> list[dict]:
    """Return all available jurisdictions.

    Returns:
        A list of jurisdiction summaries with code, name, and regulatory_body.
    """
    return JurisdictionLoader.available_jurisdictions()


@router.get("/{code}")
def get_jurisdiction(code: str, region: str | None = None) -> dict:
    """Return the full jurisdiction configuration for a country.

    Args:
        code: Country code (e.g. US, UK, AU, CA).
        region: Optional sub-national region code.

    Returns:
        Full jurisdiction config for the frontend.
    """
    try:
        ctx = JurisdictionLoader.load(code, region)
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Jurisdiction pack not found for code: {code}",
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        )
    return ctx.to_api_response()


@router.get("/{code}/regions")
def list_regions(code: str) -> list[dict]:
    """Return available sub-national regions for a jurisdiction.

    Args:
        code: Country code.

    Returns:
        A list of region summaries with code and name.
    """
    try:
        return JurisdictionLoader.available_regions(code)
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Jurisdiction pack not found for code: {code}",
        )
