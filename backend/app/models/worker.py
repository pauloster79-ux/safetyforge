"""Pydantic models for worker profiles and certifications."""

from datetime import date, datetime
from enum import Enum

from pydantic import BaseModel, Field


class WorkerStatus(str, Enum):
    """Worker employment status."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    TERMINATED = "terminated"


class CertificationType(str, Enum):
    """Standard construction industry certification types."""

    OSHA_10 = "osha_10"
    OSHA_30 = "osha_30"
    FALL_PROTECTION = "fall_protection"
    SCAFFOLD_COMPETENT = "scaffold_competent"
    CONFINED_SPACE = "confined_space"
    EXCAVATION_COMPETENT = "excavation_competent"
    FORKLIFT_OPERATOR = "forklift_operator"
    CRANE_OPERATOR_NCCCO = "crane_operator_nccco"
    AERIAL_LIFT = "aerial_lift"
    FIRST_AID_CPR = "first_aid_cpr"
    HAZCOM_GHS = "hazcom_ghs"
    SILICA_COMPETENT = "silica_competent"
    LEAD_AWARENESS = "lead_awareness"
    ASBESTOS_AWARENESS = "asbestos_awareness"
    RESPIRATORY_FIT_TEST = "respiratory_fit_test"
    RIGGING_SIGNAL = "rigging_signal"
    ELECTRICAL_SAFETY = "electrical_safety"
    FLAGGER = "flagger"
    HAZWOPER = "hazwoper"
    FIRE_WATCH = "fire_watch"
    OTHER = "other"


class Certification(BaseModel):
    """A single certification held by a worker."""

    id: str
    certification_type: CertificationType
    custom_name: str = Field(default="", description="Custom name for OTHER type")
    issued_date: date
    expiry_date: date | None = Field(None, description="None means no expiration")
    issuing_body: str = Field(default="", max_length=256)
    certificate_number: str = Field(default="", max_length=128)
    proof_document_url: str | None = Field(
        None, description="Uploaded scan/photo of cert"
    )
    status: str = Field(
        default="valid", description="Calculated: valid, expired, expiring_soon"
    )
    notes: str = Field(default="", max_length=2000)


class CertificationCreate(BaseModel):
    """Input model for adding a certification to a worker."""

    certification_type: CertificationType
    custom_name: str = Field(default="", max_length=256)
    issued_date: date
    expiry_date: date | None = None
    issuing_body: str = Field(default="", max_length=256)
    certificate_number: str = Field(default="", max_length=128)
    notes: str = Field(default="", max_length=2000)


class CertificationUpdate(BaseModel):
    """Input model for updating a certification. All fields optional."""

    certification_type: CertificationType | None = None
    custom_name: str | None = Field(None, max_length=256)
    issued_date: date | None = None
    expiry_date: date | None = None
    issuing_body: str | None = Field(None, max_length=256)
    certificate_number: str | None = Field(None, max_length=128)
    notes: str | None = Field(None, max_length=2000)


class WorkerCreate(BaseModel):
    """Input model for creating a new worker."""

    first_name: str = Field(..., min_length=1, max_length=128, description="First name")
    last_name: str = Field(..., min_length=1, max_length=128, description="Last name")
    email: str = Field(default="", max_length=256, description="Email address")
    phone: str = Field(default="", max_length=20, description="Phone number")
    role: str = Field(
        default="laborer",
        description="Role: laborer, foreman, superintendent, operator, apprentice",
    )
    trade: str = Field(
        default="general", description="Trade type matching company trades"
    )
    language_preference: str = Field(
        default="en", description="Language preference: en, es, both"
    )
    emergency_contact_name: str = Field(
        default="", max_length=128, description="Emergency contact name"
    )
    emergency_contact_phone: str = Field(
        default="", max_length=20, description="Emergency contact phone"
    )
    hire_date: date | None = Field(None, description="Date of hire")
    notes: str = Field(default="", max_length=2000, description="Additional notes")


class WorkerUpdate(BaseModel):
    """Input model for updating a worker. All fields optional."""

    first_name: str | None = Field(None, min_length=1, max_length=128)
    last_name: str | None = Field(None, min_length=1, max_length=128)
    email: str | None = Field(None, max_length=256)
    phone: str | None = Field(None, max_length=20)
    role: str | None = None
    trade: str | None = None
    language_preference: str | None = None
    emergency_contact_name: str | None = Field(None, max_length=128)
    emergency_contact_phone: str | None = Field(None, max_length=20)
    hire_date: date | None = None
    notes: str | None = Field(None, max_length=2000)
    status: WorkerStatus | None = None


class Worker(WorkerCreate):
    """Full worker model with ID, certifications, and audit fields."""

    id: str
    company_id: str
    status: WorkerStatus = WorkerStatus.ACTIVE
    certifications: list[Certification] = Field(default_factory=list)
    total_certifications: int = Field(
        default=0, description="Total number of certifications"
    )
    expiring_soon: int = Field(
        default=0, description="Certs expiring within 30 days"
    )
    expired: int = Field(default=0, description="Number of expired certs")
    created_at: datetime
    created_by: str
    updated_at: datetime
    updated_by: str
    deleted: bool = False


class WorkerListResponse(BaseModel):
    """Response model for listing workers."""

    workers: list[Worker]
    total: int


class ExpiringCertification(BaseModel):
    """A certification that is expiring soon, with worker context."""

    worker_id: str
    worker_name: str
    certification: Certification


class ExpiringCertificationsResponse(BaseModel):
    """Response model for expiring certifications endpoint."""

    certifications: list[ExpiringCertification]
    total: int


class CertificationMatrixEntry(BaseModel):
    """Status of a single cert type for a single worker."""

    worker_id: str
    worker_name: str
    certification_type: CertificationType
    status: str = Field(description="valid, expired, expiring_soon, or missing")
    expiry_date: date | None = None


class CertificationMatrixResponse(BaseModel):
    """Response model for the certification matrix endpoint."""

    matrix: list[CertificationMatrixEntry]
    workers: list[dict]
    certification_types: list[str]
