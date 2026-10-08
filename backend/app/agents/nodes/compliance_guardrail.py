"""
Compliance guardrail agent node for NexusCX Orchestration Engine.
Implements ICD §5.2: compliance_flags schema and write ownership.
"""
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)

def compliance_guardrail(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Compliance guardrail node - checks for compliance violations.

    Written by: compliance_guardrail
    Semantics: {rule_id: violated}: true = violation detected, false = checked and clear; absent = not evaluated.

    Args:
        state: Current agent state

    Returns:
        Partial state update with compliance_flags
    """
    logger.debug("Checking compliance guardrails")

    customer_metadata = state.get("customer_metadata", {})
    retrieved_sops = state.get("retrieved_sops", [])
    recommended_action = state.get("recommended_action", {})

    # Initialize compliance flags
    compliance_flags: Dict[str, bool] = {}

    # In a real implementation, we would check specific compliance rules
    # based on the retrieved SOPs, recommended actions, and customer metadata

    # For now, we'll simulate some compliance checks
    vertical = customer_metadata.get("vertical", "")

    # Check for common compliance issues based on vertical
    if vertical == "flight":
        # Flight-specific compliance checks
        # Check if refund amount exceeds policy limits
        for tool_call in recommended_action.get("tool_calls", []):
            if tool_call.get("tool") == "trigger_refund_api":
                args = tool_call.get("args", {})
                amount = args.get("amount_inr", 0)
                # Example: Flag if refund exceeds 10,000 INR without approval
                if amount > 10000:
                    compliance_flags["C-REFUND-LIMIT"] = True
                else:
                    compliance_flags["C-REFUND-LIMIT"] = False

        # Check if we have proper grounding for the action
        if recommended_action.get("tool_calls"):
            has_grounding = False
            for tool_call in recommended_action.get("tool_calls", []):
                grounding_ids = set(tool_call.get("grounding_chunk_ids", []))
                retrieved_ids = {sop["chunk_id"] for sop in retrieved_sops}
                if grounding_ids and grounding_ids.issubset(retrieved_ids):
                    has_grounding = True
                    break

            if not has_grounding:
                compliance_flags["C-GROUNDING"] = True
            else:
                compliance_flags["C-GROUNDING"] = False

    # Add some generic compliance checks
    # Check for missing customer verification
    if not customer_metadata.get("ekyc_verified", False):
        compliance_flags["C-EKYC-VERIFIED"] = False  # Violation
    else:
        compliance_flags["C-EKYC-VERIFIED"] = True   # Compliant

    # Check for high-risk transactions
    intent = customer_metadata.get("intent", "")
    if intent in ["billing", "flight_disruption"] and customer_metadata.get("past_escalation_count", 0) > 3:
        compliance_flags["C-HIGH-RISK"] = True
    else:
        compliance_flags["C-HIGH-RISK"] = False

    logger.debug(f"Compliance check completed: {len([k for k, v in compliance_flags.items() if v])} violations found")

    return {
        "compliance_flags": compliance_flags
    }