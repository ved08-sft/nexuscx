# NexusCX — phases.md
**Sequential execution plan for the AI coding assistant.** Behavior and design are defined in `SRS.md` and `ARCHITECTURE.md`; coding boundaries in `rules.md`. This file only sets order, tasks, exit criteria, and verification.

**Operating protocol**
- [ ] Complete phases strictly in order; do not begin Phase N+1 until every Phase N box is checked and its Verification Test passes.
- [ ] After each phase: `git commit -m "phase-N: <summary>"` and tag `git tag phase-N-done`.
- [ ] If a verification fails twice, stop and report the failing output instead of working around it.
- [ ] Run the `rules.md` §5 enforcement checklist before every commit.

---

## PHASE 1: Local Infrastructure, Containers & Core Setup
**Objective:** A running skeleton with all services reachable.

### Tasks
- [ ] Create the root directory structure from `ARCHITECTURE.md` §1.3; `git init`; add `.gitignore` (`.env`, `data/`, `node_modules/`, `__pycache__/`, `*.model`).
- [ ] Create `.env.example` and a local `.env` (placeholders only committed).
- [ ] Write `backend/requirements.txt` with pinned versions; `backend/Dockerfile` (multi-stage, non-root user).
- [ ] Write `docker-compose.yml`: `fastapi-app`, `chroma-db`, `redis-broker` (AOF on, healthcheck, `restart: unless-stopped`).
- [ ] Create FastAPI skeleton: `app/main.py` with `lifespan` (Redis client init/close), `core/config.py` (`pydantic-settings`), structured redacting logger.
- [ ] Implement `GET /api/v1/health` returning `{status, redis, chroma}` from live pings.
- [ ] Initialize Next.js: `npx create-next-app@latest frontend --typescript --tailwind --app --eslint`; run `npx shadcn@latest init`; install `lucide-react recharts framer-motion`.
- [ ] Configure strict TS (`strict`, `noUncheckedIndexedAccess`), ESLint `no-explicit-any`, `.flake8`, `mypy.ini`, `pytest.ini`.
- [ ] Add a root `README.md` with start commands.

### Exit criteria
- [ ] 3 containers show `running`/`healthy` in `docker compose ps`.
- [ ] `npm run dev` serves the frontend at `localhost:3000`; `npm run build` passes.
- [ ] `flake8`, `mypy`, `eslint` all pass on the skeleton.

### Verification Test
```bash
docker compose up -d --build
docker compose exec redis-broker redis-cli ping            # expect PONG
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8000/api/v1/health   # expect 200
curl -s http://localhost:8000/api/v1/health                # expect redis:"ok", chroma:"ok"
```

---

## PHASE 2: Local RAG Pipeline & WEKA Model Integration
**Objective:** Retrieval and risk scoring work standalone, without LLMs or UI.

### Tasks — RAG
- [ ] Implement `rag/store.py`: `chromadb.PersistentClient(path=CHROMA_PATH)`, cosine collection `sops`, FastEmbed `all-MiniLM-L6-v2` embedding function.
- [ ] Generate 4 synthetic SOP files into `data/sops/` (flight refund, eKYC checklist, billing disputes, shipment tracking) — no real customer data.
- [ ] Implement `rag/ingest.py` CLI: parse PDF/DOCX → chunk (700/120) → deterministic IDs → upsert with metadata.
- [ ] Implement hybrid search (dense + BM25, RRF) returning `RetrievedDoc` with a confidence value.
- [ ] Handle edge cases: empty collection, empty query, duplicate chunks, unreadable PDF page.

### Tasks — WEKA
- [ ] Write `ml/synth_data.py` (seeded, 20,000 rows) and `ml/build_arff.py`.
- [ ] Train Random Forest and J48 in WEKA; save `backend/ml/models/rf_escalation.model`, `j48_report.txt`, `model_card.json` (record ROC-AUC, recall, `data_source`).
- [ ] Implement `ml/weka_runner.py` (JVM start/stop in `lifespan`, inference via `asyncio.to_thread`).
- [ ] Implement `ml/j48_inference.py` pure-Python fallback and automatic switch on JVM failure.
- [ ] Implement `ml/risk.py` combining WEKA probability with sentiment and hold count.
- [ ] Write pytest tests: risk formula boundaries (0.85 vs 0.8501), fallback path, ARFF header validity.

### Exit criteria
- [ ] Chroma collection count survives `docker compose restart`.
- [ ] Model card shows ROC-AUC ≥ 0.85 and recall(escalated=yes) ≥ 0.75.
- [ ] `pytest tests/test_rag.py tests/test_risk.py` green.

