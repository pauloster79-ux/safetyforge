"""API contract tests for state compliance engine endpoints."""

import pytest
from fastapi.testclient import TestClient


class TestListAvailableStates:
    """Tests for GET /me/state-compliance/states."""

    def test_list_states(self, client: TestClient, test_company):
        """States endpoint returns supported states."""
        response = client.get("/api/v1/me/state-compliance/states")
        assert response.status_code == 200
        data = response.json()

        assert data["total"] == 5
        assert isinstance(data["states"], list)
        state_codes = [s["code"] for s in data["states"]]
        assert "CA" in state_codes
        assert "NY" in state_codes
        assert "WA" in state_codes
        assert "OR" in state_codes
        assert "MI" in state_codes

        # Each state has code and name
        for state in data["states"]:
            assert "code" in state
            assert "name" in state


class TestGetStateRequirements:
    """Tests for GET /me/state-compliance/requirements/{state}."""

    def test_california_requirements(self, client: TestClient, test_company):
        """California has IIPP, heat illness, and wildfire requirements."""
        response = client.get("/api/v1/me/state-compliance/requirements/CA")
        assert response.status_code == 200
        data = response.json()

        assert data["state"] == "CA"
        assert data["total"] >= 4

        req_names = [r["requirement_name"] for r in data["requirements"]]
        assert any("IIPP" in name or "Injury" in name for name in req_names)
        assert any("Heat" in name for name in req_names)
        assert any("Wildfire" in name or "Smoke" in name for name in req_names)

        # Each requirement has expected fields
        req = data["requirements"][0]
        assert "id" in req
        assert "state" in req
        assert "requirement_name" in req
        assert "description" in req
        assert "state_standard" in req
        assert "severity" in req

    def test_unsupported_state_returns_empty(self, client: TestClient, test_company):
        """Requesting an unsupported state returns empty requirements."""
        response = client.get("/api/v1/me/state-compliance/requirements/XX")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["requirements"] == []


class TestCheckStateCompliance:
    """Tests for GET /me/state-compliance/check/{state}."""

    def test_check_compliance_returns_gaps(self, client: TestClient, test_company):
        """Compliance check identifies gaps in state requirements."""
        response = client.get("/api/v1/me/state-compliance/check/CA")
        assert response.status_code == 200
        data = response.json()

        assert data["state"] == "CA"
        assert "total_requirements" in data
        assert "met_requirements" in data
        assert "gaps" in data
        assert "compliance_percentage" in data
        assert isinstance(data["gaps"], list)
        assert 0 <= data["compliance_percentage"] <= 100

        # With no documents, most requirements should be gaps
        assert data["total_requirements"] >= 4
        assert len(data["gaps"]) > 0

        # Each gap has expected structure
        if data["gaps"]:
            gap = data["gaps"][0]
            assert "requirement_id" in gap
            assert "requirement_name" in gap
            assert "status" in gap
            assert "action_needed" in gap
