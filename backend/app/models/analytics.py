"""Pydantic models for safety analytics and EMR estimation."""

from pydantic import BaseModel, Field


class SafetyDashboardMetrics(BaseModel):
    """Company-wide safety analytics dashboard."""

    # Activity metrics
    total_projects: int = Field(default=0, description="Total projects")
    active_projects: int = Field(default=0, description="Active projects")
    total_inspections: int = Field(default=0, description="Total inspections across all projects")
    inspections_this_month: int = Field(default=0, description="Inspections created this month")
    total_toolbox_talks: int = Field(default=0, description="Total toolbox talks")
    talks_this_month: int = Field(default=0, description="Toolbox talks this month")
    total_hazard_reports: int = Field(default=0, description="Total hazard reports")
    open_hazard_reports: int = Field(default=0, description="Open hazard reports")
    total_incidents: int = Field(default=0, description="Total incidents")
    incidents_this_month: int = Field(default=0, description="Incidents this month")

    # Compliance metrics
    avg_compliance_score: float = Field(default=0.0, description="Average compliance score")
    total_workers: int = Field(default=0, description="Total workers")
    workers_with_expired_certs: int = Field(default=0, description="Workers with expired certs")
    workers_with_expiring_certs: int = Field(default=0, description="Workers with certs expiring soon")

    # OSHA metrics
    trir: float = Field(default=0.0, description="Total Recordable Incident Rate")
    dart: float = Field(default=0.0, description="Days Away/Restricted/Transfer rate")

    # Mock inspection
    last_mock_score: int | None = Field(None, description="Latest mock inspection score")
    last_mock_grade: str | None = Field(None, description="Latest mock inspection grade")
    last_mock_date: str | None = Field(None, description="Latest mock inspection date")

    # EMR modeling
    current_emr: float = Field(default=1.0, description="Current Experience Modification Rate")
    projected_emr: float = Field(default=1.0, description="Projected EMR based on current performance")
    emr_premium_impact: float = Field(
        default=0.0, description="Estimated dollar impact of EMR change"
    )


class EmrEstimateRequest(BaseModel):
    """Input model for EMR estimation."""

    current_emr: float = Field(..., gt=0, le=5, description="Current EMR value")
    annual_payroll: float = Field(..., gt=0, description="Annual payroll in dollars")
    workers_comp_rate: float = Field(
        ..., gt=0, le=100, description="Workers comp rate per $100 of payroll"
    )


class EmrEstimate(BaseModel):
    """EMR estimation result with financial projections."""

    current_emr: float
    projected_emr: float
    premium_base: float = Field(description="Annual workers comp premium at 1.0 EMR")
    current_premium: float = Field(description="Current premium based on current EMR")
    projected_premium: float = Field(description="Projected premium based on projected EMR")
    potential_savings: float = Field(description="Potential annual savings")
    recommendations: list[str] = Field(default_factory=list, description="Improvement recommendations")
