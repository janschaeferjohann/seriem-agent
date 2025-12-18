# Datamodel Subagent

## Purpose

Generate `.datamodel` XML content from a natural-language specification.

This subagent is intentionally narrow: it generates XML text only. The main agent is responsible for writing the file to storage.

## Implementation

- Subagent: `backend/app/agents/subagents/datamodel_agent.py`
- Main-agent tool wrapper: `backend/app/agents/main_agent.py` → `generate_datamodel(request)`

## Inputs

- `request` (string): description of the datamodel to generate (fields, hierarchy, types, validation, multiplicity).

## Output contract

- Returns **XML only** (no prose, no markdown fences).
- Output is intended to be saved as a `.datamodel` file.

## Tool access / permissions

- **No tools** (does not read/list/write files).
- The main agent performs all filesystem operations (`write_file`, `edit_file`).


