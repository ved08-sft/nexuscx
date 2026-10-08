"""
WebSocket endpoint for NexusCX Orchestration Engine.
Implements ICD §2.1: WebSocket connection handling.
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, Dict, Any
import logging

from app.ws.manager import manager

logger = logging.getLogger(__name__)

router = APIRouter()

@router.websocket("/ws/live-stream/{session_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    session_id: str,
    token: str = Query(...),
    last_seq: Optional[int] = Query(None, alias="last_seq")
):
    """
    WebSocket endpoint for live agent interactions.

    - **session_id**: Session ID from the URL path
    - **token**: JWT token for authentication (query parameter)
    - **last_seq**: Optional int ≥ 0; server replays retained frames with seq > last_seq

    Per ICD §2.1:
    `ws://localhost:8000/ws/live-stream/{session_id}?token=<JWT>&last_seq=<int>`
    """
    # Connect the client
    agent_info = await manager.connect(websocket, token, session_id)

    try:
        while True:
            # Wait for messages from the client
            data = await websocket.receive_text()

            # Parse the incoming message
            try:
                message = json.loads(data)
                await handle_client_message(websocket, message, session_id, agent_info)
            except json.JSONDecodeError:
                logger.warning(f"Received invalid JSON from client: {data}")
                # In a real implementation, we would send an ERROR frame
            except Exception as e:
                logger.error(f"Error handling client message: {str(e)}")
                # In a real implementation, we would send an ERROR frame

    except WebSocketDisconnect:
        logger.info(f"Client disconnected from session {session_id}")
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        manager.disconnect(websocket)

async def handle_client_message(
    websocket: WebSocket,
    message: Dict[str, Any],
    session_id: str,
    agent_info: Dict[str, Any]
):
    """
    Handle incoming messages from clients.

    Args:
        websocket: The WebSocket connection
        message: The parsed message
        session_id: Session ID
        agent_info: Information about the connected agent
    """
    # Validate frame structure
    if not isinstance(message, dict):
        logger.warning("Received non-dict message from client")
        return

    # Check version
    if message.get("v") != 1:
        logger.warning(f"Received message with unsupported version: {message.get('v')}")
        return

    # Handle different frame types
    frame_type = message.get("frame_type")

    if frame_type == "CLIENT_TRANSCRIPT_CHUNK":
        await handle_transcript_chunk(websocket, message, session_id, agent_info)
    elif frame_type == "AGENT_HITL_ACTION":
        await handle_hitl_action(websocket, message, session_id, agent_info)
    elif frame_type == "PING":
        await handle_ping(websocket, message)
    elif frame_type == "PONG":
        await handle_pong(websocket, message)
    else:
        logger.warning(f"Received unknown frame type from client: {frame_type}")

async def handle_transcript_chunk(
    websocket: WebSocket,
    message: Dict[str, Any],
    session_id: str,
    agent_info: Dict[str, Any]
):
    """
    Handle CLIENT_TRANSCRIPT_CHUNK frame from client.

    In a real implementation, this would:
    1. Validate the transcript chunk
    2. Publish to Redis channel:channel:live:transcripts:{session_id}
    3. Trigger LangGraph processing
    4. Send ACK frame back to client
    """
    logger.debug(f"Received transcript chunk for session {session_id}")

    # Send ACK frame
    ack_frame = {
        "v": 1,
        "frame_type": "ACK",
        "frame_id": str(uuid.uuid4()),
        "session_id": session_id,
        "seq": None,  # Client frames don't have seq
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S.%fZ", time.gmtime()),
        "payload": {
            "ack_frame_id": message.get("frame_id"),
            "status": "accepted",
            "reason": None,
            "execution_results": []
        }
    }

    await manager.send_personal_message(ack_frame, websocket)

async def handle_hitl_action(
    websocket: WebSocket,
    message: Dict[str, Any],
    session_id: str,
    agent_info: Dict[str, Any]
):
    """
    Handle AGENT_HITL_ACTION frame from client.

    In a real implementation, this would:
    1. Validate the HITL action
    2. Execute the approved action
    3. Send ACK frame back to client
    4. Update session state in Redis
    """
    logger.info(f"Received HITL action for session {session_id}: {message.get('payload', {}).get('action')}")

    # Send ACK frame
    ack_frame = {
        "v": 1,
        "frame_type": "ACK",
        "frame_id": str(uuid.uuid4()),
        "session_id": session_id,
        "seq": None,  # Client frames don't have seq
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S.%fZ", time.gmtime()),
        "payload": {
            "ack_frame_id": message.get("frame_id"),
            "status": "accepted",
            "reason": None,
            "execution_results": [
                {
                    "action_id": "a1",  # Would come from the message
                    "status": "executed",
                    "detail": "Action executed successfully"
                }
            ]
        }
    }

    await manager.send_personal_message(ack_frame, websocket)

async def handle_ping(
    websocket: WebSocket,
    message: Dict[str, Any]
):
    """
    Handle PING frame from client.

    Args:
        websocket: The WebSocket connection
        message: The parsed message
    """
    # Respond with PONG
    pong_frame = {
        "v": 1,
        "frame_type": "PONG",
        "frame_id": str(uuid.uuid4()),
        "session_id": message.get("session_id"),
        "seq": None,
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S.%fZ", time.gmtime()),
        "payload": {
            "ping_id": message.get("frame_id")
        }
    }

    await manager.send_personal_message(pong_frame, websocket)

async def handle_pong(
    websocket: WebSocket,
    message: Dict[str, Any]
):
    """
    Handle PONG frame from client.

    Args:
        websocket: The WebSocket connection
        message: The parsed message
    """
    # Update heartbeat timestamp
    await manager.handle_heartbeat(websocket)
    logger.debug(f"Received PONG from client for session {message.get('session_id')}")

# Import json at the top since we use it in multiple functions
import json
import time
import uuid
from typing import Dict, Any, Optional