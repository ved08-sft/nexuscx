from datetime import date, datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator
from app.schemas.enums import (
    AiSuggestionOutcome,
    Channel,
    ChurnRiskClass,
    LlmProvider,
    Language,
    Vertical,
)


class AnalyticsExportRequestParams(BaseModel):
    model_config = ConfigDict(extra="forbid")

    from_date: date
    to_date: date
    format: str = Field(default="json", pattern=r"^(json|csv)$")
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=1000, ge=1, le=5000)
    vertical: Optional[Vertical] = None
    client: Optional[str] = Field(default=None, max_length=64)

    @field_validator("to_date")
    @classmethod
    def validate_date_range(cls, v: date, info) -> date:
        if "from_date" in info.data and v < info.data["from_date"]:
            raise ValueError("to_date must be greater than or equal to from_date")
        if "from_date" in info.data and (v - info.data["from_date"]).days > 92:
            raise ValueError("Date range must be 92 days or fewer")
        return v


class AnalyticsExportRow(BaseModel):
    model_config = ConfigDict(extra="forbid")

    interaction_id: str
    session_id: str
    ticket_id: str
    customer_ref: str = Field(min_length=12, max_length=12)
    agent_id: str
    client: str
    vertical: Vertical
    channel: Channel
    intent: str
    language: Language
    start_ts: datetime
    end_ts: Optional[datetime] = None
    handle_time_sec: int = Field(ge=0)
    hold_sec: int = Field(ge=0)
    acw_sec: int = Field(ge=0)
    first_contact_resolved: bool
    sla_met: bool
    risk_score_max: float = Field(ge=0.0, le=1.0)
    escalation_probability_max: float = Field(ge=0.0, le=1.0)
    churn_risk_class: ChurnRiskClass
    sentiment_avg: float = Field(ge=-1.0, le=1.0)
    escalated: bool
    compliance_score: int = Field(ge=0, le=100)
    critical_flags: int = Field(ge=0)
    warning_flags: int = Field(ge=0)
    info_flags: int = Field(ge=0)
    violated_rule_ids: str
    ai_suggestion_outcome: AiSuggestionOutcome
    ai_confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    llm_provider: LlmProvider
    fallback_used: bool
    ekyc_verified: bool
    past_escalation_count: int = Field(ge=0)


class AnalyticsExportResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    page: int
    page_size: int
    total: int
    next_page: Optional[int] = None
    generated_at: datetime
    rows: List[AnalyticsExportRow]
