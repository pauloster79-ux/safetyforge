"""Contract tests for /api/v1/me/company endpoints."""

import pytest
from fastapi.testclient import TestClient

from app.models.company import Company


class TestGetCompany:
    """Tests for GET /api/v1/me/company."""

    def test_get_company(
        self, client: TestClient, test_company: Company
    ) -> None:
        """Getting the current user's company returns 200 with company data."""
        response = client.get("/api/v1/me/company")

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Test Construction Co"
        assert data["id"] == test_company.id
        assert data["trade_type"] == "general"

    def test_get_company_no_company(self, client: TestClient) -> None:
        """Getting company when none exists returns 404."""
        response = client.get("/api/v1/me/company")

        assert response.status_code == 404


class TestCreateCompany:
    """Tests for POST /api/v1/companies (existing nested route)."""

    def test_create_company(self, client: TestClient) -> None:
        """Creating a company returns 201 with the full company model."""
        response = client.post(
            "/api/v1/companies",
            json={
                "name": "New Construction LLC",
                "address": "789 Builder Ave, Houston, TX 77001",
                "license_number": "TX-99999",
                "trade_type": "electrical",
                "owner_name": "New Owner",
                "phone": "555-999-8888",
                "email": "new@construction.com",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "New Construction LLC"
        assert data["trade_type"] == "electrical"
        assert data["id"].startswith("comp_")
        assert data["subscription_status"] == "free"

    def test_create_company_duplicate_409(
        self, client: TestClient, test_company: Company
    ) -> None:
        """Creating a second company for the same user returns 409."""
        response = client.post(
            "/api/v1/companies",
            json={
                "name": "Duplicate Company",
                "address": "999 Dup Street, Dallas, TX 75001",
                "license_number": "TX-DUPE",
                "trade_type": "plumbing",
                "owner_name": "Dup Owner",
                "phone": "555-000-0000",
                "email": "dup@company.com",
            },
        )

        assert response.status_code == 409


class TestUpdateCompany:
    """Tests for PATCH /api/v1/me/company."""

    def test_update_company(
        self, client: TestClient, test_company: Company
    ) -> None:
        """Updating a company changes the specified fields."""
        response = client.patch(
            "/api/v1/me/company",
            json={
                "name": "Updated Construction Co",
                "ein": "12-3456789",
                "safety_officer": "John Safety",
                "safety_officer_phone": "555-SAFE",
                "logo_url": "https://example.com/logo.png",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Construction Co"
        assert data["ein"] == "12-3456789"
        assert data["safety_officer"] == "John Safety"
        assert data["safety_officer_phone"] == "555-SAFE"
        assert data["logo_url"] == "https://example.com/logo.png"
