# NexusCX — icd.md
**Interface Control Document (ICD) v1.0.** Scope: wire formats only (REST, WebSocket, binary frames, Redis, WEKA shapes, LangGraph state). Behavior, personas and visuals live in `SRS.md` / `design.md`.

**Authority:** this ICD is the single source of truth for names and shapes. Where it differs from earlier docs, this file wins (§0.3).

---

# 0. GLOBAL CONVENTIONS

## 0.1 Encoding & types
| Item | Rule |
|---|---|
| Text encoding | UTF-8; strings are Unicode NFC; control chars (except `\n`, `\t`) are stripped on ingest |
| Timestamps | ISO 8601 UTC with `Z` and millisecond precision: `2026-10-05T10:15:03.221Z`. Inputs with offsets (`+05:30`) are accepted and normalized to UTC |
| IDs | `ticket_id` `^TKT-\d{4}-\d{6}$` · `customer_id` `^CUST-\d{3,10}$` · `session_id` `^S-[A-Za-z0-9-]{1,40}$` · `*_id` (server) UUIDv4 unless stated |
| Floats | JSON numbers, `.` decimal, no `NaN`/`Infinity` (rejected) |
| Booleans | JSON `true`/`false` (CSV: `true`/`false`) |
| Enums | Case-sensitive exactly as listed |
| Nulls | A key is either present with a value or `null` (when marked *nullable*); unknown extra keys are rejected (`extra="forbid"`) on inbound, ignored by clients on outbound |
| Versioning | URL major (`/api/v1`); JSON messages on Redis carry `"v": 1`; WebSocket frames carry `"v": 1` |

## 0.2 Common HTTP headers
| Header | Dir | Required | Notes |
|---|---|---|---|
| `Authorization: Bearer <JWT>` | Req | All except `/health`, `/api/v1/auth/login` | HS256; claims `sub` (agent_id), `role` ∈ `agent|supervisor|director`, `iat`, `exp`, `jti` |
| `Content-Type: application/json; charset=utf-8` | Req | POST | Others → `415` |
| `Accept: application/json` (or `text/csv` on export) | Req | No | |
| `X-Request-ID` | Req/Resp | Optional in, always out | Client value (≤ 64 chars `[A-Za-z0-9._-]`) echoed, else server UUID |
| `Idempotency-Key` | Req | Optional (ingest) | ≤ 64 chars; replays within 24 h return the original response |
| `X-RateLimit-Limit` / `-Remaining` / `-Reset` | Resp | Always | 100 req/min per `sub`; `Reset` = epoch seconds |
| `Retry-After` | Resp | On `429`, `503` | Seconds |

## 0.3 Reconciliation with earlier documents (this ICD supersedes)
| Topic | Earlier docs | ICD |
|---|---|---|
| Ticket ingest | `POST /api/v1/ingest/ticket` | `POST /api/v1/tickets/ingest` |
| Health | `GET /api/v1/health`, `/api/v1/system/health` | `GET /health` |
| WS URL | `/ws/live-stream?session_id=…` | `/ws/live-stream/{session_id}?token=…` |
| WS envelope key | `type` (lowercase) | `frame_type` (UPPER_SNAKE) |
| Redis channels | `nexus:session:{id}`, `nexus:stream:{id}` | §3 patterns |
| HITL approval | REST `/sessions/{id}/send` | `AGENT_HITL_ACTION` WS frame (REST route removed) |
| WEKA features | `handle_time_sec, hold_count, transfer_count, vertical, …` | §4 (5 features, 2 outputs) |
| `AgentState` | Pydantic-typed fields | §5 `TypedDict` |

## 0.4 Error envelope (all non-2xx REST)
```json
{
  "error": {
    "code": "INVALID_PAYLOAD",
    "message": "raw_text: String should have at least 1 character",
    "request_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
    "details": [{"loc": ["body", "raw_text"], "msg": "String should have at least 1 character", "type": "string_too_short"}]
  }
}
```
`details` is optional (validation errors only). Stack traces, prompts, and customer text are never included.

| `error.code` | HTTP | Meaning |
|---|---|---|
| `BAD_REQUEST` | 400 | Malformed JSON / unparsable query string |
| `UNAUTHENTICATED` | 401 | Missing/invalid/expired JWT |
| `FORBIDDEN` | 403 | Role not permitted |
| `NOT_FOUND` | 404 | Unknown resource |
| `DUPLICATE_TICKET` | 409 | Same `ticket_id` with a different body |
| `PAYLOAD_TOO_LARGE` | 413 | Body > 64 KB |
| `UNSUPPORTED_MEDIA_TYPE` | 415 | Wrong `Content-Type` |
| `INVALID_PAYLOAD` | 422 | Schema/range validation failure |
| `RATE_LIMITED` | 429 | > 100 req/min per agent |
| `INTERNAL_ERROR` | 500 | Unhandled fault |
| `VECTOR_STORE_UNAVAILABLE` | 503 | ChromaDB unreachable |
| `LLM_UNAVAILABLE` | 503 | Groq, Gemini and Ollama all failed |
| `SERVICE_OVERLOADED` | 503 | `psutil` guard tripped (RSS > 2.5 GB or RAM > 85%); sends `Retry-After` |

---

# 1. REST API INTERFACE CONTRACTS

## 1.1 `POST /api/v1/tickets/ingest`
Ingests one ticket or email. Processing is asynchronous: the response confirms acceptance; results arrive on the WebSocket.

| Item | Value |
|---|---|
| Auth | JWT, roles `agent`, `supervisor` |
| Success | `202 Accepted` (new) · `200 OK` + `Idempotent-Replay: true` (replayed) |
| Max body | 64 KB |

**Request body**
| Field | Type | Req | Constraints |
|---|---|---|---|
| `source_type` | enum | yes | `ticket` \| `email` |
| `ticket_id` | string | yes | `^TKT-\d{4}-\d{6}$` |
| `customer_id` | string | yes | `^CUST-\d{3,10}$` |
| `channel` | enum | yes | `voice` \| `chat` \| `email` |
| `subject` | string | no | ≤ 200 chars |
| `raw_text` | string | yes | 1–8000 chars |
| `content_format` | enum | no | `text` (default) \| `html` (tags stripped, entities decoded) |
| `language` | enum | yes | `english` \| `hinglish` |
| `received_at` | datetime | yes | ISO 8601; not more than 5 min in the future |
| `metadata.vertical` | enum | yes | `billing` \| `technical` \| `flight` \| `ekyc` \| `shipment` \| `hr` |
| `metadata.hold_count` | int | no | 0–50, default 0 |
| `metadata.transfer_count` | int | no | 0–20, default 0 |
| `metadata.prior_tickets_30d` | int | no | ≥ 0, default 0 |
| `customer_profile.avg_handling_time_sec` | number | no | 0–7200 (WEKA input; server looks up by `customer_id` if omitted) |
| `customer_profile.past_escalation_count` | int | no | 0–50 |
| `customer_profile.ekyc_verified` | bool | no | |

