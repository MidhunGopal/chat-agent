"""Pydantic models / schemas for the agentic ecosystem."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ── Enums ────────────────────────────────────────────────────────────────────

class IntentType(str, Enum):
    NEW_APPLICATION = "new_application"
    UNDERWRITING_STATUS = "underwriting_status"
    POLICY_QUERY = "policy_query"
    GENERAL_INFO = "general_info"
    DOCUMENT_UPLOAD = "document_upload"
    UNKNOWN = "unknown"


class InputChannel(str, Enum):
    WEBSITE = "direct_partner_website"
    MY_ACCOUNTS = "my_accounts_portal"
    AGENT_HUB = "agent_hub_portal"
    EMAIL = "email_inbound"
    LETTER = "letters_inbound"


class SentimentLevel(str, Enum):
    HIGH = "high"
    LOW = "low"
    UNKNOWN = "unknown"


class EscalationReason(str, Enum):
    LOW_SENTIMENT = "low_predicted_satisfaction"
    UNKNOWN_COMPLEXITY = "unknown_complexity"
    AGENT_REQUEST = "agent_requested"


class UserRole(str, Enum):
    CUSTOMER = "customer"
    AGENT = "agent"
    ADMIN = "admin"


# ── Core State ───────────────────────────────────────────────────────────────

class AgentState(BaseModel):
    """Shared state that flows through the LangGraph workflow."""

    # Input
    session_id: str = Field(default="")
    input_channel: InputChannel = Field(default=InputChannel.WEBSITE)
    user_input: str = Field(default="")
    uploaded_document: Optional[str] = Field(default=None)

    # NLP / Intent
    intent: IntentType = Field(default=IntentType.UNKNOWN)
    intent_confidence: float = Field(default=0.0)
    entities: Dict[str, Any] = Field(default_factory=dict)

    # Agent processing
    routed_agent: str = Field(default="")
    agent_response: str = Field(default="")
    context_docs: List[str] = Field(default_factory=list)

    # Sentiment
    sentiment_score: float = Field(default=0.0)
    sentiment_level: SentimentLevel = Field(default=SentimentLevel.UNKNOWN)

    # Delivery
    final_response: str = Field(default="")
    escalated: bool = Field(default=False)
    escalation_reason: Optional[EscalationReason] = Field(default=None)
    human_handoff: bool = Field(default=False)

    # Logging
    interaction_log: List[Dict[str, Any]] = Field(default_factory=list)
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


# ── Data Hub models ──────────────────────────────────────────────────────────

class PolicyRecord(BaseModel):
    policy_id: str
    holder_name: str
    policy_type: str
    status: str
    premium: float
    start_date: str
    end_date: str
    details: Dict[str, Any] = Field(default_factory=dict)
    customer_id: str = ""
    agent_id: str = ""


class ApplicationRecord(BaseModel):
    application_id: str
    applicant_name: str
    application_type: str
    status: str
    submitted_date: str
    underwriting_status: str = "pending"
    details: Dict[str, Any] = Field(default_factory=dict)
    customer_id: str = ""
    agent_id: str = ""


class UserRecord(BaseModel):
    user_id: str
    username: str
    password: str
    full_name: str
    role: str = "customer"
    email: str = ""
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class UnderwritingRecord(BaseModel):
    underwriting_id: str
    application_id: str
    status: str
    risk_score: Optional[float] = None
    notes: str = ""
    updated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class InteractionLog(BaseModel):
    log_id: str
    session_id: str
    channel: str
    intent: str
    agent_used: str
    user_query: str
    response: str
    sentiment_score: float
    escalated: bool
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
