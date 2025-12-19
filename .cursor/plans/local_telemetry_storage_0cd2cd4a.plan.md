---
name: Local Telemetry Storage
overview: Implement local-only telemetry storage using JSONL files, with a detailed event viewer UI. This is an intermediate step before the central collector exists - data is collected locally and can be batch-uploaded later.
todos:
  - id: telemetry-module
    content: Create backend/app/telemetry/ module with client, writer, and event types
    status: pending
  - id: telemetry-api
    content: Create backend/app/api/telemetry.py with events, stats, and export endpoints
    status: pending
  - id: instrument-websocket
    content: Add telemetry.emit calls to websocket.py for ChatTurn events
    status: pending
  - id: instrument-tools
    content: Add telemetry.emit calls to filesystem.py for ToolCall events
    status: pending
  - id: instrument-proposals
    content: Add telemetry.emit calls to proposals/routes.py for ProposalCreated/Decision
    status: pending
  - id: viewer-component
    content: Create telemetry-viewer component with stats cards, filters, and event table
    status: pending
  - id: viewer-service
    content: Create telemetry.service.ts for API calls and state management
    status: pending
  - id: settings-integration
    content: Add telemetry toggle and viewer link to settings component
    status: pending
---

# Local Telemetry Storage (Pre-Central Server)

## Purpose

This is an **intermediate step** before the [centralized telemetry plan](centralized_telemetry_layer_3ec91d4d.plan.md). It implements:

1. Telemetry event collection to local JSONL files
2. A detailed event viewer UI with filtering
3. Export capability for eventual batch upload to central server

No central server required - all data stays on the user's machine.

## Architecture

````mermaid
flowchart TD
  subgraph electron_app [Electron App]
    angular[Angular_Frontend]
    fastapi[FastAPI_Backend]
    
    angular -->|WebSocket_HTTP| fastapi
    fastapi -->|emit_events| writer[JSONL_Writer]
    writer --> storage[Local_JSONL_Files]
    
    angular -->|GET_events| api[Telemetry_API]
    api --> storage
  end
  
  subgraph viewer [Telemetry Viewer UI]
    eventLog[Event_Log_Table]
    filters[Filters_Date_Type_Search]
    stats[Summary_Stats]
    export[Export_Button]
  end
  
  angular --> viewer
  storage -.->|future| upload[Batch_Upload_to_Central]
```



## Storage Format

**Location**: `{app_data}/telemetry/` (Electron app data directory)**File structure**:

```javascript
telemetry/
  2024-12-19.jsonl      # One file per day
  2024-12-18.jsonl
  2024-12-17.jsonl
  ...
```

**JSONL format** (one JSON object per line):

```json
{"event_type":"SessionStart","timestamp":"2024-12-19T10:30:00Z","session_id":"abc123","user_id":"user-hash","app_version":"0.1.0","payload":{"os":"win32","machine_id":"xyz"}}
{"event_type":"ChatTurn","timestamp":"2024-12-19T10:30:15Z","session_id":"abc123","user_id":"user-hash","app_version":"0.1.0","payload":{"prompt_length":150,"response_length":500,"model":"claude-sonnet-4-20250514","latency_ms":2340}}
```

**Why JSONL**:

- Append-only (crash-safe)
- Human-readable (can open in text editor)
- Easy to parse line-by-line
- Simple to batch-upload later (just POST the file contents)
- No database dependencies

## Implementation

### Phase 1: Telemetry Writer Module

**New module** `backend/app/telemetry/`:

```javascript
backend/app/telemetry/
  __init__.py           # Exports get_telemetry_client()
  client.py             # TelemetryClient class
  events.py             # Event type definitions (Pydantic models)
  writer.py             # JSONL file writer
```

**`events.py`** - Type-safe event definitions:

```python
from pydantic import BaseModel
from datetime import datetime
from typing import Literal, Any

class TelemetryEvent(BaseModel):
    event_type: str
    timestamp: datetime
    session_id: str
    user_id: str
    app_version: str
    payload: dict[str, Any]

class SessionStartPayload(BaseModel):
    os: str
    machine_id: str

class ChatTurnPayload(BaseModel):
    prompt_length: int
    response_length: int
    model: str
    latency_ms: int
    tool_calls: int = 0

class ToolCallPayload(BaseModel):
    tool_name: str
    duration_ms: int
    success: bool
    error_type: str | None = None

class ProposalCreatedPayload(BaseModel):
    proposal_id: str
    file_count: int
    total_lines_changed: int
    operations: list[str]  # ["create", "update", "delete"]

