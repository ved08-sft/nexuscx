# NexusCX — Software Requirements Specification (SRS)
**IEEE Std 830-1998 structure** | Version 1.0 | Client: MAS Callnet India Pvt. Ltd. | Companion: `ARCHITECTURE.md`

Requirement keywords: **SHALL** = mandatory, **SHOULD** = recommended. Each requirement has an ID for traceability (Appendix B).

---

# SECTION 1: INTRODUCTION

## 1.1 Purpose & Scope
This SRS defines the functional and non-functional requirements of **NexusCX: Next-Gen Autonomous Back-Office & Quality Intelligence Engine**, an extension to MAS Callnet's CallMaster™ platform. NexusCX SHALL:
- ingest voice transcripts and text tickets (English/Hinglish);
- run a LangGraph multi-agent pipeline (intent, SOP retrieval, back-office action proposals, compliance audit);
- compute a real-time escalation risk score (WEKA model + sentiment);
- present suggestions to human agents and live risk to supervisors under Human-in-the-Loop control;
- export flat analytics for PowerBI Desktop.

**In scope:** web apps, API, WebSocket layer, ML pipeline, mock back-office APIs, analytics export.
**Out of scope:** telephony/SIP, production CallMaster™ integration (replaced by file/stream adapters), autonomous sending without approval, payment processing.

**Cost constraint (CON-1):** All components SHALL be open-source or free-tier: Next.js, FastAPI, LangGraph, Groq free tier, Google AI Studio free tier, Ollama, ChromaDB, WEKA, Redis, Docker, PowerBI Desktop.

## 1.2 Target Audience & Product Overview
| Role | Interaction |
|---|---|
| BPO support agent | Workstation: reviews AI draft, accepts/edits/rejects, sees SOP and compliance progress |
| QA supervisor | Live grid, risk alerts, Whisper/Barge-in, compliance scorecards |
| Operations manager / account manager | PowerBI dashboards via export API |
| Developer / ML engineer | Trains WEKA models, maintains SOP corpus |

## 1.3 Definitions
| Term | Meaning |
|---|---|
| HITL | Human-in-the-Loop: human approval before any customer-facing action |
| RAG | Retrieval-Augmented Generation |
| AHT | Average Handling Time = (talk + hold + after-call work) per interaction |
| FCR | First Contact Resolution |
| SOP | Standard Operating Procedure document |
| Risk Score (R) | Escalation probability index in [0,1] |

## 1.4 References
IEEE 830-1998; LangGraph, FastAPI, Pydantic v2, ChromaDB, WEKA 3.8 documentation; RFC 6455 (WebSocket).

## 1.5 Assumptions & Dependencies
- Historical call data may be synthetic during development (flagged in model card).
- Groq/Gemini free-tier rate limits apply; Ollama is the guaranteed fallback.
- PowerBI Desktop requires Windows; macOS/Linux users use the CSV export and any free BI viewer.

---

# SECTION 2: FUNCTIONAL REQUIREMENTS & DATA SCHEMAS

## 2.1 Inputs & Supported Formats
| ID | Input | Format | Processing |
|---|---|---|---|
| IN-1 | Audio | `.wav`, `.mp3`, 8 kHz telephone; ≤ 25 MB per chunk | `ffmpeg` resample to 16 kHz mono -> Groq `whisper-large-v3-turbo` (`verbose_json`); segments with `no_speech_prob > 0.6` dropped |
| IN-2 | Text ticket | JSON, UTF-8, `raw_text` 1–8000 chars, `language` ∈ {`english`,`hinglish`} | Pydantic validation; reject with 422 |
| IN-3 | SOP documents | `.pdf`, `.docx` | `pypdf`/`python-docx` -> 700-char chunks, 120 overlap -> ChromaDB with MiniLM embeddings |
| IN-4 | Training data | `.csv` -> `.arff` | Used offline by WEKA |

## 2.2 Data Schemas

