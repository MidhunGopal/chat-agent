"""
LangGraph Workflow – Customer / Agent Intent Routing Ecosystem

Implements the full flow from the architecture diagrams:

  Customer Interaction
       ↓
  Capture Input
       ↓
  NLP Processing & Intent Classification
       ↓
  ◇ Intent Type? ─────────────────────────────────────────
  │  new_application  → Application Servicing Agent       │
  │  underwriting     → Underwriting Support Agent        │
  │  policy_query     → Policy Servicing Agent            │
  │  general_info     → Policy Information Agent          │
  │  document_upload  → Document Intelligence Agent       │
  └───────────────────────────────────────────────────────┘
       ↓
  Sentiment Analysis
       ↓
  ◇ Satisfaction?
  │  HIGH    → Deliver Response → Log & Learn → END
  │  LOW     → Refine / Support Human → loop
  │  UNKNOWN → Escalate to Human Agent → Human Handoff → END
"""

from __future__ import annotations

from typing import Any, Dict, Literal

from langgraph.graph import StateGraph, END

from agents import (
    intent_router,
    application_servicing,
    underwriting_support,
    policy_servicing,
    policy_information,
    document_intelligence,
    sentiment_analyzer,
)
from data.hub import get_data_hub
from utils.helpers import new_id, now_iso

import config


# ── State type (dict-based for LangGraph) ────────────────────────────────────

# LangGraph works with typed dicts.  We define the schema here.
from typing import TypedDict, Optional, List


class WorkflowState(TypedDict, total=False):
    # Input
    session_id: str
    input_channel: str
    user_input: str
    uploaded_document: Optional[str]

    # User context
    user_id: str
    user_role: str

    # Intent
    intent: str
    intent_confidence: float
    entities: Dict[str, Any]

    # Agent
    routed_agent: str
    agent_response: str
    context_docs: List[str]

    # Sentiment
    sentiment_score: float
    sentiment_level: str
    sentiment_action: str
    refinement_suggestion: str

    # Output
    final_response: str
    escalated: bool
    escalation_reason: str
    human_handoff: bool

    # Internal
    refine_count: int
    interaction_log: List[Dict[str, Any]]


# ── Node functions ───────────────────────────────────────────────────────────

def capture_input(state: WorkflowState) -> WorkflowState:
    """Capture and sanitize user input."""
    if not state.get("session_id"):
        state["session_id"] = new_id("session")
    if not state.get("input_channel"):
        state["input_channel"] = "direct_partner_website"
    state["refine_count"] = state.get("refine_count", 0)
    return state


def classify_intent(state: WorkflowState) -> WorkflowState:
    """NLP Processing & Intent Classification."""
    result = intent_router.classify_intent(state["user_input"])
    state["intent"] = result["intent"]
    state["intent_confidence"] = result["confidence"]
    state["entities"] = result["entities"]
    return state


def route_to_agent(state: WorkflowState) -> str:
    """Conditional edge: route based on intent type."""
    intent = state.get("intent", "general_info")
    mapping = {
        "new_application": "application_servicing_node",
        "underwriting_status": "underwriting_support_node",
        "policy_query": "policy_servicing_node",
        "general_info": "policy_information_node",
        "document_upload": "document_intelligence_node",
        "out_of_scope": "out_of_scope_node",
    }
    return mapping.get(intent, "policy_information_node")


def application_servicing_node(state: WorkflowState) -> WorkflowState:
    """Route to Application Servicing Agent."""
    state["routed_agent"] = "Application Servicing Agent"
    state["agent_response"] = application_servicing.handle(
        state["user_input"], state.get("entities", {}),
        user_id=state.get("user_id", ""), user_role=state.get("user_role", "customer"),
    )
    return state


def underwriting_support_node(state: WorkflowState) -> WorkflowState:
    """Route to Underwriting Support Agent."""
    state["routed_agent"] = "Underwriting Support Agent"
    state["agent_response"] = underwriting_support.handle(
        state["user_input"], state.get("entities", {}),
        user_id=state.get("user_id", ""), user_role=state.get("user_role", "customer"),
    )
    return state


def policy_servicing_node(state: WorkflowState) -> WorkflowState:
    """Route to Policy Servicing Agent."""
    state["routed_agent"] = "Policy Servicing Agent"
    state["agent_response"] = policy_servicing.handle(
        state["user_input"], state.get("entities", {}),
        user_id=state.get("user_id", ""), user_role=state.get("user_role", "customer"),
    )
    return state


