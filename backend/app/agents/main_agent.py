"""Main supervisor agent configuration with filesystem tools and subagent delegation."""

import os

from langchain.agents import create_agent
from langchain_core.tools import tool

from app.tools import ls, read_file, write_file, edit_file, delete_file, delete_directory
from app.agents.subagents.datamodel_agent import create_datamodel_agent

# Default model if not specified in environment
DEFAULT_MODEL = "claude-sonnet-4-20250514"

# Cache for model name to use in tools
_current_model: str | None = None


@tool
def generate_datamodel(request: str) -> str:
    """Generate datamodel XML content based on a description.
    
    Use this tool when you need to create or edit .datamodel files.
    The tool returns XML content that you should then save using write_file.
    
    Args:
        request: Description of the datamodel to generate. Be specific about:
                 - What data fields are needed
                 - Data types (text, number, date, boolean)
                 - Whether fields can have multiple values
                 - Any validation requirements
                 - Hierarchical relationships between fields
        
    Returns:
        XML content for a .datamodel file, ready to be saved.
    """
    global _current_model
    model = _current_model or os.getenv("ANTHROPIC_MODEL", DEFAULT_MODEL)
    
    agent = create_datamodel_agent(model)
    result = agent.invoke({"messages": [{"role": "user", "content": request}]})
    
    # Extract the last message content
    messages = result.get("messages", [])
    if messages:
        last_message = messages[-1]
        if hasattr(last_message, "content"):
            return last_message.content
    
    return "Error: Could not generate datamodel content"


# System prompt for the supervisor agent
SYSTEM_PROMPT = """You are a helpful coding assistant with access to a local filesystem workspace and specialized capabilities for generating datamodel files.

You can help users by:
- Browsing and exploring files in the workspace
- Reading file contents
- Creating and writing new files
- Editing existing files
- Deleting files and directories
- Generating .datamodel XML files using the datamodel subagent

Available tools:
- ls: List directory contents
- read_file: Read a file's contents
- write_file: Create or overwrite a file
- edit_file: Edit a file by replacing text
- delete_file: Delete a file
- delete_directory: Delete a directory (optionally with all contents)
- generate_datamodel: Generate XML content for .datamodel files (uses specialized subagent)

All file operations are relative to the storage workspace directory.

When working with files:
1. Use ls to explore the directory structure first
2. Use read_file to understand existing code before making changes
3. Use write_file for new files or complete rewrites
4. Use edit_file for targeted changes to existing files
5. Use delete_file to remove files (be careful, this is permanent!)
6. Use delete_directory to remove directories (use recursive=True for non-empty dirs)

When creating or editing .datamodel files:
1. Use generate_datamodel to get the XML content - describe what fields and structure you need
2. Use write_file to save the generated content to a .datamodel file
3. For edits to existing datamodels, first use read_file to see the current content, then use generate_datamodel with context about what to change

Be helpful, clear, and efficient in your responses. When showing code, explain what it does."""

# Tools available to the supervisor agent
TOOLS = [ls, read_file, write_file, edit_file, delete_file, delete_directory, generate_datamodel]


def get_agent_executor(model_name: str | None = None):
    """Get a supervisor agent executor ready to handle requests.
    
    Args:
        model_name: Anthropic model to use. If None, uses ANTHROPIC_MODEL env var or default.
        
    Returns:
        Compiled supervisor agent.
    """
    global _current_model
    
    # Use provided model_name, or fall back to env var, or use default
    model = model_name or os.getenv("ANTHROPIC_MODEL", DEFAULT_MODEL)
    _current_model = model
    
    # Create the supervisor agent using LangChain's create_agent
    agent = create_agent(
        model=model,
        tools=TOOLS,
        system_prompt=SYSTEM_PROMPT,
    )
    
    return agent


def create_agent_instance(model_name: str | None = None):
    """Create the main supervisor agent with filesystem tools and subagent delegation.
    
    Args:
        model_name: Anthropic model to use. If None, uses ANTHROPIC_MODEL env var or default.
        
    Returns:
        Configured supervisor agent.
    """
    return get_agent_executor(model_name)
