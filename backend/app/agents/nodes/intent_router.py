"""
Intent router agent node for NexusCX Orchestration Engine.
Implements ICD §5.2: CustomerMetadata schema and write ownership.
"""
from typing import Dict, Any, TypedDict, Optional
from langchain_core.messages import BaseMessage, HumanMessage
from app.schemas.enums import Vertical, Language
import logging

logger = logging.getLogger(__name__)

# Define CustomerMetadata based on ICD §5.1
class CustomerMetadata(TypedDict):
    ticket_id: str
    customer_id: str
    channel: str  # "voice" | "chat" | "email"
    vertical: str  # §1.1 enum
    language: str  # "english" | "hinglish"
    hold_count: int
    transfer_count: int
    prior_tickets_30d: int
    avg_handling_time_sec: float  # WEKA input 1
    past_escalation_count: int    # WEKA input 2
    ekyc_verified: bool           # WEKA input 5
    intent: str                   # "billing"|"technical_support"|"flight_disruption"|"ekyc"|"other"
    sub_intent: str
    intent_confidence: float      # 0.0-1.0
    sentiment: float              # -1.0..1.0 (latest customer turn)
    urgency: str                  # "low"|"medium"|"high"

def intent_router(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Intent router node - extracts intent and customer metadata from messages.

    Written by: entry (profile/ticket), intent_router (intent, sentiment)
    Semantics: Per §5.1

    Args:
        state: Current agent state

    Returns:
        Partial state update with customer_metadata
    """
    logger.debug("Routing intent from messages")

    # In a real implementation, we would:
    # 1. Extract information from the ticket/email
    # 2. Use NLP/LLM to determine intent and sentiment
    # 3. Populate customer_metadata accordingly

    # For now, we'll return mock data based on the initial state
    # Extract the latest human message
    latest_message = None
    for message in reversed(state["messages"]):
        if isinstance(message, HumanMessage):
            latest_message = message
            break

    if not latest_message:
        # If no human message, return empty update
        return {}

    # Mock intent detection based on keywords
    text = latest_message.content.lower()

    # Determine intent
    if any(word in text for word in ["flight", "cancelled", "delay", "baggage"]):
        intent = "flight_disruption"
        sub_intent = "refund_status" if "refund" in text else "status_update"
    elif any(word in text for word in ["bill", "payment", "invoice", "charge"]):
        intent = "billing"
        sub_intent = "payment_issue"
    elif any(word in text for word in ["technical", "error", "broken", "not working"]):
        intent = "technical_support"
        sub_intent = "troubleshooting"
    elif any(word in text for word in ["kyc", "verify", "identity", "document"]):
        intent = "ekyc"
        sub_intent = "verification"
    else:
        intent = "other"
        sub_intent = "general_inquiry"

    # Determine sentiment (simplified)
    sentiment = 0.0
    if any(word in text for word in ["angry", "frustrated", "upset", "terrible"]):
        sentiment = -0.8
    elif any(word in text for word in ["happy", "satisfied", "thanks", "great"]):
        sentiment = 0.7
    elif any(word in text for word in ["okay", "fine", "all right"]):
        sentiment = 0.1

    # Determine intent confidence (simplified)
    intent_confidence = 0.8 if intent != "other" else 0.3

    # Determine urgency based on sentiment and intent
    urgency = "low"
    if sentiment < -0.5 or intent in ["flight_disruption", "technical_support"]:
        urgency = "high"
    elif sentiment < 0:
        urgency = "medium"

    # Create customer metadata update
    # In a real implementation, we would extract this from the ticket data
    customer_metadata: CustomerMetadata = {
        "ticket_id": state.get("customer_metadata", {}).get("ticket_id", "TKT-2026-000123"),
        "customer_id": state.get("customer_metadata", {}).get("customer_id", "CUST-88231"),
        "channel": state.get("customer_metadata", {}).get("channel", "voice"),
        "vertical": state.get("customer_metadata", {}).get("vertical", "flight"),
        "language": state.get("customer_metadata", {}).get("language", "hinglish"),
        "hold_count": state.get("customer_metadata", {}).get("hold_count", 0),
        "transfer_count": state.get("customer_metadata", {}).get("transfer_count", 0),
        "prior_tickets_30d": state.get("customer_metadata", {}).get("prior_tickets_30d", 3),
        "avg_handling_time_sec": state.get("customer_metadata", {}).get("avg_handling_time_sec", 412.0),
        "past_escalation_count": state.get("customer_metadata", {}).get("past_escalation_count", 2),
        "ekyc_verified": state.get("customer_metadata", {}).get("ekyc_verified", False),
        "intent": intent,
        "sub_intent": sub_intent,
        "intent_confidence": intent_confidence,
        "sentiment": sentiment,
        "urgency": urgency
    }

    return {
        "customer_metadata": customer_metadata
    }