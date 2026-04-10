"""Feature flag enforcement for premium features."""

from fastapi import Depends, HTTPException
from neo4j import Driver

from app.dependencies import get_company_service, get_current_user, get_neo4j_driver
from app.models.company import SubscriptionStatus
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

# Map billing plan names to feature tier keys
_PLAN_TO_TIER: dict[str, str] = {
    "Free": "free",
    "Starter": "starter",
    "Professional": "professional",
    "Business": "business",
}


def _resolve_tier(company, driver: Driver) -> str:
    """Resolve the feature tier for a company.

    Checks subscription_status and the stored plan_name in Neo4j.

    Args:
        company: The Company model.
        driver: Neo4j driver.

    Returns:
        The tier key string (free, starter, professional, business).
    """
    if company.subscription_status != SubscriptionStatus.ACTIVE:
        return "free"

    with driver.session() as session:
        result = session.run(
            """
            MATCH (c:Company {id: $company_id})
            RETURN c.subscription_plan AS plan_name
            """,
            company_id=company.id,
        )
        record = result.single()

    if record and record["plan_name"]:
        tier = _PLAN_TO_TIER.get(record["plan_name"], "")
        if tier:
            return tier

    # Active subscription with no stored plan defaults to professional
    return "professional"


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
        driver: Driver = Depends(get_neo4j_driver),
    ):
        company = company_service.get_by_user(current_user["uid"])
        if not company:
            raise HTTPException(404, "Company not found")
        tier = _resolve_tier(company, driver)
        allowed = TIER_FEATURES.get(tier, set())
        if feature_name not in allowed:
            raise HTTPException(
                status_code=403,
                detail=f"Feature '{feature_name}' requires a higher subscription tier. Current: {tier}",
            )
        return company

    return _check
