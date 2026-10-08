# NexusCX: Next-Gen Autonomous Back-Office & Quality Intelligence Engine

**Product Requirements Document v1.0** | Owner: Principal TPM / Systems Architect | Client: MAS Callnet India Pvt. Ltd. | Status: Draft for Engineering Review

---

# SECTION 1: EXECUTIVE SUMMARY & STRATEGIC ALIGNMENT

## 1.1 Product Name & Vision

- **Name:** NexusCX
- **Tagline:** *"From conversation to completion, with a human always in command."*
- **Summary:** NexusCX is a multi-agent execution and quality-intelligence extension that runs beside CallMaster™ and human agents. CallMaster™ remains the voice-bot and transcript layer. NexusCX consumes its transcripts and ticket payloads, then (a) classifies intent, (b) retrieves SOP-grounded resolutions, (c) drafts back-office actions as validated JSON tool calls, (d) audits 100% of interactions for compliance, and (e) predicts escalation and churn. Every outbound action requires human approval (HITL).

## 1.2 Target Enterprise Profile

| Attribute | Detail |
| --- | --- |
| Enterprise | MAS Callnet India Pvt. Ltd. (hybrid BPO/KPO/CX) |
| Lines of business | Inbound/outbound contact centers; eKYC validation; BFSI document processing |
| Back-office verticals | Shipment tracking, flight disruption & refunds, HR outsourcing |
| Languages | English, Hinglish (code-mixed Hindi-English, Roman script) |
| Existing system | CallMaster™ (voice bots, prompt coaching, audio transcripts) |

## 1.3 Strategic Problem Statement

CallMaster™ stops at conversation. After the call, agents manually: check flight refund eligibility, validate eKYC documents against checklists, search PDFs for SOPs, update ticket state, and write emails. Consequences:

1. **High AHT** from tab-switching and SOP lookup (baseline assumption: 40% of handle time is non-conversational work).
2. **QA coverage ≈ 2–5%** because QA is manual sampling; compliance breaches go undetected.
3. **Reactive escalation:** churn and escalation are discovered after the customer complains.

## 1.4 Value Proposition

| Goal | Target KPI | Mechanism |
| --- | --- | --- |
| Reduce AHT | −25% | Pre-drafted responses and tool calls |
| QA coverage | 100% of interactions | Compliance Guardrail Agent |
| Escalation prevention | Alert ≥ 90 s before escalation point | WEKA + sentiment risk score |
| Cost | ₹0 licensing | Free-tier/open-source stack only |

**Non-goals (v1):** replacing CallMaster™ voice stack; autonomous sending without human approval; real telephony (SIP) integration (audio arrives as files/streams from CallMaster™ export).

---

# SECTION 2: USER PERSONAS

## Persona 1: Tier-1 Contact Center / Back-Office Agent ("Riya")

- **Responsibilities:** Handles 40–60 interactions/shift; follows SOPs; updates tickets; sends confirmations.
- **Pain points:** Searching 100+ page SOP PDFs mid-call; forgetting regulatory disclosures; repetitive refund/eKYC checks; AHT penalties.
- **NexusCX solution:** Right-panel SOP snippet appears within 1.2 s; center panel offers a drafted reply plus tool-call preview; compliance progress bar shows missed mandatory steps live; one-click Accept/Edit/Reject.

## Persona 2: QA Manager & Supervisor ("Arjun")

- **Responsibilities:** Audits calls against scorecards; coaches agents; intervenes on live escalations; owns compliance.
- **Pain points:** Samples only a few calls; late discovery of violations; no live visibility into risk.
- **NexusCX solution:** Live grid of active sessions sorted by risk; red alert at `Risk > 0.85`; Barge-in/Whisper actions; auto-generated per-interaction compliance scorecards; script-deviation heatmap.

## Persona 3: BPO Operations Director & Client Account Manager ("Meera")

