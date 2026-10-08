"""
WebSocket connection manager for NexusCX Orchestration Engine.
Implements ICD §2.1-2.5: WebSocket interface contracts.
"""
import asyncio
import json
import logging
import time
import uuid
from typing import Dict, List, Set, Optional, Any
from fastapi import WebSocket, WebSocketDisconnect, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError

from app.core.config import settings
from app.redis.client import redis_client

logger = logging.getLogger(__name__)

class ConnectionManager:
    """Manages WebSocket connections for live agent interactions."""

    def __init__(self):
        # Active connections: {agent_id: Set[websocket]}
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        # Connection metadata: {websocket: {agent_id, session_id, last_heartbeat}}
        self.connection_metadata: Dict[WebSocket, Dict[str, Any]] = {}
        # Session subscribers: {session_id: Set[websocket]}
        self.session_subscribers: Dict[str, Set[WebSocket]] = {}

    async def connect(
        self,
        websocket: WebSocket,
        token: str,
        session_id: str
    ) -> Dict[str, Any]:
        """
        Accept a WebSocket connection and authenticate the client.

        Args:
            websocket: The WebSocket connection
            token: JWT token for authentication
            session_id: Session ID to join

        Returns:
            Agent information if authentication successful

        Raises:
            WebSocketDisconnect: If authentication fails
        """
        # Authenticate the token
        try:
            payload = jwt.decode(
                token,
                settings.JWT_SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM]
            )
            agent_id = payload.get("sub")
            role = payload.get("role")

            if not agent_id or not role:
                raise JWTError("Invalid token payload")

        except JWTError as e:
            logger.warning(f"WebSocket authentication failed: {str(e)}")
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            raise WebSocketDisconnect(code=status.WS_1008_POLICY_VIOLATION)

        # Check role/session permissions
        # Agent can only join sessions assigned to their sub
        # Supervisor can join any session
        # For now, we'll allow any authenticated user to connect
        # In a real implementation, we would check session assignment

        # Accept the connection
        await websocket.accept()

        # Store connection metadata
        self.connection_metadata[websocket] = {
            "agent_id": agent_id,
            "role": role,
            "session_id": session_id,
            "last_heartbeat": time.time()
        }

        # Add to active connections
        if agent_id not in self.active_connections:
            self.active_connections[agent_id] = set()
        self.active_connections[agent_id].add(websocket)

        # Add to session subscribers
        if session_id not in self.session_subscribers:
            self.session_subscribers[session_id] = set()
        self.session_subscribers[session_id].add(websocket)

        # Initialize Redis stream subscription for this session
        # In a real implementation, we would set up Redis pub/sub here

        logger.info(
            f"WebSocket connected: agent_id={agent_id}, role={role}, "
            f"session_id={session_id}, total_connections={len(self.connection_metadata)}"
        )

        # Send SERVER_HELLO frame
        await self._send_server_hello(websocket, session_id)

        return {
            "agent_id": agent_id,
            "role": role,
            "session_id": session_id
        }

    def disconnect(self, websocket: WebSocket):
        """
        Remove a WebSocket connection from tracking.

        Args:
            websocket: The WebSocket connection to remove
        """
        if websocket not in self.connection_metadata:
            return

        metadata = self.connection_metadata[websocket]
        agent_id = metadata["agent_id"]
        session_id = metadata["session_id"]

        # Remove from active connections
        if agent_id in self.active_connections:
            self.active_connections[agent_id].discard(websocket)
            if not self.active_connections[agent_id]:
                del self.active_connections[agent_id]

        # Remove from session subscribers
        if session_id in self.session_subscribers:
            self.session_subscribers[session_id].discard(websocket)
            if not self.session_subscribers[session_id]:
                del self.session_subscribers[session_id]

        # Remove connection metadata
        del self.connection_metadata[websocket]

        logger.info(
            f"WebSocket disconnected: agent_id={agent_id}, session_id={session_id}, "
            f"remaining_connections={len(self.connection_metadata)}"
        )

    async def send_personal_message(
        self,
        message: Dict[str, Any],
        websocket: WebSocket
    ):
        """
        Send a message to a specific WebSocket connection.

        Args:
            message: Message to send
            websocket: Target WebSocket connection
        """
        try:
            await websocket.send_text(json.dumps(message))
        except Exception as e:
            logger.error(f"Failed to send personal message: {str(e)}")
            self.disconnect(websocket)

    async def broadcast_to_session(
        self,
        message: Dict[str, Any],
        session_id: str
    ):
        """
        Broadcast a message to all connections subscribed to a session.

        Args:
            message: Message to broadcast
            session_id: Session ID to broadcast to
        """
        if session_id not in self.session_subscribers:
            return

        # Create a copy of the set to avoid modification during iteration
        subscribers = self.session_subscribers[session_id].copy()
        disconnected = set()

        for websocket in subscribers:
            try:
                await websocket.send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Failed to broadcast to session {session_id}: {str(e)}")
                disconnected.add(websocket)

        # Clean up disconnected websockets
        for websocket in disconnected:
            self.disconnect(websocket)

    async def broadcast_to_role(
        self,
        message: Dict[str, Any],
        role: str
    ):
        """
        Broadcast a message to all connections with a specific role.

        Args:
            message: Message to broadcast
            role: Role to broadcast to (agent, supervisor, director)
        """
        disconnected = set()

        for websocket, metadata in self.connection_metadata.items():
            if metadata["role"] == role:
                try:
                    await websocket.send_text(json.dumps(message))
                except Exception as e:
                    logger.error(f"Failed to broadcast to role {role}: {str(e)}")
                    disconnected.add(websocket)

        # Clean up disconnected websockets
        for websocket in disconnected:
            self.disconnect(websocket)

    async def handle_heartbeat(self, websocket: WebSocket):
        """
        Handle heartbeat from client to prevent timeout disconnection.

        Args:
            websocket: The WebSocket connection
        """
        if websocket in self.connection_metadata:
            self.connection_metadata[websocket]["last_heartbeat"] = time.time()

    def get_connection_count(self) -> int:
        """Get the total number of active connections."""
        return len(self.connection_metadata)

    def get_session_connection_count(self, session_id: str) -> int:
        """Get the number of connections for a specific session."""
        if session_id not in self.session_subscribers:
            return 0
        return len(self.session_subscribers[session_id])

    def get_role_connection_count(self, role: str) -> int:
        """Get the number of connections for a specific role."""
        count = 0
        for metadata in self.connection_metadata.values():
            if metadata["role"] == role:
                count += 1
        return count

    async def _send_server_hello(self, websocket: WebSocket, session_id: str):
        """
        Send SERVER_HELLO frame to a newly connected client.

        Args:
            websocket: The WebSocket connection
            session_id: Session ID
        """
        # In a real implementation, we would get this information from Redis
        server_hello = {
            "v": 1,
            "frame_type": "SERVER_HELLO",
            "frame_id": str(uuid.uuid4()),
            "session_id": session_id,
            "seq": None,  # Server frames don't have seq in SERVER_HELLO
            "ts": time.strftime("%Y-%m-%dT%H:%M:%S.%fZ", time.gmtime()),
            "payload": {
                "server_time": time.strftime("%Y-%m-%dT%H:%M:%S.%fZ", time.gmtime()),
                "session_status": "active",
                "seq_head": 0,
                "replay_from": 0,
                "replay_count": 0,
                "replay_truncated": False,
                "limits": {
                    "max_text_bytes": 65536,
                    "ping_interval_sec": 20,
                    "pong_timeout_sec": 10
                }
            }
        }

        await self.send_personal_message(server_hello, websocket)

# Global connection manager instance
manager = ConnectionManager()