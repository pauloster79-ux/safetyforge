"""Authentication router — Clerk JWT verification."""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends
from neo4j import Driver

from app.dependencies import get_current_user, get_neo4j_driver
from app.models.company import CompanyCreate, TradeType
from app.services.company_service import CompanyService
from app.services.member_service import MemberService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/verify-token")
async def verify_token(
    current_user: Annotated[dict, Depends(get_current_user)],
    driver: Annotated[Driver, Depends(get_neo4j_driver)],
) -> dict:
    """Verify a Clerk JWT and return user info with company association.

    The frontend calls this after Clerk sign-in to confirm the token is valid
    and to retrieve the user's associated company (if any). If no company exists,
    one is auto-created with sensible defaults so the user can proceed to onboarding.

    Args:
        current_user: Decoded Clerk JWT claims.
        driver: Neo4j driver for company lookup.

    Returns:
        A dict with user info, company data, and is_new_user flag.
    """
    uid = current_user["uid"]
    email = current_user["email"]

    company_service = CompanyService(driver)
    member_service = MemberService(driver)

    company = company_service.get_by_user(uid)
    is_new_user = False

    if company is None:
        # Auto-create a minimal company profile for first-time users
        email_prefix = email.split("@")[0] if email else "user"
        company_name = f"{email_prefix}'s Company"

        company_data = CompanyCreate(
            name=company_name,
            address="Not yet provided",
            license_number="PENDING",
            trade_type=TradeType.OTHER,
            owner_name=email_prefix,
            phone="000-000-0000",
            email=email,
        )

        company = company_service.create(company_data, uid)
        member_service.create_owner_member(company.id, uid, email)
        is_new_user = True
        logger.info("Auto-created company %s for new user %s", company.id, uid)

    return {
        "user": {
            "uid": uid,
            "email": email,
            "email_verified": current_user["email_verified"],
        },
        "company": company.model_dump(mode="json"),
        "is_new_user": is_new_user,
    }
