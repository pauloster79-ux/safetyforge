"""Subscription and billing management service for Paddle integration."""

import hashlib
import hmac
import logging
from datetime import datetime, timezone
from typing import Any

from google.cloud import firestore

from app.config import Settings
from app.exceptions import (
    DocumentLimitExceededError,
    InvalidWebhookSignatureError,
    ProjectLimitExceededError,
)
from app.models.billing import SubscriptionInfo
from app.models.company import Company, SubscriptionStatus
from app.services.company_service import CompanyService
from app.services.document_service import DocumentService
from app.services.project_service import ProjectService

logger = logging.getLogger(__name__)

FREE_TIER_MONTHLY_LIMIT = 3

# Plan limits: maps plan name to monthly document limit (None = unlimited)
PLAN_LIMITS: dict[str, dict] = {
    "Free": {
        "document_limit": FREE_TIER_MONTHLY_LIMIT,
        "active_projects": 1,
        "price_monthly": 0,
    },
    "Starter": {
        "document_limit": 10,
        "active_projects": 2,
        "price_monthly": 99,
    },
    "Professional": {
        "document_limit": None,
        "active_projects": 8,
        "price_monthly": 299,
    },
    "Business": {
        "document_limit": None,
        "active_projects": 20,
        "price_monthly": 599,
    },
}


