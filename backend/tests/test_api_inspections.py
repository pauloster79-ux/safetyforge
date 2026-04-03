"""API contract tests for inspection endpoints."""

import pytest
from fastapi.testclient import TestClient


def _create_project(client: TestClient) -> str:
    """Helper to create a project and return its ID."""
    resp = client.post(
        "/me/projects",
        json={
            "name": "Inspection Test Project",
            "address": "789 Safety Blvd, TX 75001",
        },
    )
    assert resp.status_code == 201
    return resp.json()["id"]


class TestCreateInspection:
    """Tests for POST /me/projects/{project_id}/inspections."""

    def test_create_inspection(self, client: TestClient, test_company):
        """Create an inspection with valid data returns 201."""
        project_id = _create_project(client)

        response = client.post(
            f"/me/projects/{project_id}/inspections",
            json={
                "inspection_type": "daily_site",
                "inspection_date": "2026-03-31",
                "inspector_name": "Jane Inspector",
                "weather_conditions": "Clear and sunny",
                "temperature": "72F",
                "workers_on_site": 25,
                "items": [
                    {
                        "item_id": "ds_ppe_01",
                        "category": "PPE Compliance",
                        "description": "Hard hats worn",
                        "status": "pass",
                        "notes": "",
                    },
                    {
                        "item_id": "ds_fall_01",
                        "category": "Fall Protection",
                        "description": "Guardrails intact",
                        "status": "pass",
                        "notes": "All good",
                    },
                ],
                "overall_notes": "Site in good condition.",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["inspection_type"] == "daily_site"
        assert data["inspector_name"] == "Jane Inspector"
        assert data["workers_on_site"] == 25
        assert data["overall_status"] == "pass"
        assert data["id"].startswith("insp_")
        assert data["project_id"] == project_id
        assert len(data["items"]) == 2
        assert data["deleted"] is False


class TestListInspections:
    """Tests for GET /me/projects/{project_id}/inspections."""

    def test_list_inspections(self, client: TestClient, test_company):
        """List inspections returns created inspections."""
        project_id = _create_project(client)

        # Create two inspections
        client.post(
            f"/me/projects/{project_id}/inspections",
            json={
                "inspection_type": "daily_site",
                "inspection_date": "2026-03-30",
                "inspector_name": "Inspector A",
            },
        )
        client.post(
            f"/me/projects/{project_id}/inspections",
            json={
                "inspection_type": "scaffold",
                "inspection_date": "2026-03-31",
                "inspector_name": "Inspector B",
            },
        )

        response = client.get(f"/me/projects/{project_id}/inspections")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert len(data["inspections"]) == 2

    def test_list_inspections_empty(self, client: TestClient, test_company):
        """List inspections for project with no inspections returns empty."""
        project_id = _create_project(client)
        response = client.get(f"/me/projects/{project_id}/inspections")
        assert response.status_code == 200
        data = response.json()
        assert data["inspections"] == []
        assert data["total"] == 0


class TestGetInspection:
    """Tests for GET /me/projects/{project_id}/inspections/{inspection_id}."""

    def test_get_inspection(self, client: TestClient, test_company):
        """Get an existing inspection returns 200."""
        project_id = _create_project(client)

        create_resp = client.post(
            f"/me/projects/{project_id}/inspections",
            json={
                "inspection_type": "daily_site",
                "inspection_date": "2026-03-31",
                "inspector_name": "Jane Inspector",
            },
        )
        inspection_id = create_resp.json()["id"]

        response = client.get(
            f"/me/projects/{project_id}/inspections/{inspection_id}"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == inspection_id
        assert data["inspector_name"] == "Jane Inspector"

    def test_get_inspection_not_found(self, client: TestClient, test_company):
        """Get a non-existent inspection returns 404."""
        project_id = _create_project(client)
        response = client.get(
            f"/me/projects/{project_id}/inspections/insp_nonexistent123"
        )
        assert response.status_code == 404


class TestInspectionOverallStatus:
    """Tests for overall status calculation."""

    def test_inspection_overall_status_pass(self, client: TestClient, test_company):
        """All items pass/na results in overall PASS."""
        project_id = _create_project(client)

        response = client.post(
            f"/me/projects/{project_id}/inspections",
            json={
                "inspection_type": "daily_site",
                "inspection_date": "2026-03-31",
                "inspector_name": "Inspector",
                "items": [
                    {
                        "item_id": "item_1",
                        "category": "PPE",
                        "description": "Hard hats",
                        "status": "pass",
                    },
                    {
                        "item_id": "item_2",
                        "category": "PPE",
                        "description": "Safety glasses",
                        "status": "na",
                    },
                    {
                        "item_id": "item_3",
                        "category": "Fall Protection",
                        "description": "Guardrails",
                        "status": "pass",
                    },
                ],
            },
        )
        assert response.status_code == 201
        assert response.json()["overall_status"] == "pass"

    def test_inspection_overall_status_fail(self, client: TestClient, test_company):
        """Any item failing results in overall FAIL."""
        project_id = _create_project(client)

        response = client.post(
            f"/me/projects/{project_id}/inspections",
            json={
                "inspection_type": "daily_site",
                "inspection_date": "2026-03-31",
                "inspector_name": "Inspector",
                "items": [
                    {
                        "item_id": "item_1",
                        "category": "PPE",
                        "description": "Hard hats",
                        "status": "pass",
                    },
                    {
                        "item_id": "item_2",
                        "category": "PPE",
                        "description": "Safety glasses",
                        "status": "fail",
                        "notes": "Worker in zone 3 missing glasses",
                    },
                    {
                        "item_id": "item_3",
                        "category": "Fall Protection",
                        "description": "Guardrails",
                        "status": "pass",
                    },
                ],
            },
        )
        assert response.status_code == 201
        assert response.json()["overall_status"] == "fail"

    def test_inspection_overall_status_partial(self, client: TestClient, test_company):
        """Items with mixed statuses (not all pass/na and no fail) result in PARTIAL."""
        project_id = _create_project(client)

        # Use a status that is neither pass, na, nor fail to trigger PARTIAL
        # In practice "partial" status on an item triggers this
        response = client.post(
            f"/me/projects/{project_id}/inspections",
            json={
                "inspection_type": "daily_site",
                "inspection_date": "2026-03-31",
                "inspector_name": "Inspector",
                "items": [
                    {
                        "item_id": "item_1",
                        "category": "PPE",
                        "description": "Hard hats",
                        "status": "pass",
                    },
                    {
                        "item_id": "item_2",
                        "category": "PPE",
                        "description": "Safety glasses",
                        "status": "partial",
                    },
                ],
            },
        )
        assert response.status_code == 201
        assert response.json()["overall_status"] == "partial"

    def test_inspection_no_items_defaults_to_pass(self, client: TestClient, test_company):
        """Inspection with no items defaults to PASS."""
        project_id = _create_project(client)

        response = client.post(
            f"/me/projects/{project_id}/inspections",
            json={
                "inspection_type": "daily_site",
                "inspection_date": "2026-03-31",
                "inspector_name": "Inspector",
                "items": [],
            },
        )
        assert response.status_code == 201
        assert response.json()["overall_status"] == "pass"


class TestInspectionTemplate:
    """Tests for GET /me/inspection-templates/{inspection_type}."""

    def test_inspection_template_returns_items(self, client: TestClient, test_company):
        """Template endpoint returns checklist items for a valid type."""
        response = client.get("/me/inspection-templates/daily_site")
        assert response.status_code == 200
        items = response.json()
        assert isinstance(items, list)
        assert len(items) > 10  # Daily site has ~21 items

        # Verify item structure
        first = items[0]
        assert "item_id" in first
        assert "category" in first
        assert "description" in first
        assert "status" in first
        assert first["status"] == "pass"

    def test_inspection_template_scaffold(self, client: TestClient, test_company):
        """Scaffold template returns scaffold-specific items."""
        response = client.get("/me/inspection-templates/scaffold")
        assert response.status_code == 200
        items = response.json()
        assert len(items) > 5
        categories = {item["category"] for item in items}
        assert "Foundation" in categories or "Structure" in categories

    def test_inspection_template_invalid_type(self, client: TestClient, test_company):
        """Invalid inspection type returns 422."""
        response = client.get("/me/inspection-templates/not_a_real_type")
        assert response.status_code == 422


class TestUpdateInspection:
    """Tests for PATCH /me/projects/{project_id}/inspections/{inspection_id}."""

    def test_update_inspection(self, client: TestClient, test_company):
        """Update inspection fields returns updated data."""
        project_id = _create_project(client)

        create_resp = client.post(
            f"/me/projects/{project_id}/inspections",
            json={
                "inspection_type": "daily_site",
                "inspection_date": "2026-03-31",
                "inspector_name": "Original Inspector",
                "weather_conditions": "Sunny",
            },
        )
        inspection_id = create_resp.json()["id"]

        response = client.patch(
            f"/me/projects/{project_id}/inspections/{inspection_id}",
            json={
                "inspector_name": "Updated Inspector",
                "weather_conditions": "Rainy",
                "workers_on_site": 15,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["inspector_name"] == "Updated Inspector"
        assert data["weather_conditions"] == "Rainy"
        assert data["workers_on_site"] == 15


class TestDeleteInspection:
    """Tests for DELETE /me/projects/{project_id}/inspections/{inspection_id}."""

    def test_delete_inspection(self, client: TestClient, test_company):
        """Soft-delete an inspection returns 204 and hides it."""
        project_id = _create_project(client)

        create_resp = client.post(
            f"/me/projects/{project_id}/inspections",
            json={
                "inspection_type": "daily_site",
                "inspection_date": "2026-03-31",
                "inspector_name": "Inspector",
            },
        )
        inspection_id = create_resp.json()["id"]

        # Delete
        response = client.delete(
            f"/me/projects/{project_id}/inspections/{inspection_id}"
        )
        assert response.status_code == 204

        # Verify gone from list
        list_resp = client.get(f"/me/projects/{project_id}/inspections")
        assert list_resp.json()["total"] == 0

        # Verify direct get 404s
        get_resp = client.get(
            f"/me/projects/{project_id}/inspections/{inspection_id}"
        )
        assert get_resp.status_code == 404