```json
{
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
  "customer_profile": {"avg_handling_time_sec": 412, "past_escalation_count": 2, "ekyc_verified": false}
}
```
**Response `202`** — headers `Location: /api/v1/sessions/S-7K2M9QX4TA`, `X-Request-ID`
```json
{
  "session_id": "S-7K2M9QX4TA",
  "interaction_id": "INT-000001",
  "ticket_id": "TKT-2026-000123",
  "status": "queued",
  "ws_url": "ws://localhost:8000/ws/live-stream/S-7K2M9QX4TA",
  "created_at": "2026-10-05T04:45:00.512Z"
}
```
**Errors:** `400` `BAD_REQUEST` · `401` · `403` · `409` `DUPLICATE_TICKET` · `413` · `415` · `422` `INVALID_PAYLOAD` · `429` · `503` `SERVICE_OVERLOADED` / `LLM_UNAVAILABLE` · `500`.
Side effects: writes `session:{session_id}:state` (§3.3), publishes first frame set to Redis. `raw_text` is never logged.

---

## 1.2 `POST /api/v1/rag/query`
Direct hybrid search against the ChromaDB `sops` collection.

| Item | Value |
|---|---|
| Auth | JWT, roles `agent`, `supervisor` |
| Success | `200 OK` (including low-confidence results) |

**Request body**
| Field | Type | Req | Constraints |
|---|---|---|---|
| `query` | string | yes | 1–1000 chars |
| `vertical` | enum | no | Same enum as §1.1; omitted = all verticals |
| `top_k` | int | no | 1–10, default 3 |
| `mode` | enum | no | `hybrid` (default) \| `dense` \| `sparse` |
| `min_score` | number | no | 0.0–1.0, default 0.0 (drops results below) |

```json
{"query": "flight cancelled by airline, how long does refund take", "vertical": "flight", "top_k": 3, "mode": "hybrid"}
```
**Response `200`**
```json
{
  "query_id": "3f6d2f0e-8f64-4d0e-9a38-2a1b8d9c5f10",
  "collection": "sops",
  "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
  "mode": "hybrid",
  "results": [
    {
      "chunk_id": "flt_sop_v3_p14_c2",
      "text": "If an airline cancels a flight, the customer is entitled to a full refund within 7 working days.",
      "source": "flight_refund_sop.docx",
      "page": 14,
      "section_title": "Airline-initiated cancellations",
      "vertical": "flight",
      "sop_version": "v3",
      "dense_score": 0.81,
      "sparse_score": 0.64,
      "fused_score": 0.032,
      "score": 0.77
    }
  ],
  "confidence": 0.77,
  "manual_required": false,
  "message": null,
  "latency_ms": 38
}
```
| Field | Type | Notes |
|---|---|---|
| `results[].score` | number 0–1 | `0.7·dense + 0.3·sparse_normalized` |
| `results[].fused_score` | number | Raw RRF value (ordering key) |
| `confidence` | number 0–1 | `score` of the top result; `0.0` if no results |
| `manual_required` | bool | `true` when `confidence < 0.60` |
| `message` | string \| null | Exactly `"Low AI Confidence: Manual Agent Intervention Required"` when `manual_required` is `true`, else `null` |

**Errors:** `401` · `403` · `422` · `429` · `503` `VECTOR_STORE_UNAVAILABLE` · `500`.

---

## 1.3 `GET /api/v1/analytics/export`
Flat, nesting-free rows for PowerBI (`Get Data → Web` with a Bearer header, or `Text/CSV`).

| Item | Value |
|---|---|
| Auth | JWT, role `director` (`supervisor` allowed read-only) |
| Success | `200 OK` |

**Query parameters**
| Param | Type | Default | Constraints |
|---|---|---|---|
| `from` | date `YYYY-MM-DD` | — (required) | |
| `to` | date | — (required) | ≥ `from`; range ≤ 92 days |
| `format` | enum | `json` | `json` \| `csv` |
| `page` | int | 1 | ≥ 1 |
| `page_size` | int | 1000 | 1–5000 |
| `vertical` | enum | all | §1.1 enum |
| `client` | string | all | ≤ 64 chars |

**JSON response** — headers `X-Total-Count: 12873`
```json
{
  "page": 1, "page_size": 1000, "total": 12873, "next_page": 2,
  "generated_at": "2026-10-05T10:20:00.000Z",
  "rows": [
    {
      "interaction_id": "INT-000001", "session_id": "S-7K2M9QX4TA", "ticket_id": "TKT-2026-000123",
      "customer_ref": "a1b2c3d4e5f6", "agent_id": "AG-17", "client": "AirlineX",
      "vertical": "flight", "channel": "voice", "intent": "flight_disruption", "language": "hinglish",
      "start_ts": "2026-10-05T10:15:00.000Z", "end_ts": "2026-10-05T10:21:52.000Z",
      "handle_time_sec": 412, "hold_sec": 55, "acw_sec": 40,
      "first_contact_resolved": true, "sla_met": true,
      "risk_score_max": 0.88, "escalation_probability_max": 0.81, "churn_risk_class": "HIGH",
      "sentiment_avg": -0.45, "escalated": true,
      "compliance_score": 86, "critical_flags": 1, "warning_flags": 2, "info_flags": 0,
      "violated_rule_ids": "C-RECDISC;C-GREET",
      "ai_suggestion_outcome": "EDIT", "ai_confidence": 0.74,
      "llm_provider": "groq", "fallback_used": false,
      "ekyc_verified": false, "past_escalation_count": 2
    }
  ]
}
```
**Row field dictionary**
| Field | Type | Nullable | Notes |
|---|---|---|---|
| `interaction_id`, `session_id`, `ticket_id` | string | no | |
| `customer_ref` | string(12) | no | First 12 hex of `sha256(customer_id + EXPORT_SALT)`; raw IDs and PII are never exported |
| `agent_id`, `client` | string | no | |
| `vertical`, `channel`, `intent`, `language` | enum string | no | Enums as in §1.1 / intent enum in §5 |
| `start_ts`, `end_ts` | datetime | `end_ts` yes | UTC |
| `handle_time_sec`, `hold_sec`, `acw_sec` | int | no | Seconds ≥ 0 |
| `first_contact_resolved`, `sla_met`, `escalated`, `fallback_used`, `ekyc_verified` | bool | no | |
| `risk_score_max`, `escalation_probability_max` | float 0–1 | no | 2 decimals |
| `churn_risk_class` | enum | no | `LOW`\|`MEDIUM`\|`HIGH` |
| `sentiment_avg` | float −1…1 | no | |
| `compliance_score` | int 0–100 | no | |
| `critical_flags`, `warning_flags`, `info_flags`, `past_escalation_count` | int | no | |
| `violated_rule_ids` | string | no | `;`-delimited, `""` if none |
| `ai_suggestion_outcome` | enum | no | `ACCEPT`\|`EDIT`\|`OVERRIDE`\|`REJECT`\|`MANUAL_REQUIRED`\|`NONE` |
| `ai_confidence` | float 0–1 | yes | |
| `llm_provider` | enum | no | `groq`\|`gemini`\|`ollama` |

