"""Pydantic models for morning safety briefs."""

from datetime import date, datetime
from enum import Enum

from pydantic import BaseModel, Field


class RiskLevel(str, Enum):
    """Project risk level based on aggregated safety data."""

    LOW = "low"
    MODERATE = "moderate"
    ELEVATED = "elevated"
    HIGH = "high"
    CRITICAL = "critical"


class BriefAlert(BaseModel):
    """A single alert item in a morning brief."""

    alert_type: str = Field(
        ...,
        description="Alert category: weather, certification, inspection, toolbox_talk, incident, schedule",
    )
    severity: str = Field(
        ..., description="Alert severity: critical, warning, info"
    )
    title: str = Field(..., description="Short alert title")
    description: str = Field(..., description="Detailed alert description")
    action_url: str = Field(default="", description="Optional deep-link URL")
    action_label: str = Field(default="", description="Optional action button label")


class MorningBrief(BaseModel):
    """Full morning safety brief with risk assessment and alerts."""

    id: str
    company_id: str
    project_id: str
    date: date
    risk_score: float = Field(..., ge=0, le=10, description="Aggregated risk score 0-10")
    risk_level: RiskLevel
    weather: dict = Field(
        default_factory=dict,
        description="Weather data: temperature, condition, wind_speed, humidity, precipitation_chance, alerts",
    )
    alerts: list[BriefAlert] = Field(default_factory=list)
    recommended_toolbox_talk_topic: str = Field(
        default="", description="AI-recommended toolbox talk topic"
    )
    summary: str = Field(default="", description="Brief narrative summary")
    created_at: datetime


class MorningBriefListResponse(BaseModel):
    """Response model for listing morning briefs."""

    briefs: list[MorningBrief]
    total: int