class ProposalDecisionPayload(BaseModel):
    proposal_id: str
    decision: Literal["approved", "rejected"]
    review_duration_ms: int

class ErrorPayload(BaseModel):
    error_type: str
    message: str
    stack_trace: str | None = None
    context: dict[str, Any] = {}
```

**`writer.py`** - JSONL file writer:

```python
from pathlib import Path
from datetime import datetime
import json
import threading

class JSONLWriter:
    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
    
    def write(self, event: TelemetryEvent):
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
        """Read events for the viewer UI."""
        events = []
        for filepath in sorted(self.base_dir.glob("*.jsonl"), reverse=True):
            # Filter by date from filename
            file_date = datetime.strptime(filepath.stem, "%Y-%m-%d")
            if start_date and file_date < start_date.date():
                continue
            if end_date and file_date > end_date.date():
                continue
            
            with open(filepath, "r", encoding="utf-8") as f:
                for line in f:
                    event = TelemetryEvent.model_validate_json(line)
                    if event_types and event.event_type not in event_types:
                        continue
                    events.append(event)
                    if len(events) >= limit:
                        return events
        return events
    
    def get_stats(self) -> dict:
        """Get summary statistics for dashboard."""
        # Count events by type, sessions, etc.
        ...
```

**`client.py`** - Main interface:

```python
from uuid import uuid4
from datetime import datetime
import os
import platform

class TelemetryClient:
    _instance: "TelemetryClient | None" = None
    
    def __init__(self, base_dir: Path, enabled: bool = True):
        self.enabled = enabled
        self.writer = JSONLWriter(base_dir)
        self.session_id = str(uuid4())
        self.user_id = self._get_user_id()
        self.app_version = os.getenv("APP_VERSION", "dev")
        
        if self.enabled:
            self._emit_session_start()
    
    def emit(self, event_type: str, payload: dict):
        if not self.enabled:
            return
        
        event = TelemetryEvent(
            event_type=event_type,
            timestamp=datetime.utcnow(),
            session_id=self.session_id,
            user_id=self.user_id,
            app_version=self.app_version,
            payload=payload,
        )
        self.writer.write(event)
    
    def _emit_session_start(self):
        self.emit("SessionStart", {
            "os": platform.system(),
            "machine_id": self._get_machine_id(),
        })
    
    @staticmethod
    def _get_machine_id() -> str:
        # Hash of machine-specific info (not PII)
        ...
    
    @staticmethod
    def _get_user_id() -> str:
        # From env or generate stable hash
        return os.getenv("TELEMETRY_USER_ID", "anonymous")

# Singleton accessor
def get_telemetry_client() -> TelemetryClient:
    if TelemetryClient._instance is None:
        from app.main import TELEMETRY_DIR, TELEMETRY_ENABLED
        TelemetryClient._instance = TelemetryClient(
            base_dir=TELEMETRY_DIR,
            enabled=TELEMETRY_ENABLED,
        )
    return TelemetryClient._instance
```



### Phase 2: Backend API for Viewer

**New file** `backend/app/api/telemetry.py`:

```python
from fastapi import APIRouter, Query
from datetime import datetime
from app.telemetry import get_telemetry_client

router = APIRouter(prefix="/api/telemetry")

@router.get("/events")
async def get_events(
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    event_types: list[str] | None = Query(None),
    search: str | None = None,
    limit: int = 500,
):
    """Get telemetry events for the viewer."""
    client = get_telemetry_client()
    events = client.writer.read_events(
        start_date=start_date,
        end_date=end_date,
        event_types=event_types,
        limit=limit,
    )
    
    # Optional text search in payload
    if search:
        events = [e for e in events if search.lower() in str(e.payload).lower()]
    
    return {"events": [e.model_dump() for e in events]}

@router.get("/stats")
async def get_stats():
    """Get summary statistics."""
    client = get_telemetry_client()
    return client.writer.get_stats()

@router.get("/export")
async def export_events(
    start_date: datetime | None = None,
    end_date: datetime | None = None,
):
    """Export events as JSONL for manual upload."""
    from fastapi.responses import StreamingResponse
    
    client = get_telemetry_client()
    events = client.writer.read_events(
        start_date=start_date,
        end_date=end_date,
        limit=100000,  # Higher limit for export
    )
    
    def generate():
        for event in events:
            yield event.model_dump_json() + "\n"
    
    return StreamingResponse(
        generate(),
        media_type="application/x-ndjson",
        headers={"Content-Disposition": "attachment; filename=telemetry-export.jsonl"}
    )

