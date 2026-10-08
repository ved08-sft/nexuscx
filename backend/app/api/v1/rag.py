"""
RAG query endpoints for NexusCX Orchestration Engine.
Implements ICD §1.2: POST /api/v1/rag/query
"""
from fastapi import APIRouter, Depends, Header, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field, validator
from typing import Optional, Literal, List, Dict, Any
import time
import logging
import jwt

from app.schemas.enums import Vertical
from app.schemas.rag import RagQueryRequest, RagQueryResponse, RagSearchResult
from app.core.config import settings
from app.rag.store import search_sops

logger = logging.getLogger(__name__)

router = APIRouter()
security = HTTPBearer()

# Mock agent database for authentication
MOCK_AGENTS = {
    "agent1": {"password": "password123", "role": "agent", "agent_id": "AG-01"},
    "agent2": {"password": "password456", "role": "agent", "agent_id": "AG-02"},
    "supervisor1": {"password": "superpass", "role": "supervisor", "agent_id": "SUP-01"},
}

def verify_token(authorization: Optional[str] = Header(None)) -> Dict[str, Any]:
    """Verify JWT token and return agent information."""
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization header"
        )

    # In a real implementation, we would verify the JWT token
    # For now, we'll use a simple mock implementation
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization format"
        )

    token = authorization[7:]  # Remove "Bearer " prefix

    # Mock token validation - in reality, we'd decode and verify the JWT
    # For this implementation, we'll accept any token that starts with "mock-token-"
    # or try to decode as a JWT token
    if token.startswith("mock-token-"):
        agent_id = token[11:]  # Extract agent ID from token
        # Look up agent in mock database
        for agent_name, agent_data in MOCK_AGENTS.items():
            if agent_data["agent_id"] == agent_id:
                return agent_data
    else:
        # Try to decode as JWT token
        try:
            # In a real implementation, we would use a proper secret key
            secret_key = "your-secret-key-here"  # Should be loaded from environment
            payload = jwt.decode(token, secret_key, algorithms=["HS256"])
            agent_id = payload.get("sub")
            if agent_id:
                # Look up agent in mock database
                for agent_name, agent_data in MOCK_AGENTS.items():
                    if agent_data["agent_id"] == agent_id:
                        return agent_data
        except jwt.JWTError:
            pass  # Fall through to invalid token

    # If we get here, token is invalid
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token"
    )

@router.post(
    "/query",
    response_model=RagQueryResponse,
    status_code=status.HTTP_200_OK,
    summary="Perform hybrid search against the SOP knowledge base",
    description="Direct hybrid search against the ChromaDB `sops` collection."
)
async def query_rag(
    request: RagQueryRequest,
    authorization: dict = Depends(verify_token)
):
    """
    Perform hybrid search against the SOP knowledge base.

    - **query**: Search query (required, 1-1000 chars)
    - **vertical**: SOP vertical to search (optional, defaults to all verticals)
    - **top_k**: Number of results to return (optional, 1-10, default: 3)
    - **mode**: Search mode (optional, hybrid/dense/sparse, default: hybrid)
    - **min_score**: Minimum score threshold (optional, 0.0-1.0, default: 0.0)

    Returns:
    - **query_id**: Unique identifier for the query
    - **collection**: Name of the collection searched
    - **embedding_model**: Embedding model used
    - **mode**: Search mode used
    - **results**: List of search results
    - **confidence**: Confidence score of the top result
    - **manual_required**: Whether manual intervention is required
    - **message**: Message if manual intervention is required
    - **latency_ms**: Query latency in milliseconds
    """
    start_time = time.time()

    # Perform the search using our RAG store
    results, confidence = search_sops(
        query=request.query,
        vertical=request.vertical,
        top_k=request.top_k
    )

    # Calculate latency
    latency_ms = int((time.time() - start_time) * 1000)

    # Determine if manual intervention is required
    manual_required = confidence < 0.60
    message = (
        "Low AI Confidence: Manual Agent Intervention Required"
        if manual_required else None
    )

    # Generate query ID
    query_id = f"3f6d2f0e-8f64-4d0e-9a38-2a1b8d9c5f10"  # In real implementation, this would be random

    return RagQueryResponse(
        query_id=query_id,
        collection="sops",
        embedding_model="sentence-transformers/all-MiniLM-L6-v2",
        mode=request.mode.value if request.mode else "hybrid",
        results=results,
        confidence=confidence,
        manual_required=manual_required,
        message=message,
        latency_ms=latency_ms
    )