- **Responsibilities:** Owns SLA, FCR, cost-per-contact, client QBRs (airline, bank, logistics).
- **Pain points:** Reports assembled manually in Excel; no root-cause view of churn; cannot prove compliance to clients.
- **NexusCX solution:** PowerBI dashboards fed by `/api/v1/analytics/export`; SLA/FCR trends; churn driver analysis; agent efficiency matrix.

---

# SECTION 3: SYSTEM ARCHITECTURE & DATA FLOW

## 3.1 Textual Flow Diagram

```
 [Voice .wav/.mp3 8kHz]        [Ticket JSON]            [SOP PDF/DOCX]
        |                           |                        |
        v                           |                (offline ingestion CLI)
  Groq Whisper-Large-v3-Turbo       |                  chunk -> embed (MiniLM)
  (ffmpeg resample 16kHz mono)      |                        |
        |  transcript segments      |                        v
        +-------------+-------------+                  ChromaDB (persistent)
                      v                                      ^
          FastAPI Router (/api/v1/ingest)                    |
          - Pydantic validation, rate limit                  |
                      |                                      |
                      v                                      |
          Redis Pub/Sub  channel: nexus:session:{id}         |
              |                          |                   |
              v                          v                   |
   WEKA Churn Pipeline          LangGraph Engine ------------+
   (RF/J48 inference wrapper)   Intent -> RAG -> Exec -> Guardrail
   + LLM sentiment score              |
              |                       |
              +--> Risk Score <-------+
                      |
          +-----------+----------------+
          v                            v
  WebSocket /ws/live-stream      PostgreSQL-free store:
  -> Next.js Agent Workstation   SQLite (nexus.db) -> /api/v1/analytics/export
  -> Next.js Supervisor Portal           -> PowerBI Desktop (.pbix)
```

Persistence: Redis for hot session state (AOF on); SQLite (`nexus.db`, file-based, zero cost) for audit trail and analytics history.

## 3.2 Data Sources & Ingestion Formats

### Audio

- Formats: `.wav`, `.mp3`, 8 kHz telephony. Pre-processing: `ffmpeg -ar 16000 -ac 1`. Chunk to ≤25 MB / 30 s windows for near-live streaming.
- STT: Groq `whisper-large-v3-turbo`, `language` hint `en`/`hi`, `response_format=verbose_json` to obtain segment timestamps.
- Edge cases: silence segments (`no_speech_prob > 0.6`) dropped; failed chunk retried once, then flagged `stt_gap=true`.

### Text/Tickets

```json
{
  "ticket_id": "TKT-2026-000123",
  "customer_id": "CUST-88231",
  "channel": "voice|chat|email",
  "raw_text": "Meri flight cancel ho gayi, refund kab milega?",
  "language": "hinglish",
  "timestamp": "2026-10-05T10:15:00+05:30",
  "metadata": {"hold_count": 1, "prior_tickets_30d": 3, "vertical": "flight"}
}
```

Pydantic model `TicketIn` enforces: `channel` Enum, `language` Enum(`english`,`hinglish`), `raw_text` 1–8000 chars, ISO-8601 timestamp.

### Documents (SOPs)

- Parsers: `pypdf`, `python-docx`. Chunking: `RecursiveCharacterTextSplitter(chunk_size=700, chunk_overlap=120)`.
- Metadata per chunk: `{"source_file","page","vertical","sop_version","section_title"}`.
- Embeddings: FastEmbed `sentence-transformers/all-MiniLM-L6-v2` (384-d, local CPU).

---

# SECTION 4: FUNCTIONAL REQUIREMENTS & MODULES

## Module 4.1: LangGraph Multi-Agent Execution Engine

### 4.1.1 State Object