### 2.2.1 Python (Pydantic v2)
```python
from __future__ import annotations
from typing import Annotated, Literal, Optional, TypedDict
from datetime import datetime
from pydantic import BaseModel, Field, field_validator
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

Channel = Literal["voice", "chat", "email"]
Language = Literal["english", "hinglish"]
Vertical = Literal["billing", "technical", "flight", "ekyc", "shipment", "hr"]

class TicketMetadata(BaseModel):
    hold_count: int = Field(0, ge=0, le=50)
    transfer_count: int = Field(0, ge=0, le=20)
    prior_tickets_30d: int = Field(0, ge=0)
    vertical: Vertical

class TicketPayload(BaseModel):
    ticket_id: str = Field(pattern=r"^TKT-\d{4}-\d{6}$")
    customer_id: str = Field(pattern=r"^CUST-\d{3,10}$")
    channel: Channel
    raw_text: str = Field(min_length=1, max_length=8000)
    language: Language
    timestamp: datetime
    metadata: TicketMetadata

    @field_validator("raw_text")
    @classmethod
    def strip_ctrl(cls, v: str) -> str:
        return "".join(ch for ch in v if ch.isprintable() or ch in "\n\t")

class IntentResult(BaseModel):
    intent: Literal["billing", "technical_support", "flight_disruption", "ekyc", "other"]
    sub_intent: str = Field(max_length=64)
    confidence: float = Field(ge=0, le=1)
    sentiment: float = Field(ge=-1, le=1)
    urgency: Literal["low", "medium", "high"]

class RetrievedDoc(BaseModel):
    chunk_id: str; text: str; source: str; page: int
    score: float = Field(ge=0, le=1)

class ToolCall(BaseModel):
    tool: Literal["draft_email", "trigger_refund_api", "update_ticket_state",
                  "schedule_callback", "verify_ekyc_checklist"]
    args: dict
    requires_approval: bool = True
    grounding_chunk_ids: list[str] = Field(min_length=1)

class ComplianceFlag(BaseModel):
    rule_id: str
    severity: Literal["info", "warning", "critical"]
    evidence_span: str
    turn_index: int

class ComplianceReport(BaseModel):
    session_id: str
    flags: list[ComplianceFlag]
    checklist: dict[str, bool]          # e.g. {"greeting": True, "recording_disclosure": False}
    score: int = Field(ge=0, le=100)    # 100 - (10*critical + 4*warning + 1*info), floor 0
    blocking: bool                      # True if any critical flag

class WekaRiskScore(BaseModel):
    session_id: str
    p_weka: float = Field(ge=0, le=1)
    s_neg: float = Field(ge=0, le=1)
    t_hold: float = Field(ge=0, le=1)
    risk: float = Field(ge=0, le=1)
    band: Literal["low", "medium", "high", "critical"]
    model_name: Literal["random_forest", "j48", "j48_python_fallback"]
    computed_at: datetime

class AgentState(TypedDict):
    session_id: str
    messages: Annotated[list[BaseMessage], add_messages]
    customer_metadata: TicketMetadata
    intent: Optional[IntentResult]
    retrieved_docs: list[RetrievedDoc]
    proposed_reply: Optional[str]
    proposed_actions: list[ToolCall]
    compliance_flags: list[ComplianceFlag]
    agent_confidence_score: float
    retries: int
    hitl_status: Literal["pending", "accepted", "edited", "rejected", "manual_required"]
    llm_provider_used: Literal["groq", "gemini", "ollama"]

class WebSocketMessage(BaseModel):
    type: Literal["transcript", "suggestion", "risk_alert", "compliance_update",
                  "supervisor_whisper", "system", "ping", "pong"]
    session_id: str
    seq: int = Field(ge=0)
    ts: datetime
    payload: dict
```

