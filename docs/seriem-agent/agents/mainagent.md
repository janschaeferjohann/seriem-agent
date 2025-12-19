# Main Agent (Supervisor)

## Purpose

The main agent is the **supervisor/orchestrator**. It:

- Handles all user interactions.
- Proposes **all filesystem writes** (via the proposal layer) for user approval.
- Delegates specialized generation/modification work to **subagents** via dedicated tools.

## Where it lives

- `backend/app/agents/main_agent.py`
  - Defines the supervisor agent (`create_agent_instance`) and the tool wrappers.
- `backend/app/api/websocket.py`
  - Streams model output and tool call events to the frontend.

## Proposal Layer

**Important**: File modifications do not happen immediately. Instead, they create **proposals** that the user must approve.

### How it works

1. Agent calls `write_file`, `edit_file`, or `delete_file`
2. Tool creates a **proposal** (stored in-memory in the backend)
3. Tool returns confirmation: `"Proposed [action] to '[path]' (proposal_id: abc123). Awaiting user approval."`
4. User sees pending proposals in the **"Pending Changes"** panel
5. User reviews the diff and either **approves** or **rejects**
6. If approved, changes are applied to the filesystem
7. If rejected, changes are discarded

### Data Flow

```
Agent → write_file() → Proposal Store → Frontend → User Review → Approve → Filesystem
                                                              → Reject → Discard
```

### Proposal Structure

```python
ChangeProposal = {
    "proposal_id": str,        # Unique identifier (e.g., "abc12345")
    "files": [
        {
            "path": str,           # Relative to workspace root
            "operation": "create" | "update" | "delete",
            "before": str | None,  # Original content (None for create)
            "after": str | None,   # New content (None for delete)
        }
    ],
    "summary": str,            # Human-readable description
    "created_at": datetime,    # When proposal was created
}
```

### API Endpoints

- `GET /api/proposals/pending` - List all pending proposals
- `GET /api/proposals/{id}` - Get proposal details with full diff
- `POST /api/proposals/{id}/approve` - Apply changes to filesystem
- `POST /api/proposals/{id}/reject` - Discard proposal
- `DELETE /api/proposals/all` - Clear all proposals

## Tooling surface

### Filesystem tools (proposal-based)

Write operations create proposals instead of immediate changes:

- `ls(path)`: list directory contents (immediate)
- `read_file(path)`: read file contents (immediate)
- `write_file(path, content)`: **creates proposal** for create/overwrite
- `edit_file(path, old_str, new_str)`: **creates proposal** for edit
- `delete_file(path)`: **creates proposal** for deletion
- `delete_directory(path, recursive=False)`: delete a directory (immediate for safety)

### Subagent-backed tools

These tools return **content only** (typically XML/JSON). The main agent then persists that content using filesystem tools (which create proposals).

- `generate_datamodel(request)`: returns `.datamodel` XML
- `generate_testcase_from_datamodel(datamodel_path, description)`: returns testcase `.xml` generated from a `.datamodel`
- `modify_testcase_xml(source_testcase_path, description)`: returns updated testcase `.xml` (structure preserved; values only)
- `generate_formio_json(description, datamodel_path?, source_formio_path?)`: returns Form.io JSON

## Delegation model (non-negotiable rule)

- **Subagents are read-only**: they may read/list files if needed, but must not write.
- **The main agent proposes all changes**: any create/edit/delete creates a proposal that the user must approve.

## Workspace Selection

The agent operates on a user-selected **workspace** (folder). This is:

- Selected via native folder picker (in Electron) or prompt (in browser)
- Stored and can be changed at any time
- All file paths are relative to the workspace root
- Git integration is auto-detected if `.git` folder exists

### Workspace API

- `POST /api/workspace/select` - Set active workspace path
- `GET /api/workspace/current` - Get current workspace info (path, git status)

## Configuration

Relevant environment variables:

- `ANTHROPIC_API_KEY`: required to call the model provider
- `ANTHROPIC_MODEL`: model name (defaults to `claude-sonnet-4-20250514` in code)
- `STORAGE_PATH`: initial workspace directory (can be changed by user)

