"""API contract tests for prequalification automation endpoints."""

import pytest
from fastapi.testclient import TestClient


class TestGeneratePrequalPackage:
    """Tests for POST /me/prequalification/generate."""

    def test_generate_package_returns_readiness(self, client: TestClient, test_company):
        """Generating a package returns readiness scores and document list."""
        response = client.post(
            "/api/v1/me/prequalification/generate",
            params={"platform": "generic", "client_name": "ABC Builders"},
        )
        assert response.status_code == 200
        data = response.json()

        assert data["platform"] == "generic"
        assert data["client_name"] == "ABC Builders"
        assert "overall_readiness" in data
        assert 0 <= data["overall_readiness"] <= 100
        assert "total_documents" in data
        assert "ready_documents" in data
        assert "missing_documents" in data
        assert "documents" in data
        assert isinstance(data["documents"], list)
        assert len(data["documents"]) > 0
        assert "questionnaire" in data
        assert isinstance(data["questionnaire"], dict)

        # Verify questionnaire has pre-filled company data
        q = data["questionnaire"]
        assert q["company_name"] == "Test Construction Co"
        assert q["email"] == "owner@testconstruction.com"

    def test_generate_isnetworld_package(self, client: TestClient, test_company):
        """ISNetworld package has platform-specific requirements."""
        response = client.post(
            "/api/v1/me/prequalification/generate",
            params={"platform": "isnetworld"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["platform"] == "isnetworld"
        assert data["total_documents"] >= 15  # ISNetworld has many requirements

        # Check that ISNetworld-specific docs are present
        doc_names = [d["document_name"] for d in data["documents"]]
        assert any("HazCom" in name or "Hazard Communication" in name for name in doc_names)
        assert any("OSHA 300" in name for name in doc_names)
        assert any("EMR" in name for name in doc_names)


class TestListPrequalPackages:
    """Tests for GET /me/prequalification/packages."""

    def test_list_packages_empty(self, client: TestClient, test_company):
        """Listing packages returns empty list when none exist."""
        response = client.get("/api/v1/me/prequalification/packages")
        assert response.status_code == 200
        data = response.json()
        assert data["packages"] == []
        assert data["total"] == 0

    def test_list_packages_after_generation(self, client: TestClient, test_company):
        """Listing packages returns generated packages."""
        # Generate a package first
        client.post(
            "/api/v1/me/prequalification/generate",
            params={"platform": "generic", "client_name": "Test GC"},
        )

        response = client.get("/api/v1/me/prequalification/packages")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert len(data["packages"]) == 1
        assert data["packages"][0]["client_name"] == "Test GC"


class TestGetPrequalRequirements:
    """Tests for GET /me/prequalification/requirements/{platform}."""

    def test_get_requirements_for_platform(self, client: TestClient, test_company):
        """Requirements endpoint returns platform-specific document list."""
        response = client.get("/api/v1/me/prequalification/requirements/isnetworld")
        assert response.status_code == 200
        data = response.json()

        assert data["platform"] == "isnetworld"
        assert data["total"] > 0
        assert isinstance(data["requirements"], list)

        # Each requirement has expected fields
        req = data["requirements"][0]
        assert "document_name" in req
        assert "category" in req
        assert "required" in req
        assert "status" in req
        assert "source" in req
