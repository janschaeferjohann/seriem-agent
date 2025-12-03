"""Main agent configuration with filesystem tools."""

import os

from langchain.agents import create_agent

from app.tools import ls, read_file, write_file, edit_file, delete_file, delete_directory

# Default model if not specified in environment
DEFAULT_MODEL = "claude-sonnet-4-20250514"

# System prompt for the main agent
SYSTEM_PROMPT = """You are a helpful coding assistant with access to a local filesystem workspace.

You can help users by:
- Browsing and exploring files in the workspace
- Reading file contents
- Creating and writing new files
- Editing existing files
- Deleting files and directories

Available tools:
- ls: List directory contents
- read_file: Read a file's contents
- write_file: Create or overwrite a file
- edit_file: Edit a file by replacing text
- delete_file: Delete a file
- delete_directory: Delete a directory (optionally with all contents)

All file operations are relative to the storage workspace directory.

When working with files:
1. Use ls to explore the directory structure first
2. Use read_file to understand existing code before making changes
3. Use write_file for new files or complete rewrites
4. Use edit_file for targeted changes to existing files
5. Use delete_file to remove files (be careful, this is permanent!)
6. Use delete_directory to remove directories (use recursive=True for non-empty dirs)

Be helpful, clear, and efficient in your responses. When showing code, explain what it does."""

# Tools available to the main agent
TOOLS = [ls, read_file, write_file, edit_file, delete_file, delete_directory]


def get_agent_executor(model_name: str | None = None):
    """Get an agent executor ready to handle requests.
    
    Args:
        model_name: Anthropic model to use. If None, uses ANTHROPIC_MODEL env var or default.
        
    Returns:
        Compiled agent.
    """
    # Use provided model_name, or fall back to env var, or use default
    model = model_name or os.getenv("ANTHROPIC_MODEL", DEFAULT_MODEL)
    
    # Create the agent using LangChain's create_agent
    agent = create_agent(
        model=model,
        tools=TOOLS,
        system_prompt=SYSTEM_PROMPT,
    )
    
    return agent


def create_agent_instance(model_name: str | None = None):
    """Create the main agent with filesystem tools.
    
    Args:
        model_name: Anthropic model to use. If None, uses ANTHROPIC_MODEL env var or default.
        
    Returns:
        Configured agent.
    """
    return get_agent_executor(model_name)