**CSV** (`Accept: text/csv` or `format=csv`): `Content-Type: text/csv; charset=utf-8`, RFC 4180, UTF-8 BOM, header row = field names above in the same order, booleans `true`/`false`, `Content-Disposition: attachment; filename="nexuscx_2026-10-01_2026-10-05_p1.csv"`.

**Errors:** `400` · `401` · `403` · `422` (`to < from`, range > 92 days, bad enum) · `429` · `500`.

---

## 1.4 `GET /health`
Unauthenticated liveness/metrics for Docker healthchecks (bound to localhost; contains no PII); exempt from rate limiting.

**Response `200`** (`status` `ok` or `degraded`) · **`503`** (`status` `down`, when Redis is unreachable)
```json
{
  "status": "ok",
  "version": "1.0.0",
  "timestamp": "2026-10-05T10:20:00.000Z",
  "uptime_sec": 8123,
  "system": {
    "cpu_percent": 23.4, "cpu_count": 8,
    "ram_percent": 61.2, "ram_used_mb": 9812, "ram_total_mb": 16032,
    "process_rss_mb": 842, "thread_count": 37
  },
  "websocket": {"active_connections": 12, "active_sessions": 9, "max_queue_depth": 3},
  "dependencies": {
    "redis":  {"status": "ok", "latency_ms": 1.2},
    "chroma": {"status": "ok", "latency_ms": 6.8, "collection_count": 412},
    "ollama": {"status": "ok", "latency_ms": 9.5},
    "groq":   {"status": "ok"},
    "weka":   {"status": "jvm"}
  },
  "llm": {"active_provider": "groq", "fallback_active": false}
}
```
| Field | Source / rule |
|---|---|
| `system.cpu_percent` | `psutil.cpu_percent(interval=None)` |
| `system.ram_percent` | `psutil.virtual_memory().percent` |
| `system.process_rss_mb` | `psutil.Process().memory_info().rss / 2**20` |
| `websocket.active_connections` | Open sockets in `ConnectionManager` |
| `dependencies.*.status` | `ok` \| `down` \| `open_circuit` (groq breaker) \| `unknown`; `weka.status` ∈ `jvm` \| `python_fallback` |
| `status` | `down` = Redis down; `degraded` = any other dependency not `ok`, RSS > 2.5 GB, or RAM > 85% |

---

## 1.5 Supporting endpoint: `POST /api/v1/auth/login`
Required by every authenticated contract above.
**Request:** `{"username": "agent1", "password": "string(1-128)"}`
**Response `200`:**
```json
{"access_token": "<JWT>", "token_type": "bearer", "expires_in": 28800, "role": "agent", "agent_id": "AG-17"}
```
**Errors:** `401` (`UNAUTHENTICATED`, identical message for unknown user and bad password) · `422` · `429`.

---

# 2. WEBSOCKET INTERFACE CONTRACTS

## 2.1 Connection
`ws://localhost:8000/ws/live-stream/{session_id}?token=<JWT>&last_seq=<int>`

| Part | Rule |
|---|---|
| `token` | Required. Browsers cannot set WS headers; the server MUST NOT log the query string |
| `last_seq` | Optional int ≥ 0; server replays retained frames with `seq > last_seq` |
| Auth failure | Server accepts the upgrade, sends `ERROR`(`UNAUTHENTICATED`), then closes **4401** (this makes the code readable by browsers; no data is sent before auth) |
| Role/session check | `agent` may join only sessions assigned to its `sub`; `supervisor` any; otherwise `ERROR`(`FORBIDDEN`) then close **4403** |
| Limits | ≤ 5 sockets per `sub`; text frame ≤ 64 KB; binary frame ≤ 65 556 B; ≤ 20 client frames/s |
| Heartbeat | Server `PING` every 20 s; client `PONG` within 10 s, else close **1011** |

**Close codes:** `1000` normal · `1001` server shutdown · `1008` policy (too many sockets) · `1009` frame too large · `1011` missed pong / internal · `4400` repeated malformed frames · `4401` auth failed · `4403` forbidden · `4429` frame-rate exceeded.

## 2.2 Frame envelope (every text frame, both directions)
```json
{
  "v": 1,
  "frame_type": "AGENT_SUGGESTION_UPDATE",
  "frame_id": "0b1f3c0e-6a1d-4f06-bb55-7c3f2a1c9d11",
  "session_id": "S-7K2M9QX4TA",
  "seq": 482,
  "ts": "2026-10-05T10:15:03.221Z",
  "payload": {}
}
```
| Field | Type | Rules |
|---|---|---|
| `v` | int | `1` |
| `frame_type` | enum | §2.3 list |
| `frame_id` | UUIDv4 | Unique per frame; client-generated for client frames |
| `session_id` | string | Must equal the URL `{session_id}`, else `ERROR`(`SESSION_MISMATCH`) |
| `seq` | int \| null | **Server→client:** strictly increasing per session (from `seq:session:{id}`); **client→server:** `null` |
| `ts` | datetime | Sender clock, UTC ms |
| `payload` | object | Type-specific, `extra="forbid"` |

