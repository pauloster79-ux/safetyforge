"""Incident log CRUD service with annual summary calculation against Neo4j.

Previously named OshaLogService; the underlying graph node is now
IncidentLogEntry (formerly OshaLogEntry) and the relationship from Company
is HAS_INCIDENT_LOG (formerly HAS_OSHA_ENTRY).

Supports jurisdiction-aware incident rate calculations:
  - US OSHA:  TRIR = (cases * 200,000) / hours
  - UK HSE:   AFR  = (cases * 100,000) / hours
  - AU:       LTIFR = (cases * 1,000,000) / hours

The underlying data model remains the OSHA 300 Log format for backward
compatibility, but the incident rate multiplier is sourced from the
company's jurisdiction context when available.
"""

from datetime import date, datetime, timezone
from typing import Any

from app.exceptions import CompanyNotFoundError, OshaLogEntryNotFoundError
from app.models.actor import Actor
from app.models.osha_log import (
    CaseClassification,
    InjuryType,
    Osha300Summary,
    OshaLogEntry,
    OshaLogEntryCreate,
    OshaLogEntryUpdate,
)
from app.services.base_service import BaseService

# Default to US OSHA multiplier for backward compatibility
_DEFAULT_INCIDENT_RATE_MULTIPLIER = 200_000


