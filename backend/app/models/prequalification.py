"""Pydantic models for prequalification automation."""

from datetime import date, datetime
from enum import Enum

from pydantic import BaseModel, Field


class PrequalPlatform(str, Enum):
    """Supported prequalification platforms."""

    ISNETWORLD = "isnetworld"
    AVETTA = "avetta"
    BROWZ = "browz"
    GENERIC = "generic"


class PrequalDocumentStatus(str, Enum):
    """Status of a document within a prequalification package."""

    READY = "ready"
    OUTDATED = "outdated"
    MISSING = "missing"
    NOT_APPLICABLE = "na"


class PrequalDocument(BaseModel):
    """A document required for prequalification.

    Attributes:
        document_name: Human-readable name of the required document.
        category: Grouping category for the document requirement.
        required: Whether this document is mandatory for submission.
        status: Current readiness status of the document.
        source: Which Kerf module provides this data.
        source_id: ID of the existing document/record if available.
        notes: Additional context or instructions.
    """

    document_name: str
    category: str
    required: bool
    status: PrequalDocumentStatus
    source: str
    source_id: str | None = None
    notes: str = ""


class PrequalPackage(BaseModel):
    """A complete prequalification submission package.

    Attributes:
        id: Unique package identifier.
        company_id: Owning company ID.
        platform: Target prequalification platform.
        client_name: The GC or owner requesting prequalification.
        submission_deadline: Optional deadline for submission.
        overall_readiness: Percentage of required documents that are ready.
        total_documents: Total number of documents in the package.
        ready_documents: Count of documents with READY status.
        outdated_documents: Count of documents with OUTDATED status.
        missing_documents: Count of documents with MISSING status.
        documents: Full list of document requirements with statuses.
        questionnaire: Pre-filled questionnaire answers.
        created_at: Timestamp of package creation.
        updated_at: Timestamp of last update.
        created_by: Firebase UID of the creator.
    """

    id: str
    company_id: str
    platform: PrequalPlatform
    client_name: str = ""
    submission_deadline: date | None = None
    overall_readiness: int
    total_documents: int
    ready_documents: int
    outdated_documents: int
    missing_documents: int
    documents: list[PrequalDocument]
    questionnaire: dict = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime
    created_by: str


class PrequalPackageListResponse(BaseModel):
    """Response model for listing prequalification packages."""

    packages: list[PrequalPackage]
    total: int


class PrequalRequirementsResponse(BaseModel):
    """Response model for platform requirements."""

    platform: PrequalPlatform
    requirements: list[PrequalDocument]
    total: int
