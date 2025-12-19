"""Telemetry event type definitions.

Simplified event types focusing on business-level metrics.
LangSmith handles detailed LLM/tool tracing when enabled.
"""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class TelemetryEvent(BaseModel):
    """Base telemetry event structure."""

    event_type: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    session_id: str
    app_version: str = "0.1.0"
    payload: dict[str, Any] = Field(default_factory=dict)


# Payload models for type safety


class SessionStartPayload(BaseModel):
    """Payload for SessionStart event."""

    os: str
    machine_id: str
    langsmith_enabled: bool = False


class SessionEndPayload(BaseModel):
    """Payload for SessionEnd event."""

    duration_seconds: int
    chat_turns: int
    proposals_created: int
    proposals_approved: int
    proposals_rejected: int


class ChatTurnPayload(BaseModel):
    """Simplified ChatTurn payload - just counts, no latency/tokens.
    
    LangSmith handles detailed metrics when enabled.
    """

    message_length: int
    had_tool_calls: bool = False
    tool_count: int = 0
    had_error: bool = False


class ProposalCreatedPayload(BaseModel):
    """Payload for ProposalCreated event."""

    proposal_id: str
    file_count: int
    operations: list[str]  # ["create", "update", "delete"]


class ProposalDecisionPayload(BaseModel):
    """Payload for ProposalDecision event."""

    proposal_id: str
    decision: Literal["approved", "rejected"]
    review_duration_ms: int = 0


class ErrorPayload(BaseModel):
    """Payload for high-level Error event."""

    error_type: str
    message: str
    context: dict[str, Any] = Field(default_factory=dict)


# Event type constants
EVENT_SESSION_START = "SessionStart"
EVENT_SESSION_END = "SessionEnd"
EVENT_CHAT_TURN = "ChatTurn"
EVENT_PROPOSAL_CREATED = "ProposalCreated"
EVENT_PROPOSAL_DECISION = "ProposalDecision"
EVENT_ERROR = "Error"

