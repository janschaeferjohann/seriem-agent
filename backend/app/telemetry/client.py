"""Telemetry client for emitting events.

Singleton client that handles event emission with optional enable/disable.
"""

import hashlib
import os
import platform
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from app.telemetry.events import (
    EVENT_CHAT_TURN,
    EVENT_ERROR,
    EVENT_PROPOSAL_CREATED,
    EVENT_PROPOSAL_DECISION,
    EVENT_SESSION_END,
    EVENT_SESSION_START,
    ChatTurnPayload,
    ErrorPayload,
    ProposalCreatedPayload,
    ProposalDecisionPayload,
    SessionEndPayload,
    SessionStartPayload,
    TelemetryEvent,
)
from app.telemetry.writer import JSONLWriter


class TelemetryClient:
    """Singleton telemetry client for event emission."""

    _instance: "TelemetryClient | None" = None

    def __init__(self, base_dir: Path, enabled: bool = True):
        """Initialize the telemetry client.
        
        Args:
            base_dir: Directory to store JSONL files
            enabled: Whether telemetry collection is enabled
        """
        self.enabled = enabled
        self.base_dir = base_dir
        self.writer = JSONLWriter(base_dir) if enabled else None
        self.session_id = str(uuid4())
        self.app_version = os.getenv("APP_VERSION", "0.1.0")
        
        # Session tracking
        self._session_start_time: datetime | None = None
        self._chat_turns = 0
        self._proposals_created = 0
        self._proposals_approved = 0
        self._proposals_rejected = 0

        if self.enabled:
            self._emit_session_start()

    def _emit_session_start(self) -> None:
        """Emit SessionStart event on initialization."""
        self._session_start_time = datetime.utcnow()
        langsmith_enabled = os.getenv("LANGSMITH_TRACING", "false").lower() == "true"

        payload = SessionStartPayload(
            os=platform.system(),
            machine_id=self._get_machine_id(),
            langsmith_enabled=langsmith_enabled,
        )

        self.emit(EVENT_SESSION_START, payload.model_dump())

    def emit(self, event_type: str, payload: dict) -> None:
        """Emit a telemetry event.
        
        Args:
            event_type: Type of event (e.g., "ChatTurn", "ProposalCreated")
            payload: Event-specific data
        """
        if not self.enabled or not self.writer:
            return

        event = TelemetryEvent(
            event_type=event_type,
            timestamp=datetime.utcnow(),
            session_id=self.session_id,
            app_version=self.app_version,
            payload=payload,
        )

        try:
            self.writer.write(event)
        except Exception:
            # Silently fail - telemetry should never break the app
            pass

    def emit_chat_turn(
        self,
        message_length: int,
        had_tool_calls: bool = False,
        tool_count: int = 0,
        had_error: bool = False,
    ) -> None:
        """Emit a ChatTurn event.
        
        Args:
            message_length: Length of the user message
            had_tool_calls: Whether the response included tool calls
            tool_count: Number of tools called
            had_error: Whether an error occurred
        """
        self._chat_turns += 1

        payload = ChatTurnPayload(
            message_length=message_length,
            had_tool_calls=had_tool_calls,
            tool_count=tool_count,
            had_error=had_error,
        )

        self.emit(EVENT_CHAT_TURN, payload.model_dump())

    def emit_proposal_created(
        self,
        proposal_id: str,
        file_count: int,
        operations: list[str],
    ) -> None:
        """Emit a ProposalCreated event.
        
        Args:
            proposal_id: Unique ID of the proposal
            file_count: Number of files in the proposal
            operations: List of operation types
        """
        self._proposals_created += 1

        payload = ProposalCreatedPayload(
            proposal_id=proposal_id,
            file_count=file_count,
            operations=operations,
        )

        self.emit(EVENT_PROPOSAL_CREATED, payload.model_dump())

    def emit_proposal_decision(
        self,
        proposal_id: str,
        decision: str,
        review_duration_ms: int = 0,
    ) -> None:
        """Emit a ProposalDecision event.
        
        Args:
            proposal_id: Unique ID of the proposal
            decision: "approved" or "rejected"
            review_duration_ms: Time spent reviewing
        """
        if decision == "approved":
            self._proposals_approved += 1
        elif decision == "rejected":
            self._proposals_rejected += 1

        payload = ProposalDecisionPayload(
            proposal_id=proposal_id,
            decision=decision,  # type: ignore
            review_duration_ms=review_duration_ms,
        )

        self.emit(EVENT_PROPOSAL_DECISION, payload.model_dump())

    def emit_error(
        self,
        error_type: str,
        message: str,
        context: dict | None = None,
    ) -> None:
        """Emit an Error event.
        
        Args:
            error_type: Category of error
            message: Error message
            context: Additional context
        """
        payload = ErrorPayload(
            error_type=error_type,
            message=message,
            context=context or {},
        )

        self.emit(EVENT_ERROR, payload.model_dump())

    def emit_session_end(self) -> None:
        """Emit SessionEnd event (called on shutdown)."""
        if not self._session_start_time:
            return

        duration = int((datetime.utcnow() - self._session_start_time).total_seconds())

        payload = SessionEndPayload(
            duration_seconds=duration,
            chat_turns=self._chat_turns,
            proposals_created=self._proposals_created,
            proposals_approved=self._proposals_approved,
            proposals_rejected=self._proposals_rejected,
        )

        self.emit(EVENT_SESSION_END, payload.model_dump())

    @staticmethod
    def _get_machine_id() -> str:
        """Get a hashed machine identifier (not PII).
        
        Returns:
            Hashed machine ID
        """
        try:
            # Use a combination of platform info for a stable hash
            info = f"{platform.node()}-{platform.machine()}-{platform.processor()}"
            return hashlib.sha256(info.encode()).hexdigest()[:16]
        except Exception:
            return "unknown"

    def set_enabled(self, enabled: bool) -> None:
        """Enable or disable telemetry collection.
        
        Args:
            enabled: Whether to enable collection
        """
        if enabled and not self.enabled:
            # Turning on
            self.writer = JSONLWriter(self.base_dir)
            self._emit_session_start()
        elif not enabled and self.enabled:
            # Turning off
            self.emit_session_end()
            self.writer = None

        self.enabled = enabled


# Module-level singleton instance
_telemetry_client: TelemetryClient | None = None


def init_telemetry(base_dir: Path, enabled: bool = True) -> TelemetryClient:
    """Initialize the global telemetry client.
    
    Args:
        base_dir: Directory to store JSONL files
        enabled: Whether telemetry is enabled
        
    Returns:
        Initialized TelemetryClient
    """
    global _telemetry_client
    _telemetry_client = TelemetryClient(base_dir, enabled)
    return _telemetry_client


def get_telemetry_client() -> TelemetryClient | None:
    """Get the global telemetry client instance.
    
    Returns:
        TelemetryClient instance, or None if not initialized
    """
    return _telemetry_client

