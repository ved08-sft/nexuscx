from contextlib import asynccontextmanager
from fastapi import FastAPI, APIRouter
from app.schemas.health import HealthResponse
from app.api.v1 import auth, tickets, rag, analytics
# from app.ws import websocket_router

# Create API router and include subrouters
api_router = APIRouter()

# Include all v1 routers
print(f"Including auth router")
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
print(f"Auth router included successfully")
print(f"Including tickets router")
api_router.include_router(tickets.router, prefix="/tickets", tags=["tickets"])
print(f"Tickets router included successfully")
print(f"Including rag router")
api_router.include_router(rag.router, prefix="/rag", tags=["rag"])
print(f"Rag router included successfully")
print(f"Including analytics router")
api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
print(f"Analytics router included successfully")

# Print api_router routes
print(f"api_router: {api_router}")
try:
    routes = []
    for route in api_router.routes:
        if hasattr(route, 'path'):
            routes.append(route.path)
        elif hasattr(route, 'routes'):  # Handle nested routers
            for subroute in route.routes:
                if hasattr(subroute, 'path'):
                    routes.append(subroute.path)
    print(f"api_router.routes: {routes}")
except Exception as e:
    print(f"Error getting routes: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize Redis / Chroma / Logger resources
    yield
    # Shutdown: Close Redis / Chroma / Logger resources


app = FastAPI(
    title="NexusCX Orchestration Engine",
    version="1.0.0",
    description="Interface Control Document v1.0 Compliant FastAPI Backend",
    lifespan=lifespan,
)

# Include API router
app.include_router(api_router, prefix="/api/v1")

# Include WebSocket router
# app.include_router(websocket_router)


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Liveness & health metric endpoint compliant with ICD §1.4."""
    # Stub response for scaffolding; wired to live ping in Phase 1
    return {
        "status": "ok",
        "version": "1.0.0",
        "timestamp": "2026-10-05T10:20:00Z",
        "uptime_sec": 0.0,
        "system": {
            "cpu_percent": 0.0,
            "cpu_count": 1,
            "ram_percent": 0.0,
            "ram_used_mb": 0.0,
            "ram_total_mb": 0.0,
            "process_rss_mb": 0.0,
            "thread_count": 1,
        },
        "websocket": {"active_connections": 0, "active_sessions": 0, "max_queue_depth": 0},
        "dependencies": {
            "redis": {"status": "ok", "latency_ms": 0.0},
            "chroma": {"status": "ok", "latency_ms": 0.0},
            "ollama": {"status": "ok"},
            "groq": {"status": "ok"},
            "weka": {"status": "python_fallback"},
        },
        "llm": {"active_provider": "groq", "fallback_active": False},
    }