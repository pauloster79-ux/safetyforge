"""API contract tests for morning brief endpoints."""

import pytest
from fastapi.testclient import TestClient


def _create_project(client: TestClient) -> str:
    """Helper to create a project and return its ID."""
    resp = client.post(
        "/me/projects",
        json={
            "name": "Morning Brief Test Project",
            "address": "100 Safety Lane, TX 75001",
        },
    )
    assert resp.status_code == 201
    return resp.json()["id"]


class TestGetTodayMorningBrief:
    """Tests for GET /me/projects/{project_id}/morning-brief."""

    def test_generate_today_brief(self, client: TestClient, test_company):
        """First request generates a new brief for today and returns 200."""
        project_id = _create_project(client)

        response = client.get(f"/me/projects/{project_id}/morning-brief")
        assert response.status_code == 200
        data = response.json()
        assert data["id"].startswith("brief_")
        assert data["project_id"] == project_id
        assert "risk_score" in data
        assert "risk_level" in data
        assert data["risk_level"] in ["low", "moderate", "elevated", "high", "critical"]
        assert "weather" in data
        assert "alerts" in data
        assert isinstance(data["alerts"], list)
        assert "recommended_toolbox_talk_topic" in data
        assert "summary" in data

    def test_returns_existing_brief_on_second_call(self, client: TestClient, test_company):
        """Second call on the same day returns the existing brief."""
        project_id = _create_project(client)

        first = client.get(f"/me/projects/{project_id}/morning-brief")
        assert first.status_code == 200
        first_id = first.json()["id"]

        second = client.get(f"/me/projects/{project_id}/morning-brief")
        assert second.status_code == 200
        assert second.json()["id"] == first_id

    def test_brief_for_nonexistent_project_returns_404(
        self, client: TestClient, test_company
    ):
        """Requesting a brief for a nonexistent project returns 404."""
        response = client.get("/me/projects/proj_nonexistent/morning-brief")
        assert response.status_code == 404


class TestListMorningBriefs:
    """Tests for GET /me/projects/{project_id}/morning-briefs."""

    def test_list_briefs(self, client: TestClient, test_company):
        """List returns generated briefs."""
        project_id = _create_project(client)

        # Generate one brief
        client.get(f"/me/projects/{project_id}/morning-brief")

        response = client.get(f"/me/projects/{project_id}/morning-briefs")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        assert len(data["briefs"]) >= 1
        assert data["briefs"][0]["project_id"] == project_id
