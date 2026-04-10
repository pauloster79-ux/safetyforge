"""API contract tests for OSHA 300 Log endpoints."""

from datetime import date

import pytest
from fastapi.testclient import TestClient


def _make_entry_payload(**overrides) -> dict:
    """Build a valid OSHA log entry payload with optional overrides.

    Args:
        **overrides: Fields to override in the default payload.

    Returns:
        A dict suitable for POST /me/osha-log/entries.
    """
    payload = {
        "employee_name": "Carlos Martinez",
        "job_title": "Carpenter",
        "date_of_injury": "2026-03-15",
        "where_event_occurred": "Loading dock, Building A",
        "description": "Worker slipped on wet surface and sprained ankle",
        "classification": "days_away_from_work",
        "injury_type": "injury",
        "days_away_from_work": 5,
        "days_of_restricted_work": 0,
        "died": False,
        "privacy_case": False,
    }
    payload.update(overrides)
    return payload


class TestCreateEntry:
    """Tests for POST /me/osha-log/entries."""

    def test_create_entry(self, client: TestClient, test_company):
        """Create an OSHA log entry with valid data returns 201."""
        response = client.post("/api/v1/me/osha-log/entries", json=_make_entry_payload())
        assert response.status_code == 201
        data = response.json()
        assert data["employee_name"] == "Carlos Martinez"
        assert data["job_title"] == "Carpenter"
        assert data["date_of_injury"] == "2026-03-15"
        assert data["where_event_occurred"] == "Loading dock, Building A"
        assert data["classification"] == "days_away_from_work"
        assert data["injury_type"] == "injury"
        assert data["days_away_from_work"] == 5
        assert data["days_of_restricted_work"] == 0
        assert data["died"] is False
        assert data["privacy_case"] is False
        assert data["id"].startswith("osha_")
        assert data["company_id"] == test_company["id"]
        assert data["year"] == 2026
        assert data["case_number"] == 1

    def test_create_entry_auto_case_number(self, client: TestClient, test_company):
        """Sequential entries in the same year get incrementing case numbers."""
        r1 = client.post("/api/v1/me/osha-log/entries", json=_make_entry_payload())
        assert r1.status_code == 201
        assert r1.json()["case_number"] == 1

        r2 = client.post(
            "/api/v1/me/osha-log/entries",
            json=_make_entry_payload(
                employee_name="John Doe",
                description="Worker cut hand on sheet metal while framing",
            ),
        )
        assert r2.status_code == 201
        assert r2.json()["case_number"] == 2

        r3 = client.post(
            "/api/v1/me/osha-log/entries",
            json=_make_entry_payload(
                employee_name="Jane Smith",
                description="Worker experienced hearing loss from jackhammer operation",
                date_of_injury="2025-06-01",
                injury_type="hearing_loss",
                classification="other_recordable",
            ),
        )
        assert r3.status_code == 201
        # Different year, so case_number resets
        assert r3.json()["case_number"] == 1
        assert r3.json()["year"] == 2025


class TestListEntries:
    """Tests for GET /me/osha-log/entries."""

    def test_list_entries_by_year(self, client: TestClient, test_company):
        """List entries filtered by year returns only matching entries."""
        # Create entries in different years
        client.post("/api/v1/me/osha-log/entries", json=_make_entry_payload())
        client.post(
            "/api/v1/me/osha-log/entries",
            json=_make_entry_payload(
                employee_name="John Doe",
                description="Worker fell from scaffold and broke arm",
                date_of_injury="2025-07-20",
                classification="days_away_from_work",
            ),
        )

        # Filter by 2026
        response = client.get("/api/v1/me/osha-log/entries?year=2026")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["entries"][0]["year"] == 2026

        # Filter by 2025
        response = client.get("/api/v1/me/osha-log/entries?year=2025")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["entries"][0]["year"] == 2025

        # No filter returns all
        response = client.get("/api/v1/me/osha-log/entries")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2


