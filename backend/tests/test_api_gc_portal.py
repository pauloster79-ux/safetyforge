"""API contract tests for GC/Sub Portal endpoints."""

import pytest
from fastapi.testclient import TestClient
from google.cloud import firestore

from app.models.company import CompanyCreate, TradeType
from app.services.company_service import CompanyService


class TestCreateRelationship:
    """Tests for POST /gc-portal/relationships."""

    def test_create_relationship(
        self, client: TestClient, test_company, company_service: CompanyService
    ):
        """Creating a relationship links GC and sub companies."""
        # Create a sub company (different user)
        sub_data = CompanyCreate(
            name="Sub Electric LLC",
            address="789 Sub Street, TX 75003",
            license_number="TX-SUB-001",
            trade_type=TradeType.ELECTRICAL,
            owner_name="Sub Owner",
            phone="555-999-0000",
            email="sub@electric.com",
        )
        sub_company = company_service.create(sub_data, "sub_user_001")

        response = client.post(
            "/api/v1/gc-portal/relationships",
            json={
                "sub_company_id": sub_company.id,
                "project_name": "Downtown Tower",
            },
        )
        assert response.status_code == 200
        data = response.json()

        assert data["gc_company_id"] == test_company.id
        assert data["sub_company_id"] == sub_company.id
        assert data["project_name"] == "Downtown Tower"
        assert data["status"] == "active"
        assert data["gc_company_name"] == "Test Construction Co"
        assert data["sub_company_name"] == "Sub Electric LLC"
        assert data["can_view_documents"] is True
        assert data["can_view_incidents"] is False  # Default off

    def test_create_relationship_sub_not_found(self, client: TestClient, test_company):
        """Creating a relationship with nonexistent sub returns 404."""
        response = client.post(
            "/api/v1/gc-portal/relationships",
            json={
                "sub_company_id": "nonexistent_company",
                "project_name": "Test",
            },
        )
        assert response.status_code == 404


class TestListSubsAndGCs:
    """Tests for GET /gc-portal/my-subs and GET /gc-portal/my-gcs."""

    def test_list_my_subs_empty(self, client: TestClient, test_company):
        """Listing subs returns empty when no relationships exist."""
        response = client.get("/api/v1/gc-portal/my-subs")
        assert response.status_code == 200
        data = response.json()
        assert data["relationships"] == []
        assert data["total"] == 0

    def test_list_my_subs_with_relationship(
        self, client: TestClient, test_company, company_service: CompanyService
    ):
        """Listing subs returns relationships after creation."""
        sub_data = CompanyCreate(
            name="Sub Plumbing Co",
            address="456 Pipe Ave, TX 75004",
            license_number="TX-SUB-002",
            trade_type=TradeType.PLUMBING,
            owner_name="Plumber Joe",
            phone="555-888-0000",
            email="joe@plumbing.com",
        )
        sub_company = company_service.create(sub_data, "sub_user_002")

        client.post(
            "/api/v1/gc-portal/relationships",
            json={"sub_company_id": sub_company.id, "project_name": "Mall Build"},
        )

        response = client.get("/api/v1/gc-portal/my-subs")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["relationships"][0]["sub_company_name"] == "Sub Plumbing Co"


class TestInviteSub:
    """Tests for POST /gc-portal/invite."""

    def test_invite_sub(self, client: TestClient, test_company):
        """Inviting a sub creates a pending invitation."""
        response = client.post(
            "/api/v1/gc-portal/invite",
            json={
                "sub_email": "newsub@construction.com",
                "project_name": "Highway Project",
            },
        )
        assert response.status_code == 200
        data = response.json()

        assert data["gc_company_id"] == test_company.id
        assert data["sub_email"] == "newsub@construction.com"
        assert data["project_name"] == "Highway Project"
        assert data["status"] == "pending"
        assert data["gc_company_name"] == "Test Construction Co"


class TestGcDashboard:
    """Tests for GET /gc-portal/dashboard."""

    def test_dashboard_empty(self, client: TestClient, test_company):
        """Dashboard returns empty when no subs exist."""
        response = client.get("/api/v1/gc-portal/dashboard")
        assert response.status_code == 200
        data = response.json()
        assert data["summaries"] == []
        assert data["total"] == 0
