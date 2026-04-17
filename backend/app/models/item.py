"""Pydantic models for Item — discrete items used by WorkItems.

Materials, equipment, fixtures, rentals, or any non-labour cost component.
"""

from datetime import datetime

from pydantic import BaseModel, Field


class ItemCreate(BaseModel):
    """Input model for creating an item on a work item."""

    description: str = Field(
        ..., min_length=2, max_length=512, description="What the item is"
    )
    product: str = Field(
        default="", max_length=256, description="Specific product name or model number"
    )
    quantity: float = Field(..., gt=0, description="Number of units")
    unit: str = Field(default="EA", max_length=20, description="Unit of measurement")
    unit_cost_cents: int = Field(..., ge=0, description="Cost per unit in cents")
    notes: str = Field(default="", max_length=2000, description="Additional notes")


class ItemUpdate(BaseModel):
    """Input model for updating an item. All fields optional.

    Source-cascade provenance fields (price_source_*, source_reasoning,
    source_url, price_fetched_at) can be updated to reflect where the
    unit_cost_cents came from.
    """

    description: str | None = Field(None, min_length=2, max_length=512)
    product: str | None = Field(None, max_length=256)
    quantity: float | None = Field(None, gt=0)
    unit: str | None = Field(None, max_length=20)
    unit_cost_cents: int | None = Field(None, ge=0)
    notes: str | None = Field(None, max_length=2000)
    # -- Source cascade provenance --
    price_source_id: str | None = Field(
        None,
        max_length=64,
        description="Points to MaterialCatalogEntry ID or past Item ID",
    )
    price_source_type: str | None = Field(
        None,
        max_length=64,
        description=(
            "One of 'material_catalog', 'purchase_history', "
            "'contractor_stated', 'estimate'"
        ),
    )
    source_reasoning: str | None = Field(
        None,
        max_length=2000,
        description="Human-readable explanation (e.g. 'From your Buckhead job, Feb 2026')",
    )
    source_url: str | None = Field(
        None, max_length=1024, description="Source URL (if researched via web)"
    )
    price_fetched_at: datetime | None = Field(
        None, description="When the price was obtained"
    )


class Item(ItemCreate):
    """Full item model with ID, computed total, and audit fields."""

    id: str
    work_item_id: str
    total_cents: int = Field(description="quantity * unit_cost_cents, in cents")
    # -- Source cascade provenance (set via MCP tools / estimating agents) --
    price_source_id: str | None = None
    price_source_type: str | None = None
    source_reasoning: str | None = None
    source_url: str | None = None
    price_fetched_at: datetime | None = None
    created_at: datetime
    created_by: str
    updated_at: datetime
    updated_by: str


class ItemListResponse(BaseModel):
    """Response model for listing items."""

    items: list[Item]
    total: int
