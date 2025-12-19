"""Telemetry API endpoints for viewing and exporting local telemetry data."""

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse

from app.telemetry import get_telemetry_client
from app.telemetry.events import TelemetryEvent

router = APIRouter(prefix="/api/telemetry", tags=["telemetry"])


@router.get("/events")
async def get_events(
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    event_types: Annotated[list[str] | None, Query()] = None,
    search: str | None = None,
    limit: int = 500,
) -> dict:
    """Get telemetry events with optional filtering.
    
    Args:
        start_date: Filter events after this date
        end_date: Filter events before this date
        event_types: Filter by event type names (can specify multiple)
        search: Text search in event payload
        limit: Maximum number of events to return (default 500)
        
    Returns:
        Dictionary with events list
    """
    client = get_telemetry_client()
    
    if not client or not client.writer:
        return {"events": [], "enabled": False}
    
    events = client.writer.read_events(
        start_date=start_date,
        end_date=end_date,
        event_types=event_types,
        limit=limit,
    )
    
    # Optional text search in payload
    if search:
        search_lower = search.lower()
        events = [
            e for e in events
            if search_lower in str(e.payload).lower()
            or search_lower in e.event_type.lower()
        ]
    
    return {
        "events": [e.model_dump() for e in events],
        "enabled": True,
    }


@router.get("/stats")
async def get_stats() -> dict:
    """Get summary statistics from all telemetry data.
    
    Returns:
        Dictionary with aggregated statistics
    """
    client = get_telemetry_client()
    
    if not client or not client.writer:
        return {
            "enabled": False,
            "total_sessions": 0,
            "total_chat_turns": 0,
            "total_proposals": 0,
            "proposals_approved": 0,
            "proposals_rejected": 0,
            "total_errors": 0,
            "first_event": None,
            "last_event": None,
        }
    
    stats = client.writer.get_stats()
    stats["enabled"] = True
    return stats


@router.get("/files")
async def get_files() -> dict:
    """Get list of telemetry data files.
    
    Returns:
        Dictionary with files list
    """
    client = get_telemetry_client()
    
    if not client or not client.writer:
        return {"files": [], "enabled": False}
    
    files = client.writer.get_file_list()
    return {"files": files, "enabled": True}


@router.get("/export")
async def export_events(
    start_date: datetime | None = None,
    end_date: datetime | None = None,
):
    """Export events as JSONL file for download or batch upload.
    
    Args:
        start_date: Filter events after this date
        end_date: Filter events before this date
        
    Returns:
        Streaming JSONL response
    """
    client = get_telemetry_client()
    
    if not client or not client.writer:
        # Return empty JSONL
        return StreamingResponse(
            iter([]),
            media_type="application/x-ndjson",
            headers={"Content-Disposition": "attachment; filename=telemetry-export.jsonl"},
        )
    
    events = client.writer.read_events(
        start_date=start_date,
        end_date=end_date,
        limit=100000,  # Higher limit for export
    )
    
    def generate():
        for event in events:
            yield event.model_dump_json() + "\n"
    
    # Generate filename with date range
    filename = "telemetry-export"
    if start_date:
        filename += f"-from-{start_date.strftime('%Y%m%d')}"
    if end_date:
        filename += f"-to-{end_date.strftime('%Y%m%d')}"
    filename += ".jsonl"
    
    return StreamingResponse(
        generate(),
        media_type="application/x-ndjson",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.delete("/events")
async def clear_old_events(before_date: datetime) -> dict:
    """Delete events older than specified date.
    
    Args:
        before_date: Delete files with dates before this
        
    Returns:
        Dictionary with count of deleted files
    """
    client = get_telemetry_client()
    
    if not client or not client.writer:
        return {"deleted_files": 0, "enabled": False}
    
    deleted = client.writer.delete_before(before_date)
    return {"deleted_files": deleted, "enabled": True}


@router.post("/enabled")
async def set_enabled(enabled: bool) -> dict:
    """Enable or disable telemetry collection.
    
    Args:
        enabled: Whether to enable telemetry
        
    Returns:
        Dictionary with new enabled state
    """
    client = get_telemetry_client()
    
    if client:
        client.set_enabled(enabled)
        return {"enabled": client.enabled}
    
    return {"enabled": False, "error": "Telemetry client not initialized"}

