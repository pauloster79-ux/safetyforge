"""Pydantic models for the GC/Sub Portal."""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, EmailStr, Field


class RelationshipStatus(str, Enum):
    """Status of a GC/Sub relationship."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"


class GcRelationship(BaseModel):
    """A relationship between a GC and a sub-contractor.

    Attributes:
        id: Unique relationship identifier.
        gc_company_id: The GC's company ID.
        sub_company_id: The sub's company ID.
        gc_company_name: Display name of the GC company.
        sub_company_name: Display name of the sub company.
        project_name: Optional project context for the relationship.
        status: Current relationship status.
        can_view_documents: Whether the GC can view sub's documents.
        can_view_inspections: Whether the GC can view sub's inspections.
        can_view_training: Whether the GC can view sub's training records.
        can_view_incidents: Whether the GC can view sub's incidents.
        can_view_osha_log: Whether the GC can view sub's OSHA log.
        created_at: Timestamp of relationship creation.
        updated_at: Timestamp of last update.
    """

    id: str
    gc_company_id: str
    sub_company_id: str
    gc_company_name: str = ""
    sub_company_name: str = ""
    project_name: str = ""
    status: RelationshipStatus = RelationshipStatus.ACTIVE
    can_view_documents: bool = True
    can_view_inspections: bool = True
    can_view_training: bool = True
    can_view_incidents: bool = False
    can_view_osha_log: bool = True
    created_at: datetime
    updated_at: datetime


class GcRelationshipCreate(BaseModel):
    """Input model for creating a GC/Sub relationship.

    Attributes:
        sub_company_id: The sub-contractor's company ID.
        project_name: Optional project name for context.
        can_view_documents: Permission to view documents.
        can_view_inspections: Permission to view inspections.
        can_view_training: Permission to view training records.
        can_view_incidents: Permission to view incidents.
        can_view_osha_log: Permission to view OSHA log.
    """

    sub_company_id: str = Field(..., min_length=1, description="Sub-contractor company ID")
    project_name: str = Field(default="", max_length=256, description="Project name")
    can_view_documents: bool = True
    can_view_inspections: bool = True
    can_view_training: bool = True
    can_view_incidents: bool = False
    can_view_osha_log: bool = True


class SubComplianceSummary(BaseModel):
    """What a GC sees about a sub's compliance.

    Attributes:
        sub_company_id: The sub-contractor's company ID.
        sub_company_name: Display name of the sub company.
        compliance_score: Average compliance score across active projects.
        emr: Current Experience Modification Rate.
        trir: Current Total Recordable Incident Rate.
        active_workers: Count of active workers.
        expired_certifications: Count of expired certifications.
        expiring_certifications: Count of certifications expiring soon.
        last_inspection_date: Date of most recent inspection.
        last_toolbox_talk_date: Date of most recent toolbox talk.
        mock_inspection_score: Latest mock inspection score.
        mock_inspection_grade: Latest mock inspection grade.
        documents_on_file: Total document count.
        inspection_current: Whether an inspection was done recently.
        talks_current: Whether a toolbox talk was done recently.
        training_current: Whether all certifications are current.
        overall_status: Compliance status indicator.
    """

    sub_company_id: str
    sub_company_name: str
    compliance_score: int = 0
    emr: float | None = None
    trir: float | None = None
    active_workers: int = 0
    expired_certifications: int = 0
    expiring_certifications: int = 0
    last_inspection_date: str | None = None
    last_toolbox_talk_date: str | None = None
    mock_inspection_score: int | None = None
    mock_inspection_grade: str | None = None
    documents_on_file: int = 0
    inspection_current: bool = False
    talks_current: bool = False
    training_current: bool = True
    overall_status: str = "compliant"


class GcRelationshipListResponse(BaseModel):
    """Response model for listing GC relationships."""

    relationships: list[GcRelationship]
    total: int


class SubComplianceDashboard(BaseModel):
    """Response model for the GC dashboard with all sub summaries."""

    summaries: list[SubComplianceSummary]
    total: int


class InviteSubRequest(BaseModel):
    """Input model for inviting a sub-contractor.

    Attributes:
        sub_email: Email address of the sub-contractor to invite.
        project_name: Optional project name for context.
    """

    sub_email: EmailStr = Field(..., description="Sub-contractor email address")
    project_name: str = Field(default="", max_length=256, description="Project name")


class GcInvitation(BaseModel):
    """A pending invitation from a GC to a sub.

    Attributes:
        id: Unique invitation identifier.
        gc_company_id: The GC's company ID.
        gc_company_name: Display name of the GC company.
        sub_email: Email address the invitation was sent to.
        project_name: Optional project name for context.
        status: Current invitation status.
        created_at: Timestamp of invitation creation.
    """

    id: str
    gc_company_id: str
    gc_company_name: str = ""
    sub_email: str
    project_name: str = ""
    status: str = "pending"
    created_at: datetime


class PaymentRelease(BaseModel):
    """A payment release record in the new ontology.

    Renamed from LienWaiver to PaymentRelease.
    """

    id: str
    gc_company_id: str
    sub_company_id: str
    project_id: str | None = None
    amount: float = Field(default=0.0, description="Payment amount")
    release_type: str = Field(
        default="conditional",
        description="Release type: 'conditional' or 'unconditional'",
    )
    status: str = Field(default="pending", description="Status: pending, executed, voided")
    notes: str = ""
    created_at: datetime
    created_by: str = ""
    created_by_type: str = Field(default="human", description="Actor type: 'human' or 'agent'")
    updated_at: datetime | None = None
    updated_by: str = ""
    updated_by_type: str = Field(default="human", description="Actor type: 'human' or 'agent'")


# Backward-compat alias
LienWaiver = PaymentRelease