## 2.3 Frame catalogue
| `frame_type` | Direction | Purpose |
|---|---|---|
| `CLIENT_TRANSCRIPT_CHUNK` | C→S | **Frame A** — text transcript chunk (binary variant in §2.4) |
| `AGENT_SUGGESTION_UPDATE` | S→C | **Frame B** — suggestion + SOP + confidence |
| `RISK_SCORE_UPDATE` | S→C | **Frame C** — WEKA prediction, sentiment, alert level |
| `AGENT_HITL_ACTION` | C→S | **Frame D** — Accept / Edit / Override / Reject |
| `SERVER_HELLO` | S→C | First frame after auth; replay info |
| `TRANSCRIPT_UPDATE` | S→C | Server echo of finalized/partial transcript lines to all subscribers |
| `COMPLIANCE_UPDATE` | S→C | Checklist + flags |
| `SYSTEM_NOTICE` | S→C | Provider failover, degraded mode, AI paused |
| `ACK` | S→C | Result of a client frame |
| `ERROR` | S→C | Protocol/validation error |
| `PING` / `PONG` | S→C / C→S | Heartbeat |

### Frame A — `CLIENT_TRANSCRIPT_CHUNK` (Client → Server)
| Payload field | Type | Constraints |
|---|---|---|
| `chunk_id` | UUIDv4 | Dedupe key (duplicate within a session is ignored, `ACK.status="duplicate"`) |
| `chunk_index` | int | ≥ 0, monotonically increasing per `speaker` |
| `speaker` | enum | `customer` \| `agent` |
| `content_type` | enum | `text` (audio uses binary frames, §2.4) |
| `text` | string | 1–2000 chars |
| `language` | enum | `english` \| `hinglish` |
| `is_final` | bool | `false` for partials (replaced by later chunk with the same `chunk_index`) |
| `audio_offset_ms` | int \| null | Offset from call start |
```json
{
  "v": 1, "frame_type": "CLIENT_TRANSCRIPT_CHUNK",
  "frame_id": "5c2f0a7e-3b1c-4c0e-9e0a-0b9f3d7a1e22", "session_id": "S-7K2M9QX4TA",
  "seq": null, "ts": "2026-10-05T10:15:02.900Z",
  "payload": {
    "chunk_id": "e7d9b0b4-9e0a-4f0b-8e55-1a2b3c4d5e6f", "chunk_index": 3, "speaker": "customer",
    "content_type": "text", "text": "Meri flight cancel ho gayi, refund kab milega?",
    "language": "hinglish", "is_final": true, "audio_offset_ms": 14200
  }
}
```
Server response: `ACK` (`status`: `accepted`\|`duplicate`\|`rejected`). A final customer chunk triggers the LangGraph run and risk re-score.

### Frame B — `AGENT_SUGGESTION_UPDATE` (Server → Client)
| Payload field | Type | Notes |
|---|---|---|
| `suggestion_id` | UUIDv4 | Referenced by Frame D |
| `turn_index` | int | Customer turn that produced it |
| `status` | enum | `ready` \| `manual_required` \| `revising` |
| `intent` | object | `{intent, sub_intent, confidence}`; `intent` ∈ `billing`\|`technical_support`\|`flight_disruption`\|`ekyc`\|`other` |
| `suggested_text` | string \| null | ≤ 120 words; `null` when `status="manual_required"` |
| `language` | enum | `english` \| `hinglish` |
| `sop_snippets` | array (≤ 3) | `{chunk_id, source, page, text, score}`; `text` ≤ 700 chars |
| `confidence` | object | `{retrieval, intent, overall}` each 0–1; `overall = retrieval × intent` |
| `low_confidence_message` | string \| null | Exact `"Low AI Confidence: Manual Agent Intervention Required"` when `overall < 0.60` |
| `recommended_actions` | array | `{action_id, tool, args, requires_approval, grounding_chunk_ids}`; `tool` ∈ `draft_email`\|`trigger_refund_api`\|`update_ticket_state`\|`schedule_callback`\|`verify_ekyc_checklist`; empty when manual |
| `blocking` | bool | `true` if any critical compliance flag unresolved (client MUST disable ACCEPT) |
| `llm_provider` | enum | `groq`\|`gemini`\|`ollama` |
| `fallback_active` | bool | `true` when not served by Groq |
| `latency_ms` | int | Graph run time |
```json
{
  "v": 1, "frame_type": "AGENT_SUGGESTION_UPDATE",
  "frame_id": "0b1f3c0e-6a1d-4f06-bb55-7c3f2a1c9d11", "session_id": "S-7K2M9QX4TA",
  "seq": 482, "ts": "2026-10-05T10:15:03.221Z",
  "payload": {
    "suggestion_id": "9a4c1c7e-52d5-4b0e-8d3e-1f0c2b7a6e90", "turn_index": 3, "status": "ready",
    "intent": {"intent": "flight_disruption", "sub_intent": "refund_status", "confidence": 0.93},
    "suggested_text": "Aapki flight airline ne cancel ki hai, isliye poora refund 7 working days mein aapke original payment method par aayega.",
    "language": "hinglish",
    "sop_snippets": [{"chunk_id": "flt_sop_v3_p14_c2", "source": "flight_refund_sop.docx", "page": 14,
                      "text": "If an airline cancels a flight, the customer is entitled to a full refund within 7 working days.", "score": 0.82}],
    "confidence": {"retrieval": 0.82, "intent": 0.93, "overall": 0.76},
    "low_confidence_message": null,
    "recommended_actions": [{"action_id": "a1", "tool": "trigger_refund_api",
      "args": {"pnr": "6E4X9Q", "amount_inr": 8450, "reason": "airline_cancellation"},
      "requires_approval": true, "grounding_chunk_ids": ["flt_sop_v3_p14_c2"]}],
    "blocking": false, "llm_provider": "groq", "fallback_active": false, "latency_ms": 940
  }
}
```

