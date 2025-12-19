# Local Backend with Proposal Layer MVP (Electron Packaged)

## Problem Statement

Users want to:

1. Work on their **own local folders/git repos**, not just `./storage`
2. **Review changes** before they're applied (diff approval)
3. **Easy installation** - double-click an .exe, not run terminal commands
4. Keep the simple localhost architecture (no central server complexity)

## Core Judgment

**Worth doing.** This solves the real problems without the architectural complexity of centralizing LLM calls or proxying file reads through Electron IPC.

## Key Insight: Electron as Launcher, Not Proxy

Electron's role is simple:

- **Launch**: Spawn the Python backend as a child process on startup
- **Host**: Display the Angular frontend in a BrowserWindow
- **Native dialogs**: Provide native folder picker for workspace selection
- **Lifecycle**: Kill backend on app close

Electron does NOT proxy file operations. The backend still has direct filesystem access.

## Prerequisite

Users must have **Python 3.11+** installed. The Electron app will:

1. Check for Python on startup
2. Show clear error if not found with install instructions
3. Auto-install pip dependencies on first run (or bundle a venv)

## Architecture

````mermaid
flowchart TD
  exe[User_Launches_SeriemAgent.exe] --> electron[Electron_Main_Process]
  electron -->|spawns| python[Python_FastAPI_Backend]
  electron -->|loads| angular[Angular_Frontend_BrowserWindow]
  angular -->|HTTP_WebSocket_localhost| python
  python -->|direct_access| fs[Local_Filesystem]
  
  subgraph proposal_flow [Proposal Flow]
    agent[Agent] -->|proposes| proposal[ChangeProposal]
    proposal -->|shown_to_user| diffUI[Diff_Review_UI]
    diffUI -->|approve| writer[Filesystem_Writer]
    diffUI -->|reject| discard[Discard]
  end
  
  python --> proposal_flow
  
  electron -.->|IPC_for_native_dialogs_only| angular
```

## Data Structures

```python
# Workspace selection
Workspace = {
    "root_path": str,      # Absolute path to user-selected folder
    "git_enabled": bool,   # Whether to offer git operations
}

# Change proposal (agent output, not yet applied)
ChangeProposal = {
    "proposal_id": str,
    "files": [
        {
            "path": str,           # Relative to workspace root
            "operation": "create" | "update" | "delete",
            "before": str | None,  # None for create
            "after": str | None,   # None for delete
        }
    ],
    "summary": str,
}

# Pending proposals (in-memory or SQLite for persistence)
PendingProposals = dict[proposal_id, ChangeProposal]
```

## Implementation

### Phase 0: Electron Shell (New)

**New folder structure** `desktop/`:

```
desktop/
  main.js           # Electron main process
  preload.js        # Secure IPC bridge (contextIsolation)
  package.json      # Electron + electron-builder config
  assets/           # App icons
```

**Main process responsibilities** (`desktop/main.js`):

```javascript
// On app ready:
// 1. Find Python executable
const pythonPath = findPython(); // Check PATH, common locations

// 2. Spawn backend
const backend = spawn(pythonPath, ['-m', 'uvicorn', 'app.main:app', '--port', '8000'], {
  cwd: path.join(__dirname, '../backend'),
  env: { ...process.env, ANTHROPIC_API_KEY: getStoredApiKey() }
});

// 3. Wait for backend ready (poll /health)
await waitForBackend('http://localhost:8000/health');

// 4. Create window loading Angular
mainWindow = new BrowserWindow({
  webPreferences: { preload: path.join(__dirname, 'preload.js') }
});
mainWindow.loadFile('../frontend/dist/index.html'); // or loadURL if dev

// 5. On close: kill backend
app.on('before-quit', () => backend.kill());
```

**Preload script** (`desktop/preload.js`):

```javascript
// Expose ONLY what frontend needs
contextBridge.exposeInMainWorld('electronAPI', {
  selectFolder: () => ipcRenderer.invoke('dialog:selectFolder'),
  getApiKey: () => ipcRenderer.invoke('config:getApiKey'),
  setApiKey: (key) => ipcRenderer.invoke('config:setApiKey', key),
});
```

### Phase 1: Workspace Selection

**Backend changes** ([`backend/app/main.py`](backend/app/main.py), [`backend/app/api/routes.py`](backend/app/api/routes.py)):

- Add `POST /api/workspace/select` - sets active workspace path
- Add `GET /api/workspace/current` - returns current workspace info
- Modify `STORAGE_ROOT` to be dynamically set per session
- Add path validation (no `..` escapes, exists check)

**Frontend changes** ([`frontend/src/app/services/file.service.ts`](frontend/src/app/services/file.service.ts)):

- Add workspace selection button that calls `window.electronAPI.selectFolder()`
- Receive absolute path from native dialog
- Call `POST /api/workspace/select` with the path
- File explorer shows selected workspace contents

### Phase 2: Proposal Layer (Core Change)

**New module** `backend/app/proposals/`:

- `models.py` - Pydantic models for ChangeProposal
- `store.py` - In-memory dict of pending proposals
- `routes.py` - API endpoints for proposal management

**Modify filesystem tools** ([`backend/app/tools/filesystem.py`](backend/app/tools/filesystem.py)):

Current `write_file` behavior:

```python
def write_file(path: str, content: str) -> str:
    # Writes immediately
    target.write_text(content)
    return f"File written: {path}"
