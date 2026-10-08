# NexusCX — Project Memory & Status Tracker (`memoryNEXUS.md`)

> **Note:** This file serves as the living project memory for NexusCX. It is constantly updated to reflect completed tasks, the active file/phase, current sprint goals, and overall project status.

---

## 1. Executive Summary & Overview
- **Project Name:** NexusCX (Nexus Customer Experience Orchestration Engine)
- **Architecture:** Hybrid Local RAG + WEKA ML Risk Classifier + LangGraph Agentic Orchestrator + Next.js Real-time Dashboard + FastAPI WebSockets.
- **Repository Location:** `c:\Users\dev tyagi\OneDrive\Documents\Desktop\NEXUSCX`
- **Primary Rules & References:**
  - System Instructions: `.antigravityrules` & `SYSTEM_INSTRUCTIONS.md`
  - API Wire Formats & Schemas: [`/docs/icd.md`](file:///c:/Users/dev%20tyagi/OneDrive/Documents/Desktop/NEXUSCX/docs/icd.md)
  - Test Strategy & TDD Workflow: [`/docs/tdd.md`](file:///c:/Users/dev%20tyagi/OneDrive/Documents/Desktop/NEXUSCX/docs/tdd.md)
  - Execution Plan: [`/docs/phases.md`](file:///c:/Users/dev%20tyagi/OneDrive/Documents/Desktop/NEXUSCX/docs/phases.md)
  - Operational Guardrails: [`/docs/rules.md`](file:///c:/Users/dev%20tyagi/OneDrive/Documents/Desktop/NEXUSCX/docs/rules.md)

---

## 2. Current Project Status

| Metric | Status |
|---|---|
| **Overall Status** | 🟡 **Phase 1 Backend Schemas & Scaffolding Complete** |
| **Active Phase** | **Phase 1: Local Infrastructure, Containers & Core Setup** |
| **Current Active File** | [`backend/tests/test_contracts.py`](file:///c:/Users/dev%20tyagi/OneDrive/Documents/Desktop/NEXUSCX/backend/tests/test_contracts.py) |
| **TDD Mode** | **Red-Green-Refactor Active (15 tests passing)** |

---

## 3. Phase Progress Checklist

### Phase 0: System Architecture & Specifications 🟢 COMPLETED
- [x] Comprehensive PRD (`NexusCX PRD.md` / `docs/prd.md`)
- [x] System Architecture & Component Design (`ARCHITECTUREnexus.md` / `docs/architecture.md`)
- [x] Software Requirements Specification (`SRSnexus.md` / `docs/srs.md`)
- [x] Interface Control Document — ICD v1.0 (`icdNEXUS.md` / `docs/icd.md`)
- [x] Test-Driven Development Playbook — TDD v1.0 (`tddNEXUS.md` / `docs/tdd.md`)
- [x] UI/UX Design Specification (`designNEXUS.md` / `docs/design.md`)
- [x] Code Rules & Operational Guardrails (`NEXUSRULES.md` / `docs/rules.md`)
- [x] Sequential Execution Phases (`phasesNEXUS.md` / `docs/phases.md`)
- [x] System Instructions Configuration (`.antigravityrules` & `SYSTEM_INSTRUCTIONS.md`)
- [x] Living Memory & Tracker Setup (`MARKDOWN FILES/memoryNEXUS.md` & `MEMORY.md`)

---

### Phase 1: Local Infrastructure, Containers & Core Setup 🟡 IN PROGRESS
- [x] Scaffold `/backend` structure (`app/`, `app/core/`, `app/schemas/`, `tests/`).
- [x] Write `backend/requirements.txt` & `backend/pytest.ini`.
- [x] Implement Pydantic v2 schemas for all REST endpoints in ICD §1 (`enums.py`, `ticket.py`, `rag.py`, `analytics.py`, `auth.py`, `health.py`, `error.py`).
- [x] Write and verify contract unit tests in `backend/tests/test_contracts.py` (15/15 tests passing).
- [x] Scaffold `app/main.py` FastAPI app with lifespan context manager and `/health` route.
- [x] Scaffold `app/core/config.py` with `pydantic-settings`.
- [ ] Create root directory structure from `docs/architecture.md` §1.3 (`git init`, `.gitignore`).
- [ ] Write `.env.example` and local `.env`.
- [ ] Write `backend/Dockerfile` (multi-stage, non-root user).
- [ ] Write `docker-compose.yml` (`fastapi-app`, `chroma-db`, `redis-broker`).
- [ ] Initialize Next.js app (`npx create-next-app@latest frontend --typescript --tailwind --app`).
- [ ] Configure ESLint, Flake8, Mypy.

---

### Phase 2: Local RAG Pipeline & WEKA Model Integration ⚪ PENDING
- [ ] Implement `rag/store.py` (ChromaDB + FastEmbed `all-MiniLM-L6-v2`).
- [ ] Ingest synthetic SOP files (`data/sops/`).
- [ ] Implement hybrid search (dense + BM25, RRF).
- [ ] Generate synthetic ARFF datasets (`ml/synth_data.py`, `ml/build_arff.py`).
- [ ] Train WEKA models (`rf_escalation.model`, `rf_churn.model`, `model_card.json`).
- [ ] Implement `ml/weka_runner.py` JVM interface + Python J48 fallback.
- [ ] Implement risk calculation engine (`ml/risk.py`).

---

### Phase 3: LangGraph Agentic Engine & Fail-Safe Routing ⚪ PENDING
- [ ] Define schemas in `schemas/` (`AgentState`, `IntentResult`, `ToolCall`, `ComplianceFlag`).
- [ ] Implement LLM router (`core/llm_router.py`) with Groq → Ollama/Gemini fallback & circuit breaker.
- [ ] Implement PII masking/rehydration (`core/pii.py`).
- [ ] Implement nodes (`intent.py`, `rag.py`, `executor.py`, `guardrail.py`).
- [ ] Construct graph in `agents/graph.py` with low-confidence routing & HITL loop.

---

### Phase 4: FastAPI WebSockets & Next.js Interactive Dashboard ⚪ PENDING
- [ ] JWT authentication & role-based security (`core/security.py`).
- [ ] WebSocket ConnectionManager (`ws/manager.py`) & Redis Pub/Sub stream replay.
- [ ] Ingest & action endpoints (`POST /api/v1/tickets/ingest`, `AGENT_HITL_ACTION` frame).
- [ ] Next.js Agent Workstation UI (TranscriptFeed, SuggestionCard, SopPanel, ComplianceBar).
- [ ] Next.js Supervisor Live Matrix UI (LiveSessionGrid, RiskGauge, Whisper controls).

---

### Phase 5: Testing, Security Audit & PowerBI REST Integration ⚪ PENDING
- [ ] Playwright E2E test suite.
- [ ] Security audit using Strix static & dynamic analysis.
- [ ] PowerBI REST export endpoint (`GET /api/v1/analytics/export`) & dataset seeding.

---

## 4. Change & Activity Log

| Date | User / Agent | Action / Update Description |
|---|---|---|
| 2026-10-05 | Antigravity AI | Initialized `/docs/`, `.antigravityrules`, `SYSTEM_INSTRUCTIONS.md`, and `MEMORY.md`. |
| 2026-10-05 | Antigravity AI | Scaffolded `/backend` structure. Implemented Pydantic v2 schemas for all ICD Section 1 REST endpoints (`ticket`, `rag`, `analytics`, `auth`, `health`, `error`). Written 15 contract unit tests in `backend/tests/test_contracts.py` and verified 100% green with `pytest`. |