### Frame C — `RISK_SCORE_UPDATE` (Server → Client)
| Payload field | Type | Notes |
|---|---|---|
| `risk_score` | float 0–1 | Composite (2 decimals out; thresholds evaluated on the unrounded value rounded to 4 dp) |
| `alert_level` | enum | `LOW` (<0.50) \| `MEDIUM` (0.50–0.70) \| `HIGH` (0.70–0.85) \| `CRITICAL` (>0.85) |
| `alert_triggered` | bool | `true` only on the debounced edge (two consecutive > 0.85, or one > 0.92), not on every critical score |
| `weka` | object | `{churn_risk_class, class_probabilities:{LOW,MEDIUM,HIGH}, escalation_probability, model_id, model_name}`; `model_name` ∈ `random_forest`\|`j48`\|`j48_python_fallback` |
| `sentiment` | object | `{current, rolling_mean_3, negativity, label}`: `current`/`rolling_mean_3` −1…1; `negativity = (1 − rolling_mean_3)/2`; `label` ∈ `negative`\|`neutral`\|`positive` |
| `weights` | object | `{weka: 0.6, sentiment: 0.4}` — weights actually applied (default `risk = escalation_probability × weights.weka + negativity × weights.sentiment`) |
| `callback_ticket_id` | string \| null | Set when `alert_triggered` created an SLA callback |
| `computed_at` | datetime | |
```json
{
  "v": 1, "frame_type": "RISK_SCORE_UPDATE", "frame_id": "c83a8d3e-1b9b-4f0b-9b0a-2d8d3f0a1c01",
  "session_id": "S-7K2M9QX4TA", "seq": 483, "ts": "2026-10-05T10:15:03.480Z",
  "payload": {
    "risk_score": 0.88, "alert_level": "CRITICAL", "alert_triggered": true,
    "weka": {"churn_risk_class": "HIGH", "class_probabilities": {"LOW": 0.05, "MEDIUM": 0.20, "HIGH": 0.75},
             "escalation_probability": 0.88, "model_id": "rf_escalation_v1", "model_name": "random_forest"},
    "sentiment": {"current": -0.62, "rolling_mean_3": -0.55, "negativity": 0.775, "label": "negative"},
    "weights": {"weka": 0.6, "sentiment": 0.4},
    "callback_ticket_id": "CB-2026-000045", "computed_at": "2026-10-05T10:15:03.470Z"
  }
}
```

### Frame D — `AGENT_HITL_ACTION` (Client → Server)
| Payload field | Type | Constraints |
|---|---|---|
| `suggestion_id` | UUIDv4 | Must match an outstanding suggestion for this session (else `ERROR` `STALE_SUGGESTION`) |
| `action` | enum | `ACCEPT` \| `EDIT` \| `OVERRIDE` \| `REJECT` |
| `final_text` | string \| null | Required for `EDIT`/`OVERRIDE` (1–2000 chars); for `ACCEPT` must be `null` (server uses its stored draft); forbidden for `REJECT` |
| `approved_action_ids` | string[] | Subset of the suggestion's `recommended_actions[].action_id`; must be `[]` for `OVERRIDE` and `REJECT`. The server executes its own stored copies — client-supplied tool args are never trusted |
| `reason_code` | enum \| null | Required for `REJECT`: `inaccurate`\|`tone`\|`policy`\|`irrelevant`\|`other`; else `null` |
| `client_ts` | datetime | Click time |

`approved_by` is taken from the JWT `sub`; any client-sent identity is rejected.
```json
{
  "v": 1, "frame_type": "AGENT_HITL_ACTION", "frame_id": "f1b2c3d4-0a1b-4c2d-8e3f-4a5b6c7d8e9f",
  "session_id": "S-7K2M9QX4TA", "seq": null, "ts": "2026-10-05T10:15:09.100Z",
  "payload": {
    "suggestion_id": "9a4c1c7e-52d5-4b0e-8d3e-1f0c2b7a6e90", "action": "EDIT",
    "final_text": "Refund 7 working days mein aapke original payment method par aa jayega.",
    "approved_action_ids": ["a1"], "reason_code": null, "client_ts": "2026-10-05T10:15:09.080Z"
  }
}
```
**Server rules:** `ACCEPT` is refused (`ACK.status="rejected"`, `reason="BLOCKED_BY_COMPLIANCE"`) when `blocking=true` or the suggestion was `manual_required`. Each accepted action is written to `hitl_audit` and executed idempotently.

### Supporting frames
| Frame | Payload |
|---|---|
| `SERVER_HELLO` | `{"server_time", "session_status": "active\|paused\|ended", "seq_head": int, "replay_from": int, "replay_count": int, "replay_truncated": bool, "limits": {"max_text_bytes": 65536, "ping_interval_sec": 20, "pong_timeout_sec": 10}}` |
| `TRANSCRIPT_UPDATE` | `{chunk_id, chunk_index, speaker, text, language, is_final, stt_gap: bool}` |
| `COMPLIANCE_UPDATE` | `{score: int 0-100, blocking: bool, checklist: {"<RULE_ID>": "pending\|done\|violated"}, flags: [{rule_id, severity: "info\|warning\|critical", evidence_span, turn_index}]}` |
| `SYSTEM_NOTICE` | `{code: "PROVIDER_FALLBACK\|AI_PAUSED\|STT_DEGRADED\|SERVICE_OVERLOADED", message, provider: "groq\|gemini\|ollama\|null", degraded: bool}` |
| `ACK` | `{ack_frame_id, status: "accepted\|duplicate\|rejected", reason: string\|null, execution_results: [{action_id, status: "executed\|skipped\|failed", detail}]}` |
| `ERROR` | `{code, message, fatal: bool, ref_frame_id: UUID\|null}`; codes: `UNAUTHENTICATED`, `FORBIDDEN`, `SESSION_MISMATCH`, `INVALID_FRAME`, `STALE_SUGGESTION`, `BAD_BINARY_HEADER`, `RATE_LIMITED`, `INTERNAL_ERROR` |
| `PING` | `{}` (server `frame_id` is the ping id) |
| `PONG` | `{"ping_id": "<frame_id of the PING>"}` |

## 2.4 Binary audio frame (Client → Server, WebSocket opcode 0x2)
Big-endian (network order), fixed 20-byte header followed by the payload.

| Offset | Size | Field | Value |
|---|---|---|---|
| 0 | 4 | `magic` | ASCII `NXAU` = `4E 58 41 55` |
| 4 | 1 | `version` | `0x01` |
| 5 | 1 | `codec` | `0x01` PCM signed 16-bit LE · `0x02` G.711 µ-law |
| 6 | 2 | `sample_rate_hz` | uint16 — `8000` (`1F 40`) or `16000` (`3E 80`) |
| 8 | 1 | `channels` | `0x01` (mono only) |
| 9 | 1 | `speaker` | `0x01` customer · `0x02` agent |
| 10 | 2 | `reserved` | `00 00` |
| 12 | 4 | `chunk_seq` | uint32, increments per chunk per speaker |
| 16 | 4 | `payload_len` | uint32, 1–65 536 |
| 20 | N | `payload` | Raw samples (no container header) |