def policy_information_node(state: WorkflowState) -> WorkflowState:
    """Route to Policy Information Agent."""
    state["routed_agent"] = "Policy Information Agent"
    state["agent_response"] = policy_information.handle(
        state["user_input"], state.get("entities", {})
    )
    return state


def document_intelligence_node(state: WorkflowState) -> WorkflowState:
    """Route to Document Intelligence Agent."""
    state["routed_agent"] = "Document Intelligence Agent"
    state["agent_response"] = document_intelligence.handle(
        state["user_input"],
        state.get("entities", {}),
        state.get("uploaded_document"),
    )
    return state

  
def out_of_scope_node(state: WorkflowState) -> WorkflowState:
    """Handle out-of-scope queries with a polite decline."""
    state["routed_agent"] = "Out-of-Scope Handler"

    user_role = state.get("user_role", "guest")

    if user_role in ("customer", "agent", "admin"):
        # Authenticated users see the full capability list
        state["agent_response"] = (
            "I'm sorry, but I can only help with insurance-related questions such as:\n\n"
            "- **Policy information** \u2013 coverage, premiums, claims, renewals\n"
            "- **Applications** \u2013 new applications, status checks\n"
            "- **Underwriting** \u2013 risk assessment, approval status\n"
            "- **Documents** \u2013 uploading or processing insurance documents\n"
            "- **General insurance FAQs** \u2013 products, processes, contact info\n\n"
            "Please ask me something related to your insurance needs and I'll be happy to assist!"
        )
    else:
        # Guest users can only access the knowledge agent
        state["agent_response"] = (
            "I'm sorry, but I can only help with insurance-related questions such as:\n\n"
            "- **General insurance FAQs** \u2013 products, processes, contact info\n\n"
            "Please ask me something related to your insurance needs and I'll be happy to assist!\n\n"
            "*To access policies, applications, and more features, please **log in**.*"
        )

    return state


def sentiment_analysis_node(state: WorkflowState) -> WorkflowState:
    """Sentiment Analysis on the agent response."""
    result = sentiment_analyzer.analyze(state["user_input"], state["agent_response"])
    state["sentiment_score"] = result["sentiment_score"]
    state["sentiment_level"] = result["satisfaction_level"]
    state["sentiment_action"] = result["action"]
    state["refinement_suggestion"] = result.get("refinement_suggestion", "")
    return state


def route_on_sentiment(state: WorkflowState) -> str:
    """Conditional edge: route based on sentiment analysis."""
    action = state.get("sentiment_action", "deliver")
    refine_count = state.get("refine_count", 0)

    if action == "deliver":
        return "deliver_response_node"
    elif action == "refine" and refine_count < 2:
        return "refine_response_node"
    elif action == "escalate":
        return "escalate_node"
    else:
        # If already refined twice, deliver anyway
        return "deliver_response_node"


def refine_response_node(state: WorkflowState) -> WorkflowState:
    """Refine Response or Support Human Agent."""
    refined = sentiment_analyzer.refine_response(
        state["user_input"],
        state["agent_response"],
        state.get("refinement_suggestion", "Make it more helpful and empathetic."),
    )
    state["agent_response"] = refined
    state["refine_count"] = state.get("refine_count", 0) + 1
    return state


def deliver_response_node(state: WorkflowState) -> WorkflowState:
    """Deliver Response to the customer."""
    state["final_response"] = state["agent_response"]
    state["escalated"] = False
    state["human_handoff"] = False
    return state


def escalate_node(state: WorkflowState) -> WorkflowState:
    """Escalate to Human Agent → Human Handoff."""
    state["escalated"] = True
    state["escalation_reason"] = "unknown_complexity"
    state["human_handoff"] = True
    state["final_response"] = (
        f"I understand your concern. I'm connecting you with a specialist who can "
        f"better assist you with this matter.\n\n"
        f"**Summary for human agent:**\n"
        f"- **Query:** {state['user_input']}\n"
        f"- **Intent:** {state.get('intent', 'N/A')}\n"
        f"- **Initial AI Response:** {state['agent_response'][:500]}\n"
        f"- **Sentiment Score:** {state.get('sentiment_score', 'N/A')}\n"
    )
    return state


