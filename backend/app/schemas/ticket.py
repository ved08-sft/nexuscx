from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field
from app.schemas.enums import Channel, ContentFormat, Language, SourceType, Vertical


TICKET_ID_REGEX = r"^TKT-\d{4}-\d{6}$"
CUSTOMER_ID_REGEX = r"^CUST-\d{3,10}$"
SESSION_ID_REGEX = r"^S-[A-Za-z0-9-]{1,40}$"


class TicketMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid")

    vertical: Vertical
    hold_count: int = Field(default=0, ge=0, le=50)
    transfer_count: int = Field(default=0, ge=0, le=20)
    prior_tickets_30d: int = Field(default=0, ge=0)


class CustomerProfile(BaseModel):
    model_config = ConfigDict(extra="forbid")

    avg_handling_time_sec: Optional[float] = Field(default=None, ge=0.0, le=7200.0)
    past_escalation_count: Optional[int] = Field(default=None, ge=0, le=50)
    ekyc_verified: Optional[bool] = None


class TicketIngestRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_type: SourceType
    ticket_id: str = Field(pattern=TICKET_ID_REGEX)
    customer_id: str = Field(pattern=CUSTOMER_ID_REGEX)
    channel: Channel
    subject: Optional[str] = Field(default=None, max_length=200)
    raw_text: str = Field(min_length=1, max_length=8000)
    content_format: ContentFormat = ContentFormat.TEXT
    language: Language
    received_at: datetime
    metadata: TicketMetadata
    customer_profile: Optional[CustomerProfile] = None


class TicketIngestResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    session_id: str = Field(pattern=SESSION_ID_REGEX)
    interaction_id: str
    ticket_id: str
    status: str = "queued"
    ws_url: str
    created_at: datetime
