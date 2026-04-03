"""API contract tests for environmental compliance endpoints."""

import pytest
from fastapi.testclient import TestClient


def _create_project(client: TestClient) -> str:
    """Helper to create a project and return its ID."""
    resp = client.post(
        "/me/projects",
        json={
            "name": "Environmental Test Project",
            "address": "101 Green Blvd, TX 75001",
        },
    )
    assert resp.status_code == 201
    return resp.json()["id"]


class TestCreateEnvironmentalProgram:
    """Tests for POST /me/environmental/programs."""

    def test_create_program(self, client: TestClient, test_company):
        """Create an environmental program with valid data returns 201."""
        response = client.post(
            "/me/environmental/programs",
            json={
                "program_type": "silica_exposure_control",
                "title": "Silica Exposure Control Plan",
                "content": {"sections": ["scope", "controls", "monitoring"]},
                "applicable_projects": [],
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["program_type"] == "silica_exposure_control"
        assert data["title"] == "Silica Exposure Control Plan"
        assert data["id"].startswith("envp_")
        assert data["status"] == "active"
        assert data["deleted"] is False


class TestListEnvironmentalPrograms:
    """Tests for GET /me/environmental/programs."""

    def test_list_programs(self, client: TestClient, test_company):
        """List programs returns created programs."""
        client.post(
            "/me/environmental/programs",
            json={
                "program_type": "silica_exposure_control",
                "title": "Silica Plan",
            },
        )
        client.post(
            "/me/environmental/programs",
            json={
                "program_type": "lead_compliance",
                "title": "Lead Plan",
            },
        )

        response = client.get("/me/environmental/programs")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert len(data["programs"]) == 2


class TestExposureMonitoringRecords:
    """Tests for exposure monitoring record endpoints."""

    def test_create_and_list_exposure_records(self, client: TestClient, test_company):
        """Create an exposure record and verify it appears in the list."""
        project_id = _create_project(client)

        create_resp = client.post(
            f"/me/projects/{project_id}/exposure-records",
            json={
                "monitoring_type": "silica",
                "monitoring_date": "2026-03-15",
                "location": "Level 3 concrete cutting",
                "worker_name": "Mike Torres",
                "sample_type": "personal",
                "duration_hours": 8.0,
                "result_value": 35.0,
                "result_unit": "ug/m3",
                "action_level": 25.0,
                "pel": 50.0,
                "controls_in_place": "Wet cutting, P100 respirator",
            },
        )
        assert create_resp.status_code == 201
        record = create_resp.json()
        assert record["id"].startswith("expr_")
        assert record["exceeds_action_level"] is True
        assert record["exceeds_pel"] is False
        assert record["monitoring_type"] == "silica"

        list_resp = client.get(f"/me/projects/{project_id}/exposure-records")
        assert list_resp.status_code == 200
        assert list_resp.json()["total"] == 1

    def test_exposure_summary(self, client: TestClient, test_company):
        """Exposure summary aggregates results by type."""
        project_id = _create_project(client)

        # Create two silica records
        for val in [30.0, 60.0]:
            client.post(
                f"/me/projects/{project_id}/exposure-records",
                json={
                    "monitoring_type": "silica",
                    "monitoring_date": "2026-03-15",
                    "location": "Cutting area",
                    "worker_name": "Worker A",
                    "sample_type": "personal",
                    "duration_hours": 8.0,
                    "result_value": val,
                    "result_unit": "ug/m3",
                    "action_level": 25.0,
                    "pel": 50.0,
                },
            )

        resp = client.get(f"/me/projects/{project_id}/exposure-records/summary")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_samples"] == 2
        assert len(data["summaries"]) == 1
        summary = data["summaries"][0]
        assert summary["monitoring_type"] == "silica"
        assert summary["total_samples"] == 2
        assert summary["max_result"] == 60.0
        assert summary["samples_above_pel"] == 1


class TestSwpppInspections:
    """Tests for SWPPP inspection endpoints."""

    def test_create_and_list_swppp(self, client: TestClient, test_company):
        """Create a SWPPP inspection and verify it appears in the list."""
        project_id = _create_project(client)

        create_resp = client.post(
            f"/me/projects/{project_id}/swppp-inspections",
            json={
                "inspection_date": "2026-03-20",
                "inspector_name": "Jane Green",
                "inspection_type": "routine_weekly",
                "precipitation_last_24h": 0.5,
                "bmp_items": [
                    {"name": "Silt fence", "status": "pass", "notes": "Intact"},
                    {"name": "Inlet protection", "status": "fail", "notes": "Displaced"},
                ],
                "corrective_actions": "Replace inlet protection by EOD",
                "overall_status": "fail",
            },
        )
        assert create_resp.status_code == 201
        insp = create_resp.json()
        assert insp["id"].startswith("swpp_")
        assert insp["overall_status"] == "fail"
        assert len(insp["bmp_items"]) == 2

        list_resp = client.get(f"/me/projects/{project_id}/swppp-inspections")
        assert list_resp.status_code == 200
        assert list_resp.json()["total"] == 1
