"""Pydantic models for OSHA 300 Log entries and 300A summary."""

from datetime import date, datetime
from enum import Enum

from pydantic import BaseModel, Field


class InjuryType(str, Enum):
    """OSHA injury/illness type classification."""

    INJURY = "injury"
    SKIN_DISORDER = "skin_disorder"
    RESPIRATORY = "respiratory"
    POISONING = "poisoning"
    HEARING_LOSS = "hearing_loss"
    OTHER_ILLNESS = "other_illness"


class CaseClassification(str, Enum):
    """OSHA case outcome classification."""

    DEATH = "death"
    DAYS_AWAY = "days_away_from_work"
    RESTRICTED = "job_transfer_or_restriction"
    OTHER_RECORDABLE = "other_recordable"


class OshaLogEntry(BaseModel):
    """A single OSHA 300 Log entry (one recordable case)."""

    id: str
    case_number: int = Field(description="Sequential within the year")
    employee_name: str
    job_title: str
    date_of_injury: date
    where_event_occurred: str = Field(description="e.g., Loading dock, Building A")
    description: str = Field(description="Brief description of injury/illness")
    classification: CaseClassification
    injury_type: InjuryType
    days_away_from_work: int = 0
    days_of_restricted_work: int = 0
    died: bool = False
    privacy_case: bool = Field(
        default=False,
        description="If true, don't show employee name on 300 Log",
    )
    year: int = Field(description="Calendar year for this entry")
    company_id: str
    created_at: datetime
    created_by: str
    updated_at: datetime
    updated_by: str


class OshaLogEntryCreate(BaseModel):
    """Input model for creating an OSHA 300 Log entry."""

    employee_name: str = Field(..., min_length=2, max_length=128)
    job_title: str = Field(..., min_length=2, max_length=128)
    date_of_injury: date
    where_event_occurred: str = Field(..., min_length=2, max_length=256)
    description: str = Field(..., min_length=10, max_length=2000)
    classification: CaseClassification
    injury_type: InjuryType
    days_away_from_work: int = Field(default=0, ge=0)
    days_of_restricted_work: int = Field(default=0, ge=0)
    died: bool = False
    privacy_case: bool = False


class OshaLogEntryUpdate(BaseModel):
    """Input model for updating an OSHA 300 Log entry. All fields optional."""

    employee_name: str | None = Field(None, min_length=2, max_length=128)
    job_title: str | None = Field(None, min_length=2, max_length=128)
    date_of_injury: date | None = None
    where_event_occurred: str | None = Field(None, min_length=2, max_length=256)
    description: str | None = Field(None, min_length=10, max_length=2000)
    classification: CaseClassification | None = None
    injury_type: InjuryType | None = None
    days_away_from_work: int | None = Field(None, ge=0)
    days_of_restricted_work: int | None = Field(None, ge=0)
    died: bool | None = None
    privacy_case: bool | None = None


class OshaLogEntryListResponse(BaseModel):
    """Response model for listing OSHA 300 Log entries."""

    entries: list[OshaLogEntry]
    total: int


class Osha300Summary(BaseModel):
    """The OSHA 300A Annual Summary -- calculated from log entries."""

    year: int
    company_name: str
    establishment_name: str
    establishment_address: str
    industry_description: str = "Construction"
    naics_code: str = "236"
    annual_average_employees: int = 0
    total_hours_worked: int = 0
    # Totals (calculated from entries)
    total_deaths: int = 0
    total_days_away: int = 0
    total_restricted: int = 0
    total_other_recordable: int = 0
    total_days_away_count: int = 0
    total_restricted_days_count: int = 0
    # Injury/illness type totals
    total_injuries: int = 0
    total_skin_disorders: int = 0
    total_respiratory: int = 0
    total_poisonings: int = 0
    total_hearing_loss: int = 0
    total_other_illnesses: int = 0
    # Incidence rates (per 200,000 hours)
    trir: float = 0.0
    dart: float = 0.0
    # Status
    certified_by: str = ""
    certified_date: date | None = None
    posted: bool = False


class CertifySummaryRequest(BaseModel):
    """Input model for certifying the 300A summary."""

    certified_by: str = Field(..., min_length=2, max_length=128)
    annual_average_employees: int = Field(default=0, ge=0)
    total_hours_worked: int = Field(default=0, ge=0)


class OshaLogYearsResponse(BaseModel):
    """Response model for listing years with OSHA log entries."""

    years: list[int]
