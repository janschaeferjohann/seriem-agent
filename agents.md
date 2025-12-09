# Agent Architecture

## Overview

Seriem Agent uses a modular agent architecture built on LangChain with Anthropic Claude models. The system is designed to support hierarchical agent structures with a main orchestrator and specialized subagents.

## Current Implementation

### Main Agent

The main agent handles all user interactions and has access to filesystem tools for working with the local storage directory.

**Model**: Claude Sonnet (claude-sonnet-4-20250514)

**Tools**:
- `ls(path)` - List directory contents
- `read_file(path)` - Read file content  
- `write_file(path, content)` - Create or overwrite a file
- `edit_file(path, old_str, new_str)` - Edit file using string replacement

**System Prompt Focus**:
- Coding assistance
- File management
- Clear, helpful responses

## Planned Subagents

The architecture supports adding specialized subagents for task delegation:

### Code Generation Subagent (Planned)
- Generates code based on specifications
- Follows project coding standards
- Creates boilerplate and scaffolding

### Code Review Subagent (Planned)
- Reviews code for bugs and issues
- Suggests improvements
- Checks style consistency

### Test Generation Subagent (Planned)
- Creates unit tests
- Generates test cases
- Validates test coverage

## Architecture Diagram

```
┌─────────────────────────────────────────────────────┐
│                    User Interface                    │
│              (Angular Chat + File Explorer)          │
└─────────────────────┬───────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────┐
│                   FastAPI Backend                    │
│            (REST API + WebSocket)                    │
└─────────────────────┬───────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────┐
│                    Main Agent                        │
│              (LangChain + Claude)                    │
│                                                      │
│  ┌─────────────────────────────────────────────┐    │
│  │            Filesystem Tools                  │    │
│  │   ls | read_file | write_file | edit_file   │    │
│  └─────────────────────────────────────────────┘    │
│                                                      │
│  ┌─────────────────────────────────────────────┐    │
│  │         Subagents (Future)                   │    │
│  │   code_gen | code_review | test_gen         │    │
│  └─────────────────────────────────────────────┘    │
└─────────────────────┬───────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────┐
│                Local Storage                         │
│              (./storage directory)                   │
└─────────────────────────────────────────────────────┘
```

## Adding New Subagents

To add a new subagent:

1. Create a new file in `backend/app/agents/subagents/`
2. Define the subagent configuration:

```python
subagent_config = {
    "name": "your-subagent",
    "description": "Description for when to use this subagent",
    "system_prompt": "Specialized instructions...",
    "tools": [your_tools],
}
```

3. Register with the main agent in `main_agent.py`
4. The main agent will automatically delegate appropriate tasks

## Configuration

Agent behavior is configured via environment variables:

- `ANTHROPIC_API_KEY` - Required for Claude API access
- `STORAGE_PATH` - Path to agent workspace (default: `./storage`)



