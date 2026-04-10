"""Pydantic models for assembled graph context.

The AssembledContext is a structured snapshot of company/project data
assembled from Neo4j graph traversals. Composite services (analytics,
morning_brief, mock_inspection, gc_portal, prequalification) use it
instead of making redundant calls to multiple sub-services.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


# -- Lightweight sub-models (counts and flags) ---------------------------------


class ProjectCounts(BaseModel):
    """Project-level aggregations."""

    total: int = 0
    active: int = 0


class WorkerCounts(BaseModel):
    """Aggregated worker/certification counts."""

    total: int = 0
    active: int = 0
    expired_certs: int = 0
    expiring_certs: int = 0
    has_training_records: bool = False


class DocumentCounts(BaseModel):
    """Aggregated document statistics."""

    total: int = 0
    by_type: dict[str, int] = Field(default_factory=dict)
    by_status: dict[str, int] = Field(default_factory=dict)


class ActivityCounts(BaseModel):
    """Cross-project activity aggregations for analytics."""

    total_inspections: int = 0
    inspections_this_month: int = 0
    total_talks: int = 0
    talks_this_month: int = 0
    total_hazard_reports: int = 0
    open_hazard_reports: int = 0
    total_incidents: int = 0
    incidents_this_month: int = 0


# -- Per-entity detail models --------------------------------------------------


class ProjectSummary(BaseModel):
    """Lightweight project info for context assembly."""

    id: str
    name: str
    status: str


class ProjectActivitySummary(BaseModel):
    """Per-project activity existence checks."""

    project_id: str
    project_name: str
    has_recent_inspection: bool = False
    has_recent_talk: bool = False
    latest_inspection_date: str | None = None
    latest_talk_date: str | None = None


class WorkerDetail(BaseModel):
    """Full worker info needed by mock inspection."""

    id: str
    first_name: str
    last_name: str
    role: str | None = None
    status: str = "active"
    certifications: list[dict[str, Any]] = Field(default_factory=list)


class DocumentSummary(BaseModel):
    """Document info. Full content only when include_content=True."""

    id: str
    title: str
    document_type: str
    content: dict[str, Any] | None = None


class OshaContext(BaseModel):
    """OSHA log aggregated data."""

    entry_count_current_year: int = 0
    years_with_entries: list[int] = Field(default_factory=list)
    trir: float = 0.0
    dart: float = 0.0
    posted_previous_year: bool = False
    trir_by_year: dict[int, float] = Field(default_factory=dict)
    dart_by_year: dict[int, float] = Field(default_factory=dict)


class MockInspectionSummary(BaseModel):
    """Latest mock inspection result snapshot."""

    score: int | None = None
    grade: str | None = None
    created_at: str | None = None


# -- Top-level assembled context -----------------------------------------------


class AssembledContext(BaseModel):
    """Unified context assembled from graph traversals.

    All sections are Optional. Consumers request only what they need
    via the ContextAssemblerService methods.
    """

    company_id: str
    project_id: str | None = None
    assembled_at: datetime

    # Lightweight counts
    project_counts: ProjectCounts | None = None
    worker_counts: WorkerCounts | None = None
    document_counts: DocumentCounts | None = None
    activity_counts: ActivityCounts | None = None

    # Per-project activity checks
    project_activity: list[ProjectActivitySummary] | None = None

    # Full object lists
    projects: list[ProjectSummary] | None = None
    workers: list[WorkerDetail] | None = None
    documents: list[DocumentSummary] | None = None

    # OSHA data
    osha: OshaContext | None = None

    # Mock inspection
    latest_mock: MockInspectionSummary | None = None
