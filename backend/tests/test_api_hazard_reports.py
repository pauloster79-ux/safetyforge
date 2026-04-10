"""API contract tests for hazard report endpoints."""

import json
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient


# -- Sample AI analysis response used across tests --

SAMPLE_AI_ANALYSIS = {
    "identified_hazards": [
        {
            "hazard_id": "h_1",
            "description": "Worker on scaffold without fall protection harness",
            "severity": "high",
            "osha_standard": "29 CFR 1926.451(g)(1)",
            "category": "Fall Protection",
            "recommended_action": "Immediately provide and require use of personal fall arrest systems",
            "location_in_image": "Center of image, second level scaffold",
        },
        {
            "hazard_id": "h_2",
            "description": "Loose debris on walkway creating trip hazard",
            "severity": "medium",
            "osha_standard": "29 CFR 1926.25(a)",
            "category": "Housekeeping",
            "recommended_action": "Clear debris and establish regular housekeeping schedule",
            "location_in_image": "Bottom right of image, ground level",
        },
        {
            "hazard_id": "h_3",
            "description": "Missing hard hat on worker near overhead operations",
            "severity": "low",
            "osha_standard": "29 CFR 1926.100(a)",
            "category": "PPE",
            "recommended_action": "Enforce mandatory hard hat policy in all active work areas",
            "location_in_image": "Left side of image, near crane area",
        },
    ],
    "summary": "The site has significant fall protection deficiencies and housekeeping issues that require immediate attention.",
    "positive_observations": [
        "Barricades are properly placed around the excavation area",
        "Fire extinguishers are visible and accessible",
    ],
}

# Minimal base64 PNG (1x1 transparent pixel) for testing
TINY_PNG_BASE64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR4"
    "2mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
)


def _create_project(client: TestClient) -> str:
    """Helper to create a project and return its ID."""
    resp = client.post(
        "/api/v1/me/projects",
        json={
            "name": "Hazard Test Project",
            "address": "456 Safety Lane, TX 75001",
        },
    )
    assert resp.status_code == 201
    return resp.json()["id"]


def _mock_anthropic_vision(ai_response: dict):
    """Return a context manager that patches the Anthropic client for vision calls.

    Args:
        ai_response: The dict to return as the parsed AI response.

    Returns:
        A patch context manager.
    """
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text=json.dumps(ai_response))]

    return patch(
        "app.services.hazard_analysis_service.anthropic.Anthropic",
        return_value=MagicMock(
            messages=MagicMock(create=MagicMock(return_value=mock_response))
        ),
    )


class TestCreateHazardReport:
    """Tests for POST /me/projects/{project_id}/hazard-reports."""

    def test_create_hazard_report(self, client: TestClient, test_company):
        """Create a hazard report with valid photo data returns 201 with AI analysis."""
        project_id = _create_project(client)

        with _mock_anthropic_vision(SAMPLE_AI_ANALYSIS):
            response = client.post(
                f"/api/v1/me/projects/{project_id}/hazard-reports",
                json={
                    "project_id": project_id,
                    "photo_base64": f"data:image/png;base64,{TINY_PNG_BASE64}",
                    "media_type": "image/png",
                    "description": "Work area near scaffold",
                    "location": "Building A, north side",
                },
            )

        assert response.status_code == 201
        data = response.json()
        assert data["id"].startswith("hzrd_")
        assert data["project_id"] == project_id
        assert data["description"] == "Work area near scaffold"
        assert data["location"] == "Building A, north side"
        assert data["status"] == "open"
        assert data["hazard_count"] == 3
        assert data["highest_severity"] == "high"
        assert len(data["identified_hazards"]) == 3
        assert data["identified_hazards"][0]["osha_standard"] == "29 CFR 1926.451(g)(1)"
        assert data["identified_hazards"][0]["category"] == "Fall Protection"
        assert data["ai_analysis"]["summary"] is not None

    def test_create_hazard_report_project_not_found(
        self, client: TestClient, test_company
    ):
        """Creating a report for a nonexistent project returns 404."""
        with _mock_anthropic_vision(SAMPLE_AI_ANALYSIS):
            response = client.post(
                "/api/v1/me/projects/proj_nonexistent/hazard-reports",
                json={
                    "project_id": "proj_nonexistent",
                    "photo_base64": TINY_PNG_BASE64,
                    "media_type": "image/png",
                },
            )

        assert response.status_code == 404


