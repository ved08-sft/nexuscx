from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field
from app.schemas.enums import RagMode, Vertical


LOW_CONFIDENCE_MESSAGE = "Low AI Confidence: Manual Agent Intervention Required"


class RagQueryRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    query: str = Field(min_length=1, max_length=1000)
    vertical: Optional[Vertical] = None
    top_k: int = Field(default=3, ge=1, le=10)
    mode: RagMode = RagMode.HYBRID
    min_score: float = Field(default=0.0, ge=0.0, le=1.0)


class RagSearchResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    chunk_id: str
    text: str
    source: str
    page: int
    section_title: Optional[str] = None
    vertical: Vertical
    sop_version: Optional[str] = None
    dense_score: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    sparse_score: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    fused_score: Optional[float] = None
    score: float = Field(ge=0.0, le=1.0)


class RagQueryResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    query_id: str
    collection: str = "sops"
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    mode: RagMode
    results: List[RagSearchResult]
    confidence: float = Field(ge=0.0, le=1.0)
    manual_required: bool
    message: Optional[str] = None
    latency_ms: int
