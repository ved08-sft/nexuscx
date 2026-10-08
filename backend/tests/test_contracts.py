from datetime import date, datetime, timezone
import pytest
from pydantic import ValidationError

from app.schemas.analytics import AnalyticsExportRequestParams, AnalyticsExportResponse, AnalyticsExportRow
from app.schemas.auth import LoginRequest, LoginResponse
from app.schemas.enums import (
    AiSuggestionOutcome,
    Channel,
    ChurnRiskClass,
    ContentFormat,
    ErrorCode,
    Language,
    LlmProvider,
    RagMode,
    SourceType,
    UserRole,
    Vertical,
)
from app.schemas.error import ErrorBody, ErrorDetail, ErrorResponse
from app.schemas.health import (
    DependencyStatus,
    HealthResponse,
    LlmMetrics,
    SystemMetrics,
    WebsocketMetrics,
)
from app.schemas.rag import RagQueryRequest, RagQueryResponse, RagSearchResult
from app.schemas.ticket import (
    CustomerProfile,
    TicketIngestRequest,
    TicketIngestResponse,
    TicketMetadata,
)


# ============================================================================
# 1. TICKET INGEST CONTRACT TESTS (§1.1)
# ============================================================================

def test_ticket_ingest_request_valid():
    payload = {
        "source_type": "email",
        "ticket_id": "TKT-2026-000123",
        "customer_id": "CUST-88231",
        "channel": "email",
        "subject": "Flight cancelled - refund status",
        "raw_text": "Meri flight 6E-4X9Q cancel ho gayi hai. Refund kab milega?",
        "content_format": "text",
        "language": "hinglish",
        "received_at": "2026-10-05T10:15:00+05:30",
        "metadata": {"vertical": "flight", "hold_count": 0, "transfer_count": 0, "prior_tickets_30d": 3},
        "customer_profile": {"avg_handling_time_sec": 412.0, "past_escalation_count": 2, "ekyc_verified": False},
    }
    req = TicketIngestRequest.model_validate(payload)
    assert req.ticket_id == "TKT-2026-000123"
    assert req.customer_id == "CUST-88231"
    assert req.metadata.vertical == Vertical.FLIGHT


@pytest.mark.parametrize("invalid_ticket_id", ["TKT-123", "BAD-2026-000123", "TKT-2026-1234567"])
def test_ticket_ingest_invalid_ticket_id_pattern(invalid_ticket_id):
    payload = {
        "source_type": "ticket",
        "ticket_id": invalid_ticket_id,
        "customer_id": "CUST-88231",
        "channel": "voice",
        "raw_text": "Hello world",
        "language": "english",
        "received_at": "2026-10-05T10:15:00Z",
        "metadata": {"vertical": "billing"},
    }
    with pytest.raises(ValidationError) as exc_info:
        TicketIngestRequest.model_validate(payload)
    assert "ticket_id" in str(exc_info.value)


def test_ticket_ingest_extra_fields_forbidden():
    payload = {
        "source_type": "ticket",
        "ticket_id": "TKT-2026-000123",
        "customer_id": "CUST-88231",
        "channel": "voice",
        "raw_text": "Hello world",
        "language": "english",
        "received_at": "2026-10-05T10:15:00Z",
        "metadata": {"vertical": "billing"},
        "unsupported_extra_key": "forbidden_value",
    }
    with pytest.raises(ValidationError) as exc_info:
        TicketIngestRequest.model_validate(payload)
    assert "extra_fields" in str(exc_info.value) or "unsupported_extra_key" in str(exc_info.value)


# ============================================================================
# 2. RAG QUERY CONTRACT TESTS (§1.2)
# ============================================================================

def test_rag_query_request_valid():
    req = RagQueryRequest(query="flight refund policy", vertical=Vertical.FLIGHT, top_k=3, mode=RagMode.HYBRID)
    assert req.query == "flight refund policy"
    assert req.top_k == 3


@pytest.mark.parametrize("top_k", [0, 11])
def test_rag_query_top_k_bounds(top_k):
    with pytest.raises(ValidationError):
        RagQueryRequest(query="flight refund policy", top_k=top_k)