### 2.2.2 TypeScript (`frontend/src/lib/types.ts`)
```ts
export type Channel = "voice" | "chat" | "email";
export type Band = "low" | "medium" | "high" | "critical";
export type HitlStatus = "pending" | "accepted" | "edited" | "rejected" | "manual_required";

export interface TicketPayload {
  ticket_id: string; customer_id: string; channel: Channel; raw_text: string;
  language: "english" | "hinglish"; timestamp: string;
  metadata: { hold_count: number; transfer_count: number; prior_tickets_30d: number; vertical: string };
}
export interface ToolCall {
  tool: "draft_email" | "trigger_refund_api" | "update_ticket_state" | "schedule_callback" | "verify_ekyc_checklist";
  args: Record<string, unknown>; requires_approval: boolean; grounding_chunk_ids: string[];
}
export interface ComplianceReport {
  session_id: string; score: number; blocking: boolean;
  flags: { rule_id: string; severity: "info" | "warning" | "critical"; evidence_span: string; turn_index: number }[];
  checklist: Record<string, boolean>;
}
export interface WekaRiskScore {
  session_id: string; p_weka: number; s_neg: number; t_hold: number; risk: number;
  band: Band; model_name: string; computed_at: string;
}
export interface AgentStateView {
  session_id: string; intent?: { intent: string; confidence: number; sentiment: number };
  retrieved_docs: { chunk_id: string; text: string; source: string; page: number; score: number }[];
  proposed_reply?: string; proposed_actions: ToolCall[];
  agent_confidence_score: number; hitl_status: HitlStatus; llm_provider_used: string;
}
export type WebSocketMessage =
  | { type: "transcript"; session_id: string; seq: number; ts: string; payload: { speaker: "agent" | "customer"; text: string; final: boolean } }
  | { type: "suggestion"; session_id: string; seq: number; ts: string; payload: AgentStateView }
  | { type: "risk_alert"; session_id: string; seq: number; ts: string; payload: WekaRiskScore }
  | { type: "compliance_update"; session_id: string; seq: number; ts: string; payload: ComplianceReport }
  | { type: "supervisor_whisper"; session_id: string; seq: number; ts: string; payload: { text: string; from: string } }
  | { type: "system"; session_id: string; seq: number; ts: string; payload: { provider?: string; degraded?: boolean; message?: string } }
  | { type: "ping" | "pong"; session_id: string; seq: number; ts: string; payload: Record<string, never> };
```

## 2.3 Module Functional Requirements

### FR-1: LangGraph Agentic Engine
**Graph:** `intent_router -> rag_retriever -> {backoffice_executor | manual_required} -> compliance_guardrail -> {END | backoffice_executor (revise loop)}`

