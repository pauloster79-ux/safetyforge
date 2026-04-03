"""Pydantic models for document templates."""

from pydantic import BaseModel, Field


class FieldDefinition(BaseModel):
    """Definition of a required input field for a template."""

    name: str = Field(..., description="Field identifier")
    label: str = Field(..., description="Human-readable label")
    field_type: str = Field(
        ..., description="Input type: text, textarea, date, select, number, email, phone"
    )
    required: bool = Field(default=True, description="Whether the field is required")
    placeholder: str = Field(default="", description="Placeholder text for the input")
    options: list[str] | None = Field(
        default=None, description="Options for select-type fields"
    )
    description: str = Field(default="", description="Help text for the field")


class SectionDefinition(BaseModel):
    """Definition of a document section within a template."""

    section_id: str = Field(..., description="Section identifier")
    title: str = Field(..., description="Section heading")
    description: str = Field(..., description="What this section covers")
    ai_generated: bool = Field(
        default=True, description="Whether AI generates this section content"
    )


class Template(BaseModel):
    """Complete template definition for a safety document type."""

    template_id: str = Field(..., description="Unique template identifier")
    name: str = Field(..., description="Template display name")
    description: str = Field(..., description="Template description for users")
    document_type: str = Field(..., description="Corresponding DocumentType value")
    required_fields: list[FieldDefinition] = Field(
        ..., description="Fields the user must fill in"
    )
    sections: list[SectionDefinition] = Field(
        ..., description="Sections that make up the document"
    )
    osha_references: list[str] = Field(
        ..., description="Relevant OSHA standard references"
    )
    estimated_generation_time_seconds: int = Field(
        default=30, description="Approximate time to generate this document"
    )


class TemplateListResponse(BaseModel):
    """Response model for listing templates."""

    templates: list[Template]
    total: int
