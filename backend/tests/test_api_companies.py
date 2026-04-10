"""Contract tests for company endpoints."""

from fastapi.testclient import TestClient


class TestGetCompany:
    """Tests for GET /api/v1/me/company."""

    def test_get_company(self, client: TestClient, test_company: dict) -> None:
        """Getting the current user's company returns 200 with company data."""
        response = client.get("/api/v1/me/company")

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Test Construction Co"
        assert data["id"] == test_company["id"]
        assert data["trade_type"] == "general"

    def test_get_company_no_company(self, client: TestClient) -> None:
        """Getting company when none exists returns 404."""
        response = client.get("/api/v1/me/company")

        assert response.status_code == 404


class TestCreateCompany:
    """Tests for POST /api/v1/companies."""

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
        assert data["created_by"] == "test_user_001"

    def test_create_company_duplicate_409(
        self, client: TestClient, test_company: dict
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

    def test_create_company_validation_error(self, client: TestClient) -> None:
        """Creating a company with invalid data returns 422."""
        response = client.post(
            "/api/v1/companies",
            json={
                "name": "X",
                "address": "Short",
                "license_number": "",
                "trade_type": "general",
                "owner_name": "O",
                "phone": "123",
                "email": "not-an-email",
            },
        )

        assert response.status_code == 422


class TestUpdateCompany:
    """Tests for PATCH /api/v1/me/company."""

    def test_update_company(self, client: TestClient, test_company: dict) -> None:
        """Updating a company changes the specified fields."""
        response = client.patch(
            "/api/v1/me/company",
            json={
                "name": "Updated Construction Co",
                "ein": "12-3456789",
                "safety_officer": "John Safety",
                "safety_officer_phone": "555-7233",
                "logo_url": "https://example.com/logo.png",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Construction Co"
        assert data["ein"] == "12-3456789"
        assert data["safety_officer"] == "John Safety"
        assert data["safety_officer_phone"] == "555-7233"
        assert data["logo_url"] == "https://example.com/logo.png"
        assert data["address"] == test_company["address"]

    def test_update_company_no_company(self, client: TestClient) -> None:
        """Updating when no company exists returns 404."""
        response = client.patch(
            "/api/v1/me/company",
            json={"name": "Ghost Company"},
        )

        assert response.status_code == 404


class TestGetCompanyById:
    """Tests for GET /api/v1/companies/{company_id}."""

    def test_get_company_by_id(self, client: TestClient, test_company: dict) -> None:
        """Getting a company by ID returns 200."""
        response = client.get(f"/api/v1/companies/{test_company['id']}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_company["id"]
        assert data["name"] == test_company["name"]

    def test_get_company_not_found(self, client: TestClient) -> None:
        """Getting a non-existent company returns 404."""
        response = client.get("/api/v1/companies/comp_nonexistent")

        assert response.status_code == 404