```python
class AgentState(TypedDict):
    session_id: str
    messages: Annotated[list[BaseMessage], add_messages]
    customer_metadata: CustomerMetadata        # Pydantic: customer_id, vertical, language, prior_tickets_30d, hold_count
    intent: Optional[IntentResult]
    retrieved_docs: list[RetrievedDoc]         # text, source, page, score
    proposed_actions: list[ToolCall]
    compliance_flags: list[ComplianceFlag]
    agent_confidence_score: float              # 0.0-1.0, = rag_confidence * intent.confidence
    hitl_status: Literal["pending","accepted","edited","rejected","manual_required"]
    llm_provider_used: Literal["groq","gemini","ollama"]
```

### 4.1.2 Graph Topology

```
START -> intent_router -> rag_retriever -> [conditional: confidence >= 0.60?]
            yes -> backoffice_executor -> compliance_guardrail -> END(emit to UI)
            no  -> manual_required_node -> compliance_guardrail -> END
compliance_guardrail --(critical flag & retries<2)--> backoffice_executor   # cyclic revise loop
```

Checkpointing: `RedisSaver`-style checkpointer keyed by `session_id` so state survives container restart. Max cycles: 2 per turn (prevents infinite loops).

### 4.1.3 Agent Specifications

**Agent 1: Intent & Routing Agent** (`intent_router`)

- Model: Groq `llama-3.3-70b-versatile`, `temperature=0`, `response_format=json_object`.
- Output schema:

```python
class IntentResult(BaseModel):
    intent: Literal["billing","technical_support","flight_disruption","ekyc","other"]
    sub_intent: str                      # e.g. "refund_status", "doc_mismatch"
    confidence: float = Field(ge=0, le=1)
    sentiment: float = Field(ge=-1, le=1)
    urgency: Literal["low","medium","high"]
    detected_language: Literal["english","hinglish"]
```

- Validation failure: one retry with error appended to prompt; second failure -> `intent="other"`, `confidence=0.0`, routed to manual.
- Hinglish: system prompt includes 6 few-shot examples of code-mixed utterances.

**Agent 2: Dynamic RAG Context Retrieval Agent** (`rag_retriever`)

- Hybrid search: dense (Chroma cosine, top-8) + sparse BM25 (`rank_bm25` over cached chunk corpus, top-8), merged by Reciprocal Rank Fusion: `RRF(d) = Σ 1/(60 + rank_i(d))`.
- Metadata filter: `where={"vertical": intent_vertical}`.
- Confidence: `rag_confidence = 1 - cosine_distance(top1)` blended: `0.7*dense_sim + 0.3*bm25_norm`.
- Output: top-3 `RetrievedDoc{text, source, page, score}`. `agent_confidence_score = rag_confidence * intent.confidence`.
- Edge cases: empty collection -> confidence 0.0; duplicate chunks de-duplicated by `sha1(text)`.

**Agent 3: Automated Back-Office Execution Agent** (`backoffice_executor`)

- Produces a suggested customer reply (≤120 words, matching customer language) and zero or more tool calls. It never executes; it proposes.

```python
class ToolCall(BaseModel):
    tool: Literal["draft_email","trigger_refund_api","update_ticket_state","schedule_callback","verify_ekyc_checklist"]
    args: dict
    requires_approval: bool = True
    grounding_chunk_ids: list[str]       # must be non-empty, else call rejected
```

Example:

```json
{"tool":"trigger_refund_api","args":{"pnr":"6E4X9Q","amount_inr":8450,"reason":"airline_cancellation"},"requires_approval":true,"grounding_chunk_ids":["flt_sop_v3_p14_c2"]}
```

- Mock endpoints under `/mock/v1/*` (FastAPI) simulate airline/refund/ticketing systems. Idempotency key `sha256(session_id+tool+args)` blocks duplicate execution.
- Business rule guard: `trigger_refund_api.amount_inr` above SOP threshold -> forced `manual_required`.

**Agent 4: Real-time Compliance & Guardrail Agent** (`compliance_guardrail`)

