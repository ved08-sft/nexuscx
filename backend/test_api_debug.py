"""
API test for NexusCX Orchestration Engine.
Tests the FastAPI endpoints implemented in Phase 3.
"""
import asyncio
import json
from typing import Dict, Any

import httpx
from fastapi.testclient import TestClient

from app.main import app

# Configure logging
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_health_endpoint():
    """Test the health endpoint."""
    client = TestClient(app)
    response = client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["version"] == "1.0.0"

    logger.info("Health endpoint test PASSED")
    return True

def test_auth_login():
    """Test the auth login endpoint."""
    client = TestClient(app)
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "agent1", "password": "password123"}
    )

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["expires_in"] == 28800
    assert data["role"] == "agent"
    assert data["agent_id"] == "AG-01"

    logger.info("Auth login endpoint test PASSED")
    return True, data["access_token"]

def test_tickets_ingest(token: str):
    """Test the tickets ingest endpoint."""
    print(f"Received token: {token}")
    client = TestClient(app)
    response = client.post(
        "/api/v1/tickets/ingest",
        json={
            "source_type": "ticket",
            "ticket_id": "TKT-2026-000456",
            "customer_id": "CUST-112233",
            "channel": "voice",
            "subject": "Test ticket",
            "raw_text": "This is a test ticket for verification purposes.",
            "content_format": "text",
            "language": "english",
            "received_at": "2026-10-05T10:15:00Z",
            "metadata": {
                "vertical": "billing",
                "hold_count": 0,
                "transfer_count": 0,
                "prior_tickets_30d": 0
            },
            "customer_profile": {
                "avg_handling_time_sec": 300,
                "past_escalation_count": 0,
                "ekyc_verified": True
            }
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    print(f"Response status: {response.status_code}")
    print(f"Response body: {response.text}")

    # Should return 202 Accepted
    assert response.status_code == 202
    data = response.json()
    assert "session_id" in data
    assert data["session_id"].startswith("S-")
    assert "interaction_id" in data
    assert data["interaction_id"].startswith("INT-")
    assert data["ticket_id"] == "TKT-2026-000456"
    assert data["status"] == "queued"
    assert "ws_url" in data
    assert data["ws_url"].startswith("ws://")
    assert "created_at" in data

    logger.info("Tickets ingest endpoint test PASSED")
    return True

def test_rag_query(token: str):
    """Test the RAG query endpoint."""
    client = TestClient(app)
    response = client.post(
        "/api/v1/rag/query",
        json={
            "query": "flight cancelled refund",
            "vertical": "flight",
            "top_k": 3,
            "mode": "hybrid"
        },
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert "query_id" in data
    assert data["collection"] == "sops"
    assert "embedding_model" in data
    assert data["mode"] == "hybrid"
    assert "results" in data
    assert isinstance(data["results"], list)
    assert "confidence" in data
    assert isinstance(data["confidence"], float)
    assert "manual_required" in data
    assert isinstance(data["manual_required"], bool)
    assert "message" in data
    assert data["message"] is None or isinstance(data["message"], str)
    assert "latency_ms" in data
    assert isinstance(data["latency_ms"], int)

    logger.info("RAG query endpoint test PASSED")
    return True

def run_all_tests():
    """Run all API tests."""
    logger.info("Starting API tests")

    # Test health endpoint
    if not test_health_endpoint():
        return False

    # Test auth login
    login_result, token = test_auth_login()
    if not login_result:
        return False

    # Test tickets ingest
    if not test_tickets_ingest(token):
        return False

    # Test RAG query
    if not test_rag_query(token):
        return False

    logger.info("All API tests PASSED")
    return True

if __name__ == "__main__":
    # Run the tests
    try:
        result = run_all_tests()
        if result:
            print("PASS: All API tests PASSED")
        else:
            print("FAIL: Some API tests FAILED")
    except Exception as e:
        logger.error(f"API tests FAILED with exception: {str(e)}", exc_info=True)
        print(f"FAIL: API tests FAILED with exception: {str(e)}")
        import traceback
        traceback.print_exc()