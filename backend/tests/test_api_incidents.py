"""API contract tests for incident endpoints."""

import pytest
from fastapi.testclient import TestClient


def _create_project(client: TestClient) -> str:
    """Helper to create a project and return its ID."""
    resp = client.post(
        "/api/v1/me/projects",
        json={
            "name": "Incident Test Project",
            "address": "200 Hazard Drive, TX 75001",
        },
    )
    assert resp.status_code == 201
    return resp.json()["id"]


def _create_incident(client: TestClient, project_id: str, **overrides) -> dict:
    """Helper to create an incident and return the response data."""
    payload = {
        "project_id": project_id,
        "incident_date": "2026-03-31",
        "incident_time": "10:30",
        "location": "Building A, 3rd floor",
        "severity": "first_aid",
        "description": "Worker slipped on wet surface and sustained minor abrasion to right knee.",
    }
    payload.update(overrides)
    resp = client.post(f"/api/v1/me/projects/{project_id}/incidents", json=payload)
    assert resp.status_code == 201
    return resp.json()


class TestCreateIncident:
    """Tests for POST /me/projects/{project_id}/incidents."""

    def test_create_incident(self, client: TestClient, test_company):
        """Create an incident with valid data returns 201."""
        project_id = _create_project(client)
        data = _create_incident(client, project_id)

        assert data["id"].startswith("inc_")
        assert data["project_id"] == project_id
        assert data["severity"] == "first_aid"
        assert data["status"] == "reported"
        assert data["osha_recordable"] is False
        assert data["osha_reportable"] is False

    def test_create_fatality_incident_is_osha_reportable(
        self, client: TestClient, test_company
    ):
        """A fatality incident is automatically marked OSHA recordable and reportable."""
        project_id = _create_project(client)
        data = _create_incident(
            client,
            project_id,
            severity="fatality",
            description="Fatal fall from scaffolding without proper fall protection equipment.",
        )
        assert data["osha_recordable"] is True
        assert data["osha_reportable"] is True

    def test_create_medical_treatment_is_recordable(
        self, client: TestClient, test_company
    ):
        """A medical treatment incident is recordable but not reportable."""
        project_id = _create_project(client)
        data = _create_incident(
            client,
            project_id,
            severity="medical_treatment",
            description="Worker required stitches after laceration from circular saw operation.",
        )
        assert data["osha_recordable"] is True
        assert data["osha_reportable"] is False


class TestListIncidents:
    """Tests for GET /me/projects/{project_id}/incidents."""

    def test_list_incidents(self, client: TestClient, test_company):
        """List returns created incidents."""
        project_id = _create_project(client)
        _create_incident(client, project_id)
        _create_incident(
            client,
            project_id,
            severity="near_miss",
            description="Unsecured load nearly struck worker. Near miss event reported.",
        )

        response = client.get(f"/api/v1/me/projects/{project_id}/incidents")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert len(data["incidents"]) == 2


class TestUpdateIncident:
    """Tests for PATCH /me/projects/{project_id}/incidents/{id}."""

    def test_update_incident_status(self, client: TestClient, test_company):
        """Update incident status returns updated data."""
        project_id = _create_project(client)
        incident = _create_incident(client, project_id)
        incident_id = incident["id"]

        response = client.patch(
            f"/api/v1/me/projects/{project_id}/incidents/{incident_id}",
            json={"status": "investigating"},
        )
        assert response.status_code == 200
        assert response.json()["status"] == "investigating"


class TestDeleteIncident:
    """Tests for DELETE /me/projects/{project_id}/incidents/{id}."""

    def test_delete_incident(self, client: TestClient, test_company):
        """Delete incident returns 204 and get returns 404."""
        project_id = _create_project(client)
        incident = _create_incident(client, project_id)
        incident_id = incident["id"]

        response = client.delete(
            f"/api/v1/me/projects/{project_id}/incidents/{incident_id}"
        )
        assert response.status_code == 204

        get_resp = client.get(
            f"/api/v1/me/projects/{project_id}/incidents/{incident_id}"
        )
        assert get_resp.status_code == 404
