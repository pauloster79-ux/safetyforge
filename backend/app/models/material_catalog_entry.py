"""Pydantic models for MaterialCatalogEntry — company-scoped material price catalog.

MaterialCatalogEntry nodes are price observations a contractor has collected
(from suppliers, past jobs, or research). They feed Layer 3 of the source
cascade when pricing Items during estimating.

Graph model: (Company)-[:HAS_CATALOG_ENTRY]->(MaterialCatalogEntry)
"""

from datetime import datetime

from pydantic import BaseModel, Field


class MaterialCatalogEntryCreate(BaseModel):
    """Input model for creating a material catalog entry."""

    description: str = Field(
        ..., min_length=2, max_length=512, description="What the material is"
    )
    product_code: str | None = Field(
        None, max_length=128, description="Supplier product code or SKU"
    )
    unit: str = Field(..., max_length=20, description="Unit of measurement (e.g. 'EA', 'LF')")
    unit_cost_cents: int = Field(..., ge=0, description="Cost per unit in cents")
    supplier_name: str | None = Field(None, max_length=256, description="Supplier name")
    source_url: str | None = Field(
        None, max_length=1024, description="Source URL (e.g. supplier site)"
    )
    location: str | None = Field(
        None,
        max_length=128,
        description="City or region where this price applies (for locality pricing)",
    )


class MaterialCatalogEntryUpdate(BaseModel):
    """Input model for updating a material catalog entry. All fields optional."""

    description: str | None = Field(None, min_length=2, max_length=512)
    product_code: str | None = Field(None, max_length=128)
    unit: str | None = Field(None, max_length=20)
    unit_cost_cents: int | None = Field(None, ge=0)
    supplier_name: str | None = Field(None, max_length=256)
    source_url: str | None = Field(None, max_length=1024)
    location: str | None = Field(None, max_length=128)
    last_verified_at: datetime | None = None


class MaterialCatalogEntry(BaseModel):
    """Full material catalog entry with ID and audit fields."""

    id: str
    company_id: str
    description: str
    product_code: str | None = None
    unit: str
    unit_cost_cents: int
    supplier_name: str | None = None
    source_url: str | None = None
    location: str | None = None
    fetched_at: datetime
    last_verified_at: datetime | None = None
    created_at: datetime
    created_by: str
    updated_at: datetime
    updated_by: str


class MaterialCatalogEntryListResponse(BaseModel):
    """Response model for listing catalog entries."""

    entries: list[MaterialCatalogEntry]
    total: int


class MaterialHistoryMatch(BaseModel):
    """A match from the contractor's past Item history for a material description."""

    project_name: str
    supplier: str | None = None
    unit_cost_cents: int
    date: datetime
