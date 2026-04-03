"""Pydantic models for safety documents."""

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


class DocumentStatus(str, Enum):
    """Document lifecycle status."""

    DRAFT = "draft"
    FINAL = "final"
    ARCHIVED = "archived"


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
    status: DocumentStatus = DocumentStatus.DRAFT
    content: dict[str, Any] = Field(default_factory=dict)
    project_info: dict[str, Any] = Field(default_factory=dict)
    generated_at: datetime | None = None
    created_at: datetime
    created_by: str
    updated_at: datetime
    updated_by: str
    pdf_url: str | None = None
    deleted: bool = False


class DocumentListResponse(BaseModel):
    """Response model for listing documents."""

    documents: list[Document]
    total: int
