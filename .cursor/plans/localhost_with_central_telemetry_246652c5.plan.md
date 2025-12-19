# Localhost_App_With_Central_Telemetry_MVP

## Requirement (confirmed)

- The app remains **localhost-only** (Angular + FastAPI) and is distributed via **internal git**.
- You still need **centralized logfiles + behavior telemetry**, and you explicitly want **full-content logs** (prompts, model outputs, before/after file contents).

## Core judgment

Worth doing. You can get real product feedback/observability **without** the complexity of Electron packaging or centralizing all execution. The only “hard” part is making telemetry **reliable (offline queue)** and **queryable**.

## MVP architecture (local runtime + central collector)

````mermaid
flowchart TD
  user[UserBrowser] --> fe[AngularFrontend_Localhost]
  fe --> be[FastAPI_AgentRuntime_Localhost]

  be --> anthropic[AnthropicAPI]

  be --> spool[LocalTelemetrySpool_JSONL_Gzip]
  spool -->|batched_upload| collector[CentralTelemetryCollector_FastAPI]
  collector --> store[CentralStorage_JSONL_or_Postgres]
```

## What to collect (full-content, but with sane limits)

### Event types (MVP)

- **SessionStart**: userId, machineId, appVersion (git SHA), OS, timestamps
- **ChatTurn**: userPrompt, assistantFinal, model, latency
- **ToolCall**: toolName, args, result (careful: can be huge), duration, error
- **FileOperation**: opId, path, opType(write/edit/delete), beforeContent, afterContent, unifiedDiff, locAdded, locRemoved
- **ChangeDecision**: opId, decision(accept/reject/revert), optional reason
- **Error**: stack trace + context

### Guardrails (MVP must-have)

- **Size caps**: e.g. don’t upload raw file contents beyond N MB; store large payloads as separate compressed “attachments” (still centrally, but not inline).
- **Backpressure**: if upload fails, keep spooling locally; never block the UI.
- **Retention**: rotate daily; purge after X days (even internal systems drown in garbage).

## Implementation plan (alternative to Electron/central-LLM plan)

### 1) Central telemetry collector (new internal service)

- Run a small FastAPI app (internal host) with:
    - `POST /api/v1/events` accepts **batched events** (JSON array) with `Content-Encoding: gzip`
    - `POST /api/v1/attachments` for oversized payload blobs
    - `GET /api/v1/health`
- Auth: simplest MVP is **PAT/Bearer token** per user/team.
- Storage: start dumb:
    - **JSONL files** partitioned by date/user, or
    - **Postgres** if you want basic querying from day 1.

### 2) Local telemetry client (in the localhost backend)

- Add a `TelemetryClient` that:
    - writes events to a **local spool** (JSONL, gzip per batch)
    - flushes periodically in a background task
    - retries with exponential backoff
- Config via env vars:
    - `TELEMETRY_ENABLED=1`
    - `TELEMETRY_ENDPOINT=https://.../api/v1/events`
    - `TELEMETRY_TOKEN=...`
    - `TELEMETRY_USER_ID=...` (or derive from OS username)

### 3) Instrument the real seams (minimal code churn)

- **WebSocket chat path**: hook into [`backend/app/api/websocket.py`](backend/app/api/websocket.py)
    - emit ChatTurn + ToolCall events (you already see `on_tool_start/on_tool_end`)
- **REST chat path**: hook into [`backend/app/api/routes.py`](backend/app/api/routes.py)
- **Filesystem tool calls**: instrument [`backend/app/tools/filesystem.py`](backend/app/tools/filesystem.py)
    - for `write_file`/`edit_file`:
        - read old content (if exists)
        - compute unified diff + LOC added/removed
        - emit FileOperation event

This avoids breaking the agent contract: tools still behave the same, they just get telemetry side-effects.

### 4) “Accepted diff” capture (MVP options)

Because there is no diff-approval UI today, implement a minimal decision loop:

- Add a small “Changes” panel in the Angular UI that lists recent FileOperations.
- Add local endpoints:
    - `GET /api/changes/recent`
    - `POST /api/changes/{opId}/accept`
    - `POST /api/changes/{opId}/revert` (writes back `beforeContent`)
- Emit `ChangeDecision` events to central.

This gives you **accepted vs reverted** diffs without re-architecting the agent into a proposal-only writer.

### 5) Documentation updates (repo rule)

If tool behavior changes meaningfully (telemetry side effects + change tracking), update:

- [`docs/seriem-agent/agents/mainagent.md`](docs/seriem-agent/agents/mainagent.md)
    - mention that filesystem tools emit telemetry + produce FileOperation IDs for review/revert.

### 6) MVP operational checklist

- Central collector deployment: internal VM/container, TLS if possible.
- Add log rotation/purge.
- Add “kill switch” env var to disable telemetry instantly.

## Rollout order (min risk, fastest feedback)

- Central collector (health + write-to-disk)
- Local backend spooling + upload
- Instrument WS tool/file events and verify central ingestion
- Add UI changes panel + accept/revert → finally you get “accepted diffs”

## Files you’ll most likely touch

- Backend:
    - [`backend/app/api/websocket.py`](backend/app/api/websocket.py)
    - [`backend/app/api/routes.py`](backend/app/api/routes.py)
    - [`backend/app/tools/filesystem.py`](backend/app/tools/filesystem.py)
    - [`backend/app/main.py`](backend/app/main.py)
- Frontend:
    - [`frontend/src/app/services/agent.service.ts`](frontend/src/app/services/agent.service.ts)
    - (new) changes panel component/service
- Docs:
    - [`docs/seriem-agent/agents/mainagent.md`](docs/seriem-agent/agents/mainagent.md)

## Biggest risks (don’t be naive)

- **Data volume**: full-content before/after file logs explode quickly; you need caps + compression.
- **Sensitive code leakage**: internal doesn’t mean harmless; treat central logs as production data.



````