| ID | Requirement |
|---|---|
| FR-1.1 | The system SHALL classify each customer turn into `IntentResult` using Groq `llama-3.3-70b-versatile` at `temperature=0` with JSON output validated by Pydantic. |
| FR-1.2 | On schema failure the Intent node SHALL retry once with the validation error appended; on second failure it SHALL set `intent="other"`, `confidence=0.0` and route to `manual_required`. |
| FR-1.3 | The RAG node SHALL perform hybrid retrieval: dense top-8 (Chroma cosine) + BM25 top-8, merged by Reciprocal Rank Fusion `RRF(d)=Σ 1/(60+rank_i(d))`, filtered by `vertical`, returning top-3 chunks. |
| FR-1.4 | Retrieval confidence SHALL be `0.7*dense_similarity + 0.3*bm25_normalized` for the top chunk; `agent_confidence_score = retrieval_confidence * intent.confidence`. |
| FR-1.5 | If `agent_confidence_score < 0.60` the graph SHALL route to `manual_required`, emit no draft and no tool calls. |
| FR-1.6 | The Executor SHALL produce `proposed_reply` (≤ 120 words, in the customer's language) and zero or more `ToolCall`s; each ToolCall SHALL include non-empty `grounding_chunk_ids`, else it is discarded. |
| FR-1.7 | The Executor SHALL NOT perform side effects; tool calls execute only after human approval via `POST /api/v1/sessions/{id}/send`. Execution SHALL be idempotent using key `sha256(session_id+tool+canonical_args)`. |
| FR-1.8 | Refund tool calls above the SOP-defined threshold SHALL force `hitl_status="manual_required"`. |
| FR-1.9 | The Guardrail SHALL run deterministic checks (greeting within first 2 agent turns, prohibited terms, mandatory disclosures) in < 10 ms, plus an LLM tone/PII check. |
| FR-1.10 | A `critical` flag SHALL set `blocking=true`, and trigger at most 2 revise cycles (`recursion_limit=12`); if still critical, the draft is shown with Accept disabled. |
| FR-1.11 | Graph state SHALL be checkpointed in Redis keyed by `session_id` and resume after service restart. |
| FR-1.12 | LLM provider chain SHALL be Groq -> Gemini 2.5 Flash -> Ollama with a circuit breaker (60 s open). Provider used SHALL be recorded in `llm_provider_used`. |

**Compliance rules (seed set):**
| rule_id | Check | Severity |
|---|---|---|
| C-GREET | Greeting present | warning |
| C-RECDISC | Call-recording disclosure given | critical |
| C-IDVER | Identity verification before account data | critical |
| C-PROHIB | Prohibited phrase ("guaranteed", "100% refund", abusive terms) | critical |
| C-PII | PII in draft (Aadhaar/PAN/card regex) | critical |
| C-CLOSE | Closing/summary statement | info |

### FR-2: WEKA Risk Classifier
| ID | Requirement |
|---|---|
| FR-2.1 | Features SHALL be: `handle_time_sec`, `sentiment_score`, `past_ticket_freq_30d`, `hold_count`, `transfer_count`, `vertical`; class `escalated ∈ {yes,no}`. |
| FR-2.2 | Training SHALL use WEKA `RandomForest -I 200 -depth 12 -S 42` and `J48 -C 0.25 -M 5`, 10-fold CV; acceptance: ROC-AUC ≥ 0.85, recall(yes) ≥ 0.75. |
| FR-2.3 | Inference SHALL return `P_weka = distribution[yes]` via `python-weka-wrapper3`; on JVM failure the system SHALL use the Python J48 rule translation and set `model_name="j48_python_fallback"`. |
| FR-2.4 | **Risk formula:** `R = clip(0.55·P_weka + 0.30·S_neg + 0.15·T_hold, 0, 1)` where `S_neg=(1−sentiment)/2` (rolling mean of last 3 customer turns) and `T_hold=min(hold_count/3,1)`. |
| FR-2.5 | Bands: Low `<0.50`, Medium `0.50–0.70`, High `0.70–0.85`, Critical `>0.85`. |
| FR-2.6 | **AHT:** `AHT = Σ(talk_sec + hold_sec + acw_sec) / N_interactions`. **AHT reduction %** = `(AHT_baseline − AHT_nexus)/AHT_baseline × 100`; target ≥ 25%. |
| FR-2.7 | **Alert trigger:** when `R > 0.85` on two consecutive evaluations (or one evaluation `> 0.92`), the system SHALL publish `risk_alert`, mark the supervisor tile red, and create a `schedule_callback` ticket `{priority:"P1", sla_minutes:30}`. Cooldown 120 s per session. |
| FR-2.8 | Re-scoring SHALL occur on every customer turn and every 15 s of call time (30 s under CPU > 90%). |
| FR-2.9 | Each score SHALL be persisted to `risk_events`. |

### FR-3: Next.js Frontend Dashboards
| ID | Requirement |
|---|---|
| FR-3.1 | **Workstation** (`/workstation/[sessionId]`) SHALL use a 3-panel layout: Left live transcript; Center AI suggestion; Right SOP context + compliance progress. |
| FR-3.2 | Center panel SHALL provide **Accept** (send reply + approve tool calls), **Edit** (inline textarea; diff logged), **Reject** (mandatory reason code from enum: `inaccurate`, `tone`, `policy`, `irrelevant`, `other`). |
| FR-3.3 | **Override:** agent SHALL be able to type a fully manual response and delete any tool call; a "Pause AI" toggle SHALL stop graph invocation for that session. |
| FR-3.4 | Accept SHALL be disabled when `blocking=true` or `hitl_status="manual_required"`. |
| FR-3.5 | Compliance progress bar SHALL show `completed_mandatory/total_mandatory`; critical flags render red. |
| FR-3.6 | **Supervisor** (`/supervisor`) SHALL display a live grid card per active session: agent, customer ID, duration, intent, risk gauge, compliance score, provider badge; sorted by risk descending; red pulse + chime at `R>0.85`. |
| FR-3.7 | Supervisor actions: **Whisper** (message visible only to the agent), **Barge-in** (notifies agent, joins thread), **Open transcript**. |
| FR-3.8 | UI SHALL access the backend through a `useLiveStream` hook implementing backoff reconnect (1 s -> 30 s, ±20% jitter) and `last_seq` replay. |
| FR-3.9 | RBAC SHALL be enforced: roles `agent`, `supervisor`, `director` (JWT claim `role`); unauthorized routes return 403. |
| FR-3.10 | UI SHALL show a degraded-mode badge when `system` message has `degraded=true`. |

### FR-4: Human-in-the-Loop & Fail-Safes
| ID | Requirement |
|---|---|
| FR-4.1 | If retrieval confidence `< 0.60` (or intent confidence `< 0.60`) the UI SHALL display exactly: **"Low AI Confidence: Manual Agent Intervention Required"**; AI generation is suppressed. |
| FR-4.2 | No customer-facing message or tool execution SHALL occur without an `approved_by` agent ID stored in `hitl_audit`. |
| FR-4.3 | All edits/rejections SHALL be stored as `{original, final, outcome, reason_code, ts}`. |
| FR-4.4 | On Groq 429/5xx/timeout (2.5 s) or disconnect, the LLM router SHALL switch to Gemini, then Ollama (`llama3.1:8b`) such that total switchover from fault detection is ≤ 500 ms, without closing the agent's WebSocket. |
| FR-4.5 | Ollama outputs SHALL pass the same Pydantic validation; invalid output -> `manual_required`. |
| FR-4.6 | If STT fails for a chunk, the transcript SHALL show a gap marker and `stt_gap=true` SHALL be stored. |
| FR-4.7 | All provider switches SHALL be logged and surfaced as `system` WS messages. |

### FR-5: PowerBI Reporting Schema
**Endpoint:** `GET /api/v1/analytics/export` — role `director`. Query: `from`, `to` (ISO date), `format` (`json`|`csv`), `page`, `page_size ≤ 5000`.

**Response (flat, no nesting):**
```json
{
  "page": 1, "page_size": 5000, "total": 12873,
  "rows": [{
    "interaction_id": "INT-000001", "ticket_id": "TKT-2026-000123", "agent_id": "AG-17",
    "client": "AirlineX", "vertical": "flight", "channel": "voice", "intent": "flight_disruption",
    "start_ts": "2026-10-05T10:15:00Z", "handle_time_sec": 412, "hold_sec": 55, "acw_sec": 40,
    "first_contact_resolved": true, "sla_met": true,
    "risk_score_max": 0.88, "p_weka": 0.81, "sentiment_avg": -0.45, "escalated": true,
    "compliance_score": 86, "critical_flags": 1, "warning_flags": 2,
    "violated_rule_ids": "C-RECDISC", "ai_suggestion_outcome": "edited",
    "ai_confidence": 0.74, "llm_provider": "groq", "churn_probability": 0.62
  }]
}
```
**Derived fields:** `sla_met = handle_time_sec ≤ vertical_sla_sec`; `churn_probability = 0.6*p_weka + 0.4*S_neg` (documented proxy).

**Required PowerBI views**
| # | View | Visuals / measures |
|---|---|---|
| 1 | Executive SLA & FCR | KPI cards: `SLA% = AVERAGE(sla_met)`, `FCR%`, AHT, escalation rate; daily line chart; slicers (client, vertical) |
| 2 | QA Compliance & Script Deviation Heatmap | Matrix `violated_rule_ids` × `agent_id`, conditional color by violation rate; coverage KPI = 100% |
| 3 | Churn & Escalation Root-Cause | Key influencers / decomposition tree on `escalated`; bar chart of WEKA feature importance |
| 4 | Agent Productivity Matrix | Scatter AHT vs compliance score; table with AI accept/edit/reject rates |

### FR-6: Infrastructure & Networking (supporting requirements)
| ID | Requirement |
|---|---|
| FR-6.1 | `WS /ws/live-stream?token=<JWT>&session_id=<id>`: JWT validated before accept (close `4401` on failure). |
| FR-6.2 | Server `ping` every 20 s; client `pong` within 10 s else close `1011`. |
| FR-6.3 | Replay missed messages from Redis Stream (`MAXLEN 500`) using client `last_seq`. |
| FR-6.4 | Per-socket queue capacity 200; on overflow drop oldest partial `transcript` first. |
| FR-6.5 | Rate limit: 100 requests/min per agent ID (Redis sliding window), `429` + `Retry-After`. |
| FR-6.6 | `psutil` monitor every 5 s: CPU, RAM, process RSS, socket count; RSS > 2.5 GB or RAM > 85% -> reject new sessions (503) and evict idle sockets (> 120 s). |
| FR-6.7 | Docker Compose SHALL define exactly 3 services: `fastapi-app`, `chroma-db`, `redis-broker`, each with `restart: unless-stopped`. |

## 2.4 Persistent Data Model (SQLite `nexus.db`)
```sql
CREATE TABLE interactions(interaction_id TEXT PRIMARY KEY, ticket_id TEXT, customer_id TEXT, agent_id TEXT,
  client TEXT, vertical TEXT, channel TEXT, intent TEXT, start_ts TEXT, end_ts TEXT, handle_time_sec INT,
  hold_sec INT, acw_sec INT, fcr INT, sla_met INT, risk_score_max REAL, escalated INT,
  compliance_score INT, churn_probability REAL, llm_provider TEXT);
CREATE TABLE compliance_flags(id INTEGER PRIMARY KEY, interaction_id TEXT, rule_id TEXT, severity TEXT, evidence TEXT, turn_index INT);
CREATE TABLE hitl_audit(id INTEGER PRIMARY KEY, interaction_id TEXT, original TEXT, final TEXT, outcome TEXT, reason_code TEXT, approved_by TEXT, ts TEXT);
CREATE TABLE risk_events(id INTEGER PRIMARY KEY, interaction_id TEXT, risk REAL, p_weka REAL, s_neg REAL, t_hold REAL, band TEXT, ts TEXT);
CREATE TABLE tool_executions(idempotency_key TEXT PRIMARY KEY, interaction_id TEXT, tool TEXT, args_json TEXT, status TEXT, ts TEXT);
```

## 2.5 External Interface Requirements
| Interface | Spec |
|---|---|
| REST | `/api/v1/*`, JSON, OpenAPI at `/docs`, Bearer JWT |
| WebSocket | RFC 6455, JSON envelope (§2.2) |
| LLM | Groq HTTPS, Google AI Studio HTTPS, Ollama `http://localhost:11434` |
| Mock back-office | `/mock/v1/refunds`, `/mock/v1/tickets`, `/mock/v1/ekyc` (deterministic responses for testing) |

---

# SECTION 3: NON-FUNCTIONAL REQUIREMENTS

## 3.1 Performance & Latency
| ID | Requirement |
|---|---|
| NFR-P1 | End-to-end WebSocket roundtrip (final customer utterance received -> `suggestion` rendered) p95 **< 1.2 s** on the Groq path. |
| NFR-P2 | Ollama path p95 < 4 s (degraded mode). |
| NFR-P3 | Deterministic guardrail checks < 10 ms; Chroma query < 150 ms for ≤ 50k chunks. |
| NFR-P4 | System SHALL sustain ≥ 50 concurrent sessions on 4 cores / 8 GB RAM (`scripts/load_test.py`). |
| NFR-P5 | Provider failover ≤ 500 ms. |

## 3.2 Security & Privacy
| ID | Requirement |
|---|---|
| NFR-S1 | ChromaDB, SQLite and Redis data SHALL reside on local disk/volumes; none exposed beyond localhost. |
| NFR-S2 | **Zero PII to external endpoints:** before any Groq/Gemini call, `pii.mask()` SHALL redact names where detected in metadata, phone numbers (`\b[6-9]\d{9}\b`), Aadhaar (`\b\d{4}\s?\d{4}\s?\d{4}\b`), PAN (`\b[A-Z]{5}\d{4}[A-Z]\b`), card numbers, emails. Masked tokens (e.g., `<AADHAAR_1>`) are re-hydrated locally. |
| NFR-S3 | Secrets SHALL be read only from `.env`; `.env` is git-ignored; no secrets in logs. |
| NFR-S4 | JWT HS256, expiry 8 h; RBAC per FR-3.9; CORS restricted to `http://localhost:3000`; WebSocket `Origin` validated. |
| NFR-S5 | Inputs SHALL be validated by Pydantic; customer text is treated strictly as data (prompt-injection mitigation: delimiters, no tool execution from model-quoted customer text). |
| NFR-S6 | Audit tables (`hitl_audit`, `compliance_flags`) are append-only at the application layer. |
| NFR-S7 | Security scan with Strix (localhost, synthetic data) SHALL show no open high/critical findings before release. |

## 3.3 System Reliability & Availability
| ID | Requirement |
|---|---|
| NFR-R1 | Local service availability 99.9% (≤ 8.8 h downtime/yr equivalent) via `restart: unless-stopped` and healthchecks. |
| NFR-R2 | Redis AOF persistence enabled; session state and LangGraph checkpoints SHALL be recoverable after container restart within 10 s. |
| NFR-R3 | Graceful shutdown SHALL close sockets with code `1001` and flush pending SQLite writes. |
| NFR-R4 | Memory guard per FR-6.6 SHALL prevent unbounded growth during ticket spikes. |

## 3.4 Maintainability & Quality
| ID | Requirement |
|---|---|
| NFR-M1 | Backend test coverage ≥ 80%; `flake8` and `mypy` clean; frontend `eslint` clean. |
| NFR-M2 | Playwright E2E suite covers workstation, supervisor, reconnect, low-confidence flows. |
| NFR-M3 | OpenAPI schema auto-generated and matches Pydantic models. |

## 3.5 Usability & Accessibility
- Keyboard shortcuts: `Ctrl+Enter` Accept, `Ctrl+E` Edit, `Ctrl+Backspace` Reject.
- Contrast ratio ≥ 4.5:1; risk is never conveyed by color alone (icon + text label).
- Hinglish text rendering with Roman script and Devanagari fallback fonts.

---

# APPENDIX A: Acceptance Test Summary
| Test | Expected |
|---|---|
| Ticket "Meri flight cancel ho gayi, refund kab milega?" | Intent `flight_disruption`; flight SOP chunk; `trigger_refund_api` proposal; reply in Hinglish |
| Query with no SOP match | Confidence < 0.60; required banner; no draft |
| Kill Groq (invalid key) | `system` message `provider=ollama`; socket stays open; ≤ 500 ms switch |
| Risk input 0.9 twice | Supervisor tile red; P1 callback created once; 120 s cooldown |
| Draft containing "guaranteed refund" | `C-PROHIB` critical; Accept disabled until edited |
| Aadhaar number in ticket | Absent from outbound LLM request logs |

# APPENDIX B: Traceability Matrix
| Business goal | Requirements |
|---|---|
| Reduce AHT ≥ 25% | FR-1.x, FR-2.6, FR-3.1–3.2 |
| 100% QA coverage | FR-1.9–1.10, FR-5 view 2 |
| Proactive escalation | FR-2.x, FR-3.6 |
| Safe automation | FR-1.7, FR-4.x |
| Zero cost / privacy | CON-1, NFR-S1–S2 |
