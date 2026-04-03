"""Billing router — Paddle webhooks and subscription status."""

from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from google.cloud import firestore

from app.config import Settings, get_settings
from app.dependencies import get_current_user, get_firestore_client
from app.exceptions import CompanyNotFoundError, InvalidWebhookSignatureError
from app.models.billing import SubscriptionInfo
from app.services.billing_service import BillingService
from app.services.company_service import CompanyService

router = APIRouter(prefix="/billing", tags=["billing"])


@router.post("/webhooks/paddle", status_code=status.HTTP_200_OK)
async def paddle_webhook(
    request: Request,
    db: Annotated[firestore.Client, Depends(get_firestore_client)],
    settings: Annotated[Settings, Depends(get_settings)],
    paddle_signature: str = Header(..., alias="Paddle-Signature"),
) -> dict:
    """Receive and process Paddle webhook events.

    This endpoint does not require authentication — it is secured by
    HMAC-SHA256 signature verification using the Paddle webhook secret.

    Args:
        request: The raw FastAPI request for body extraction.
        db: Firestore client.
        settings: Application settings with Paddle webhook secret.
        paddle_signature: The Paddle-Signature header value.

    Returns:
        A confirmation dict.
    """
    raw_body = await request.body()

    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON payload",
        )

    billing_service = BillingService(db, settings)

    try:
        billing_service.handle_webhook(payload, paddle_signature, raw_body)
    except InvalidWebhookSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid webhook signature",
        )
    except CompanyNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )

    return {"status": "ok"}


@router.get("/subscription/{company_id}", response_model=SubscriptionInfo)
async def get_subscription_status(
    company_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[firestore.Client, Depends(get_firestore_client)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> SubscriptionInfo:
    """Get the subscription status and usage for a company.

    Args:
        company_id: The company to check.
        current_user: Authenticated user claims.
        db: Firestore client.
        settings: Application settings.

    Returns:
        A SubscriptionInfo model with plan and usage details.
    """
    company_service = CompanyService(db)
    try:
        company = company_service.get(company_id)
    except CompanyNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Company not found: {company_id}",
        )

    if company.created_by != current_user["uid"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this company's billing information",
        )

    billing_service = BillingService(db, settings)
    return billing_service.get_subscription_status(company_id)