def log_interaction_node(state: WorkflowState) -> WorkflowState:
    """Log Interaction & Learn."""
    hub = get_data_hub()
    hub.log_interaction(
        {
            "log_id": new_id("log"),
            "session_id": state.get("session_id", ""),
            "channel": state.get("input_channel", ""),
            "intent": state.get("intent", ""),
            "agent_used": state.get("routed_agent", ""),
            "user_query": state.get("user_input", ""),
            "response": state.get("final_response", "")[:2000],
            "sentiment_score": state.get("sentiment_score", 0.0),
            "escalated": state.get("escalated", False),
            "timestamp": now_iso(),
        }
    )
    return state


# ── Build the Graph ──────────────────────────────────────────────────────────

def build_workflow() -> StateGraph:
    """Construct and compile the LangGraph workflow."""

    workflow = StateGraph(WorkflowState)

    # Add nodes
    workflow.add_node("capture_input", capture_input)
    workflow.add_node("classify_intent", classify_intent)
    workflow.add_node("application_servicing_node", application_servicing_node)
    workflow.add_node("underwriting_support_node", underwriting_support_node)
    workflow.add_node("policy_servicing_node", policy_servicing_node)
    workflow.add_node("policy_information_node", policy_information_node)
    workflow.add_node("document_intelligence_node", document_intelligence_node)
    workflow.add_node("out_of_scope_node", out_of_scope_node)
    workflow.add_node("sentiment_analysis_node", sentiment_analysis_node)
    workflow.add_node("refine_response_node", refine_response_node)
    workflow.add_node("deliver_response_node", deliver_response_node)
    workflow.add_node("escalate_node", escalate_node)
    workflow.add_node("log_interaction_node", log_interaction_node)

    # Entry point
    workflow.set_entry_point("capture_input")

    # Edges
    workflow.add_edge("capture_input", "classify_intent")

    # Conditional: intent routing
    workflow.add_conditional_edges(
        "classify_intent",
        route_to_agent,
        {
            "application_servicing_node": "application_servicing_node",
            "underwriting_support_node": "underwriting_support_node",
            "policy_servicing_node": "policy_servicing_node",
            "policy_information_node": "policy_information_node",
            "document_intelligence_node": "document_intelligence_node",
            "out_of_scope_node": "out_of_scope_node",
        },
    )

    # All agents → sentiment analysis
    workflow.add_edge("application_servicing_node", "sentiment_analysis_node")
    workflow.add_edge("underwriting_support_node", "sentiment_analysis_node")
    workflow.add_edge("policy_servicing_node", "sentiment_analysis_node")
    workflow.add_edge("policy_information_node", "sentiment_analysis_node")
    workflow.add_edge("document_intelligence_node", "sentiment_analysis_node")

    # Out-of-scope bypasses sentiment (to prevent refine from answering the question)
    workflow.add_edge("out_of_scope_node", "deliver_response_node")

    # Conditional: sentiment routing
    workflow.add_conditional_edges(
        "sentiment_analysis_node",
        route_on_sentiment,
        {
            "deliver_response_node": "deliver_response_node",
            "refine_response_node": "refine_response_node",
            "escalate_node": "escalate_node",
        },
    )

    # Refine loops back to sentiment
    workflow.add_edge("refine_response_node", "sentiment_analysis_node")

    # Deliver → log → end
    workflow.add_edge("deliver_response_node", "log_interaction_node")
    workflow.add_edge("log_interaction_node", END)

    # Escalate → log → end
    workflow.add_edge("escalate_node", "log_interaction_node")

    return workflow.compile()


# ── Convenience runner ───────────────────────────────────────────────────────

_compiled = None


def get_workflow():
    global _compiled
    if _compiled is None:
        _compiled = build_workflow()
    return _compiled


def run_query(
    user_input: str,
    session_id: str = "",
    input_channel: str = "direct_partner_website",
    uploaded_document: str | None = None,
    user_id: str = "",
    user_role: str = "customer",
) -> Dict[str, Any]:
    """Run a single query through the full agentic workflow."""
    wf = get_workflow()

    initial_state: WorkflowState = {
        "session_id": session_id or new_id("session"),
        "input_channel": input_channel,
        "user_input": user_input,
        "uploaded_document": uploaded_document,
        "user_id": user_id,
        "user_role": user_role,
        "intent": "",
        "intent_confidence": 0.0,
        "entities": {},
        "routed_agent": "",
        "agent_response": "",
        "context_docs": [],
        "sentiment_score": 0.0,
        "sentiment_level": "",
        "sentiment_action": "",
        "refinement_suggestion": "",
        "final_response": "",
        "escalated": False,
        "escalation_reason": "",
        "human_handoff": False,
        "refine_count": 0,
        "interaction_log": [],
    }

    result = wf.invoke(initial_state)
    return result
