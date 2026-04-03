"""Feature flag enforcement for premium features."""

from fastapi import Depends, HTTPException

from app.dependencies import get_company_service, get_current_user
from app.services.company_service import CompanyService

TIER_FEATURES: dict[str, set[str]] = {
    "free": set(),
    "starter": {"mock_inspection", "morning_brief"},
    "professional": {
        "mock_inspection",
        "morning_brief",
        "photo_hazard",
        "voice_input",
        "prequalification_auto",
    },
    "business": {
        "mock_inspection",
        "morning_brief",
        "photo_hazard",
        "voice_input",
        "gc_portal",
        "prequalification_auto",
    },
}


def require_feature(feature_name: str):
    """FastAPI dependency that checks if the company's subscription tier includes a feature.

    Args:
        feature_name: The feature identifier to check (e.g. ``mock_inspection``).

    Returns:
        A FastAPI dependency callable that resolves the company and validates
        the feature is available on their current tier.
    """

    async def _check(
        current_user: dict = Depends(get_current_user),
        company_service: CompanyService = Depends(get_company_service),
    ):
        company = company_service.get_by_user(current_user["uid"])
        if not company:
            raise HTTPException(404, "Company not found")
        tier = getattr(company, "subscription_tier", "free") or "free"
        allowed = TIER_FEATURES.get(tier.lower(), set())
        if feature_name not in allowed:
            raise HTTPException(
                status_code=403,
                detail=f"Feature '{feature_name}' requires a higher subscription tier. Current: {tier}",
            )
        return company

    return _check
