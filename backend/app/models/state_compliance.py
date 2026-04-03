"""Pydantic models for state compliance engine."""

from pydantic import BaseModel, Field


class StateRequirement(BaseModel):
    """A state-specific requirement beyond federal OSHA.

    Attributes:
        id: Unique requirement identifier.
        state: Two-letter state code.
        requirement_name: Human-readable requirement name.
        description: Detailed description of the requirement.
        federal_equivalent: The federal standard this extends, if any.
        state_standard: State-specific standard reference.
        additional_details: Extra context or implementation guidance.
        applies_to: Scope of applicability.
        severity: Whether the requirement is mandatory or recommended.
    """

    id: str
    state: str
    requirement_name: str
    description: str
    federal_equivalent: str | None = None
    state_standard: str
    additional_details: str = ""
    applies_to: str = "all"
    severity: str = "mandatory"


class StateComplianceGap(BaseModel):
    """A single compliance gap found during a state check.

    Attributes:
        requirement_id: ID of the unmet requirement.
        requirement_name: Human-readable name.
        status: Current status of compliance for this item.
        action_needed: What the contractor needs to do.
    """

    requirement_id: str
    requirement_name: str
    status: str
    action_needed: str


class StateComplianceCheck(BaseModel):
    """Result of checking a company's compliance against state requirements.

    Attributes:
        state: Two-letter state code.
        total_requirements: Total requirements for this state.
        met_requirements: Count of requirements that are met.
        gaps: List of compliance gaps found.
        compliance_percentage: Percentage of requirements met.
    """

    state: str
    total_requirements: int
    met_requirements: int
    gaps: list[StateComplianceGap]
    compliance_percentage: int


class StateListResponse(BaseModel):
    """Response model for listing available states."""

    states: list[dict] = Field(
        default_factory=list,
        description="List of state objects with code and name",
    )
    total: int


class StateRequirementsResponse(BaseModel):
    """Response model for state requirements."""

    state: str
    requirements: list[StateRequirement]
    total: int
