from datetime import datetime
from typing import Dict, Any, Optional
from pydantic import BaseModel, ConfigDict, Field


class SystemMetrics(BaseModel):
    model_config = ConfigDict(extra="forbid")

    cpu_percent: float = Field(ge=0.0, le=100.0)
    cpu_count: int = Field(ge=1)
    ram_percent: float = Field(ge=0.0, le=100.0)
    ram_used_mb: float = Field(ge=0.0)
    ram_total_mb: float = Field(ge=0.0)
    process_rss_mb: float = Field(ge=0.0)
    thread_count: int = Field(ge=1)


class WebsocketMetrics(BaseModel):
    model_config = ConfigDict(extra="forbid")

    active_connections: int = Field(ge=0)
    active_sessions: int = Field(ge=0)
    max_queue_depth: int = Field(ge=0)


class DependencyStatus(BaseModel):
    model_config = ConfigDict(extra="allow")

    status: str
    latency_ms: Optional[float] = None
    collection_count: Optional[int] = None


class LlmMetrics(BaseModel):
    model_config = ConfigDict(extra="forbid")

    active_provider: str
    fallback_active: bool


class HealthResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: str
    version: str = "1.0.0"
    timestamp: datetime
    uptime_sec: float = Field(ge=0.0)
    system: SystemMetrics
    websocket: WebsocketMetrics
    dependencies: Dict[str, DependencyStatus]
    llm: LlmMetrics
