"""Pydantic models for IndustryProductivityBaseline — shared industry productivity rates.

IndustryProductivityBaseline nodes are industry-average productivity rates
(RSMeans-style) used as the weakest fallback in the Layer 3 source cascade.
Low confidence by design — always overridden by a contractor's own insights,
productivity rates, or history when available.

These are seeded data, not user-mutable.
"""

from pydantic import BaseModel, Field


class IndustryProductivityBaseline(BaseModel):
    """An industry-average productivity baseline for a trade/work type."""

    id: str
    trade: str = Field(..., description="Trade (e.g. 'electrical', 'plumbing')")
    work_description: str = Field(
        ..., description="What the work is (e.g. 'conduit rough-in')"
    )
    rate: float = Field(..., description="Production rate per time unit")
    rate_unit: str = Field(..., description="Unit of output (LF, SF, EA, CY)")
    time_unit: str = Field(
        ..., description="Time unit: 'per_hour', 'per_day', 'per_shift'"
    )
    crew_size: int = Field(..., ge=1, description="Crew size this rate assumes")
    source: str = Field(
        ..., description="Citation (e.g. 'RSMeans 2024', 'NCE 2024')"
    )
    confidence: float = Field(
        default=0.3,
        ge=0.0,
        le=1.0,
        description="Baseline confidence (low by design — industry averages)",
    )


class IndustryProductivityBaselineListResponse(BaseModel):
    """Response model for listing industry baselines."""

    baselines: list[IndustryProductivityBaseline]
    total: int