### Verification Test
```bash
docker compose exec fastapi-app python scripts/verify_phase2.py
# Script must: (1) query "refund for cancelled flight" and print top chunk + confidence >= 0.60,
# (2) query gibberish and assert confidence < 0.60,
# (3) score a dummy ticket {handle_time_sec:620, sentiment:-0.7, past_tickets:5, hold_count:3}
#     and print P_weka, risk, band, model_name; assert 0 <= risk <= 1 and band == "critical".
```

---

## PHASE 3: LangGraph Agentic Engine & Fail-Safe Routing
**Objective:** The 4-node graph runs end to end with provider fallback, tested without the UI.

### Tasks
- [ ] Define schemas in `schemas/` (`AgentState`, `IntentResult`, `ToolCall`, `ComplianceFlag`) exactly per `SRS.md` §2.2.
- [ ] Implement `core/llm_router.py`: Groq (timeout 1.2 s) → Ollama, circuit breaker 60 s, optional Gemini behind `LLM_ENABLE_GEMINI`; Pydantic-validated outputs; prompt budget check ≤ 2000 tokens.
- [ ] Implement `core/pii.py` mask/rehydrate; unit test with Aadhaar, PAN, phone, email samples.
- [ ] Implement nodes, one file each: `intent.py`, `rag.py`, `executor.py`, `guardrail.py`.
- [ ] Implement `agents/graph.py`: conditional edge on confidence < 0.60 → `manual_required`; guardrail revise loop (max 2 cycles, `recursion_limit=12`); Redis checkpointer.
- [ ] Add a Redis token bucket for LLM calls.
- [ ] Write tests with mocked LLM: state progression, low-confidence routing, schema-failure retry, guardrail critical-flag loop, empty `grounding_chunk_ids` rejection.
- [ ] Write fallback tests: mock Groq `429`, timeout, and 5xx; assert Ollama is called and total switch ≤ 500 ms.

### Exit criteria
- [ ] `pytest tests/test_agents.py tests/test_llm_router.py tests/test_pii.py` green.
- [ ] Golden set of 20 mock tickets (English + Hinglish) reaches ≥ 85% intent accuracy with live Groq.
- [ ] `ollama run llama3.1:8b` works locally and the graph completes with Groq disabled.

### Verification Test
```bash
docker compose exec fastapi-app pytest tests/test_agents.py -v
docker compose exec fastapi-app python scripts/verify_phase3.py
# Script feeds mock complaint: "Meri flight cancel ho gayi, refund kab milega?" and prints
# state progression: intent_router -> rag_retriever -> backoffice_executor -> compliance_guardrail,
# plus llm_provider_used. Re-run with GROQ_API_KEY=invalid; expect provider "ollama" and no exception.
```

---

## PHASE 4: FastAPI WebSockets & Next.js Interactive Dashboard
**Objective:** Live, bidirectional UI wired to the engine.

### Tasks — Backend
- [ ] Implement JWT auth (`core/security.py`) with roles `agent`, `supervisor`, `director`; seed 3 demo users via env.
- [ ] Implement `ws/manager.py` (`ConnectionManager`): token check before accept, ping 20 s / pong 10 s, per-socket queue (200), Redis Stream replay by `last_seq`.
- [ ] Implement Redis Pub/Sub fan-out and `asyncio.gather` of graph + risk on ingest.
- [ ] Implement `POST /api/v1/ingest/ticket`, `POST /api/v1/sessions/{id}/send` (requires `approved_by`), rate limiting (100 req/min/agent), `psutil` monitor task.
- [ ] Implement risk-alert logic (two consecutive > 0.85, cooldown 120 s) and callback ticket creation.
- [ ] Write `scripts/simulate_call.py`: streams scripted customer/agent text chunks (English + Hinglish) to the ingest endpoint at 1–2 s intervals, including an escalating-sentiment scenario.

### Tasks — Frontend
- [ ] Run `skillui` on a chosen reference; write `DESIGN.md`, Tailwind tokens, `/styleguide` page.
- [ ] Define all event/state interfaces in `lib/types.ts` (discriminated union on `type`).
- [ ] Implement `hooks/useLiveStream.ts` with backoff, jitter, `last_seq`, type-guarded parsing.
- [ ] Build Agent Workstation: `TranscriptFeed`, `SuggestionCard` (Accept / Edit / Reject + manual override), `SopPanel`, `ComplianceBar`, low-confidence banner.
- [ ] Build Supervisor Live Matrix: `LiveSessionGrid`, `RiskGauge`, Whisper / Barge-in controls, scorecard table.
- [ ] Wrap every real-time component in `<ErrorBoundary>`; add `error.tsx` and loading/empty states.
- [ ] Add `middleware.ts` role guards and login page.

