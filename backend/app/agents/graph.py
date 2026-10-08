"""
LangGraph agentic engine for NexusCX Orchestration Engine.
Implements ICD §5: LangGraph Internal State Schema and transitions.
"""
from typing import Dict, Any, TypedDict, Annotated, List, Literal
from langchain_core.messages import BaseMessage, HumanMessage
from langgraph.graph.message import add_messages
from langgraph.graph import StateGraph, END

from app.agents.nodes.intent_router import intent_router
from app.agents.nodes.rag_retriever import rag_retriever
from app.agents.nodes.backoffice_executor import backoffice_executor
from app.agents.nodes.manual_required import manual_required
from app.agents.nodes.compliance_guardrail import compliance_guardrail

# Define the AgentState based on ICD §5
class AgentState(TypedDict):
    session_id: str
    messages: Annotated[List[BaseMessage], add_messages]
    customer_metadata: Dict[str, Any]
    retrieved_sops: List[Dict[str, Any]]
    compliance_flags: Dict[str, bool]
    weka_risk_score: float
    agent_confidence: float
    recommended_action: Dict[str, Any]
    fallback_active: bool

def create_agent_graph():
    """
    Create the LangGraph agentic engine based on ICD §5.4 transitions.

    Transitions:
    - intent_router → rag_retriever (always)
    - rag_retriever → backoffice_executor (agent_confidence >= 0.60)
    - rag_retriever → manual_required (agent_confidence < 0.60)
    - backoffice_executor, manual_required → compliance_guardrail (always)
    - compliance_guardrail → backoffice_executor (any compliance_flags[r] is True with critical severity AND revision_count < 2)
    - compliance_guardrail → END (otherwise)
    """
    # Create the state graph
    workflow = StateGraph(AgentState)

    # Add nodes
    workflow.add_node("intent_router", intent_router)
    workflow.add_node("rag_retriever", rag_retriever)
    workflow.add_node("backoffice_executor", backoffice_executor)
    workflow.add_node("manual_required", manual_required)
    workflow.add_node("compliance_guardrail", compliance_guardrail)

    # Set entry point
    workflow.set_entry_point("intent_router")

    # Add edges based on ICD §5.4 transitions
    workflow.add_edge("intent_router", "rag_retriever")  # always

    # Conditional edges from rag_retriever
    workflow.add_conditional_edges(
        "rag_retriever",
        lambda state: "backoffice_executor" if state["agent_confidence"] >= 0.60 else "manual_required",
        {
            "backoffice_executor": "backoffice_executor",
            "manual_required": "manual_required"
        }
    )

    # Both backoffice_executor and manual_required go to compliance_guardrail
    workflow.add_edge("backoffice_executor", "compliance_guardrail")
    workflow.add_edge("manual_required", "compliance_guardrail")

    # Conditional edges from compliance_guardrail
    workflow.add_conditional_edges(
        "compliance_guardrail",
        lambda state: "backoffice_executor" if (
            any(state["compliance_flags"].get(r, False) for r in ["C-RECDISC", "C-GREET"]) and  # Example critical rules
            state["recommended_action"].get("revision_count", 0) < 2
        ) else "END",
        {
            "backoffice_executor": "backoffice_executor",
            "END": END
        }
    )

    # Compile the graph
    return workflow.compile()

# Create the graph instance
agent_graph = create_agent_graph()