- Deterministic checks (regex/keyword, \<10 ms): greeting present in first 2 agent turns; prohibited-word list (abuse, "guaranteed returns", "100% refund"); mandatory disclosures (call recording notice, identity verification before account data).
- LLM checks (Llama-3.3-70B, JSON): tone, unauthorized promises, PII leakage in drafted reply.

```python
class ComplianceFlag(BaseModel):
    rule_id: str; severity: Literal["info","warning","critical"]
    evidence_span: str; turn_index: int
```

- Compliance score per session: `100 - (10*critical + 4*warning + 1*info)`, floored at 0. A `critical` flag blocks the Accept button until the draft is edited.

## Module 4.2: WEKA Data Mining & Predictive Escalation Pipeline

### 4.2.1 Dataset & ARFF Conversion

Source: historical BPO metrics exported from `nexus.db` / CSV. Script `ml/build_arff.py` writes:

```
@relation bpo_escalation
@attribute handle_time_sec numeric
@attribute sentiment_score numeric
@attribute past_ticket_freq_30d numeric
@attribute hold_count numeric
@attribute transfer_count numeric
@attribute vertical {billing,technical,flight,ekyc}
@attribute escalated {yes,no}
@data
412,-0.62,4,2,1,flight,yes
```

Preprocessing: median imputation; `handle_time_sec` capped at the 99th percentile; stratified 70/30 split; class imbalance handled with WEKA `SMOTE` filter on training fold only. If no real data exists, a synthetic generator (`ml/synth_data.py`, 20,000 rows, seeded) is used and clearly labeled in model metadata.

### 4.2.2 Offline Training

- WEKA Explorer/CLI: `weka.classifiers.trees.RandomForest -I 200 -depth 12 -S 42` and `weka.classifiers.trees.J48 -C 0.25 -M 5`.
- 10-fold cross-validation. Acceptance: Random Forest ROC-AUC ≥ 0.85, recall(escalated=yes) ≥ 0.75.
- Artifacts: `models/rf_escalation.model` (serialized), `models/j48_rules.txt` (human-readable tree, shown to QA for explainability), `models/model_card.json`.

### 4.2.3 Inference Integration

- Primary: `python-weka-wrapper3` (JVM started once at FastAPI startup via `jvm.start()`), `Classifier.distribution_for_instance()` returns `P_weka`.
- Fallback if JVM unavailable: J48 rules parsed to a Python `predict_j48()` function (`ml/j48_inference.py`) returning a proxy probability.
- Re-scoring cadence: every new customer turn and every 15 s of elapsed call time.

### 4.2.4 Escalation Risk Score Formula

```
R = clip( 0.55 * P_weka  +  0.30 * S_neg  +  0.15 * T_hold , 0, 1 )

P_weka : WEKA probability of escalated=yes            in [0,1]
S_neg  : (1 - sentiment_llm) / 2, sentiment_llm in [-1,1] (Intent agent, rolling mean of last 3 customer turns)
T_hold : min(hold_count / 3, 1)
```

Escalation-Risk band: `<0.50 Low`, `0.50–0.70 Medium`, `0.70–0.85 High`, `>0.85 Critical`.

### 4.2.5 Trigger Conditions

If `R > 0.85` (debounced: two consecutive scores, or one score >0.92):

1. Publish `risk_alert` on Redis -> WebSocket -> supervisor grid tile turns red, audible chime.
2. Auto-create SLA callback ticket: `schedule_callback` with `sla_minutes=30`, `priority="P1"`, linked `parent_ticket_id`.
3. Log to `risk_events` table. Alert cooldown 120 s per session to prevent alert storms.

## Module 4.3: Next.js Web Applications

Stack: Next.js 14 App Router, TypeScript, Tailwind, shadcn/ui, Lucide, Recharts/ECharts. Routes: `/workstation/[sessionId]`, `/supervisor`, `/login`.

### 4.3.1 Agent Workstation (3-panel, CSS grid `grid-cols-[3fr_4fr_3fr]`)