### Exit criteria
- [ ] Two browser tabs on the same session receive identical `suggestion` messages.
- [ ] Killing and restarting `redis-broker` causes automatic client reconnect within 5 s with no UI crash.
- [ ] Accept is disabled on `manual_required` and on `blocking=true`.
- [ ] `npm run lint`, `npx tsc --noEmit`, `npm run build` clean.

### Verification Test
```bash
docker compose up -d
(cd frontend && npm run dev) &
python scripts/simulate_call.py --session S-1001 --scenario escalating --interval 1.5
# Observe at localhost:3000/workstation/S-1001 and /supervisor:
#  - transcript lines appear within 1.2 s of each chunk
#  - suggestion card populates with SOP source
#  - supervisor tile turns red when risk > 0.85 (alert fires once, then 120 s cooldown)
python scripts/simulate_call.py --session S-1002 --scenario low_confidence
#  - banner reads exactly: "Low AI Confidence: Manual Agent Intervention Required"
```

---

## PHASE 5: Testing, Security Audit & PowerBI REST Integration
**Objective:** Prove correctness, security, and reporting.

### Tasks — E2E tests
- [ ] Install Playwright: `npm i -D @playwright/test && npx playwright install --with-deps chromium`.
- [ ] Write specs: `workstation.spec.ts` (streaming transcript, Accept/Edit/Reject, override), `supervisor.spec.ts` (red tile ≤ 500 ms, Whisper), `ws-reconnect.spec.ts` (`page.routeWebSocket` close → reconnect → replay), `low-confidence.spec.ts`.
- [ ] Capture baseline screenshots into `e2e/__screenshots__/`.
- [ ] Write `scripts/load_test.py` (50 concurrent sessions); record p95 roundtrip and RSS from the monitor endpoint.

### Tasks — Security
- [ ] Install Strix (`curl -sSL https://strix.ai/install | bash`); set `STRIX_LLM` to a free provider (Groq key or local Ollama) and `LLM_API_KEY` / `LLM_API_BASE` accordingly.
- [ ] Run `strix --target ./backend --scan-mode quick` (source) and `strix -n --target http://localhost:8000 --scan-mode standard` (localhost only).
- [ ] Triage every finding: fix, or document a justified false positive in `docs/security/strix-report.md`; re-run until clean.
- [ ] Add regression tests for each fixed finding (auth bypass, oversized payload, WS origin, prompt injection, PII in logs).

### Tasks — PowerBI
- [ ] Implement `GET /api/v1/analytics/export` (flat rows, pagination, JSON/CSV, `director` role) per `SRS.md` FR-5.
- [ ] Seed `nexus.db` with ≥ 2,000 synthetic interactions via `scripts/seed_analytics.py`.
- [ ] In PowerBI Desktop: Get Data → Web (with Bearer header) or Text/CSV; build the 4 views listed in `SRS.md` FR-5; save `powerbi/NexusCX.pbix`.
- [ ] Export dashboard screenshots to `docs/powerbi/`.

### Exit criteria
- [ ] All Playwright specs, `pytest --cov=app` (≥ 80%), `flake8`, `mypy --strict`, `eslint` pass.
- [ ] Load test: p95 < 1.2 s on Groq path, no memory growth > 10% over a 10-minute run.
- [ ] Strix report shows zero high/critical open findings.
- [ ] PowerBI refresh succeeds and row count equals `SELECT COUNT(*) FROM interactions`.

### Verification Test
```bash
(cd frontend && npx playwright test)                         # all green
(cd backend && flake8 app tests && mypy --strict app && pytest -q --cov=app --cov-fail-under=80)
strix -n --target http://localhost:8000 --scan-mode standard # report: 0 high/critical
curl -H "Authorization: Bearer $DIRECTOR_TOKEN" \
  "http://localhost:8000/api/v1/analytics/export?format=json&page_size=5" | jq '.rows[0] | keys'
# Then refresh PowerBI: all four report pages render with data; save .pbix.
```

---

## FINAL RELEASE GATE
- [ ] `git tag v1.0.0` only after all five phases are tagged `phase-N-done`.
- [ ] Fresh-clone test: `git clone` → `cp .env.example .env` → fill keys → `docker compose up -d --build` → run Phase 1 and Phase 4 verification scripts successfully.
- [ ] `docs/DEPENDENCIES.md` lists every added package; no forbidden libraries present (`rules.md` §1.3).
