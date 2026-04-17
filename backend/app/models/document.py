"""Pydantic models for safety documents and document chunks."""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class DocumentType(str, Enum):
    """Available safety document types."""

    SSSP = "sssp"
    JHA = "jha"
    TOOLBOX_TALK = "toolbox_talk"
    INCIDENT_REPORT = "incident_report"
    FALL_PROTECTION = "fall_protection"
    SAFETY_PLAN = "safety_plan"
    RISK_ASSESSMENT = "risk_assessment"
    METHOD_STATEMENT = "method_statement"
    ENVIRONMENTAL_COMPLIANCE = "environmental_compliance"
    CONTRACT = "contract"
    SPECIFICATION = "specification"
    DRAWING = "drawing"
    INSURANCE_CERTIFICATE = "insurance_certificate"
    PERMIT = "permit"
    REPORT = "report"


class DocumentStatus(str, Enum):
    """Document lifecycle status."""

    DRAFT = "draft"
    ACTIVE = "active"
    FINAL = "final"
    ARCHIVED = "archived"
    SUPERSEDED = "superseded"


class IngestionStatus(str, Enum):
    """Document ingestion pipeline status."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETE = "complete"
    FAILED = "failed"


class DocumentCreate(BaseModel):
    """Input model for creating a new document."""

    title: str = Field(..., min_length=2, max_length=256, description="Document title")
    document_type: DocumentType = Field(..., description="Type of safety document")
    project_info: dict[str, Any] = Field(
        ...,
        description="Project-specific fields: site_address, scope_of_work, project_name, etc.",
    )


class DocumentUpdate(BaseModel):
    """Input model for updating a document. All fields optional."""

    title: str | None = Field(None, min_length=2, max_length=256)
    content: dict[str, Any] | None = Field(None, description="Document content sections as JSON")
    status: DocumentStatus | None = None


class DocumentGenerateRequest(BaseModel):
    """Input model for generating document content via AI."""

    document_type: DocumentType = Field(..., description="Type of safety document to generate")
    project_info: dict[str, Any] = Field(
        ...,
        description="Project-specific information for generation",
    )
    title: str = Field(..., min_length=2, max_length=256, description="Document title")


class Document(BaseModel):
    """Full document model with ID and audit fields."""

    id: str
    company_id: str
    title: str
    document_type: DocumentType
    type: str = Field(
        default="",
        description="Extended type field — used when document_type is insufficient "
                    "(e.g. 'environmental_compliance' for environmental programs)",
    )
    status: DocumentStatus = DocumentStatus.DRAFT
    content: dict[str, Any] = Field(default_factory=dict)
    project_info: dict[str, Any] = Field(default_factory=dict)
    file_url: str | None = None
    file_type: str | None = None
    ingestion_status: IngestionStatus | None = None
    chunk_count: int = 0
    generated_at: datetime | None = None
    created_at: datetime
    created_by: str
    created_by_type: str = Field(default="human", description="Actor type: 'human' or 'agent'")
    updated_at: datetime
    updated_by: str
    updated_by_type: str = Field(default="human", description="Actor type: 'human' or 'agent'")
    pdf_url: str | None = None
    deleted: bool = False


class DocumentListResponse(BaseModel):
    """Response model for listing documents."""

    documents: list[Document]
    total: int


# -- DocumentChunk models --------------------------------------------------------


class DocumentChunk(BaseModel):
    """A text chunk extracted from a document, stored as a graph node."""

    id: str
    document_id: str
    text: str
    page: int | None = None
    position: int | None = None
    chunk_index: int
    has_embedding: bool = False
    created_at: datetime


class DocumentChunkResult(BaseModel):
    """Search result for a document chunk with relevance score."""

    chunk_id: str
    text: str
    page: int | None = None
    chunk_index: int
    document_id: str
    document_title: str
    document_type: str | None = None
    score: float


class DocumentSearchRequest(BaseModel):
    """Request model for hybrid document search."""

    query: str = Field(..., min_length=1, max_length=1000, description="Search query")
    project_id: str | None = Field(None, description="Filter by project ID")
    document_type: DocumentType | None = Field(None, description="Filter by document type")
    top_k: int = Field(default=10, ge=1, le=50, description="Number of results to return")


class DocumentSearchResponse(BaseModel):
    """Response model for document search results."""

    results: list[DocumentChunkResult]
    total: int


class DocumentUploadResponse(BaseModel):
    """Response model for file upload."""

    document_id: str
    title: str
    file_type: str
    ingestion_status: IngestionStatus
    message: str