| Panel | Components | Behavior |
| --- | --- | --- |
| **Left: Live Feed** | `TranscriptFeed`, `SentimentSparkline`, `LanguageBadge` | Auto-scroll; speaker-tagged bubbles; partial transcripts in italics until finalized |
| **Center: AI Suggestion** | `SuggestionCard`, `ToolCallPreview`, buttons **Accept / Edit / Reject** | Accept sends reply + executes approved tool calls; Edit opens inline textarea, logs diff; Reject requires reason code (dropdown) |
| **Right: Context** | `SopSnippetList`, `ConfidenceMeter`, `ComplianceProgressBar` | Shows source file/page; progress bar = completed mandatory steps / total; red segment on critical flag |

Low-confidence state: center panel renders an amber banner *"Low AI Confidence: Manual Agent Intervention Required"* and disables Accept (see 5.1).

### 4.3.2 Supervisor Dashboard

- `LiveSessionGrid`: card per active session (agent, customer ID, duration, risk gauge, compliance score, intent chip). Sort by risk desc. Red pulse animation at `R>0.85`.
- Actions per card: **Whisper** (supervisor text/audio visible only to agent, WS message type `supervisor_whisper`), **Barge-in** (flag `barge_in=true`, notifies agent, opens supervisor into session thread), **Open Transcript**.
- `AgentScorecardTable`: compliance avg, acceptance rate, edit rate, AHT.
- Role-based access: JWT with roles `agent|supervisor|director`; supervisor routes return 403 for `agent`.

## Module 4.4: Computer Networks & OS Infrastructure

### 4.4.1 WebSocket Behavior (`ws://localhost:8000/ws/live-stream?token=<JWT>&session_id=...`)

- **Handshake:** HTTP Upgrade; JWT validated before `accept()`; invalid -> close code `4401`.
- **Message envelope:**

```json
{"type":"transcript|suggestion|risk_alert|compliance_update|supervisor_whisper|ping|pong|system",
 "session_id":"S-1001","seq":482,"ts":"2026-10-05T10:15:03.221Z","payload":{}}
```

- **Heartbeat:** server `ping` every 20 s; client must `pong` within 10 s, else close `1011` and free resources.
- **Reconnection (client):** exponential backoff 1 s, 2 s, 4 s … capped at 30 s with ±20% jitter. On reconnect send `last_seq`; server replays missed messages from Redis Stream `nexus:stream:{session_id}` (retention 500 entries).
- **Fan-out:** `ConnectionManager` maintains `dict[session_id, set[WebSocket]]`; Redis Pub/Sub lets any uvicorn worker deliver to the right sockets. Back-pressure: per-socket `asyncio.Queue(maxsize=200)`; on overflow drop oldest `transcript` partials first.
- **Rate limiting:** Redis sliding-window (`ZADD`/`ZREMRANGEBYSCORE`) middleware: **100 req/min per agent ID**, returns `429` with `Retry-After`. LLM calls additionally throttled by a Redis token bucket matching Groq free-tier limits.

### 4.4.2 Docker Compose (3 services)

```yaml
services:
  fastapi-app:
    build: {context: ./backend, target: runtime}   # multi-stage: builder (pip wheels) -> slim runtime, JRE for WEKA
    ports: ["8000:8000"]
    env_file: .env
    depends_on: {chroma-db: {condition: service_started}, redis-broker: {condition: service_healthy}}
    restart: unless-stopped
    deploy: {resources: {limits: {memory: 3g}}}
  chroma-db:
    image: chromadb/chroma:latest
    volumes: ["./data/chroma:/chroma/chroma"]
    restart: unless-stopped
  redis-broker:
    image: redis:7-alpine
    command: ["redis-server","--appendonly","yes","--maxmemory","512mb","--maxmemory-policy","allkeys-lru"]
    volumes: ["./data/redis:/data"]
    healthcheck: {test: ["CMD","redis-cli","ping"], interval: 5s}
    restart: unless-stopped
```