Example header (µ-law, 8 kHz, customer, chunk 7, 1000 bytes of audio ≈ 125 ms):
`4E 58 41 55 01 02 1F 40 01 01 00 00 00 00 00 07 00 00 03 E8`

```python
import struct
HDR = struct.Struct(">4sBBHBB2sII")      # 20 bytes
magic, ver, codec, rate, ch, spk, _res, seq, n = HDR.unpack(frame[:20])
assert magic == b"NXAU" and ver == 1 and ch == 1 and len(frame) == 20 + n
```
Server pipeline: validate header → buffer up to 30 s per speaker → µ-law decode if needed → resample to 16 kHz mono → wrap in WAV → Groq `whisper-large-v3-turbo` → emit `TRANSCRIPT_UPDATE` + publish to `channel:live:transcripts:{session_id}`. Header violations → `ERROR`(`BAD_BINARY_HEADER`, `fatal=false`); 5 violations in 10 s → close `4400`.

## 2.5 Ordering & replay
- Server→client frames get `seq` from `INCR seq:session:{session_id}` and are written to `stream:session:{session_id}:frames` **before** fan-out.
- Reconnect with `last_seq=N`: `SERVER_HELLO` first (`replay_from=N+1`), then retained frames in order, then live frames. If `N` is older than the oldest retained entry (500 max), `replay_truncated=true`.
- Per-socket send queue 200 frames; on overflow the oldest non-final `TRANSCRIPT_UPDATE` frames are dropped first; all other types are never dropped.

---

# 3. REDIS CONTRACTS

**Conventions:** keys lowercase, `:`-delimited, `{session_id}` / `{agent_id}` match §0.1 patterns; values UTF-8 JSON with `"v": 1` unless noted; every key has a TTL; Redis runs with AOF on (`maxmemory-policy volatile-lru` so only TTL keys are evicted).

## 3.1 Pub/Sub channels
| Channel | Publisher | Subscribers | Purpose |
|---|---|---|---|
| `channel:live:transcripts:{session_id}` | STT / ingest / client-chunk handler | WS manager, LangGraph runner, risk runner | Live transcript chunks |
| `channel:live:frames:{session_id}` | Graph runner, risk runner, compliance, notices | WS manager (all workers) | Server→client frames of §2.3 (full envelope JSON) |
| `channel:supervisor:alerts` | Risk runner | WS manager → every supervisor socket | Cross-session `Risk Score > 0.85` alerts |

**Channel 1 message** — `channel:live:transcripts:{session_id}`
```json
{
  "v": 1, "session_id": "S-7K2M9QX4TA", "chunk_id": "e7d9b0b4-9e0a-4f0b-8e55-1a2b3c4d5e6f",
  "chunk_index": 3, "speaker": "customer", "text": "Meri flight cancel ho gayi, refund kab milega?",
  "language": "hinglish", "is_final": true,
  "stt": {"provider": "groq", "model": "whisper-large-v3-turbo", "no_speech_prob": 0.02, "duration_ms": 3100},
  "audio_offset_ms": 14200, "ts": "2026-10-05T10:15:02.950Z"
}
```
`stt` is `null` for text-origin chunks. Ordering is by `(speaker, chunk_index)`; consumers ignore duplicate `chunk_id`s.

**Channel 2 message** — `channel:supervisor:alerts`
```json
{
  "v": 1, "alert_id": "6d0f5b1e-3c7a-4b8e-9f10-5a7c9e2d4b66", "session_id": "S-7K2M9QX4TA",
  "agent_id": "AG-17", "risk_score": 0.88, "alert_level": "CRITICAL",
  "weka": {"churn_risk_class": "HIGH", "escalation_probability": 0.88, "model_name": "random_forest"},
  "sentiment_negativity": 0.775, "callback_ticket_id": "CB-2026-000045",
  "triggered_at": "2026-10-05T10:15:03.470Z", "cooldown_until": "2026-10-05T10:17:03.470Z"
}
```
Published only when `alert_triggered=true` (debounced; at most once per session per 120 s). The WS manager forwards it to supervisors as a `SYSTEM_NOTICE`-independent `RISK_SCORE_UPDATE` carrying the alert (`session_id` of the alerting call).

## 3.2 Keyspace
| Key pattern | Type | TTL | Content / purpose |
|---|---|---|---|
| `session:{session_id}:state` | STRING (JSON) | **3600 s**, reset on every write (`SET … EX 3600`) | §3.3 |
| `stream:session:{session_id}:frames` | STREAM | 3600 s (re-`EXPIRE` on write) | `XADD … MAXLEN ~ 500 * seq <int> frame <JSON envelope>` |
| `seq:session:{session_id}` | STRING (int) | 3600 s | `INCR` counter for server `seq` |
| `idem:ingest:{idempotency_key}` | STRING (JSON) | 86400 s | `{request_hash, response_body, status}` |
| `ratelimit:agent:{agent_id}` | ZSET | 70 s | Sliding 60 s window; member = request id, score = epoch ms; limit 100 |
| `ratelimit:llm:groq` | HASH | 120 s | Token bucket `{tokens, updated_ms}` |
| `breaker:llm:{provider}` | STRING | **60 s** | `"open"`; presence means skip provider (`groq`\|`gemini`) |
| `alert:streak:{session_id}` | STRING (int) | 300 s | Consecutive risk readings > 0.85 |
| `alert:cooldown:{session_id}` | STRING | **120 s** | Set with `SET … NX EX 120`; blocks repeat alerts |
| `ws:conns:{agent_id}` | SET | 86400 s | Active connection ids (max 5) |
| `sys:metrics:latest` | HASH | 15 s | Last `psutil` sample (`cpu_percent`, `ram_percent`, `rss_mb`, `ws_count`) |
| `lg:checkpoint:{session_id}:*` | library-managed | 3600 s | LangGraph checkpoints (opaque; do not read directly) |