@router.delete("/events")
async def clear_old_events(before_date: datetime):
    """Delete events older than specified date."""
    client = get_telemetry_client()
    deleted = client.writer.delete_before(before_date)
    return {"deleted_files": deleted}
```



### Phase 3: Instrument Application Code

**Modify** [`backend/app/main.py`](backend/app/main.py):

```python
# Add near top, after load_dotenv
from pathlib import Path

# Telemetry configuration
TELEMETRY_ENABLED = os.getenv("TELEMETRY_ENABLED", "1") == "1"
TELEMETRY_DIR = Path(os.getenv("TELEMETRY_DIR", "./telemetry"))

# Import telemetry router
from app.api.telemetry import router as telemetry_router
app.include_router(telemetry_router)
```

**Modify** [`backend/app/api/websocket.py`](backend/app/api/websocket.py):

```python
from app.telemetry import get_telemetry_client
import time

# In message handler
async def handle_message(websocket, message):
    start_time = time.time()
    telemetry = get_telemetry_client()
    
    # ... existing code to process message ...
    
    elapsed_ms = int((time.time() - start_time) * 1000)
    telemetry.emit("ChatTurn", {
        "prompt_length": len(message),
        "response_length": len(response),
        "model": model_name,
        "latency_ms": elapsed_ms,
        "tool_calls": tool_call_count,
    })
```

**Modify** [`backend/app/tools/filesystem.py`](backend/app/tools/filesystem.py):

```python
from app.telemetry import get_telemetry_client
import time

# Wrap tool functions to emit telemetry
def _emit_tool_call(tool_name: str, start_time: float, success: bool, error: str | None = None):
    telemetry = get_telemetry_client()
    telemetry.emit("ToolCall", {
        "tool_name": tool_name,
        "duration_ms": int((time.time() - start_time) * 1000),
        "success": success,
        "error_type": error,
    })
