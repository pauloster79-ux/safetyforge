"""Tests for billing service and subscription management."""

import hashlib
import hmac

import pytest
from fastapi.testclient import TestClient

from app.exceptions import DocumentLimitExceededError
from app.models.company import Company, CompanyCreate, TradeType
from app.models.document import DocumentCreate, DocumentType
from app.services.billing_service import BillingService, FREE_TIER_MONTHLY_LIMIT, PLAN_LIMITS
from app.services.company_service import CompanyService
from app.services.document_service import DocumentService
from tests.conftest import TEST_SETTINGS, TEST_USER


class TestFreeTierLimitEnforcement:
    """Tests for free tier document limits."""

    def _create_free_company(self, company_service: CompanyService) -> Company:
        """Create a company on the free tier (not upgraded like test_company)."""
        data = CompanyCreate(
            name="Free Tier Co",
            address="999 Free Street, Testville, TX 75001",
            license_number="TX-FREE",
            trade_type=TradeType.GENERAL,
            owner_name="Free Owner",
            phone="555-000-0000",
            email="free@testconstruction.com",
        )
        return company_service.create(data, "free_user_001")

    def test_free_tier_limit_enforcement(
        self,
        billing_service: BillingService,
        document_service: DocumentService,
        company_service: CompanyService,
    ) -> None:
        """Free tier users are blocked after reaching the monthly limit."""
        free_company = self._create_free_company(company_service)
        # Create documents up to the limit
        for i in range(FREE_TIER_MONTHLY_LIMIT):
            data = DocumentCreate(
                title=f"Doc {i}",
                document_type=DocumentType.SSSP,
                project_info={"name": f"Project {i}"},
            )
            document_service.create(free_company.id, data, "free_user_001")

        # The next attempt should raise
        with pytest.raises(DocumentLimitExceededError):
            billing_service.check_document_limit(free_company.id)

    def test_free_tier_under_limit_allowed(
        self,
        billing_service: BillingService,
        document_service: DocumentService,
        company_service: CompanyService,
    ) -> None:
        """Free tier users below the limit can create documents."""
        free_company = self._create_free_company(company_service)
        # Create one document (under the limit of 3)
        data = DocumentCreate(
            title="Single Doc",
            document_type=DocumentType.JHA,
            project_info={"task": "Task"},
        )
        document_service.create(free_company.id, data, "free_user_001")

        # Should not raise
        billing_service.check_document_limit(free_company.id)


class TestPaidTierNoLimit:
    """Tests for paid tier document limits."""

    def test_paid_tier_no_limit(
        self,
        billing_service: BillingService,
        document_service: DocumentService,
        company_service: CompanyService,
        test_company: Company,
    ) -> None:
        """Paid (Professional) tier users have no document limit."""
        from app.models.company import SubscriptionStatus

        # Upgrade company to active subscription
        company_service.update_subscription(
            test_company["id"], SubscriptionStatus.ACTIVE, "sub_test_123"
        )

        # Create more documents than free tier allows
        for i in range(FREE_TIER_MONTHLY_LIMIT + 5):
            data = DocumentCreate(
                title=f"Paid Doc {i}",
                document_type=DocumentType.SSSP,
                project_info={"name": f"Project {i}"},
            )
            document_service.create(test_company["id"], data, TEST_USER["uid"])

        # Should not raise for paid tier
        billing_service.check_document_limit(test_company["id"])


class TestWebhookSignatureVerification:
    """Tests for Paddle webhook signature verification."""

    def test_webhook_signature_verification(
        self, billing_service: BillingService
    ) -> None:
        """Valid Paddle webhook signatures pass verification."""
        payload = b'{"event_type": "subscription.created", "data": {}}'
        secret = TEST_SETTINGS.paddle_webhook_secret
        ts = "1234567890"
        signed_payload = f"{ts}:{payload.decode('utf-8')}"
        h1 = hmac.new(
            secret.encode("utf-8"),
            signed_payload.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        paddle_signature = f"ts={ts};h1={h1}"

        # Should not raise
        billing_service.verify_webhook_signature(payload, paddle_signature)

    def test_webhook_invalid_signature_raises(
        self, billing_service: BillingService
    ) -> None:
        """Invalid Paddle webhook signatures are rejected."""
        from app.exceptions import InvalidWebhookSignatureError

        payload = b'{"event_type": "subscription.created", "data": {}}'

        with pytest.raises(InvalidWebhookSignatureError):
            billing_service.verify_webhook_signature(payload, "ts=123;h1=invalid")


class TestPlanLimitsConfig:
    """Tests for the PLAN_LIMITS configuration."""

    def test_plan_limits_has_required_tiers(self) -> None:
        """PLAN_LIMITS contains all expected plan tiers."""
        expected_plans = {"Free", "Starter", "Professional", "Business"}
        assert set(PLAN_LIMITS.keys()) == expected_plans

    def test_starter_tier_limits(self) -> None:
        """Starter tier has a document limit of 10."""
        assert PLAN_LIMITS["Starter"]["document_limit"] == 10
        assert PLAN_LIMITS["Starter"]["price_monthly"] == 99

    def test_professional_tier_unlimited(self) -> None:
        """Professional tier has unlimited documents."""
        assert PLAN_LIMITS["Professional"]["document_limit"] is None
        assert PLAN_LIMITS["Professional"]["price_monthly"] == 299

    def test_business_tier_unlimited(self) -> None:
        """Business tier has unlimited documents."""
        assert PLAN_LIMITS["Business"]["document_limit"] is None
        assert PLAN_LIMITS["Business"]["price_monthly"] == 599