## 3.3 `session:{session_id}:state` schema
```json
{
  "v": 1,
  "session_id": "S-7K2M9QX4TA", "interaction_id": "INT-000001", "ticket_id": "TKT-2026-000123",
  "customer_id": "CUST-88231", "agent_id": "AG-17",
  "channel": "voice", "vertical": "flight", "language": "hinglish",
  "status": "active", "ai_paused": false,
  "created_at": "2026-10-05T10:15:00.000Z", "updated_at": "2026-10-05T10:15:03.480Z",
  "turn_index": 3, "last_seq": 483,
  "customer_profile": {"avg_handling_time_sec": 412.0, "past_escalation_count": 2, "ekyc_verified": false},
  "sentiment_history": [-0.40, -0.55, -0.62],
  "risk": {"latest": 0.88, "max": 0.88, "streak": 2, "last_alert_at": "2026-10-05T10:15:03.470Z"},
  "hitl": {"status": "pending", "suggestion_id": "9a4c1c7e-52d5-4b0e-8d3e-1f0c2b7a6e90"},
  "llm": {"provider": "groq", "fallback_active": false}
}
```
| Field | Type / rule |
|---|---|
| `status` | `active` \| `paused` \| `ended` |
| `sentiment_history` | ≤ 10 floats, most recent last |
| `hitl.status` | `pending` \| `accepted` \| `edited` \| `overridden` \| `rejected` \| `manual_required` |
| Write rule | Read-modify-write inside a Lua script or `WATCH/MULTI`; last-write-wins is not acceptable for `risk.streak` |
| Contains no raw transcript text | Transcripts live only in SQLite and the stream's frames |

---

# 4. WEKA MODEL INTERFACE CONTRACT

Two classifiers share one feature header; each has its own class attribute.
| Model id | File | Class attribute | Used for |
|---|---|---|---|
| `rf_churn_v1` | `models/rf_churn.model` | `churn_risk_class {LOW,MEDIUM,HIGH}` | `churn_risk_class`, `class_probabilities` |
| `rf_escalation_v1` | `models/rf_escalation.model` | `escalated {yes,no}` | `escalation_probability = P(yes)` |
| `j48_*_v1` | `models/j48_*.txt` | same | Python rule-translation fallback |

## 4.1 Input feature vector
| # | Name | ARFF type | Python type | Range / values | Source |
|---|---|---|---|---|---|
| 1 | `avg_handling_time_sec` | `numeric` | `float` | 0.0–7200.0 (values above are clipped) | Customer's historical AHT (`customer_profile`) |
| 2 | `past_escalation_count` | `numeric` | `float` (integer-valued) | 0–50 (clipped) | `customer_profile` |
| 3 | `customer_sentiment_score` | `numeric` | `float` | −1.0 to 1.0 (reject outside) | LLM sentiment, rolling mean of last 3 customer turns |
| 4 | `channel_type` | `{voice,chat,email}` | `str` | exactly one of the three | Ticket `channel` |
| 5 | `ekyc_verified` | `{true,false}` | `str` (`"true"`/`"false"`) | exactly one of the two | `customer_profile.ekyc_verified` (bool → lowercase string) |

**ARFF header (`train_churn.arff`)**
```
@relation nexuscx_risk_v1
@attribute avg_handling_time_sec numeric
@attribute past_escalation_count numeric
@attribute customer_sentiment_score numeric
@attribute channel_type {voice,chat,email}
@attribute ekyc_verified {true,false}
@attribute churn_risk_class {LOW,MEDIUM,HIGH}
@data
412,2,-0.62,voice,false,HIGH
95,0,0.40,chat,true,LOW
```
`train_escalation.arff` is identical except the last attribute: `@attribute escalated {yes,no}`.

**Python input dict**
```python
features: dict[str, float | str] = {
    "avg_handling_time_sec": 412.0,
    "past_escalation_count": 2.0,
    "customer_sentiment_score": -0.62,
    "channel_type": "voice",
    "ekyc_verified": "false",
}
```
**Instance encoding (order = ARFF declaration order; nominals are indices):**
`channel_type`: `voice=0, chat=1, email=2` · `ekyc_verified`: **`true=0, false=1`** (declaration order) · class `churn_risk_class`: `LOW=0, MEDIUM=1, HIGH=2` · `escalated`: `yes=0, no=1`.
```python
vector = [412.0, 2.0, -0.62, 0.0, 1.0]     # + class slot = Instance.missing_value()
```
**Validation (before inference):** all five keys present (missing optional numeric values use the `imputation` medians from the model card; `channel_type` and `ekyc_verified` have no imputation and are rejected if absent); numeric values finite; sentiment within range; nominal values exact (never silently remapped); violations raise `FeatureValidationError` → mapped to `422` / `manual_required`.

## 4.2 Output
```python
prediction: dict[str, object] = {
    "churn_risk_class": "HIGH",                                     # LOW | MEDIUM | HIGH (argmax of rf_churn_v1)
    "class_probabilities": {"LOW": 0.05, "MEDIUM": 0.20, "HIGH": 0.75},   # sums to 1.0 ± 1e-6
    "escalation_probability": 0.88,                                 # P(escalated=yes) from rf_escalation_v1
    "model_id": "rf_escalation_v1",
    "model_name": "random_forest",                                  # random_forest | j48 | j48_python_fallback
    "inference_ms": 4,
    "fallback": False,
}
```
| Field | Type | Range / rule |
|---|---|---|
| `churn_risk_class` | nominal | `LOW` \| `MEDIUM` \| `HIGH` |
| `class_probabilities.*` | float | 0.0–1.0 each |
| `escalation_probability` | float | **0.00–1.00**; rounded to 2 dp at API/WS boundaries, full precision internally |
| `fallback` | bool | `true` when the Python J48 translation answered (JVM unavailable) |

## 4.3 `models/model_card.json`
```json
{
  "schema_version": 1,
  "models": [
    {"model_id": "rf_churn_v1", "algorithm": "weka.classifiers.trees.RandomForest", "options": "-I 200 -depth 12 -S 42",
     "file": "rf_churn.model", "sha256": "<64 hex>", "class_attribute": "churn_risk_class"},
    {"model_id": "rf_escalation_v1", "algorithm": "weka.classifiers.trees.RandomForest", "options": "-I 200 -depth 12 -S 42",
     "file": "rf_escalation.model", "sha256": "<64 hex>", "class_attribute": "escalated"}
  ],
  "weka_version": "3.8.6", "trained_at": "2026-10-05T09:00:00Z",
  "data_source": "synthetic", "n_rows": 20000,
  "feature_order": ["avg_handling_time_sec", "past_escalation_count", "customer_sentiment_score", "channel_type", "ekyc_verified"],
  "nominal_maps": {"channel_type": ["voice", "chat", "email"], "ekyc_verified": ["true", "false"],
                   "churn_risk_class": ["LOW", "MEDIUM", "HIGH"], "escalated": ["yes", "no"]},
  "caps": {"avg_handling_time_sec": 7200, "past_escalation_count": 50},
  "imputation": {"avg_handling_time_sec": 480.0, "past_escalation_count": 0.0, "customer_sentiment_score": 0.0},
  "metrics": {"rf_churn_v1": {"roc_auc_macro": 0.0, "recall_high": 0.0}, "rf_escalation_v1": {"roc_auc": 0.0, "recall_yes": 0.0}}
}
```
At startup the loader MUST verify each file's SHA-256 against the card and refuse to load on mismatch; `feature_order` and `nominal_maps` are authoritative for encoding. Metric values above are placeholders filled by training.

