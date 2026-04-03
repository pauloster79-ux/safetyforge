"""Incident record CRUD service with annual summary calculation against Firestore.

Supports jurisdiction-aware incident rate calculations:
  - US OSHA:  TRIR = (cases * 200,000) / hours
  - UK HSE:   AFR  = (cases * 100,000) / hours
  - AU:       LTIFR = (cases * 1,000,000) / hours

The underlying data model remains the OSHA 300 Log format for backward
compatibility, but the incident rate multiplier is sourced from the
company's jurisdiction context when available.
"""

import secrets
from datetime import date, datetime, timezone
from typing import Any

from google.cloud import firestore

from app.exceptions import CompanyNotFoundError, OshaLogEntryNotFoundError
from app.models.osha_log import (
    CaseClassification,
    InjuryType,
    Osha300Summary,
    OshaLogEntry,
    OshaLogEntryCreate,
    OshaLogEntryUpdate,
)

# Default to US OSHA multiplier for backward compatibility
_DEFAULT_INCIDENT_RATE_MULTIPLIER = 200_000


class OshaLogService:
    """Manages incident record entries and summaries in Firestore.

    Supports jurisdiction-aware incident rate calculations via the
    incident_rate_multiplier parameter. Defaults to US OSHA (200,000).

    Args:
        db: Firestore client instance.
        incident_rate_multiplier: The multiplier for rate calculations.
            US=200,000, UK=100,000, AU=1,000,000.
    """

    def __init__(
        self,
        db: firestore.Client,
        incident_rate_multiplier: int = _DEFAULT_INCIDENT_RATE_MULTIPLIER,
    ) -> None:
        self.db = db
        self._incident_rate_multiplier = incident_rate_multiplier

    def _company_ref(self, company_id: str) -> firestore.DocumentReference:
        """Return a reference to the company document.

        Args:
            company_id: The parent company ID.

        Returns:
            Firestore document reference.
        """
        return self.db.collection("companies").document(company_id)

    def _collection(self, company_id: str) -> firestore.CollectionReference:
        """Return the osha_log_entries subcollection for a company.

        Args:
            company_id: The parent company ID.

        Returns:
            Firestore collection reference.
        """
        return self._company_ref(company_id).collection("osha_log_entries")

    def _generate_id(self) -> str:
        """Generate a unique OSHA log entry ID.

        Returns:
            A prefixed hex ID string.
        """
        return f"osha_{secrets.token_hex(8)}"

    def _verify_company_exists(self, company_id: str) -> None:
        """Verify that the parent company exists.

        Args:
            company_id: The company ID to check.

        Raises:
            CompanyNotFoundError: If the company does not exist.
        """
        if not self._company_ref(company_id).get().exists:
            raise CompanyNotFoundError(company_id)

    def _get_next_case_number(self, company_id: str, year: int) -> int:
        """Get the next sequential case number for the given year.

        Args:
            company_id: The owning company ID.
            year: The calendar year.

        Returns:
            The next case number (1-based).
        """
        query = self._collection(company_id).where("year", "==", year)
        docs = list(query.stream())
        if not docs:
            return 1
        max_case = 0
        for doc in docs:
            data = doc.to_dict()
            case_num = data.get("case_number", 0)
            if case_num > max_case:
                max_case = case_num
        return max_case + 1

    def create_entry(
        self, company_id: str, data: OshaLogEntryCreate, user_id: str
    ) -> OshaLogEntry:
        """Create a new OSHA 300 Log entry.

        Auto-assigns the next sequential case number for the injury year.

        Args:
            company_id: The owning company ID.
            data: Validated entry creation data.
            user_id: Firebase UID of the creating user.

        Returns:
            The created OshaLogEntry with all fields populated.

        Raises:
            CompanyNotFoundError: If the company does not exist.
        """
        self._verify_company_exists(company_id)

        now = datetime.now(timezone.utc)
        entry_id = self._generate_id()
        year = data.date_of_injury.year
        case_number = self._get_next_case_number(company_id, year)

        entry_dict: dict[str, Any] = {
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
            "company_id": company_id,
            "created_at": now,
            "created_by": user_id,
            "updated_at": now,
            "updated_by": user_id,
        }

        self._collection(company_id).document(entry_id).set(entry_dict)
        return OshaLogEntry(**entry_dict)

    def get_entry(self, company_id: str, entry_id: str) -> OshaLogEntry:
        """Fetch a single OSHA log entry.

        Args:
            company_id: The owning company ID.
            entry_id: The entry ID to fetch.

        Returns:
            The OshaLogEntry model.

        Raises:
            OshaLogEntryNotFoundError: If the entry does not exist.
        """
        doc = self._collection(company_id).document(entry_id).get()
        if not doc.exists:
            raise OshaLogEntryNotFoundError(entry_id)
        return OshaLogEntry(**doc.to_dict())

    def list_entries(
        self,
        company_id: str,
        year: int | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> dict:
        """List OSHA log entries for a company with optional year filter.

        Args:
            company_id: The owning company ID.
            year: Optional calendar year filter.
            limit: Maximum number of entries to return.
            offset: Number of entries to skip.

        Returns:
            A dict with 'entries' list and 'total' count.
        """
        base_query: firestore.Query = self._collection(company_id)

        if year is not None:
            base_query = base_query.where("year", "==", year)

        all_docs = []
        for doc in base_query.stream():
            all_docs.append(doc.to_dict())

        total = len(all_docs)

        # Sort by case_number ascending within each year
        all_docs.sort(key=lambda d: (d.get("year", 0), d.get("case_number", 0)))
        paginated = all_docs[offset : offset + limit]

        entries = [OshaLogEntry(**d) for d in paginated]
        return {"entries": entries, "total": total}

    def update_entry(
        self,
        company_id: str,
        entry_id: str,
        data: OshaLogEntryUpdate,
        user_id: str,
    ) -> OshaLogEntry:
        """Update an existing OSHA log entry.

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
        doc_ref = self._collection(company_id).document(entry_id)
        doc = doc_ref.get()

        if not doc.exists:
            raise OshaLogEntryNotFoundError(entry_id)

        update_data: dict[str, Any] = {}
        for field_name, value in data.model_dump(exclude_none=True).items():
            if field_name == "date_of_injury" and value is not None:
                update_data[field_name] = (
                    value.isoformat() if hasattr(value, "isoformat") else value
                )
                # Update the year field if date changes
                if hasattr(value, "year"):
                    update_data["year"] = value.year
            elif hasattr(value, "value"):
                # Enum values
                update_data[field_name] = value.value
            else:
                update_data[field_name] = value

        if not update_data:
            return OshaLogEntry(**doc.to_dict())

        update_data["updated_at"] = datetime.now(timezone.utc)
        update_data["updated_by"] = user_id

        doc_ref.update(update_data)

        updated_doc = doc_ref.get()
        return OshaLogEntry(**updated_doc.to_dict())

    def delete_entry(self, company_id: str, entry_id: str) -> None:
        """Permanently delete an OSHA log entry.

        Args:
            company_id: The owning company ID.
            entry_id: The entry ID to delete.

        Raises:
            OshaLogEntryNotFoundError: If the entry does not exist.
        """
        doc_ref = self._collection(company_id).document(entry_id)
        doc = doc_ref.get()

        if not doc.exists:
            raise OshaLogEntryNotFoundError(entry_id)

        doc_ref.delete()

    def get_300a_summary(self, company_id: str, year: int) -> Osha300Summary:
        """Calculate the OSHA 300A Annual Summary from log entries.

        Aggregates all entries for the given year and computes totals,
        injury type counts, and incidence rates (TRIR, DART).

        Args:
            company_id: The owning company ID.
            year: The calendar year to summarize.

        Returns:
            The computed Osha300Summary.
        """
        # Get company info for the summary header
        company_doc = self._company_ref(company_id).get()
        company_data = company_doc.to_dict() if company_doc.exists else {}

        company_name = company_data.get("name", "")
        establishment_name = company_data.get("name", "")
        establishment_address = company_data.get("address", "")

        # Get all entries for the year
        query = self._collection(company_id).where("year", "==", year)
        entries = [doc.to_dict() for doc in query.stream()]

        # Classification counts
        total_deaths = 0
        total_days_away = 0
        total_restricted = 0
        total_other_recordable = 0

        # Day counts
        total_days_away_count = 0
        total_restricted_days_count = 0

        # Injury type counts
        total_injuries = 0
        total_skin_disorders = 0
        total_respiratory = 0
        total_poisonings = 0
        total_hearing_loss = 0
        total_other_illnesses = 0

        for entry in entries:
            classification = entry.get("classification", "")
            if classification == CaseClassification.DEATH.value:
                total_deaths += 1
            elif classification == CaseClassification.DAYS_AWAY.value:
                total_days_away += 1
            elif classification == CaseClassification.RESTRICTED.value:
                total_restricted += 1
            elif classification == CaseClassification.OTHER_RECORDABLE.value:
                total_other_recordable += 1

            total_days_away_count += entry.get("days_away_from_work", 0)
            total_restricted_days_count += entry.get("days_of_restricted_work", 0)

            injury_type = entry.get("injury_type", "")
            if injury_type == InjuryType.INJURY.value:
                total_injuries += 1
            elif injury_type == InjuryType.SKIN_DISORDER.value:
                total_skin_disorders += 1
            elif injury_type == InjuryType.RESPIRATORY.value:
                total_respiratory += 1
            elif injury_type == InjuryType.POISONING.value:
                total_poisonings += 1
            elif injury_type == InjuryType.HEARING_LOSS.value:
                total_hearing_loss += 1
            elif injury_type == InjuryType.OTHER_ILLNESS.value:
                total_other_illnesses += 1

        # Check for stored summary data (annual_average_employees, total_hours_worked)
        summary_ref = (
            self._company_ref(company_id)
            .collection("osha_summaries")
            .document(str(year))
        )
        summary_doc = summary_ref.get()
        summary_data = summary_doc.to_dict() if summary_doc.exists else {}

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

        # Calculate incidence rates using jurisdiction-aware multiplier
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
            company_name=company_name,
            establishment_name=establishment_name,
            establishment_address=establishment_address,
            annual_average_employees=annual_average_employees,
            total_hours_worked=total_hours_worked,
            total_deaths=total_deaths,
            total_days_away=total_days_away,
            total_restricted=total_restricted,
            total_other_recordable=total_other_recordable,
            total_days_away_count=total_days_away_count,
            total_restricted_days_count=total_restricted_days_count,
            total_injuries=total_injuries,
            total_skin_disorders=total_skin_disorders,
            total_respiratory=total_respiratory,
            total_poisonings=total_poisonings,
            total_hearing_loss=total_hearing_loss,
            total_other_illnesses=total_other_illnesses,
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
        summary_ref = (
            self._company_ref(company_id)
            .collection("osha_summaries")
            .document(str(year))
        )

        today = date.today()
        summary_ref.set(
            {
                "certified_by": certified_by,
                "certified_date": today.isoformat(),
                "annual_average_employees": annual_average_employees,
                "total_hours_worked": total_hours_worked,
                "posted": True,
                "year": year,
            }
        )

        return self.get_300a_summary(company_id, year)

    def get_years_with_entries(self, company_id: str) -> list[int]:
        """Return a sorted list of years that have OSHA log entries.

        Args:
            company_id: The owning company ID.

        Returns:
            A sorted list of unique years (descending).
        """
        all_docs = self._collection(company_id).stream()
        years: set[int] = set()
        for doc in all_docs:
            data = doc.to_dict()
            year = data.get("year")
            if year is not None:
                years.add(year)
        return sorted(years, reverse=True)
