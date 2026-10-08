"""
Authentication endpoints for NexusCX Orchestration Engine.
Implements ICD §1.5: POST /api/v1/auth/login
"""
from fastapi import APIRouter, Header, HTTPException, status
from pydantic import BaseModel, Field
import jwt
import time
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()

# Mock agent database
MOCK_AGENTS = {
    "agent1": {"password": "password123", "role": "agent", "agent_id": "AG-01"},
    "agent2": {"password": "password456", "role": "agent", "agent_id": "AG-02"},
    "supervisor1": {"password": "superpass", "role": "supervisor", "agent_id": "SUP-01"},
    "director1": {"password": "directorpass", "role": "director", "agent_id": "DIR-01"},
}

class LoginRequest(BaseModel):
    username: str = Field(..., example="agent1")
    password: str = Field(..., example="password123")

class LoginResponse(BaseModel):
    access_token: str = Field(..., example="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...")
    token_type: str = Field(default="bearer")
    expires_in: int = Field(..., example=28800)
    role: str = Field(..., example="agent")
    agent_id: str = Field(..., example="AG-01")

@router.post(
    "/login",
    response_model=LoginResponse,
    status_code=status.HTTP_200_OK,
    summary="Authenticate agent and receive JWT token",
    description="Required by every authenticated contract above."
)
async def login(request: LoginRequest):
    """
    Authenticate agent and receive JWT token.

    - **username**: Agent username
    - **password**: Agent password

    Returns:
    - **access_token**: JWT token for authentication
    - **token_type**: Token type (bearer)
    - **expires_in**: Token expiration time in seconds
    - **role**: Agent role (agent, supervisor, or director)
    - **agent_id**: Unique agent identifier
    """
    # Validate credentials
    agent = MOCK_AGENTS.get(request.username)
    if not agent or agent["password"] != request.password:
        logger.warning(f"Failed login attempt for username: {request.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )

    # Generate JWT token
    # In a real implementation, we would use a proper secret key
    secret_key = "your-secret-key-here"  # Should be loaded from environment
    payload = {
        "sub": agent["agent_id"],
        "role": agent["role"],
        "iat": int(time.time()),
        "exp": int(time.time()) + 28800,  # 8 hours
        "jti": f"{int(time.time())}-{agent['agent_id']}"
    }

    access_token = jwt.encode(payload, secret_key, algorithm="HS256")

    logger.info(f"Successful login for agent: {agent['agent_id']} with role: {agent['role']}")

    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=28800,
        role=agent["role"],
        agent_id=agent["agent_id"]
    )