"""
Backoffice executor agent node for NexusCX Orchestration Engine.
Implements ICD §5.2: ToolCallDict and RecommendedAction schemas.
"""
from typing import Dict, Any, List, Optional, TypedDict
import logging
import uuid

from app.schemas.enums import Vertical

logger = logging.getLogger(__name__)

# Define ToolCallDict based on ICD §5.1
class ToolCallDict(TypedDict):
    action_id: str  # "a1", "a2", ...
    tool: str       # draft_email | trigger_refund_api | update_ticket_state | schedule_callback | verify_ekyc_checklist
    args: Dict[str, Any]
    requires_approval: bool  # always True in v1
    grounding_chunk_ids: List[str]  # non-empty, subset of retrieved_sops chunk_ids

# Define RecommendedAction based on ICD §5.1
class RecommendedAction(TypedDict):
    status: str                     # "ready" | "manual_required" | "revising"
    suggested_text: Optional[str]
    tool_calls: List[ToolCallDict]
    revision_count: int             # 0-2; guardrail loop bound
    low_confidence_message: Optional[str]

def backoffice_executor(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Backoffice executor node - generates suggested actions based on retrieved SOPs.

    Written by: backoffice_executor, manual_required
    Semantics: Per RecommendedAction; status="manual_required" iff agent_confidence < 0.60

    Args:
        state: Current agent state

    Returns:
        Partial state update with recommended_action
    """
    logger.debug("Executing backoffice actions")

    customer_metadata = state.get("customer_metadata", {})
    retrieved_sops = state.get("retrieved_sops", [])
    agent_confidence = state.get("agent_confidence", 0.0)
    revision_count = state.get("recommended_action", {}).get("revision_count", 0)

    # Determine if manual intervention is required
    manual_required = agent_confidence < 0.60

    # Initialize tool calls
    tool_calls: List[ToolCallDict] = []

    # Generate suggested text based on retrieved SOPs
    suggested_text = None
    low_confidence_message = None

    if retrieved_sops and not manual_required:
        # Generate suggested text from the top SOP
        top_sop = retrieved_sops[0]
        suggested_text = f"Based on our procedures: {top_sop['text']}"

        # Generate tool calls based on intent and vertical
        intent = customer_metadata.get("intent", "other")
        vertical = customer_metadata.get("vertical", "")

        if intent == "flight_disruption" and vertical == "flight":
            # Flight disruption - suggest refund processing
            tool_calls.append({
                "action_id": "a1",
                "tool": "trigger_refund_api",
                "args": {
                    "pnr": "6E4X9Q",  # Would be extracted from ticket
                    "amount_inr": 8450,
                    "reason": "airline_cancellation"
                },
                "requires_approval": True,
                "grounding_chunk_ids": [top_sop["chunk_id"]]
            })
        elif intent == "billing" and vertical == "billing":
            # Billing issue - suggest payment plan or refund
            tool_calls.append({
                "action_id": "a1",
                "tool": "trigger_refund_api",
                "args": {
                    "amount_inr": 2500,
                    "reason": "billing_adjustment"
                },
                "requires_approval": True,
                "grounding_chunk_ids": [top_sop["chunk_id"]]
            })

    elif manual_required:
        # Set low confidence message
        low_confidence_message = "Low AI Confidence: Manual Agent Intervention Required"

    # Determine status
    if manual_required:
        status = "manual_required"
    elif retrieved_sops and tool_calls:
        status = "ready"
    else:
        status = "revising"

    # Create recommended action
    recommended_action: RecommendedAction = {
        "status": status,
        "suggested_text": suggested_text,
        "tool_calls": tool_calls,
        "revision_count": revision_count,
        "low_confidence_message": low_confidence_message
    }

    logger.debug(f"Generated recommended action: {status} with {len(tool_calls)} tool calls")

    return {
        "recommended_action": recommended_action
    }