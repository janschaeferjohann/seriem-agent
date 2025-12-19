"""JSONL file writer for telemetry events.

Writes events to date-partitioned JSONL files for easy reading and export.
"""

import threading
from datetime import datetime
from pathlib import Path

from app.telemetry.events import TelemetryEvent


class JSONLWriter:
    """Thread-safe JSONL file writer."""

    def __init__(self, base_dir: Path):
        """Initialize writer with base directory.
        
        Args:
            base_dir: Directory to store JSONL files (one per day)
        """
        self.base_dir = base_dir
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()

    def write(self, event: TelemetryEvent) -> None:
        """Write an event to the appropriate daily file.
        
        Args:
            event: TelemetryEvent to write
        """
        date_str = event.timestamp.strftime("%Y-%m-%d")
        filepath = self.base_dir / f"{date_str}.jsonl"

        with self._lock:
            with open(filepath, "a", encoding="utf-8") as f:
                f.write(event.model_dump_json() + "\n")

    def read_events(
        self,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        event_types: list[str] | None = None,
        limit: int = 1000,
    ) -> list[TelemetryEvent]:
        """Read events from JSONL files with optional filtering.
        
        Args:
            start_date: Filter events after this date
            end_date: Filter events before this date
            event_types: Filter by event type names
            limit: Maximum number of events to return
            
        Returns:
            List of TelemetryEvent objects, newest first
        """
        events: list[TelemetryEvent] = []

        # Get all JSONL files sorted by date (newest first)
        jsonl_files = sorted(self.base_dir.glob("*.jsonl"), reverse=True)

        for filepath in jsonl_files:
            # Parse date from filename
            try:
                file_date = datetime.strptime(filepath.stem, "%Y-%m-%d")
            except ValueError:
                continue

            # Skip files outside date range
            if start_date and file_date.date() < start_date.date():
                continue
            if end_date and file_date.date() > end_date.date():
                continue

            # Read events from file
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue

                        try:
                            event = TelemetryEvent.model_validate_json(line)
                        except Exception:
                            continue

                        # Filter by event type
                        if event_types and event.event_type not in event_types:
                            continue

                        # Filter by date range (more precise than file-level)
                        if start_date and event.timestamp < start_date:
                            continue
                        if end_date and event.timestamp > end_date:
                            continue

                        events.append(event)

                        if len(events) >= limit:
                            # Sort by timestamp descending and return
                            events.sort(key=lambda e: e.timestamp, reverse=True)
                            return events
            except Exception:
                continue

        # Sort by timestamp descending
        events.sort(key=lambda e: e.timestamp, reverse=True)
        return events

    def get_stats(self) -> dict:
        """Get summary statistics from all telemetry data.
        
        Returns:
            Dictionary with aggregated statistics
        """
        stats = {
            "total_sessions": 0,
            "total_chat_turns": 0,
            "total_proposals": 0,
            "proposals_approved": 0,
            "proposals_rejected": 0,
            "total_errors": 0,
            "first_event": None,
            "last_event": None,
        }

        jsonl_files = sorted(self.base_dir.glob("*.jsonl"))

        for filepath in jsonl_files:
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue

                        try:
                            event = TelemetryEvent.model_validate_json(line)
                        except Exception:
                            continue

                        # Update first/last event timestamps
                        if stats["first_event"] is None or event.timestamp < stats["first_event"]:
                            stats["first_event"] = event.timestamp
                        if stats["last_event"] is None or event.timestamp > stats["last_event"]:
                            stats["last_event"] = event.timestamp

                        # Count by event type
                        if event.event_type == "SessionStart":
                            stats["total_sessions"] += 1
                        elif event.event_type == "ChatTurn":
                            stats["total_chat_turns"] += 1
                        elif event.event_type == "ProposalCreated":
                            stats["total_proposals"] += 1
                        elif event.event_type == "ProposalDecision":
                            decision = event.payload.get("decision")
                            if decision == "approved":
                                stats["proposals_approved"] += 1
                            elif decision == "rejected":
                                stats["proposals_rejected"] += 1
                        elif event.event_type == "Error":
                            stats["total_errors"] += 1
            except Exception:
                continue

        # Convert datetime to ISO strings for JSON serialization
        if stats["first_event"]:
            stats["first_event"] = stats["first_event"].isoformat()
        if stats["last_event"]:
            stats["last_event"] = stats["last_event"].isoformat()

        return stats

    def delete_before(self, before_date: datetime) -> int:
        """Delete JSONL files older than the specified date.
        
        Args:
            before_date: Delete files with dates before this
            
        Returns:
            Number of files deleted
        """
        deleted = 0

        for filepath in self.base_dir.glob("*.jsonl"):
            try:
                file_date = datetime.strptime(filepath.stem, "%Y-%m-%d")
                if file_date.date() < before_date.date():
                    filepath.unlink()
                    deleted += 1
            except (ValueError, OSError):
                continue

        return deleted

    def get_file_list(self) -> list[dict]:
        """Get list of telemetry files with metadata.
        
        Returns:
            List of dicts with filename, date, and size
        """
        files = []

        for filepath in sorted(self.base_dir.glob("*.jsonl"), reverse=True):
            try:
                file_date = datetime.strptime(filepath.stem, "%Y-%m-%d")
                stat = filepath.stat()
                files.append({
                    "filename": filepath.name,
                    "date": file_date.isoformat(),
                    "size_bytes": stat.st_size,
                })
            except (ValueError, OSError):
                continue

        return files

