"""
Manual required agent node for NexusCX Orchestration Engine.
Handles cases where AI confidence is too low for automatic processing.
"""
from typing import Dict, Any, List, Optional, TypedDict
import logging

logger = logging.getLogger(__name__)

# Reuse RecommendedAction from backoffice_executor
from app.agents.nodes.backoffice_executor import RecommendedAction

def manual_required(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Manual required node - handles low confidence cases.

    Written by: backoffice_executor
    Semantics: Per RecommendedAction; status="manual_required" iff agent_confidence < 0.60

    Args:
        state: Current agent state

    Returns:
        Partial state update with recommended_action
    """
    logger.debug("Handling manual required case")

    # Get current recommended action or create default
    current_action = state.get("recommended_action", {})
    revision_count = current_action.get("revision_count", 0)

    # Increment revision count (but cap at 2 to prevent infinite loops)
    new_revision_count = min(revision_count + 1, 2)

    # Create recommended action for manual required
    recommended_action: RecommendedAction = {
        "status": "manual_required",
        "suggested_text": None,  # No suggestion when manual required
        "tool_calls": [],        # No tool calls when manual required
        "revision_count": new_revision_count,
        "low_confidence_message": "Low AI Confidence: Manual Agent Intervention Required"
    }

    logger.debug(f"Manual required: revision_count={new_revision_count}")

    return {
        "recommended_action": recommended_action
    }