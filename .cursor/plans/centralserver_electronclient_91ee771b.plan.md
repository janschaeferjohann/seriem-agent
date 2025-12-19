# CentralizedBackend_ElectronLocalWorkspace_MVP

## Goals (what we will build)

- **Local workspace per user**: the UI operates on the user’s chosen local Git repo/folder.
- **Centralized model calls**: only the backend talks to Anthropic (API key stays server-side).
- **Human-in-the-loop safety**: every change is presented as a **diff** and requires **explicit approve/apply**.
- **Traces/logs for MVP**: backend records **all user requests + model outputs + proposed changes + apply decisions** (you chose **structured log files**, not an admin UI).

## Non-goals (for MVP)

- Perfect privacy controls/retention controls beyond “we log everything” (you explicitly chose full content logging).
- Full autonomous “server browses your local disk” tooling (we avoid remote tool-call plumbing initially).

## Core data structures (keep it dumb)

- **Workspace**: `{workspaceId, userId, rootPathLocal, gitEnabled:true}` (rootPathLocal never leaves the client unless you explicitly log it).
- **ChangeProposal**: `{proposalId, requestId, userId, files:[{path, before, after}], summary, modelMeta}`
- **TraceEvent (JSONL)**: `{ts, requestId, userId, sessionId, eventType, payload}`

This eliminates special cases: the server never touches disk; the client never touches Anthropic.

## Target architecture (data flow)

````mermaid
flowchart TD
  ElectronClient[ElectronClient] -->|AuthToken,ChatOrEditRequest,Context| BackendAPI[BackendAPI_FastAPI]
  BackendAPI -->|AnthropicRequest| AnthropicAPI[AnthropicAPI]
  AnthropicAPI -->|ModelOutput| BackendAPI
  BackendAPI -->|ChangeProposal(files_before_after)| ElectronClient
  ElectronClient -->|ApproveOrReject,ApplyResult| BackendAPI
  BackendAPI -->|AppendJSONL| TraceLogs[TraceLogs_JSONL]
```

## Backend work (central server)

### 1) Authentication (minimal but real)

- Add token-based auth so every request is attributable to a **userId**.
- MVP-friendly default: **Personal Access Token (PAT)** per user (no password UI required).
    - Later upgrade path: password login + JWT.

**Files likely touched/added**:

- Add auth module under [`backend/app/api/`](backend/app/api/) (new `auth.py` + wiring in [`backend/app/main.py`](backend/app/main.py))

### 2) Central “LLM proxy” endpoint that returns ChangeProposals

- Add an endpoint like `POST /api/proposals` that accepts:
    - `userPrompt`
    - `context` (selected file contents, optional `git diff`, optional “open files” list)
- Backend calls Anthropic and returns a **structured ChangeProposal** (per-file before/after).
    - This is intentionally **not** “server tools writing files”.

**Files likely touched/added**:

- [`backend/app/api/routes.py`](backend/app/api/routes.py) (add proposal endpoint)
- Potentially a new module [`backend/app/llm/`](backend/app/llm/) for:
    - prompt templates
    - response validation/parsing (Pydantic)
    - retry-on-invalid-json

### 3) Logging/tracing (JSONL)

- Write JSON lines to `backend/logs/trace-YYYY-MM-DD.jsonl` (already gitignored).
- Log at least:
    - request start/end
    - userPrompt + context metadata
    - model request/response (full content, as you chose)
    - proposal payload (diff/before/after)
    - approve/reject and apply result

**Files likely touched/added**:

- [`backend/app/main.py`](backend/app/main.py) (middleware for `requestId` + logging)
- New `backend/app/observability/logger.py`

### 4) WebSocket (optional for MVP)

You already have streaming via [`backend/app/api/websocket.py`](backend/app/api/websocket.py) and the Angular client consumes it in `frontend/src/app/services/agent.service.ts`.

- Keep it for chat streaming.
- Add a new message type for proposals (e.g. `proposal`) **or** keep proposals on HTTP first.

## Electron client work (user-specific local app)

### 5) Wrap the existing Angular UI in Electron

- Add an Electron main process + preload that loads the built Angular app.
- Keep `nodeIntegration: false`, `contextIsolation: true`.

**New folder (suggested)**:

- `desktop/` (Electron main/preload, build config)

### 6) Local filesystem + git layer (in Electron main process)

- Implement a `WorkspaceManager` that:
    - prompts user to **select a repo/folder**
    - enforces safe path rules (no `..` escapes)
- Implement minimal IPC APIs exposed to Angular:
    - `selectWorkspace()`
    - `listDir(relPath)`
    - `readFile(relPath)`
    - `writeFile(relPath, content)`
    - `gitStatus()` / `gitDiff()` (since `git_required`)

### 7) Replace server-storage file explorer with local file explorer

Today the file explorer calls the backend:

- `frontend/src/app/services/file.service.ts` uses `http://localhost:8000/api/files`
- `frontend/src/app/services/file-preview.service.ts` uses `/api/files/{path}`

Plan:

- Create a small abstraction so web-mode can still use HTTP, but Electron uses IPC.
- Update:
    - [`frontend/src/app/services/file.service.ts`](frontend/src/app/services/file.service.ts)
    - [`frontend/src/app/services/file-preview.service.ts`](frontend/src/app/services/file-preview.service.ts)

This keeps “never break userspace”: browser mode can keep the old behavior for dev.

### 8) Diff review + approve/apply UI

You already have Monaco wired for file preview:

- [`frontend/src/app/components/file-preview/file-preview.component.ts`](frontend/src/app/components/file-preview/file-preview.component.ts)
- [`frontend/src/app/services/monaco-loader.service.ts`](frontend/src/app/services/monaco-loader.service.ts)

Plan:

- Add a `change-review` component that renders:
    - per-file diff (Monaco DiffEditor or unified diff rendering)
    - “Approve & Apply” / “Reject”
- Apply changes only on approval:
    - write `after` content for each changed file (simple, deterministic)
    - optionally `git commit -m "seriem-agent: <summary>"`

### 9) Keyboard shortcuts (Electron-strength)

- In renderer (Angular): shortcuts for send, open command palette, approve/reject.
- In Electron menu: OS-native accelerators.

## Documentation updates (required by repo rules)

Because the main agent will no longer “write to server storage” in the MVP architecture, update:

- [`docs/seriem-agent/agents/mainagent.md`](docs/seriem-agent/agents/mainagent.md)
    - change “main agent is the only writer” → “client applies ChangeProposals after approval”.

## Rollout order (minimize risk)

- Backend: auth + JSONL logging + proposal endpoint (no Electron needed yet).
- Electron: workspace selection + local file explorer/preview.
- Integrate: request proposal → show diff → approve/apply → log decision.

## Biggest risks (don’t be naive)

- **Payload size**: sending full file contents to server/logs can get huge; MVP needs size limits.
- **Security**: Electron must sandbox IPC and enforce rootPathLocal.




````