class OshaLogService(BaseService):
    """Manages incident log entries and summaries in Neo4j.

    Graph model:
        (Company)-[:HAS_INCIDENT_LOG]->(IncidentLogEntry)
        (Company)-[:HAS_OSHA_SUMMARY]->(OshaSummary)

    Node label IncidentLogEntry was previously OshaLogEntry.
    Relationship HAS_INCIDENT_LOG was previously HAS_OSHA_ENTRY.
    ID prefix is now 'ile_' (was 'osha_').

    Supports jurisdiction-aware incident rate calculations via the
    incident_rate_multiplier parameter. Defaults to US OSHA (200,000).

    Args:
        driver: Neo4j driver instance.
        incident_rate_multiplier: The multiplier for rate calculations.
            US=200,000, UK=100,000, AU=1,000,000.
    """

    def __init__(
        self,
        driver: Any,
        incident_rate_multiplier: int = _DEFAULT_INCIDENT_RATE_MULTIPLIER,
    ) -> None:
        super().__init__(driver)
        self._incident_rate_multiplier = incident_rate_multiplier

    def _verify_company_exists(self, company_id: str) -> None:
        """Verify that the parent company exists.

        Args:
            company_id: The company ID to check.

        Raises:
            CompanyNotFoundError: If the company does not exist.
        """
        result = self._read_tx_single(
            "MATCH (c:Company {id: $id}) RETURN c.id AS id",
            {"id": company_id},
        )
        if result is None:
            raise CompanyNotFoundError(company_id)

    def _get_next_case_number(self, company_id: str, year: int) -> int:
        """Get the next sequential case number for the given year.

        Args:
            company_id: The owning company ID.
            year: The calendar year.

        Returns:
            The next case number (1-based).
        """
        result = self._read_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:HAS_INCIDENT_LOG]->(e:IncidentLogEntry)
            WHERE e.year = $year
            RETURN max(e.case_number) AS max_case
            """,
            {"company_id": company_id, "year": year},
        )
        if result is None or result["max_case"] is None:
            return 1
        return result["max_case"] + 1

    def create_entry(
        self, company_id: str, data: OshaLogEntryCreate, user_id: str
    ) -> OshaLogEntry:
        """Create a new incident log entry.

        Auto-assigns the next sequential case number for the injury year.
        Uses the IncidentLogEntry node label and HAS_INCIDENT_LOG relationship.
        ID prefix is 'ile_'.

        Args:
            company_id: The owning company ID.
            data: Validated entry creation data.
            user_id: Firebase UID of the creating user.

        Returns:
            The created OshaLogEntry (IncidentLogEntry) with all fields populated.

        Raises:
            CompanyNotFoundError: If the company does not exist.
        """
        self._verify_company_exists(company_id)

        actor = Actor.human(user_id)
        entry_id = self._generate_id("ile")
        year = data.date_of_injury.year
        case_number = self._get_next_case_number(company_id, year)

        props: dict[str, Any] = {
            "id": entry_id,
            "case_number": case_number,
            "employee_name": data.employee_name,
            "job_title": data.job_title,
            "date_of_injury": data.date_of_injury.isoformat(),
            "where_event_occurred": data.where_event_occurred,
            "description": data.description,
            "classification": data.classification.value,
            "injury_type": data.injury_type.value,
            "days_away_from_work": data.days_away_from_work,
            "days_of_restricted_work": data.days_of_restricted_work,
            "died": data.died,
            "privacy_case": data.privacy_case,
            "year": year,
            **self._provenance_create(actor),
        }

        result = self._write_tx_single(
            """
            MATCH (c:Company {id: $company_id})
            CREATE (e:IncidentLogEntry $props)
            CREATE (c)-[:HAS_INCIDENT_LOG]->(e)
            RETURN e {.*, company_id: c.id} AS entry
            """,
            {"company_id": company_id, "props": props},
        )
        if result is None:
            raise CompanyNotFoundError(company_id)
        self._emit_audit(
            event_type="entity.created",
            entity_id=entry_id,
            entity_type="IncidentLogEntry",
            company_id=company_id,
            actor=actor,
            summary=f"Created incident log entry for {data.employee_name}",
        )
        return OshaLogEntry(**result["entry"])

    def get_entry(self, company_id: str, entry_id: str) -> OshaLogEntry:
        """Fetch a single incident log entry.

        Args:
            company_id: The owning company ID.
            entry_id: The entry ID to fetch.

        Returns:
            The OshaLogEntry model.

        Raises:
            OshaLogEntryNotFoundError: If the entry does not exist.
        """
        result = self._read_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:HAS_INCIDENT_LOG]->(e:IncidentLogEntry {id: $entry_id})
            RETURN e {.*, company_id: c.id} AS entry
            """,
            {"company_id": company_id, "entry_id": entry_id},
        )
        if result is None:
            raise OshaLogEntryNotFoundError(entry_id)
        return OshaLogEntry(**result["entry"])

    def list_entries(
        self,
        company_id: str,
        year: int | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> dict:
        """List incident log entries for a company with optional year filter.

        Args:
            company_id: The owning company ID.
            year: Optional calendar year filter.
            limit: Maximum number of entries to return.
            offset: Number of entries to skip.

        Returns:
            A dict with 'entries' list and 'total' count.
        """
        where_clauses: list[str] = []
        params: dict[str, Any] = {
            "company_id": company_id,
            "limit": limit,
            "offset": offset,
        }

        if year is not None:
            where_clauses.append("e.year = $year")
            params["year"] = year

        where_str = " AND ".join(where_clauses)
        where_clause = f"WHERE {where_str}" if where_str else ""

        count_result = self._read_tx_single(
            f"""
            MATCH (c:Company {{id: $company_id}})-[:HAS_INCIDENT_LOG]->(e:IncidentLogEntry)
            {where_clause}
            RETURN count(e) AS total
            """,
            params,
        )
        total = count_result["total"] if count_result else 0

        results = self._read_tx(
            f"""
            MATCH (c:Company {{id: $company_id}})-[:HAS_INCIDENT_LOG]->(e:IncidentLogEntry)
            {where_clause}
            RETURN e {{.*, company_id: c.id}} AS entry
            ORDER BY e.year ASC, e.case_number ASC
            SKIP $offset LIMIT $limit
            """,
            params,
        )

        entries = [OshaLogEntry(**r["entry"]) for r in results]
        return {"entries": entries, "total": total}

    def update_entry(
        self,
        company_id: str,
        entry_id: str,
        data: OshaLogEntryUpdate,
        user_id: str,
    ) -> OshaLogEntry:
        """Update an existing incident log entry.

        Args:
            company_id: The owning company ID.
            entry_id: The entry ID to update.
            data: Fields to update (only non-None fields are applied).
            user_id: Firebase UID of the updating user.

        Returns:
            The updated OshaLogEntry model.

        Raises:
            OshaLogEntryNotFoundError: If the entry does not exist.
        """
        update_data: dict[str, Any] = {}
        for field_name, value in data.model_dump(exclude_none=True).items():
            if field_name == "date_of_injury" and value is not None:
                update_data[field_name] = (
                    value.isoformat() if hasattr(value, "isoformat") else value
                )
                if hasattr(value, "year"):
                    update_data["year"] = value.year
            elif hasattr(value, "value"):
                update_data[field_name] = value.value
            else:
                update_data[field_name] = value

        if not update_data:
            return self.get_entry(company_id, entry_id)

        actor = Actor.human(user_id)
        update_data.update(self._provenance_update(actor))

        result = self._write_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:HAS_INCIDENT_LOG]->(e:IncidentLogEntry {id: $entry_id})
            SET e += $props
            RETURN e {.*, company_id: c.id} AS entry
            """,
            {"company_id": company_id, "entry_id": entry_id, "props": update_data},
        )
        if result is None:
            raise OshaLogEntryNotFoundError(entry_id)
        self._emit_audit(
            event_type="entity.updated",
            entity_id=entry_id,
            entity_type="IncidentLogEntry",
            company_id=company_id,
            actor=actor,
            summary=f"Updated incident log entry {entry_id}",
        )
        return OshaLogEntry(**result["entry"])

    def delete_entry(self, company_id: str, entry_id: str) -> None:
        """Permanently delete an incident log entry.

        Args:
            company_id: The owning company ID.
            entry_id: The entry ID to delete.

        Raises:
            OshaLogEntryNotFoundError: If the entry does not exist.
        """
        result = self._write_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:HAS_INCIDENT_LOG]->(e:IncidentLogEntry {id: $entry_id})
            WITH e, e.id AS eid
            DETACH DELETE e
            RETURN eid AS id
            """,
            {"company_id": company_id, "entry_id": entry_id},
        )
        if result is None:
            raise OshaLogEntryNotFoundError(entry_id)

    def get_300a_summary(self, company_id: str, year: int) -> Osha300Summary:
        """Calculate the OSHA 300A Annual Summary from incident log entries.

        Aggregates all IncidentLogEntry nodes for the given year and computes
        totals, injury type counts, and incidence rates (TRIR, DART).

        Args:
            company_id: The owning company ID.
            year: The calendar year to summarize.

        Returns:
            The computed Osha300Summary.
        """
        # Get company info
        company_result = self._read_tx_single(
            "MATCH (c:Company {id: $id}) RETURN c.name AS name, c.address AS address",
            {"id": company_id},
        )
        company_name = company_result["name"] if company_result else ""
        company_address = company_result["address"] if company_result else ""

        # Aggregate entries for the year
        agg_result = self._read_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:HAS_INCIDENT_LOG]->(e:IncidentLogEntry)
            WHERE e.year = $year
            RETURN
                count(e) AS total_entries,
                sum(CASE WHEN e.classification = 'death' THEN 1 ELSE 0 END) AS total_deaths,
                sum(CASE WHEN e.classification = 'days_away_from_work' THEN 1 ELSE 0 END) AS total_days_away,
                sum(CASE WHEN e.classification = 'job_transfer_or_restriction' THEN 1 ELSE 0 END) AS total_restricted,
                sum(CASE WHEN e.classification = 'other_recordable' THEN 1 ELSE 0 END) AS total_other_recordable,
                sum(e.days_away_from_work) AS total_days_away_count,
                sum(e.days_of_restricted_work) AS total_restricted_days_count,
                sum(CASE WHEN e.injury_type = 'injury' THEN 1 ELSE 0 END) AS total_injuries,
                sum(CASE WHEN e.injury_type = 'skin_disorder' THEN 1 ELSE 0 END) AS total_skin_disorders,
                sum(CASE WHEN e.injury_type = 'respiratory' THEN 1 ELSE 0 END) AS total_respiratory,
                sum(CASE WHEN e.injury_type = 'poisoning' THEN 1 ELSE 0 END) AS total_poisonings,
                sum(CASE WHEN e.injury_type = 'hearing_loss' THEN 1 ELSE 0 END) AS total_hearing_loss,
                sum(CASE WHEN e.injury_type = 'other_illness' THEN 1 ELSE 0 END) AS total_other_illnesses
            """,
            {"company_id": company_id, "year": year},
        )

        if agg_result is None or agg_result["total_entries"] == 0:
            agg = {
                "total_deaths": 0, "total_days_away": 0, "total_restricted": 0,
                "total_other_recordable": 0, "total_days_away_count": 0,
                "total_restricted_days_count": 0, "total_injuries": 0,
                "total_skin_disorders": 0, "total_respiratory": 0,
                "total_poisonings": 0, "total_hearing_loss": 0,
                "total_other_illnesses": 0,
            }
        else:
            agg = agg_result

        # Get stored summary data (certification, hours)
        summary_result = self._read_tx_single(
            """
            MATCH (c:Company {id: $company_id})-[:HAS_OSHA_SUMMARY]->(s:OshaSummary {year: $year})
            RETURN s {.*} AS summary
            """,
            {"company_id": company_id, "year": year},
        )
        summary_data = summary_result["summary"] if summary_result else {}

        annual_average_employees = summary_data.get("annual_average_employees", 0)
        total_hours_worked = summary_data.get("total_hours_worked", 0)
        certified_by = summary_data.get("certified_by", "")
        certified_date_raw = summary_data.get("certified_date")
        certified_date = None
        if certified_date_raw:
            if isinstance(certified_date_raw, str):
                certified_date = date.fromisoformat(certified_date_raw)
            elif isinstance(certified_date_raw, date):
                certified_date = certified_date_raw
        posted = summary_data.get("posted", False)

        # Calculate incidence rates
        total_deaths = agg["total_deaths"] or 0
        total_days_away = agg["total_days_away"] or 0
        total_restricted = agg["total_restricted"] or 0
        total_other_recordable = agg["total_other_recordable"] or 0

        total_recordable = (
            total_deaths + total_days_away + total_restricted + total_other_recordable
        )
        multiplier = self._incident_rate_multiplier
        trir = 0.0
        dart = 0.0
        if total_hours_worked > 0:
            trir = (total_recordable * multiplier) / total_hours_worked
            dart_cases = total_days_away + total_restricted
            dart = (dart_cases * multiplier) / total_hours_worked

        return Osha300Summary(
            year=year,
            company_name=company_name or "",
            establishment_name=company_name or "",
            establishment_address=company_address or "",
            annual_average_employees=annual_average_employees,
            total_hours_worked=total_hours_worked,
            total_deaths=total_deaths,
            total_days_away=total_days_away,
            total_restricted=total_restricted,
            total_other_recordable=total_other_recordable,
            total_days_away_count=agg["total_days_away_count"] or 0,
            total_restricted_days_count=agg["total_restricted_days_count"] or 0,
            total_injuries=agg["total_injuries"] or 0,
            total_skin_disorders=agg["total_skin_disorders"] or 0,
            total_respiratory=agg["total_respiratory"] or 0,
            total_poisonings=agg["total_poisonings"] or 0,
            total_hearing_loss=agg["total_hearing_loss"] or 0,
            total_other_illnesses=agg["total_other_illnesses"] or 0,
            trir=round(trir, 2),
            dart=round(dart, 2),
            certified_by=certified_by,
            certified_date=certified_date,
            posted=posted,
        )

    def certify_summary(
        self,
        company_id: str,
        year: int,
        certified_by: str,
        annual_average_employees: int = 0,
        total_hours_worked: int = 0,
    ) -> Osha300Summary:
        """Certify the OSHA 300A summary for a given year.

        Stores certification data and employee/hours info, then returns
        the recalculated summary.

        Args:
            company_id: The owning company ID.
            year: The calendar year to certify.
            certified_by: Name of the certifying official.
            annual_average_employees: Annual average employee count.
            total_hours_worked: Total hours worked during the year.

        Returns:
            The certified Osha300Summary with updated rates.
        """
        today = date.today()
        self._write_tx(
            """
            MATCH (c:Company {id: $company_id})
            MERGE (c)-[:HAS_OSHA_SUMMARY]->(s:OshaSummary {year: $year})
            SET s.certified_by = $certified_by,
                s.certified_date = $certified_date,
                s.annual_average_employees = $employees,
                s.total_hours_worked = $hours,
                s.posted = true,
                s.year = $year
            """,
            {
                "company_id": company_id,
                "year": year,
                "certified_by": certified_by,
                "certified_date": today.isoformat(),
                "employees": annual_average_employees,
                "hours": total_hours_worked,
            },
        )

        return self.get_300a_summary(company_id, year)

    def get_years_with_entries(self, company_id: str) -> list[int]:
        """Return a sorted list of years that have incident log entries.

        Args:
            company_id: The owning company ID.

        Returns:
            A sorted list of unique years (descending).
        """
        results = self._read_tx(
            """
            MATCH (c:Company {id: $company_id})-[:HAS_INCIDENT_LOG]->(e:IncidentLogEntry)
            RETURN DISTINCT e.year AS year
            ORDER BY year DESC
            """,
            {"company_id": company_id},
        )
        return [r["year"] for r in results]