Note: the Next.js app runs via `npm run dev/start` on the host (port 3000) to stay within the three-container constraint. Ollama runs on the host at `:11434` (`host.docker.internal`).

### 4.4.3 `psutil` Monitor Daemon

Background `asyncio` task (thread via `run_in_executor`), 5-second interval, publishes to `nexus:sys_metrics` and `/api/v1/system/health`:

- `cpu_percent`, `virtual_memory().percent`, process RSS, open WebSocket count, queue depths.
- **Thresholds:** RSS > 2.5 GB or RAM > 85% -> stop accepting new sessions (HTTP 503), evict idle sockets (no traffic >120 s), run `gc.collect()`; CPU > 90% for 30 s -> pause WEKA re-scoring cadence to 30 s. Recovery below 70% restores normal.

## Module 4.5: PowerBI Executive Analytics Engine

### 4.5.1 Export API

`GET /api/v1/analytics/export?from=2026-10-01&to=2026-10-05&format=json|csv&granularity=interaction` (JWT role `director`; flat rows, no nested objects, pagination `page_size≤5000`).

```json
{"interaction_id":"INT-001","ticket_id":"TKT-2026-000123","agent_id":"AG-17","vertical":"flight",
 "channel":"voice","intent":"flight_disruption","start_ts":"2026-10-05T10:15:00Z","handle_time_sec":412,
 "first_contact_resolved":true,"sla_met":true,"risk_score_max":0.88,"escalated":true,
 "weka_p":0.81,"sentiment_avg":-0.45,"compliance_score":86,"critical_flags":1,"script_deviation_rules":"disclosure_missing",
 "ai_suggestion_outcome":"edited","ai_confidence":0.74,"hold_count":2,"churn_probability":0.62}
```

Power Query connects via `Web.Contents` (JSON) or CSV; scheduled manual refresh in Desktop.

### 4.5.2 Dashboard Views

1. **Executive SLA & FCR:** KPI cards (SLA %, FCR %, AHT, escalation rate); line chart by day; slicers: vertical, client, shift.
2. **100% QA Compliance & Script Deviation Heatmap:** matrix rule_id × agent_id colored by violation rate; drill-through to interaction list.
3. **Churn & Escalation Root-Cause Drivers:** decomposition tree / key-influencers visual on `escalated` using hold_count, sentiment, prior tickets, vertical; WEKA feature importance as bar chart.
4. **Agent Productivity & Handling-Time Matrix:** scatter AHT vs compliance score, quadrant lines at team medians; table with AI acceptance rate and edit rate.

---

# SECTION 5: HITL, FAIL-SAFES & RELIABILITY

## 5.1 Low-Confidence Fallback

Condition: `rag_confidence < 0.60` OR `intent.confidence < 0.60` (`agent_confidence_score` shown to agent). Behavior: executor node skipped, no draft or tool calls generated, UI shows **"Low AI Confidence: Manual Agent Intervention Required"**, event logged as `hitl_status="manual_required"`. SOP snippets still displayed for reference.

## 5.2 Agent Manual Override

- No message leaves the system without an explicit agent click (`POST /api/v1/sessions/{id}/send` requires `approved_by`).
- Agent may overwrite any draft, delete tool calls, or type from scratch. All overrides stored: `{original, final, diff, reason_code}` in `hitl_audit`.
- Kill switch: per-session "Pause AI" toggle stops graph invocation for that session.

## 5.3 API Failure & Offline Fallback

```
Groq call (timeout 2.5 s, 1 fast retry max 150 ms)
  -> on 429 / 5xx / timeout / disconnect:
       circuit breaker opens -> route to Gemini 2.5 Flash (Google AI Studio)   [target <=300 ms switch]
       -> if Gemini fails -> Ollama llama3.1:8b @ http://localhost:11434       [total switch <=500 ms from detection]
Circuit half-opens after 60 s; success closes it.
```

