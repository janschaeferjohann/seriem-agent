# Main Agent (Supervisor)

## Purpose

The main agent is the **supervisor/orchestrator**. It:

- Handles all user interactions.
- Performs **all filesystem writes** under the storage root (`write_file`, `edit_file`, deletes).
- Delegates specialized generation/modification work to **subagents** via dedicated tools.

## Where it lives

- `backend/app/agents/main_agent.py`
  - Defines the supervisor agent (`create_agent_instance`) and the tool wrappers.
- `backend/app/api/websocket.py`
  - Streams model output and tool call events to the frontend.

## Tooling surface

### Filesystem tools (direct)

- `ls(path)`: list directory contents
- `read_file(path)`: read file contents
- `write_file(path, content)`: create/overwrite a file
- `edit_file(path, old_str, new_str)`: targeted string replacement
- `delete_file(path)`: delete a file
- `delete_directory(path, recursive=False)`: delete a directory

### Subagent-backed tools

These tools return **content only** (typically XML). The main agent then persists that content using filesystem tools if the user asked for it.

- `generate_datamodel(request)`: returns `.datamodel` XML
- `generate_testcase_from_datamodel(datamodel_path, description)`: returns testcase `.xml` generated from a `.datamodel`
- `modify_testcase_xml(source_testcase_path, description)`: returns updated testcase `.xml` (structure preserved; values only)

## Delegation model (non-negotiable rule)

- **Subagents are read-only**: they may read/list files if needed, but must not write.
- **The main agent is the only writer**: any create/edit/delete is performed by the main agent via tools.

## Configuration

Relevant environment variables:

- `ANTHROPIC_API_KEY`: required to call the model provider
- `ANTHROPIC_MODEL`: model name (defaults to `claude-sonnet-4-20250514` in code)
- `STORAGE_PATH`: storage root directory (defaults to `./storage`)

