"""API contract tests for analytics endpoints."""

import pytest
from fastapi.testclient import TestClient


class TestDashboardMetrics:
    """Tests for GET /me/analytics/dashboard."""

    def test_dashboard_returns_metrics(self, client: TestClient, test_company):
        """Dashboard endpoint returns all metric fields."""
        response = client.get("/api/v1/me/analytics/dashboard")
        assert response.status_code == 200
        data = response.json()

        # Activity metrics
        assert "total_projects" in data
        assert "active_projects" in data
        assert "total_inspections" in data
        assert "inspections_this_month" in data
        assert "total_toolbox_talks" in data
        assert "talks_this_month" in data
        assert "total_hazard_reports" in data
        assert "open_hazard_reports" in data
        assert "total_incidents" in data
        assert "incidents_this_month" in data

        # Compliance metrics
        assert "avg_compliance_score" in data
        assert "total_workers" in data
        assert "workers_with_expired_certs" in data
        assert "workers_with_expiring_certs" in data

        # OSHA metrics
        assert "trir" in data
        assert "dart" in data

        # Mock inspection
        assert "last_mock_score" in data
        assert "last_mock_grade" in data

        # EMR
        assert "current_emr" in data
        assert "projected_emr" in data
        assert "emr_premium_impact" in data

    def test_dashboard_with_project_data(self, client: TestClient, test_company):
        """Dashboard reflects created project data."""
        # Create a project
        client.post(
            "/api/v1/me/projects",
            json={
                "name": "Analytics Test Project",
                "address": "300 Data Way, TX 75001",
            },
        )

        response = client.get("/api/v1/me/analytics/dashboard")
        assert response.status_code == 200
        data = response.json()
        assert data["total_projects"] >= 1
        assert data["active_projects"] >= 1


class TestEmrEstimate:
    """Tests for POST /me/analytics/emr-estimate."""

    def test_emr_estimate(self, client: TestClient, test_company):
        """EMR estimate returns projected savings and recommendations."""
        response = client.post(
            "/api/v1/me/analytics/emr-estimate",
            json={
                "current_emr": 1.2,
                "annual_payroll": 2000000,
                "workers_comp_rate": 8.5,
            },
        )
        assert response.status_code == 200
        data = response.json()

        assert "current_emr" in data
        assert data["current_emr"] == 1.2
        assert "projected_emr" in data
        assert "premium_base" in data
        assert "current_premium" in data
        assert "projected_premium" in data
        assert "potential_savings" in data
        assert "recommendations" in data
        assert isinstance(data["recommendations"], list)
        assert len(data["recommendations"]) > 0

        # Verify premium calculation
        expected_base = 2000000 * (8.5 / 100)
        assert data["premium_base"] == expected_base
        assert data["current_premium"] == expected_base * 1.2
