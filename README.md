# NexusCX: Next-Gen Autonomous Back-Office & Quality Intelligence Engine

NexusCX is a multi-agent execution and quality-intelligence extension that runs beside CallMaster™ and human agents. CallMaster™ remains the voice-bot and transcript layer. NexusCX consumes its transcripts and ticket payloads, then (a) classifies intent, (b) retrieves SOP-grounded resolutions, (c) drafts back-office actions as validated JSON tool calls, (d) audits 100% of interactions for compliance, and (e) predicts escalation and churn. Every outbound action requires human approval (HITL).

## Project Structure

```
nexuscx/
├── AGENTS.md  CLAUDE.md  ARCHITECTURE.md  SRS.md  DESIGN.md  .env.example  .gitignore
├── docker-compose.yml
├── backend/
│   ├── Dockerfile  requirements.txt  pytest.ini  .flake8  mypy.ini
│   ├── app/
│   │   ├── main.py
│   │   ├── core/{config.py, llm_router.py, ratelimit.py, monitor.py, security.py, pii.py}
│   │   ├── schemas/{ticket.py, state.py, compliance.py, risk.py, ws.py}
│   │   ├── agents/{graph.py, intent.py, rag.py, executor.py, guardrail.py}
│   │   ├── rag/{ingest.py, store.py}
│   │   ├── ml/{weka_runner.py, j48_inference.py, risk.py}
│   │   ├── routers/{ingest.py, sessions.py, analytics.py, health.py, mock_api.py}
│   │   ├── ws/{manager.py, handlers.py}
│   │   └── db/{models.py, session.py}
│   ├── ml/{synth_data.py, build_arff.py, train_weka.sh, models/}
│   └── tests/{test_schemas.py, test_agents.py, test_risk.py, test_ws.py, test_llm_router.py}
├── frontend/
│   ├── package.json  tailwind.config.ts  playwright.config.ts  .eslintrc.json
│   └── src/{app/{workstation/[sessionId]/page.tsx, supervisor/page.tsx, login/page.tsx},
│            components/{TranscriptFeed, SuggestionCard, SopPanel, ComplianceBar, RiskGauge, LiveSessionGrid}.tsx,
│            hooks/useLiveStream.ts, lib/{types.ts, api.ts}}
│   └── e2e/{workstation.spec.ts, supervisor.spec.ts, ws-reconnect.spec.ts}
├── data/{sops/, chroma/, redis/, audio_samples/}
├── powerbi/NexusCX.pbix
└── scripts/{seed_sops.sh, load_test.py}
```

## Getting Started

1. Copy `.env.example` to `.env` and fill in your API keys
2. Install dependencies: `docker compose up -d --build`
3. Initialize the database and models: `./scripts/seed_sops.sh`
4. Start the Next.js frontend: `cd frontend && npm run dev`
5. Visit http://localhost:3000 to access the application

## Phases

The project is divided into 5 phases:
1. Local Infrastructure, Containers & Core Setup
2. Local RAG Pipeline & WEKA Model Integration
3. LangGraph Agentic Engine & Fail-Safe Routing
4. FastAPI WebSockets & Next.js Interactive Dashboard
5. Testing, Security Audit & PowerBI REST Integration

Check `memoryNEXUS.md` for the current phase status and progress.