---

# 5. LANGGRAPH INTERNAL STATE SCHEMA

```python
from typing import Annotated, Any, Dict, List, TypedDict
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    session_id: str
    messages: Annotated[List[BaseMessage], add_messages]   # append-only reducer (required so nodes append, not overwrite)
    customer_metadata: Dict[str, Any]
    retrieved_sops: List[Dict[str, Any]]
    compliance_flags: Dict[str, bool]
    weka_risk_score: float
    agent_confidence: float
    recommended_action: Dict[str, Any]
    fallback_active: bool
```
All nine keys are always present (initialized per 5.3); nodes return partial dicts containing only the keys they own.

## 5.1 Required shapes of the `Dict[str, Any]` fields
Validated with Pydantic at every node boundary (never trust raw dicts):
```python
class CustomerMetadata(TypedDict):          # AgentState.customer_metadata
    ticket_id: str
    customer_id: str
    channel: str                            # "voice" | "chat" | "email"
    vertical: str                           # §1.1 enum
    language: str                           # "english" | "hinglish"
    hold_count: int
    transfer_count: int
    prior_tickets_30d: int
    avg_handling_time_sec: float            # WEKA input 1
    past_escalation_count: int              # WEKA input 2
    ekyc_verified: bool                     # WEKA input 5
    intent: str                             # "billing"|"technical_support"|"flight_disruption"|"ekyc"|"other"
    sub_intent: str
    intent_confidence: float                # 0.0-1.0
    sentiment: float                        # -1.0..1.0 (latest customer turn)
    urgency: str                            # "low"|"medium"|"high"

class RetrievedSop(TypedDict):              # each item of AgentState.retrieved_sops (max 3)
    chunk_id: str
    text: str                               # <= 700 chars
    source: str
    page: int
    vertical: str
    score: float                            # 0.0-1.0

class ToolCallDict(TypedDict):
    action_id: str                          # "a1", "a2", ...
    tool: str                               # draft_email | trigger_refund_api | update_ticket_state | schedule_callback | verify_ekyc_checklist
    args: Dict[str, Any]
    requires_approval: bool                 # always True in v1
    grounding_chunk_ids: List[str]          # non-empty, subset of retrieved_sops chunk_ids

class RecommendedAction(TypedDict):         # AgentState.recommended_action
    status: str                             # "ready" | "manual_required" | "revising"
    suggested_text: str | None
    tool_calls: List[ToolCallDict]
    revision_count: int                     # 0-2; guardrail loop bound
    low_confidence_message: str | None
```
## 5.2 Field semantics & write ownership
| Field | Written by | Semantics |
|---|---|---|
| `session_id` | entry | Immutable; equals WS/Redis `session_id` |
| `messages` | entry, executor | Conversation turns; reducer appends |
| `customer_metadata` | entry (profile/ticket), `intent_router` (intent, sentiment) | Per §5.1 |
| `retrieved_sops` | `rag_retriever` | Top-3 by fused score; `[]` if none |
| `compliance_flags` | `compliance_guardrail` | `{rule_id: violated}`: `true` = violation detected, `false` = checked and clear; absent = not evaluated. Severity comes from the static rule catalog, not the state |
| `weka_risk_score` | risk runner (parallel to graph) | Composite risk 0.0–1.0 (the `risk_score` of Frame C); `0.0` until first computation |
| `agent_confidence` | `rag_retriever` | `retrieval_confidence × customer_metadata.intent_confidence`, 0.0–1.0 |
| `recommended_action` | `backoffice_executor`, `manual_required` | Per `RecommendedAction`; `status="manual_required"` iff `agent_confidence < 0.60` |
| `fallback_active` | `llm_router` (via any node) | `true` if the most recent LLM call was served by Gemini or Ollama |

## 5.3 Initial state
```python
initial: AgentState = {
    "session_id": "S-7K2M9QX4TA",
    "messages": [HumanMessage(content="Meri flight cancel ho gayi, refund kab milega?")],
    "customer_metadata": {...},             # §5.1, intent fields default to "other"/0.0/0.0/"low"
    "retrieved_sops": [],
    "compliance_flags": {},
    "weka_risk_score": 0.0,
    "agent_confidence": 0.0,
    "recommended_action": {"status": "revising", "suggested_text": None, "tool_calls": [],
                           "revision_count": 0, "low_confidence_message": None},
    "fallback_active": False,
}
```
## 5.4 Transitions (state-contract view)
| From → To | Condition (reads) |
|---|---|
| `intent_router` → `rag_retriever` | always |
| `rag_retriever` → `backoffice_executor` | `agent_confidence >= 0.60` |
| `rag_retriever` → `manual_required` | `agent_confidence < 0.60` |
| `backoffice_executor`, `manual_required` → `compliance_guardrail` | always |
| `compliance_guardrail` → `backoffice_executor` | any `compliance_flags[r] is True` with critical severity **and** `recommended_action.revision_count < 2` (executor increments `revision_count`) |
| `compliance_guardrail` → `END` | otherwise; invoke with `recursion_limit=12` |

**Mapping to wire frames:** `recommended_action` + `retrieved_sops` + `agent_confidence` → Frame B; `weka_risk_score` + WEKA output → Frame C; `compliance_flags` → `COMPLIANCE_UPDATE`; `fallback_active` → `SYSTEM_NOTICE` and Frame B `fallback_active`.

---

# 6. CHANGE CONTROL
- Any change to a field name, type, enum, key pattern, or byte offset requires: (1) a version bump (`v`, URL major, or `schema_version`), (2) an update to this file, (3) updated contract tests (`tdd.md`).
- Additive optional fields are allowed within a version; removals and renames are not.