class TestGetEntry:
    """Tests for GET /me/osha-log/entries/{id}."""

    def test_get_entry(self, client: TestClient, test_company):
        """Get a specific entry by ID returns full details."""
        create_response = client.post(
            "/api/v1/me/osha-log/entries", json=_make_entry_payload()
        )
        entry_id = create_response.json()["id"]

        response = client.get(f"/api/v1/me/osha-log/entries/{entry_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == entry_id
        assert data["employee_name"] == "Carlos Martinez"

    def test_get_entry_not_found(self, client: TestClient, test_company):
        """Get a nonexistent entry returns 404."""
        response = client.get("/api/v1/me/osha-log/entries/osha_nonexistent")
        assert response.status_code == 404


class TestUpdateEntry:
    """Tests for PATCH /me/osha-log/entries/{id}."""

    def test_update_entry(self, client: TestClient, test_company):
        """Update entry fields returns updated data."""
        create_response = client.post(
            "/api/v1/me/osha-log/entries", json=_make_entry_payload()
        )
        entry_id = create_response.json()["id"]

        response = client.patch(
            f"/api/v1/me/osha-log/entries/{entry_id}",
            json={
                "days_away_from_work": 10,
                "description": "Updated: Worker slipped on wet surface, more severe than initially thought",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["days_away_from_work"] == 10
        assert "more severe" in data["description"]
        # Unchanged fields preserved
        assert data["employee_name"] == "Carlos Martinez"

    def test_update_entry_not_found(self, client: TestClient, test_company):
        """Update a nonexistent entry returns 404."""
        response = client.patch(
            "/api/v1/me/osha-log/entries/osha_nonexistent",
            json={"days_away_from_work": 10},
        )
        assert response.status_code == 404


class TestDeleteEntry:
    """Tests for DELETE /me/osha-log/entries/{id}."""

    def test_delete_entry(self, client: TestClient, test_company):
        """Delete an entry returns 204 and entry is gone."""
        create_response = client.post(
            "/api/v1/me/osha-log/entries", json=_make_entry_payload()
        )
        entry_id = create_response.json()["id"]

        response = client.delete(f"/api/v1/me/osha-log/entries/{entry_id}")
        assert response.status_code == 204

        # Verify it's gone
        get_response = client.get(f"/api/v1/me/osha-log/entries/{entry_id}")
        assert get_response.status_code == 404

    def test_delete_entry_not_found(self, client: TestClient, test_company):
        """Delete a nonexistent entry returns 404."""
        response = client.delete("/api/v1/me/osha-log/entries/osha_nonexistent")
        assert response.status_code == 404


class TestOsha300aSummary:
    """Tests for GET /me/osha-log/summary."""

    def _create_test_entries(self, client: TestClient):
        """Create a set of test entries for summary calculation.

        Args:
            client: The test client.
        """
        # Entry 1: Days away (injury)
        client.post(
            "/api/v1/me/osha-log/entries",
            json=_make_entry_payload(
                employee_name="Worker One",
                days_away_from_work=5,
                days_of_restricted_work=0,
                classification="days_away_from_work",
                injury_type="injury",
            ),
        )
        # Entry 2: Restricted (skin disorder)
        client.post(
            "/api/v1/me/osha-log/entries",
            json=_make_entry_payload(
                employee_name="Worker Two",
                days_away_from_work=0,
                days_of_restricted_work=10,
                classification="job_transfer_or_restriction",
                injury_type="skin_disorder",
                description="Chemical burn on forearm from concrete exposure",
            ),
        )
        # Entry 3: Other recordable (respiratory)
        client.post(
            "/api/v1/me/osha-log/entries",
            json=_make_entry_payload(
                employee_name="Worker Three",
                days_away_from_work=0,
                days_of_restricted_work=0,
                classification="other_recordable",
                injury_type="respiratory",
                description="Silica dust exposure resulting in medical treatment",
            ),
        )
        # Entry 4: Death (injury)
        client.post(
            "/api/v1/me/osha-log/entries",
            json=_make_entry_payload(
                employee_name="Worker Four",
                days_away_from_work=0,
                days_of_restricted_work=0,
                classification="death",
                injury_type="injury",
                died=True,
                description="Fatal fall from elevated platform at construction site",
            ),
        )

    def test_300a_summary_calculation(self, client: TestClient, test_company):
        """Summary correctly aggregates entry counts and types."""
        self._create_test_entries(client)

        response = client.get("/api/v1/me/osha-log/summary?year=2026")
        assert response.status_code == 200
        data = response.json()

        assert data["year"] == 2026
        assert data["total_deaths"] == 1
        assert data["total_days_away"] == 1
        assert data["total_restricted"] == 1
        assert data["total_other_recordable"] == 1
        assert data["total_days_away_count"] == 5
        assert data["total_restricted_days_count"] == 10
        assert data["total_injuries"] == 2  # Worker One + Worker Four
        assert data["total_skin_disorders"] == 1
        assert data["total_respiratory"] == 1
        assert data["total_poisonings"] == 0
        assert data["total_hearing_loss"] == 0
        assert data["total_other_illnesses"] == 0

    def test_trir_calculation(self, client: TestClient, test_company):
        """TRIR is calculated correctly when hours are provided via certify."""
        self._create_test_entries(client)

        # Certify with hours data: 4 recordable cases, 400,000 hours
        # TRIR = (4 * 200,000) / 400,000 = 2.0
        client.post(
            "/api/v1/me/osha-log/summary/certify?year=2026",
            json={
                "certified_by": "Safety Director",
                "annual_average_employees": 50,
                "total_hours_worked": 400000,
            },
        )

        response = client.get("/api/v1/me/osha-log/summary?year=2026")
        assert response.status_code == 200
        data = response.json()
        assert data["trir"] == 2.0

    def test_dart_calculation(self, client: TestClient, test_company):
        """DART is calculated correctly when hours are provided via certify."""
        self._create_test_entries(client)

        # DART cases: days_away (1) + restricted (1) = 2
        # DART = (2 * 200,000) / 400,000 = 1.0
        client.post(
            "/api/v1/me/osha-log/summary/certify?year=2026",
            json={
                "certified_by": "Safety Director",
                "annual_average_employees": 50,
                "total_hours_worked": 400000,
            },
        )

        response = client.get("/api/v1/me/osha-log/summary?year=2026")
        assert response.status_code == 200
        data = response.json()
        assert data["dart"] == 1.0

    def test_summary_empty_year(self, client: TestClient, test_company):
        """Summary for a year with no entries returns zero counts."""
        response = client.get("/api/v1/me/osha-log/summary?year=2020")
        assert response.status_code == 200
        data = response.json()
        assert data["year"] == 2020
        assert data["total_deaths"] == 0
        assert data["total_days_away"] == 0
        assert data["trir"] == 0.0
        assert data["dart"] == 0.0


class TestCertifySummary:
    """Tests for POST /me/osha-log/summary/certify."""

    def test_certify_summary(self, client: TestClient, test_company):
        """Certify summary stores certification data and recalculates rates."""
        # Create one entry first
        client.post("/api/v1/me/osha-log/entries", json=_make_entry_payload())

        response = client.post(
            "/api/v1/me/osha-log/summary/certify?year=2026",
            json={
                "certified_by": "John Smith, Safety Manager",
                "annual_average_employees": 25,
                "total_hours_worked": 50000,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["certified_by"] == "John Smith, Safety Manager"
        assert data["certified_date"] is not None
        assert data["posted"] is True
        assert data["annual_average_employees"] == 25
        assert data["total_hours_worked"] == 50000
        # TRIR = (1 * 200,000) / 50,000 = 4.0
        assert data["trir"] == 4.0


class TestListYears:
    """Tests for GET /me/osha-log/years."""

    def test_list_years(self, client: TestClient, test_company):
        """List years returns all years with entries, sorted descending."""
        client.post("/api/v1/me/osha-log/entries", json=_make_entry_payload())
        client.post(
            "/api/v1/me/osha-log/entries",
            json=_make_entry_payload(
                employee_name="Old Entry",
                date_of_injury="2024-01-10",
                description="Worker strained back while lifting heavy materials",
            ),
        )
        client.post(
            "/api/v1/me/osha-log/entries",
            json=_make_entry_payload(
                employee_name="Another Entry",
                date_of_injury="2025-06-15",
                description="Worker sustained electrical shock from exposed wiring",
            ),
        )

        response = client.get("/api/v1/me/osha-log/years")
        assert response.status_code == 200
        data = response.json()
        assert data["years"] == [2026, 2025, 2024]

    def test_list_years_empty(self, client: TestClient, test_company):
        """List years with no entries returns empty list."""
        response = client.get("/api/v1/me/osha-log/years")
        assert response.status_code == 200
        data = response.json()
        assert data["years"] == []