```

New `write_file` behavior:

```python
def write_file(path: str, content: str) -> str:
    # Creates proposal instead of writing
    before = target.read_text() if target.exists() else None
    proposal = create_proposal(path, "update" if before else "create", before, content)
    store_pending_proposal(proposal)
    return f"Proposed change to {path} (proposal_id: {proposal.id}). Awaiting approval."
```

Same pattern for `edit_file` and `delete_file`.

**New API endpoints**:

- `GET /api/proposals/pending` - list pending proposals
- `GET /api/proposals/{id}` - get proposal details with diff
- `POST /api/proposals/{id}/approve` - apply changes to filesystem
- `POST /api/proposals/{id}/reject` - discard proposal

### Phase 3: Diff Review UI

**New component** `frontend/src/app/components/change-review/`:

- Shows pending proposals in a panel
- Per-file diff view using Monaco DiffEditor (already have Monaco loaded)
- "Approve" / "Reject" buttons per proposal
- Optional: "Approve All" for batch operations

**Integration with existing UI**:

- Add "Pending Changes" badge/indicator to sidebar
- When agent completes a task with proposals, auto-open review panel
- Toast notification: "3 changes pending review"

### Phase 4: Optional Git Integration

If workspace is a git repo:

- `POST /api/proposals/{id}/approve?commit=true&message=...` - approve + git commit
- Show git status in file explorer
- Show uncommitted changes indicator

## Files to Create/Modify

| File | Change |

|------|--------|

| `desktop/main.js` | NEW: Electron main process |

| `desktop/preload.js` | NEW: Secure IPC bridge |

| `desktop/package.json` | NEW: Electron + electron-builder config |

| [`backend/app/main.py`](backend/app/main.py) | Dynamic workspace root |

| [`backend/app/api/routes.py`](backend/app/api/routes.py) | Workspace + proposal endpoints |

| `backend/app/proposals/` | NEW: Proposal models, store, routes |

| [`backend/app/tools/filesystem.py`](backend/app/tools/filesystem.py) | Proposal-based writes |

| [`backend/app/agents/main_agent.py`](backend/app/agents/main_agent.py) | Update system prompt to mention approval flow |

| [`frontend/src/app/services/file.service.ts`](frontend/src/app/services/file.service.ts) | Workspace selection via Electron IPC |

| `frontend/src/app/components/change-review/` | NEW: Diff review component |

| [`docs/seriem-agent/agents/mainagent.md`](docs/seriem-agent/agents/mainagent.md) | Document proposal model |

## Electron Build Configuration

**Package.json** (`desktop/package.json`):

```json
{
  "name": "seriem-agent",
  "version": "0.1.0",
  "main": "main.js",
  "scripts": {
    "start": "electron .",
    "build": "electron-builder"
  },
  "build": {
    "appId": "com.seriem.agent",
    "productName": "Seriem Agent",
    "directories": { "output": "dist" },
    "win": {
      "target": "nsis",
      "icon": "assets/icon.ico"
    },
    "extraResources": [
      { "from": "../backend", "to": "backend", "filter": ["**/*", "!venv/**", "!__pycache__/**"] },
      { "from": "../frontend/dist", "to": "frontend" }
    ]
  }
}
```

**First-run flow**:

1. App starts, checks for Python
2. If missing: show dialog with download link
3. If found: check `backend/venv` exists
4. If no venv: run `python -m venv venv && venv/Scripts/pip install -r requirements.txt`
5. Start backend with venv Python

## What This Doesn't Do (Explicit Non-Goals)

- **No centralized server**: Backend runs locally, API key stays local
- **No bundled Python**: Users must have Python 3.11+ installed (keeps package small)
- **No remote telemetry** (see separate telemetry plan if needed)
- **No multi-user auth**: Single user = single backend instance

## Risks and Mitigations

| Risk | Mitigation |

|------|------------|

| Python not installed | Clear error dialog with install link |

| Agent expects immediate write confirmation | Update system prompt; tool returns "pending approval" |

| Large proposals (many files) | Paginate proposal list; lazy-load diffs |

| User forgets to approve | Show persistent badge; auto-reject after timeout? |

| Port 8000 in use | Try alternative ports; show error if all fail |

## Rollout Order

1. **Electron shell** - basic app that spawns backend and loads frontend
2. **Native folder picker IPC** - workspace selection works
3. **Workspace selection API** (backend) - dynamic root path
4. **Proposal store + API** (backend) - test via curl
5. **Modify filesystem tools** to create proposals - agent behavior changes
6. **Diff review UI** - users can now approve/reject
7. **Electron build** - package as .exe with electron-builder
8. **Git integration** - optional commit on approve
9. **Documentation** - update mainagent.md

## Comparison with Centralized Plan

| Aspect | This Plan | Centralized Plan |

|--------|-----------|------------------|

| Backend location | Local (bundled in Electron) | Central server |

| Electron role | Launcher + native dialogs only | Complex IPC proxy for all file ops |

| File reads | Direct (backend has access) | Must proxy through client |

| API key | Local config (Electron secure storage) | Server-side |

| Complexity | Medium | High |

| Multi-user | No (single instance) | Yes |

| Offline capable | Yes (except LLM calls) | No |



````