def test_rag_query_empty_query_fails():
    with pytest.raises(ValidationError):
        RagQueryRequest(query="")


# ============================================================================
# 3. ANALYTICS EXPORT CONTRACT TESTS (§1.3)
# ============================================================================

def test_analytics_export_date_validation():
    # to_date earlier than from_date
    with pytest.raises(ValidationError) as exc:
        AnalyticsExportRequestParams(from_date=date(2026, 10, 5), to_date=date(2026, 10, 1))
    assert "to_date" in str(exc.value)

    # range > 92 days
    with pytest.raises(ValidationError) as exc:
        AnalyticsExportRequestParams(from_date=date(2026, 1, 1), to_date=date(2026, 6, 1))
    assert "92 days" in str(exc.value)


def test_analytics_export_row_valid():
    row_data = {
        "interaction_id": "INT-000001",
        "session_id": "S-7K2M9QX4TA",
        "ticket_id": "TKT-2026-000123",
        "customer_ref": "a1b2c3d4e5f6",
        "agent_id": "AG-17",
        "client": "AirlineX",
        "vertical": "flight",
        "channel": "voice",
        "intent": "flight_disruption",
        "language": "hinglish",
        "start_ts": "2026-10-05T10:15:00Z",
        "end_ts": "2026-10-05T10:21:52Z",
        "handle_time_sec": 412,
        "hold_sec": 55,
        "acw_sec": 40,
        "first_contact_resolved": True,
        "sla_met": True,
        "risk_score_max": 0.88,
        "escalation_probability_max": 0.81,
        "churn_risk_class": "HIGH",
        "sentiment_avg": -0.45,
        "escalated": True,
        "compliance_score": 86,
        "critical_flags": 1,
        "warning_flags": 2,
        "info_flags": 0,
        "violated_rule_ids": "C-RECDISC;C-GREET",
        "ai_suggestion_outcome": "EDIT",
        "ai_confidence": 0.74,
        "llm_provider": "groq",
        "fallback_used": False,
        "ekyc_verified": False,
        "past_escalation_count": 2,
    }
    row = AnalyticsExportRow.model_validate(row_data)
    assert row.customer_ref == "a1b2c3d4e5f6"
    assert row.churn_risk_class == ChurnRiskClass.HIGH


# ============================================================================
# 4. AUTH LOGIN CONTRACT TESTS (§1.5)
# ============================================================================

def test_login_request_valid():
    req = LoginRequest(username="agent1", password="securepassword123")
    assert req.username == "agent1"


def test_login_request_empty_password_fails():
    with pytest.raises(ValidationError):
        LoginRequest(username="agent1", password="")


# ============================================================================
# 5. HEALTH & ERROR ENVELOPE CONTRACT TESTS (§1.4 & §0.4)
# ============================================================================

def test_health_response_valid():
    health_data = {
        "status": "ok",
        "version": "1.0.0",
        "timestamp": "2026-10-05T10:20:00Z",
        "uptime_sec": 8123.5,
        "system": {
            "cpu_percent": 23.4,
            "cpu_count": 8,
            "ram_percent": 61.2,
            "ram_used_mb": 9812.0,
            "ram_total_mb": 16032.0,
            "process_rss_mb": 842.0,
            "thread_count": 37,
        },
        "websocket": {"active_connections": 12, "active_sessions": 9, "max_queue_depth": 3},
        "dependencies": {
            "redis": {"status": "ok", "latency_ms": 1.2},
            "chroma": {"status": "ok", "latency_ms": 6.8, "collection_count": 412},
        },
        "llm": {"active_provider": "groq", "fallback_active": False},
    }
    resp = HealthResponse.model_validate(health_data)
    assert resp.status == "ok"
    assert resp.system.cpu_percent == 23.4


def test_error_envelope_valid():
    err_data = {
        "error": {
            "code": "INVALID_PAYLOAD",
            "message": "raw_text: String should have at least 1 character",
            "request_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
            "details": [{"loc": ["body", "raw_text"], "msg": "String should have at least 1 character", "type": "string_too_short"}],
        }
    }
    resp = ErrorResponse.model_validate(err_data)
    assert resp.error.code == ErrorCode.INVALID_PAYLOAD
    assert len(resp.error.details) == 1
