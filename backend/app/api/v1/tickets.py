"""
Ticket ingest endpoints for NexusCX Orchestration Engine.
Implements ICD §1.1: POST /api/v1/tickets/ingest
"""
from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field, validator
from typing import Optional, Literal, Dict, Any
import uuid
import time
import jwt
import logging

from app.schemas.enums import Vertical, Language, ContentFormat, SourceType, Channel
from app.schemas.ticket import TicketIngestRequest, TicketIngestResponse
from app.core.config import settings
from app.rag.store import upsert_sop_chunks, search_sops

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
    "/ingest",
    response_model=TicketIngestResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Ingest a ticket or email for processing",
    description="Ingests one ticket or email. Processing is asynchronous: the response confirms acceptance; results arrive on the WebSocket."
)
async def ingest_ticket(
    request: TicketIngestRequest,
    http_request: Request,
    authorization: dict = Depends(verify_token),
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    x_request_id: Optional[str] = Header(None, alias="X-Request-ID")
):
    """
    Ingest a ticket or email for asynchronous processing.

    - **source_type**: Type of source (ticket or email)
    - **ticket_id**: Unique ticket identifier (format: TKT-XXXX-XXXXXX)
    - **customer_id**: Unique customer identifier (format: CUST-XXXXXXXXXX)
    - **channel**: Communication channel (voice, chat, or email)
    - **subject**: Ticket subject (optional, max 200 chars)
    - **raw_text**: Ticket content (required, 1-8000 chars)
    - **content_format**: Format of content (text or html, default: text)
    - **language**: Language of content (english or hinglish)
    - **received_at**: Timestamp when ticket was received (ISO 8601)
    - **metadata**: Additional ticket metadata (hold_count, transfer_count, prior_tickets_30d, vertical)
    - **customer_profile**: Customer profile information

    Returns:
    - **session_id**: Unique session identifier for WebSocket connection
    - **interaction_id**: Unique interaction identifier
    - **ticket_id**: Echoed ticket identifier
    - **status**: Processing status (queued)
    - **ws_url**: WebSocket URL for real-time updates
    - **created_at**: Timestamp when request was processed
    """
    # Generate IDs
    session_id = f"S-{uuid.uuid4().hex[:10].upper()}"
    interaction_id = f"INT-{uuid.uuid4().hex[:6].upper()}"

    # In a real implementation, we would:
    # 1. Store the ticket in a database
    # 2. Publish to Redis channels for processing
    # 3. Initialize session state in Redis
    # 4. Start the LangGraph processing pipeline

    # For now, we'll simulate the processing by logging and returning the response
    logger.info(f"Ingested ticket {request.ticket_id} for customer {request.customer_id}")
    logger.info(f"Session ID: {session_id}, Interaction ID: {interaction_id}")

    # Construct WebSocket URL
    ws_url = f"ws://{http_request.url.hostname}:{http_request.url.port or 8000}/ws/live-stream/{session_id}"

    # Add authorization token as query parameter (as per ICD)
    # In a real implementation, we would extract the token from the authorization header
    mock_token = f"mock-token-{authorization['agent_id']}"
    ws_url += f"?token={mock_token}"

    # Create timestamp in ISO 8601 format
    now = time.gmtime()
    created_at = f"{now.tm_year:04d}-{now.tm_mon:02d}-{now.tm_mday:02d}T{now.tm_hour:02d}:{now.tm_min:02d}:{now.tm_sec:02d}.{int(time.time() * 1000000) % 1000000:06d}Z"

    return TicketIngestResponse(
        session_id=session_id,
        interaction_id=interaction_id,
        ticket_id=request.ticket_id,
        status="queued",
        ws_url=ws_url,
        created_at=created_at
    )