- WebSocket stays open; a `system` message `{"provider":"ollama","degraded":true}` shows a UI badge.
- Whisper fallback: local `faster-whisper` (base) if Groq STT fails (optional dependency).
- Ollama output validated with the same Pydantic schemas; on invalid JSON -> manual_required.

---

# SECTION 6: NON-FUNCTIONAL REQUIREMENTS

| Category | Requirement |
| --- | --- |
| **Performance** | End-to-end WS roundtrip (final customer utterance -> suggestion rendered) p95 **\< 1.2 s** on Groq path; p95 \< 4 s on Ollama path; ≥ 50 concurrent sessions on 8 GB RAM / 4-core dev machine |
| **Security & Privacy** | ChromaDB and SQLite local-only; PII (names, phone, Aadhaar/PAN, account numbers) masked via regex (`Aadhaar: \b\d{4}\s?\d{4}\s?\d{4}\b`, PAN `[A-Z]{5}\d{4}[A-Z]`) **before** any cloud LLM call; keys only in `.env` (git-ignored); JWT HS256, 8 h expiry; CORS restricted to `http://localhost:3000`; audit log immutable (append-only) |
| **Reliability** | 99.9% local service uptime via `restart: unless-stopped`, healthchecks, Redis AOF persistence; graceful shutdown drains sockets (close `1001`) |
| **Observability** | Structured JSON logs; `/api/v1/system/health`; per-agent latency histograms |
| **Maintainability** | Pytest coverage ≥ 80% on agents/schemas; typed code (`mypy --strict` on `app/`); OpenAPI auto-docs at `/docs` |
| **Cost** | ₹0: Groq/Gemini free tiers, Ollama, ChromaDB, WEKA, Redis, Docker, PowerBI Desktop free |

## Appendix A: Core Database Schema (SQLite)

```sql
CREATE TABLE interactions(interaction_id TEXT PRIMARY KEY, ticket_id TEXT, customer_id TEXT, agent_id TEXT,
  vertical TEXT, channel TEXT, intent TEXT, start_ts TEXT, end_ts TEXT, handle_time_sec INT,
  fcr INT, sla_met INT, risk_score_max REAL, escalated INT, compliance_score INT, churn_probability REAL);
CREATE TABLE compliance_flags(id INTEGER PRIMARY KEY, interaction_id TEXT, rule_id TEXT, severity TEXT, evidence TEXT, turn_index INT);
CREATE TABLE hitl_audit(id INTEGER PRIMARY KEY, interaction_id TEXT, original TEXT, final TEXT, outcome TEXT, reason_code TEXT, ts TEXT);
CREATE TABLE risk_events(id INTEGER PRIMARY KEY, interaction_id TEXT, risk REAL, p_weka REAL, s_neg REAL, t_hold REAL, ts TEXT);
```

## Appendix B: Repository Layout

```
nexuscx/
  backend/app/{main.py, routers/, agents/{graph.py,intent.py,rag.py,executor.py,guardrail.py}, ml/, ws/, core/{config.py,ratelimit.py,monitor.py}}
  backend/ml/{build_arff.py, synth_data.py, models/}
  frontend/app/{workstation/[sessionId], supervisor, login}
  data/{chroma, redis, sops}
  docker-compose.yml  .env.example
```

## Appendix C: Delivery Milestones

| Phase | Weeks | Deliverable |
| --- | --- | --- |
| 1 | 1–2 | Docker stack, ingestion, Chroma SOP index, Whisper STT |
| 2 | 3–5 | LangGraph agents, provider fallback, HITL API |
| 3 | 6–7 | WEKA training, risk scoring, alerts |
| 4 | 8–9 | Next.js workstation & supervisor portal, WebSockets |
| 5 | 10 | Analytics export, PowerBI dashboards, load/soak tests |