class BillingService:
    """Manages subscriptions and billing via Paddle webhooks.

    Args:
        db: Firestore client instance.
        settings: Application settings with Paddle credentials.
    """

    def __init__(self, db: firestore.Client, settings: Settings) -> None:
        self.db = db
        self.settings = settings
        self.company_service = CompanyService(db)
        self.document_service = DocumentService(db)
        self.project_service = ProjectService(db)

    def _webhook_events_collection(self) -> firestore.CollectionReference:
        """Return the webhook_events collection reference for idempotency tracking.

        Returns:
            A Firestore collection reference.
        """
        return self.db.collection("webhook_events")

    def is_webhook_processed(self, event_id: str) -> bool:
        """Check whether a webhook event has already been processed.

        Args:
            event_id: The unique event identifier from the webhook payload.

        Returns:
            True if the event was already processed, False otherwise.
        """
        doc = self._webhook_events_collection().document(event_id).get()
        return doc.exists

    def mark_webhook_processed(
        self, event_id: str, event_type: str, company_id: str
    ) -> None:
        """Record a webhook event as processed for idempotency.

        Args:
            event_id: The unique event identifier.
            event_type: The webhook event type (e.g. subscription_created).
            company_id: The company ID associated with the event.
        """
        self._webhook_events_collection().document(event_id).set(
            {
                "event_id": event_id,
                "event_type": event_type,
                "processed_at": datetime.now(timezone.utc),
                "company_id": company_id,
            }
        )

    def verify_webhook_signature(self, raw_body: bytes, paddle_signature: str) -> None:
        """Verify a Paddle webhook signature using HMAC-SHA256.

        Paddle-Signature header format: ``ts=TIMESTAMP;h1=HASH``

        Args:
            raw_body: The raw request body bytes.
            paddle_signature: The Paddle-Signature header value.

        Raises:
            InvalidWebhookSignatureError: If the signature does not match.
        """
        secret = self.settings.paddle_webhook_secret
        if not secret:
            raise InvalidWebhookSignatureError()

        parts: dict[str, str] = {}
        for part in paddle_signature.split(";"):
            key, _, value = part.partition("=")
            parts[key] = value

        ts = parts.get("ts", "")
        h1 = parts.get("h1", "")

        if not ts or not h1:
            raise InvalidWebhookSignatureError()

        signed_payload = f"{ts}:{raw_body.decode('utf-8')}"
        expected = hmac.new(
            secret.encode("utf-8"),
            signed_payload.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        if not hmac.compare_digest(expected, h1):
            raise InvalidWebhookSignatureError()

    def handle_webhook(self, payload: dict[str, Any], paddle_signature: str, raw_body: bytes) -> None:
        """Process a Paddle webhook event.

        Verifies the signature, extracts event data, and updates the
        company's subscription status accordingly.

        Args:
            payload: The parsed webhook JSON payload.
            paddle_signature: The Paddle-Signature header value.
            raw_body: The raw request body bytes for signature verification.

        Raises:
            InvalidWebhookSignatureError: If the signature is invalid.
        """
        self.verify_webhook_signature(raw_body, paddle_signature)

        event_type = payload.get("event_type", "")
        notification_id = payload.get("notification_id", "")
        data = payload.get("data", {})

        # Extract company_id from custom_data
        custom_data = data.get("custom_data", {})
        company_id = custom_data.get("company_id")

        if not company_id:
            logger.warning("Webhook received without company_id in custom_data: %s", event_type)
            return

        subscription_id = str(data.get("id", ""))

        # Idempotency check using notification_id
        event_id = notification_id or f"{subscription_id}_{event_type}"
        if self.is_webhook_processed(event_id):
            logger.info("Skipping already-processed webhook event: %s", event_id)
            return

        # Map Paddle event types to subscription statuses
        status_map: dict[str, SubscriptionStatus | None] = {
            "subscription.created": SubscriptionStatus.ACTIVE,
            "subscription.updated": None,  # check data.status
            "subscription.canceled": SubscriptionStatus.CANCELLED,
            "subscription.paused": SubscriptionStatus.PAUSED,
            "subscription.resumed": SubscriptionStatus.ACTIVE,
            "transaction.payment_failed": SubscriptionStatus.PAST_DUE,
        }

        if event_type not in status_map:
            logger.info("Ignoring unhandled webhook event: %s", event_type)
            return

        new_status = status_map[event_type]
        if new_status is None:
            # subscription.updated — resolve from data.status
            new_status = self._resolve_update_status(data)

        # Resolve and store plan name from price ID
        items = data.get("items", [])
        if items:
            price_id = items[0].get("price", {}).get("id", "")
            plan_name = self._resolve_plan_name_from_price(price_id)
        else:
            plan_name = None

        try:
            self.company_service.update_subscription(
                company_id=company_id,
                status=new_status,
                subscription_id=subscription_id,
            )
            # Store plan_name if resolved
            if plan_name:
                doc_ref = self.company_service._collection().document(company_id)
                doc_ref.update({"plan_name": plan_name})

            self.mark_webhook_processed(event_id, event_type, company_id)
            logger.info(
                "Updated company %s subscription to %s (event: %s)",
                company_id,
                new_status.value,
                event_type,
            )
        except Exception:
            logger.exception("Failed to update subscription for company %s", company_id)
            raise

    def _resolve_update_status(self, data: dict[str, Any]) -> SubscriptionStatus:
        """Determine the subscription status from a subscription.updated event.

        Args:
            data: The subscription data from the webhook payload.

        Returns:
            The resolved SubscriptionStatus.
        """
        paddle_status = data.get("status", "")
        mapping = {
            "active": SubscriptionStatus.ACTIVE,
            "past_due": SubscriptionStatus.PAST_DUE,
            "canceled": SubscriptionStatus.CANCELLED,
            "paused": SubscriptionStatus.PAUSED,
            "trialing": SubscriptionStatus.ACTIVE,
        }
        return mapping.get(paddle_status, SubscriptionStatus.ACTIVE)

    def _resolve_plan_name_from_price(self, price_id: str) -> str:
        """Map a Paddle price ID to a plan name.

        Args:
            price_id: The Paddle price ID from the webhook item.

        Returns:
            The plan name string.
        """
        price_map = {
            self.settings.paddle_price_starter: "Starter",
            self.settings.paddle_price_professional: "Professional",
            self.settings.paddle_price_business: "Business",
        }
        return price_map.get(price_id, "Free")

    def _resolve_plan_name(self, company: Company) -> str:
        """Resolve the plan name for a company based on subscription status.

        Checks the company's Firestore data for a stored plan_name field.
        Falls back to 'Free' for non-active subscriptions.

        Args:
            company: The Company model.

        Returns:
            The plan name string.
        """
        if company.subscription_status != SubscriptionStatus.ACTIVE:
            return "Free"

        # Look for stored plan_name in the Firestore document
        doc = self.company_service._collection().document(company.id).get()
        if doc.exists:
            data = doc.to_dict()
            stored_plan = data.get("plan_name")
            if stored_plan and stored_plan in PLAN_LIMITS:
                return stored_plan

        # Default paid plan if not stored
        return "Professional"

    def get_subscription_status(self, company_id: str) -> SubscriptionInfo:
        """Get the current subscription status for a company.

        Args:
            company_id: The company ID to check.

        Returns:
            A SubscriptionInfo model with usage and plan details.
        """
        company = self.company_service.get(company_id)
        docs_used = self.document_service.count_documents_this_month(company_id)

        plan_name = self._resolve_plan_name(company)
        plan_config = PLAN_LIMITS.get(plan_name, PLAN_LIMITS["Free"])

        return SubscriptionInfo(
            company_id=company_id,
            status=company.subscription_status.value,
            plan_name=plan_name,
            documents_used_this_month=docs_used,
            documents_limit=plan_config["document_limit"],
            current_period_end=None,
            cancel_at_period_end=company.subscription_status == SubscriptionStatus.CANCELLED,
        )

    def _maybe_reset_billing_period(self, company_id: str) -> None:
        """Reset the monthly document counter if the billing period has rolled over.

        Checks the ``billing_period_start`` field on the company document. If the
        current month differs from the stored month, resets
        ``documents_used_this_month`` to 0 and updates ``billing_period_start``
        to the first day of the current month.

        Args:
            company_id: The company document ID.
        """
        doc_ref = self.company_service._collection().document(company_id)
        doc = doc_ref.get()
        if not doc.exists:
            return

        data = doc.to_dict()
        now = datetime.now(timezone.utc)
        billing_period_start = data.get("billing_period_start")

        needs_reset = False
        if billing_period_start is None:
            needs_reset = True
        else:
            # Firestore may return a datetime or a date string
            if isinstance(billing_period_start, datetime):
                period_month = billing_period_start.month
                period_year = billing_period_start.year
            else:
                period_month = None
                period_year = None

            if period_month != now.month or period_year != now.year:
                needs_reset = True

        if needs_reset:
            first_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            doc_ref.update(
                {
                    "documents_used_this_month": 0,
                    "billing_period_start": first_of_month,
                }
            )
            logger.info(
                "Reset billing period for company %s to %s",
                company_id,
                first_of_month.isoformat(),
            )

    def check_document_limit(self, company_id: str) -> None:
        """Check whether a company can create another document.

        Uses PLAN_LIMITS to determine the monthly document cap. Plans with
        a None limit (Professional, Business) have no restriction. Automatically
        resets the monthly counter when the billing period rolls over.

        Args:
            company_id: The company ID to check.

        Raises:
            DocumentLimitExceededError: If the plan's document limit has been reached.
        """
        # Reset counter if billing period has rolled over
        self._maybe_reset_billing_period(company_id)

        company = self.company_service.get(company_id)
        plan_name = self._resolve_plan_name(company)
        plan_config = PLAN_LIMITS.get(plan_name, PLAN_LIMITS["Free"])
        limit = plan_config["document_limit"]

        if limit is None:
            return

        docs_used = self.document_service.count_documents_this_month(company_id)
        if docs_used >= limit:
            raise DocumentLimitExceededError(company_id, limit)

    def check_project_limit(self, company_id: str) -> None:
        """Check whether a company can create another active project.

        Uses PLAN_LIMITS to determine the active project cap for the
        company's current subscription tier.

        Args:
            company_id: The company ID to check.

        Raises:
            ProjectLimitExceededError: If the plan's active project limit has been reached.
        """
        company = self.company_service.get(company_id)
        plan_name = self._resolve_plan_name(company)
        plan_config = PLAN_LIMITS.get(plan_name, PLAN_LIMITS["Free"])
        limit = plan_config["active_projects"]

        # Count active projects (status != completed)
        result = self.project_service.list_projects(company_id, limit=1000)
        active_count = sum(
            1
            for p in result["projects"]
            if p.status not in ("completed",)
        )

        if active_count >= limit:
            raise ProjectLimitExceededError(company_id, limit)

    def create_checkout(self, company_id: str, tier: str) -> str:
        """Create a Paddle checkout URL for the specified tier.

        Args:
            company_id: The company requesting the checkout.
            tier: The target tier (starter, professional, or business).

        Returns:
            A checkout URL string.

        Raises:
            ValueError: If the tier is not valid.
        """
        import httpx

        price_ids = {
            "starter": self.settings.paddle_price_starter,
            "professional": self.settings.paddle_price_professional,
            "business": self.settings.paddle_price_business,
        }
        price_id = price_ids.get(tier.lower())
        if not price_id:
            raise ValueError(
                f"Invalid tier '{tier}'. Must be one of: {', '.join(sorted(price_ids))}"
            )

        response = httpx.post(
            f"{self.settings.paddle_api_url}/transactions",
            headers={
                "Authorization": f"Bearer {self.settings.paddle_api_key}",
                "Content-Type": "application/json",
            },
            json={
                "items": [{"price_id": price_id, "quantity": 1}],
                "custom_data": {"company_id": company_id},
                "checkout": {"url": "https://app.safetyforge.com/billing?success=true"},
            },
        )
        response.raise_for_status()
        data = response.json()["data"]
        return data["checkout"]["url"]

    def cancel_subscription(self, subscription_id: str) -> dict:
        """Cancel a subscription via the Paddle API.

        Args:
            subscription_id: The Paddle subscription ID to cancel.

        Returns:
            A dict with subscription data from Paddle.

        Raises:
            httpx.HTTPStatusError: If the API request fails.
        """
        import httpx

        response = httpx.post(
            f"{self.settings.paddle_api_url}/subscriptions/{subscription_id}/cancel",
            headers={
                "Authorization": f"Bearer {self.settings.paddle_api_key}",
                "Content-Type": "application/json",
            },
            json={"effective_from": "next_billing_period"},
        )
        response.raise_for_status()
        return response.json().get("data", {})