```



### Phase 4: Telemetry Viewer UI

**New component** `frontend/src/app/components/telemetry-viewer/`:

```typescript
// telemetry-viewer.component.ts
@Component({
  selector: 'app-telemetry-viewer',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="telemetry-viewer">
      <header class="viewer-header">
        <h2>Telemetry</h2>
        <button class="export-btn" (click)="exportEvents()">Export JSONL</button>
      </header>
      
      <!-- Stats Summary -->
      <div class="stats-cards">
        <div class="stat-card">
          <span class="stat-value">{{ stats()?.total_sessions || 0 }}</span>
          <span class="stat-label">Sessions</span>
        </div>
        <div class="stat-card">
          <span class="stat-value">{{ stats()?.total_chat_turns || 0 }}</span>
          <span class="stat-label">Chat Turns</span>
        </div>
        <div class="stat-card">
          <span class="stat-value">{{ stats()?.proposals_approved || 0 }}/{{ stats()?.proposals_total || 0 }}</span>
          <span class="stat-label">Proposals Approved</span>
        </div>
        <div class="stat-card">
          <span class="stat-value">{{ stats()?.error_count || 0 }}</span>
          <span class="stat-label">Errors</span>
        </div>
      </div>
      
      <!-- Filters -->
      <div class="filters">
        <input type="date" [(ngModel)]="startDate" placeholder="Start date" />
        <input type="date" [(ngModel)]="endDate" placeholder="End date" />
        <select [(ngModel)]="selectedEventType" (change)="loadEvents()">
          <option value="">All Events</option>
          <option value="SessionStart">SessionStart</option>
          <option value="ChatTurn">ChatTurn</option>
          <option value="ToolCall">ToolCall</option>
          <option value="ProposalCreated">ProposalCreated</option>
          <option value="ProposalDecision">ProposalDecision</option>
          <option value="Error">Error</option>
        </select>
        <input type="text" [(ngModel)]="searchQuery" placeholder="Search..." (input)="onSearchDebounced()" />
      </div>
      
      <!-- Event Log Table -->
      <div class="event-log">
        <table>
          <thead>
            <tr>
              <th>Time</th>
              <th>Type</th>
              <th>Session</th>
              <th>Details</th>
            </tr>
          </thead>
          <tbody>
            @for (event of events(); track event.timestamp) {
              <tr [class]="'event-' + event.event_type.toLowerCase()">
                <td class="time">{{ event.timestamp | date:'short' }}</td>
                <td class="type">
                  <span class="event-badge">{{ event.event_type }}</span>
                </td>
                <td class="session">{{ event.session_id | slice:0:8 }}</td>
                <td class="details">
                  <button class="expand-btn" (click)="toggleExpand(event)">
                    {{ expandedEvents.has(event) ? '−' : '+' }}
                  </button>
                  <span class="summary">{{ getEventSummary(event) }}</span>
                  @if (expandedEvents.has(event)) {
                    <pre class="payload">{{ event.payload | json }}</pre>
                  }
                </td>
              </tr>
            }
          </tbody>
        </table>
      </div>
    </div>
  `,
})
export class TelemetryViewerComponent {
  // ... implementation
}
```

**New service** `frontend/src/app/services/telemetry.service.ts`:

```typescript
@Injectable({ providedIn: 'root' })
export class TelemetryService {
  private readonly apiUrl = 'http://localhost:8000/api/telemetry';
  
  readonly events = signal<TelemetryEvent[]>([]);
  readonly stats = signal<TelemetryStats | null>(null);
  readonly isLoading = signal(false);
  
  constructor(private http: HttpClient) {}
  
  loadEvents(filters: EventFilters): void {
    this.isLoading.set(true);
    const params = new HttpParams()
      .set('limit', '500')
      .set('event_types', filters.eventTypes?.join(',') || '');
    
    this.http.get<{events: TelemetryEvent[]}>(`${this.apiUrl}/events`, { params })
      .subscribe(res => {
        this.events.set(res.events);
        this.isLoading.set(false);
      });
  }
  
  loadStats(): void {
    this.http.get<TelemetryStats>(`${this.apiUrl}/stats`)
      .subscribe(stats => this.stats.set(stats));
  }
  
  exportEvents(): void {
    window.open(`${this.apiUrl}/export`, '_blank');
  }
}
```



### Phase 5: Settings Integration

Add telemetry toggle to settings (connects to [settings plan](fronten_ea4150ad.plan.md)):

```typescript
// In settings component
<section class="settings-section">
  <h3>Telemetry</h3>
  <label class="toggle-row">
    <input type="checkbox" [(ngModel)]="settings.telemetryEnabled" />
    <span>Collect usage data locally</span>
  </label>
  <p class="hint">Data is stored on your machine only. Use "Export" to share with the team.</p>
  <button (click)="openTelemetryViewer()">View Local Telemetry</button>
</section>
```



## Files to Create/Modify

| File | Change |
|------|--------|
| `backend/app/telemetry/__init__.py` | NEW: Module init |
| `backend/app/telemetry/client.py` | NEW: TelemetryClient singleton |
| `backend/app/telemetry/events.py` | NEW: Event type definitions |
| `backend/app/telemetry/writer.py` | NEW: JSONL file writer |
| `backend/app/api/telemetry.py` | NEW: REST endpoints for viewer |
| [`backend/app/main.py`](backend/app/main.py) | Add telemetry config + router |
| [`backend/app/api/websocket.py`](backend/app/api/websocket.py) | Emit ChatTurn events |
| [`backend/app/tools/filesystem.py`](backend/app/tools/filesystem.py) | Emit ToolCall events |
| `backend/app/proposals/routes.py` | Emit ProposalCreated/ProposalDecision events |
| `frontend/src/app/components/telemetry-viewer/` | NEW: Viewer component |
| `frontend/src/app/services/telemetry.service.ts` | NEW: Telemetry API service |
| `frontend/src/app/components/settings/` | Add telemetry toggle + viewer link |

## Dependencies

This plan depends on:
- **[Settings page](frontend_settings_page_ea4150ad.plan.md)** - Telemetry toggle lives in the settings UI
- **[Proposal layer](local_proposal_layer_bd7aa7a7.plan.md)** - ProposalCreated/ProposalDecision events require the proposal system

## Migration Path to Central Server

When the central collector is ready:

1. Add `backend/app/telemetry/uploader.py` (from centralized plan)
2. Configure `TELEMETRY_ENDPOINT` and `TELEMETRY_TOKEN`
3. Uploader reads existing JSONL files and batch-uploads them
4. After successful upload, optionally delete local files (or keep as backup)

The JSONL format is designed to be directly uploadable - each line is a valid event that the central collector can ingest.

## Rollout Order

1. **Telemetry module** - client + writer + event types
2. **API endpoints** - events, stats, export
3. **Instrument websocket** - ChatTurn events
4. **Instrument tools** - ToolCall events
5. **Instrument proposals** - ProposalCreated/ProposalDecision events
6. **Viewer UI** - stats cards + event table + filters
7. **Settings integration** - telemetry toggle + viewer link




````