"""API contract tests for equipment and fleet management endpoints."""

import pytest
from fastapi.testclient import TestClient


class TestCreateEquipment:
    """Tests for POST /me/equipment."""

    def test_create_equipment(self, client: TestClient, test_company):
        """Create equipment with valid data returns 201."""
        response = client.post(
            "/me/equipment",
            json={
                "name": "CAT 320 Excavator",
                "equipment_type": "excavator",
                "make": "Caterpillar",
                "model": "320",
                "year": 2022,
                "serial_number": "CAT320XYZ123",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "CAT 320 Excavator"
        assert data["equipment_type"] == "excavator"
        assert data["id"].startswith("eqp_")
        assert data["status"] == "active"
        assert data["deleted"] is False


class TestListEquipment:
    """Tests for GET /me/equipment."""

    def test_list_equipment(self, client: TestClient, test_company):
        """List equipment returns created items."""
        client.post(
            "/me/equipment",
            json={"name": "Excavator A", "equipment_type": "excavator"},
        )
        client.post(
            "/me/equipment",
            json={"name": "Forklift B", "equipment_type": "forklift"},
        )

        response = client.get("/me/equipment")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert len(data["equipment"]) == 2


class TestGetEquipment:
    """Tests for GET /me/equipment/{id}."""

    def test_get_equipment(self, client: TestClient, test_company):
        """Get an existing equipment returns 200."""
        create_resp = client.post(
            "/me/equipment",
            json={"name": "Test Crane", "equipment_type": "crane"},
        )
        equip_id = create_resp.json()["id"]

        response = client.get(f"/me/equipment/{equip_id}")
        assert response.status_code == 200
        assert response.json()["name"] == "Test Crane"

    def test_get_equipment_not_found(self, client: TestClient, test_company):
        """Get nonexistent equipment returns 404."""
        response = client.get("/me/equipment/eqp_nonexistent")
        assert response.status_code == 404


class TestEquipmentInspectionLog:
    """Tests for equipment inspection log endpoints."""

    def test_create_and_list_inspection_log(self, client: TestClient, test_company):
        """Create an inspection log and verify it appears in the list."""
        create_resp = client.post(
            "/me/equipment",
            json={"name": "Forklift #3", "equipment_type": "forklift"},
        )
        equip_id = create_resp.json()["id"]

        log_resp = client.post(
            f"/me/equipment/{equip_id}/inspections",
            json={
                "inspection_date": "2026-03-31",
                "inspector_name": "Bob Safety",
                "inspection_type": "pre_shift",
                "items": [
                    {"item": "Tires", "status": "pass", "notes": ""},
                    {"item": "Forks", "status": "pass", "notes": ""},
                ],
                "overall_status": "pass",
            },
        )
        assert log_resp.status_code == 201
        log = log_resp.json()
        assert log["id"].startswith("eqlog_")
        assert log["equipment_id"] == equip_id
        assert log["overall_status"] == "pass"

        list_resp = client.get(f"/me/equipment/{equip_id}/inspections")
        assert list_resp.status_code == 200
        assert list_resp.json()["total"] == 1


class TestEquipmentInspectionTemplate:
    """Tests for GET /me/equipment/{id}/inspection-template."""

    def test_get_crane_template(self, client: TestClient, test_company):
        """Get inspection template for a crane returns checklist items."""
        create_resp = client.post(
            "/me/equipment",
            json={"name": "Liebherr LTM 1300", "equipment_type": "crane"},
        )
        equip_id = create_resp.json()["id"]

        response = client.get(f"/me/equipment/{equip_id}/inspection-template")
        assert response.status_code == 200
        data = response.json()
        assert data["equipment_type"] == "crane"
        assert len(data["template"]) == 12
        items = [t["item"] for t in data["template"]]
        assert "Boom condition" in items
        assert "Fire extinguisher present and charged" in items


class TestEquipmentSummary:
    """Tests for GET /me/equipment/summary."""

    def test_equipment_summary(self, client: TestClient, test_company):
        """Equipment summary returns correct counts."""
        client.post(
            "/me/equipment",
            json={"name": "Crane 1", "equipment_type": "crane"},
        )
        client.post(
            "/me/equipment",
            json={"name": "Crane 2", "equipment_type": "crane"},
        )
        client.post(
            "/me/equipment",
            json={"name": "Truck 1", "equipment_type": "vehicle"},
        )

        response = client.get("/me/equipment/summary")
        assert response.status_code == 200
        data = response.json()
        assert data["total_equipment"] == 3
        assert data["by_type"]["crane"] == 2
        assert data["by_type"]["vehicle"] == 1
        assert data["by_status"]["active"] == 3
