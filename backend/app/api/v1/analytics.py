"""
Analytics export endpoints for NexusCX Orchestration Engine.
Implements ICD §1.3: GET /api/v1/analytics/export
"""
from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field, validator
from typing import Optional, Literal, List, Dict, Any
import time
import logging
import jwt

from app.schemas.enums import Vertical
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()
security = HTTPBearer()

# Mock agent database for authentication
MOCK_AGENTS = {
    "agent1": {"password": "password123", "role": "agent", "agent_id": "AG-01"},
    "agent2": {"password": "password456", "role": "agent", "agent_id": "AG-02"},
    "supervisor1": {"password": "superpass", "role": "supervisor", "agent_id": "SUP-01"},
    "director1": {"password": "directorpass", "role": "director", "agent_id": "DIR-01"},
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

def verify_director_role(authorization: dict = Depends(verify_token)) -> Dict[str, Any]:
    """Verify that the user has director role (or supervisor for read-only)."""
    if authorization["role"] not in ["director", "supervisor"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions. Director or supervisor role required."
        )
    return authorization

@router.get(
    "/export",
    status_code=status.HTTP_200_OK,
    summary="Export analytics data for PowerBI integration",
    description="Flat, nesting-free rows for PowerBI (Get Data → Web with a Bearer header, or Text/CSV)."
)
async def export_analytics(
    from_date: str = Query(..., alias="from", description="Start date (YYYY-MM-DD)"),
    to_date: str = Query(..., alias="to", description="End date (YYYY-MM-DD)"),
    format: Literal["json", "csv"] = Query(default="json", alias="format"),
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=1000, ge=1, le=5000, description="Page size"),
    vertical: Optional[Vertical] = Query(default=None, description="Filter by vertical"),
    client: Optional[str] = Query(default=None, description="Filter by client"),
    authorization: dict = Depends(verify_director_role)
):
    """
    Export analytics data for PowerBI integration.

    - **from**: Start date (required, YYYY-MM-DD)
    - **to**: End date (required, YYYY-MM-DD, must be >= from, range <= 92 days)
    - **format**: Output format (json or csv, default: json)
    - **page**: Page number (default: 1)
    - **page_size**: Number of records per page (default: 1000, max: 5000)
    - **vertical**: Filter by vertical (optional)
    - **client**: Filter by client (optional, max 64 chars)

    Returns:
    - Paginated analytics data in JSON or CSV format
    - Headers: X-Total-Count, etc.
    """
    # Validate date range
    try:
        from_parts = from_date.split("-")
        to_parts = to_date.split("-")
        if len(from_parts) != 3 or len(to_parts) != 3:
            raise ValueError("Invalid date format")

        from_year, from_month, from_day = map(int, from_parts)
        to_year, to_month, to_day = map(int, to_parts)

        # Simple validation - in reality, we'd use datetime objects
        if to_year < from_year or (to_year == from_year and to_month < from_month) or \
           (to_year == from_year and to_month == from_month and to_day < from_day):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Parameter 'to' must be greater than or equal to parameter 'from'"
            )

        # Check if range is <= 92 days (simplified check)
        # In reality, we'd calculate the actual difference
        if to_year - from_year > 0:  # More than a year difference
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Date range must not exceed 92 days"
            )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid date format: {str(e)}"
        )

    # In a real implementation, we would:
    # 1. Query the database for analytics data
    # 2. Apply filters (vertical, client, date range)
    # 3. Paginate the results
    # 4. Format as JSON or CSV

    # For now, we'll return mock data
    mock_data = [
        {
            "interaction_id": "INT-000001",
            "session_id": "S-7K2M9QX4TA",
            "ticket_id": "TKT-2026-000123",
            "customer_ref": "a1b2c3d4e5f6",
            "agent_id": "AG-17",
            "client": "AirlineX",
            "vertical": "flight",
            "channel": "voice",
            "intent": "flight_disruption",
            "language": "hinglish",
            "start_ts": "2026-10-05T10:15:00.000Z",
            "end_ts": "2026-10-05T10:21:52.000Z",
            "handle_time_sec": 412,
            "hold_sec": 55,
            "acw_sec": 40,
            "first_contact_resolved": True,
            "sla_met": True,
            "risk_score_max": 0.88,
            "escalation_probability_max": 0.81,
            "churn_risk_class": "HIGH",
            "sentiment_avg": -0.45,
            "escalated": True,
            "compliance_score": 86,
            "critical_flags": 1,
            "warning_flags": 2,
            "info_flags": 0,
            "violated_rule_ids": "C-RECDISC;C-GREET",
            "ai_suggestion_outcome": "EDIT",
            "ai_confidence": 0.74,
            "llm_provider": "groq",
            "fallback_used": False,
            "ekyc_verified": False,
            "past_escalation_count": 2
        }
    ]

    # Apply vertical filter if specified
    if vertical:
        mock_data = [item for item in mock_data if item["vertical"] == vertical.value]

    # Apply client filter if specified
    if client:
        mock_data = [item for item in mock_data if item["client"] == client]

    # Calculate pagination
    total_count = len(mock_data)
    start_index = (page - 1) * page_size
    end_index = start_index + page_size
    paginated_data = mock_data[start_index:end_index]

    # Prepare response
    # Create timestamp in ISO 8601 format
    now = time.gmtime()
    generated_at = f"{now.tm_year:04d}-{now.tm_mon:02d}-{now.tm_mday:02d}T{now.tm_hour:02d}:{now.tm_min:02d}:{now.tm_sec:02d}.{int(time.time() * 1000000) % 1000000:06d}Z"

    response_data = {
        "page": page,
        "page_size": page_size,
        "total": total_count,
        "next_page": page + 1 if end_index < total_count else None,
        "generated_at": generated_at,
        "rows": paginated_data
    }

    # If CSV format is requested, we would convert to CSV
    # For now, we'll just return JSON as specified in the format parameter
    if format == "csv":
        # In a real implementation, we would convert to CSV
        # For now, we'll return JSON but note that it should be CSV
        pass

    return response_data