"""
RAG retriever agent node for NexusCX Orchestration Engine.
Implements ICD §5.2: RetrievedSop schema and write ownership.
"""
from typing import Dict, Any, List, Optional, TypedDict
import logging

from app.rag.store import search_sops

logger = logging.getLogger(__name__)

# Define RetrievedSop based on ICD §5.1
class RetrievedSop(TypedDict):
    chunk_id: str
    text: str  # <= 700 chars
    source: str
    page: int
    vertical: str
    score: float  # 0.0-1.0

def rag_retriever(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    RAG retriever node - retrieves relevant SOPs based on customer metadata.

    Written by: rag_retriever
    Semantics: Top-3 by fused score; [] if none

    Args:
        state: Current agent state

    Returns:
        Partial state update with retrieved_sops and agent_confidence
    """
    logger.debug("Retrieving relevant SOPs")

    # Extract query from customer metadata
    customer_metadata = state.get("customer_metadata", {})
    query_parts = []

    # Add intent and sub_intent to query
    if customer_metadata.get("intent"):
        query_parts.append(customer_metadata["intent"])
    if customer_metadata.get("sub_intent"):
        query_parts.append(customer_metadata["sub_intent"])

    # Add any relevant information from the latest message
    latest_message = None
    for message in reversed(state["messages"]):
        if hasattr(message, 'content') and message.content:
            query_parts.append(message.content)
            break

    query = " ".join(query_parts) if query_parts else "general inquiry"

    # Determine vertical from customer metadata
    vertical = customer_metadata.get("vertical")
    if vertical:
        # Convert string to enum if needed
        try:
            from app.schemas.enums import Vertical
            vertical_enum = Vertical(vertical)
        except ValueError:
            vertical_enum = None
    else:
        vertical_enum = None

    # Perform RAG search
    try:
        results, confidence = search_sops(
            query=query,
            vertical=vertical_enum.value if vertical_enum else None,
            top_k=3
        )

        # Convert results to RetrievedSop format
        retrieved_sops: List[RetrievedSop] = []
        for result in results:
            retrieved_sop: RetrievedSop = {
                "chunk_id": result.chunk_id,
                "text": result.text[:700],  # Ensure <= 700 chars
                "source": result.source,
                "page": result.page,
                "vertical": result.vertical.value if hasattr(result.vertical, 'value') else str(result.vertical),
                "score": result.score
            }
            retrieved_sops.append(retrieved_sop)

        # Calculate agent confidence as retrieval confidence × intent confidence
        retrieval_confidence = confidence
        intent_confidence = customer_metadata.get("intent_confidence", 0.0)
        agent_confidence = retrieval_confidence * intent_confidence

        logger.debug(f"Retrieved {len(retrieved_sops)} SOPs with confidence {agent_confidence:.3f}")

        return {
            "retrieved_sops": retrieved_sops,
            "agent_confidence": agent_confidence
        }

    except Exception as e:
        logger.error(f"Error in RAG retrieval: {str(e)}")
        # Return empty results on error
        return {
            "retrieved_sops": [],
            "agent_confidence": 0.0
        }