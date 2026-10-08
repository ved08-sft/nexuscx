"""
Phase 3 implementation test for NexusCX Orchestration Engine.
Tests the Multi-Agent orchestrator, Supervisor, and specialized agents.
"""
import asyncio
import logging
from typing import Dict, Any

from app.agents.graph import agent_graph
from app.agents.nodes.intent_router import CustomerMetadata

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_initial_state() -> Dict[str, Any]:
    """Create an initial state for testing the agent graph."""
    from langchain_core.messages import HumanMessage

    return {
        "session_id": "S-TEST001",
        "messages": [HumanMessage(content="Meri flight 6E-4X9Q cancel ho gayi hai. Refund kab milega?")],
        "customer_metadata": {
            "ticket_id": "TKT-2026-000123",
            "customer_id": "CUST-88231",
            "channel": "voice",
            "vertical": "flight",
            "language": "hinglish",
            "hold_count": 0,
            "transfer_count": 0,
            "prior_tickets_30d": 3,
            "avg_handling_time_sec": 412.0,
            "past_escalation_count": 2,
            "ekyc_verified": False,
            "intent": "other",  # Will be updated by intent_router
            "sub_intent": "",
            "intent_confidence": 0.0,
            "sentiment": 0.0,
            "urgency": "low"
        },
        "retrieved_sops": [],
        "compliance_flags": {},
        "weka_risk_score": 0.0,
        "agent_confidence": 0.0,
        "recommended_action": {
            "status": "revising",
            "suggested_text": None,
            "tool_calls": [],
            "revision_count": 0,
            "low_confidence_message": None
        },
        "fallback_active": False
    }

async def test_agent_graph():
    """Test the agent graph with a sample input."""
    logger.info("Starting Phase 3 agent graph test")

    # Create initial state
    initial_state = create_initial_state()
    logger.info(f"Initial state: {initial_state}")

    # Run the agent graph
    try:
        # Note: In a real implementation, we would use agent_graph.ainvoke()
        # But for simplicity in this test, we'll invoke synchronously
        final_state = agent_graph.invoke(initial_state)

        logger.info(f"Final state: {final_state}")

        # Validate the results
        assert "customer_metadata" in final_state
        assert "retrieved_sops" in final_state
        assert "compliance_flags" in final_state
        assert "weka_risk_score" in final_state
        assert "agent_confidence" in final_state
        assert "recommended_action" in final_state

        logger.info("Phase 3 agent graph test PASSED")
        return True

    except Exception as e:
        logger.error(f"Phase 3 agent graph test FAILED: {str(e)}")
        return False

if __name__ == "__main__":
    # Run the test
    result = asyncio.run(test_agent_graph())
    if result:
        print("PASS: Phase 3 implementation test PASSED")
    else:
        print("FAIL: Phase 3 implementation test FAILED")