class TestListHazardReports:
    """Tests for GET /me/projects/{project_id}/hazard-reports."""

    def test_list_hazard_reports(self, client: TestClient, test_company):
        """List hazard reports returns created reports."""
        project_id = _create_project(client)

        # Create two reports
        with _mock_anthropic_vision(SAMPLE_AI_ANALYSIS):
            client.post(
                f"/api/v1/me/projects/{project_id}/hazard-reports",
                json={
                    "project_id": project_id,
                    "photo_base64": TINY_PNG_BASE64,
                    "media_type": "image/png",
                    "description": "Area 1",
                },
            )
            client.post(
                f"/api/v1/me/projects/{project_id}/hazard-reports",
                json={
                    "project_id": project_id,
                    "photo_base64": TINY_PNG_BASE64,
                    "media_type": "image/png",
                    "description": "Area 2",
                },
            )

        response = client.get(f"/api/v1/me/projects/{project_id}/hazard-reports")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert len(data["reports"]) == 2

    def test_list_hazard_reports_empty(self, client: TestClient, test_company):
        """List reports for a project with no reports returns empty."""
        project_id = _create_project(client)
        response = client.get(f"/api/v1/me/projects/{project_id}/hazard-reports")
        assert response.status_code == 200
        data = response.json()
        assert data["reports"] == []
        assert data["total"] == 0

    def test_list_hazard_reports_filter_by_status(
        self, client: TestClient, test_company
    ):
        """Filtering by status returns only matching reports."""
        project_id = _create_project(client)

        with _mock_anthropic_vision(SAMPLE_AI_ANALYSIS):
            resp = client.post(
                f"/api/v1/me/projects/{project_id}/hazard-reports",
                json={
                    "project_id": project_id,
                    "photo_base64": TINY_PNG_BASE64,
                    "media_type": "image/png",
                },
            )
            report_id = resp.json()["id"]

        # Update one to corrected
        client.patch(
            f"/api/v1/me/projects/{project_id}/hazard-reports/{report_id}",
            json={"status": "corrected", "corrective_action_taken": "Fixed it"},
        )

        # Filter by corrected
        response = client.get(
            f"/api/v1/me/projects/{project_id}/hazard-reports?status=corrected"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["reports"][0]["status"] == "corrected"

        # Filter by open should return 0
        response = client.get(
            f"/api/v1/me/projects/{project_id}/hazard-reports?status=open"
        )
        assert response.status_code == 200
        assert response.json()["total"] == 0


class TestGetHazardReport:
    """Tests for GET /me/projects/{project_id}/hazard-reports/{report_id}."""

    def test_get_hazard_report(self, client: TestClient, test_company):
        """Get an existing hazard report returns 200."""
        project_id = _create_project(client)

        with _mock_anthropic_vision(SAMPLE_AI_ANALYSIS):
            create_resp = client.post(
                f"/api/v1/me/projects/{project_id}/hazard-reports",
                json={
                    "project_id": project_id,
                    "photo_base64": TINY_PNG_BASE64,
                    "media_type": "image/png",
                    "description": "Test area",
                },
            )

        report_id = create_resp.json()["id"]
        response = client.get(
            f"/api/v1/me/projects/{project_id}/hazard-reports/{report_id}"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == report_id
        assert data["hazard_count"] == 3

    def test_get_hazard_report_not_found(self, client: TestClient, test_company):
        """Get a nonexistent report returns 404."""
        project_id = _create_project(client)
        response = client.get(
            f"/api/v1/me/projects/{project_id}/hazard-reports/hzrd_nonexistent"
        )
        assert response.status_code == 404


class TestUpdateHazardReportStatus:
    """Tests for PATCH /me/projects/{project_id}/hazard-reports/{report_id}."""

    def test_update_status_to_corrected(self, client: TestClient, test_company):
        """Updating status to corrected sets corrected_at and corrected_by."""
        project_id = _create_project(client)

        with _mock_anthropic_vision(SAMPLE_AI_ANALYSIS):
            create_resp = client.post(
                f"/api/v1/me/projects/{project_id}/hazard-reports",
                json={
                    "project_id": project_id,
                    "photo_base64": TINY_PNG_BASE64,
                    "media_type": "image/png",
                },
            )

        report_id = create_resp.json()["id"]
        response = client.patch(
            f"/api/v1/me/projects/{project_id}/hazard-reports/{report_id}",
            json={
                "status": "corrected",
                "corrective_action_taken": "Installed guardrails and provided harnesses",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "corrected"
        assert data["corrective_action_taken"] == "Installed guardrails and provided harnesses"
        assert data["corrected_at"] is not None
        assert data["corrected_by"] != ""

    def test_update_status_to_in_progress(self, client: TestClient, test_company):
        """Updating status to in_progress works without setting corrected fields."""
        project_id = _create_project(client)

        with _mock_anthropic_vision(SAMPLE_AI_ANALYSIS):
            create_resp = client.post(
                f"/api/v1/me/projects/{project_id}/hazard-reports",
                json={
                    "project_id": project_id,
                    "photo_base64": TINY_PNG_BASE64,
                    "media_type": "image/png",
                },
            )

        report_id = create_resp.json()["id"]
        response = client.patch(
            f"/api/v1/me/projects/{project_id}/hazard-reports/{report_id}",
            json={"status": "in_progress"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "in_progress"
        assert data["corrected_at"] is None

    def test_update_not_found(self, client: TestClient, test_company):
        """Updating a nonexistent report returns 404."""
        project_id = _create_project(client)
        response = client.patch(
            f"/api/v1/me/projects/{project_id}/hazard-reports/hzrd_nonexistent",
            json={"status": "corrected"},
        )
        assert response.status_code == 404


class TestDeleteHazardReport:
    """Tests for DELETE /me/projects/{project_id}/hazard-reports/{report_id}."""

    def test_delete_hazard_report(self, client: TestClient, test_company):
        """Deleting a report returns 204 and report is no longer accessible."""
        project_id = _create_project(client)

        with _mock_anthropic_vision(SAMPLE_AI_ANALYSIS):
            create_resp = client.post(
                f"/api/v1/me/projects/{project_id}/hazard-reports",
                json={
                    "project_id": project_id,
                    "photo_base64": TINY_PNG_BASE64,
                    "media_type": "image/png",
                },
            )

        report_id = create_resp.json()["id"]
        delete_resp = client.delete(
            f"/api/v1/me/projects/{project_id}/hazard-reports/{report_id}"
        )
        assert delete_resp.status_code == 204

        # Verify it's gone
        get_resp = client.get(
            f"/api/v1/me/projects/{project_id}/hazard-reports/{report_id}"
        )
        assert get_resp.status_code == 404

    def test_delete_not_found(self, client: TestClient, test_company):
        """Deleting a nonexistent report returns 404."""
        project_id = _create_project(client)
        response = client.delete(
            f"/api/v1/me/projects/{project_id}/hazard-reports/hzrd_nonexistent"
        )
        assert response.status_code == 404


class TestQuickAnalysis:
    """Tests for POST /me/analyze-photo."""

    def test_quick_analysis_endpoint(self, client: TestClient, test_company):
        """Quick analysis returns hazards without creating a report."""
        with _mock_anthropic_vision(SAMPLE_AI_ANALYSIS):
            response = client.post(
                "/api/v1/me/analyze-photo",
                json={
                    "photo_base64": TINY_PNG_BASE64,
                    "media_type": "image/png",
                    "description": "Quick check of work area",
                    "location": "Building B entrance",
                },
            )

        assert response.status_code == 200
        data = response.json()
        assert "identified_hazards" in data
        assert len(data["identified_hazards"]) == 3
        assert "summary" in data
        assert "positive_observations" in data

    def test_quick_analysis_with_data_uri_prefix(
        self, client: TestClient, test_company
    ):
        """Quick analysis correctly strips data URI prefix."""
        with _mock_anthropic_vision(SAMPLE_AI_ANALYSIS):
            response = client.post(
                "/api/v1/me/analyze-photo",
                json={
                    "photo_base64": f"data:image/jpeg;base64,{TINY_PNG_BASE64}",
                    "media_type": "image/jpeg",
                },
            )

        assert response.status_code == 200
        data = response.json()
        assert len(data["identified_hazards"]) == 3


class TestHazardSeverityRanking:
    """Tests for hazard severity ranking logic."""

    def test_highest_severity_imminent_danger(
        self, client: TestClient, test_company
    ):
        """Report with imminent_danger hazard shows that as highest severity."""
        imminent_analysis = {
            "identified_hazards": [
                {
                    "hazard_id": "h_1",
                    "description": "Unsupported trench wall about to collapse",
                    "severity": "imminent_danger",
                    "osha_standard": "29 CFR 1926.652(a)(1)",
                    "category": "Excavation",
                    "recommended_action": "Evacuate trench immediately and install shoring",
                    "location_in_image": "Center of image",
                },
                {
                    "hazard_id": "h_2",
                    "description": "Missing hard hat",
                    "severity": "low",
                    "osha_standard": "29 CFR 1926.100(a)",
                    "category": "PPE",
                    "recommended_action": "Provide hard hat",
                    "location_in_image": "Left side",
                },
            ],
            "summary": "Critical excavation hazard requiring immediate action.",
            "positive_observations": [],
        }

        project_id = _create_project(client)

        with _mock_anthropic_vision(imminent_analysis):
            response = client.post(
                f"/api/v1/me/projects/{project_id}/hazard-reports",
                json={
                    "project_id": project_id,
                    "photo_base64": TINY_PNG_BASE64,
                    "media_type": "image/png",
                },
            )

        assert response.status_code == 201
        data = response.json()
        assert data["highest_severity"] == "imminent_danger"
        assert data["hazard_count"] == 2

    def test_no_hazards_found(self, client: TestClient, test_company):
        """Report with no hazards has null highest_severity and zero count."""
        clean_analysis = {
            "identified_hazards": [],
            "summary": "No hazards identified. Site appears to be in good condition.",
            "positive_observations": ["All workers wearing proper PPE"],
        }

        project_id = _create_project(client)

        with _mock_anthropic_vision(clean_analysis):
            response = client.post(
                f"/api/v1/me/projects/{project_id}/hazard-reports",
                json={
                    "project_id": project_id,
                    "photo_base64": TINY_PNG_BASE64,
                    "media_type": "image/png",
                },
            )

        assert response.status_code == 201
        data = response.json()
        assert data["highest_severity"] is None
        assert data["hazard_count"] == 0
        assert data["identified_hazards"] == []
