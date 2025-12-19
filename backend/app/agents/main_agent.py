"""Main supervisor agent configuration with filesystem tools and subagent delegation."""

import json
import os
import re

from langchain.agents import create_agent
from langchain_core.tools import tool

from app.tools import ls, read_file, write_file, edit_file, delete_file, delete_directory
from app.agents.subagents.datamodel_agent import create_datamodel_agent
from app.agents.subagents.formio_agent import create_formio_agent
from app.agents.subagents.testcase_agent import (
    create_testcase_from_datamodel_agent,
    create_testcase_modifier_agent,
)

# Default model if not specified in environment
DEFAULT_MODEL = "claude-sonnet-4-20250514"

# Cache for model name to use in tools
_current_model: str | None = None


def _message_content_to_str(content: object) -> str:
    """Coerce LangChain message content into a plain string.

    Anthropic message content can be a string or a list/dict of content blocks.
    """
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, dict):
        # Common content-block shapes: {"type": "text", "text": "..."}
        if "text" in content:
            return str(content["text"])
        if "content" in content:
            return str(content["content"])
        return str(content)
    if isinstance(content, list):
        return "".join(_message_content_to_str(part) for part in content)

    text_attr = getattr(content, "text", None)
    if text_attr is not None:
        return str(text_attr)

    return str(content)


@tool
def generate_datamodel(request: str) -> str:
    """Generate datamodel XML content based on a description.
    
    Use this tool when you need to create or edit .datamodel files.
    The tool returns XML content that you should then save using write_file.
    IMPORTANT: Do NOT paste the full XML into the normal chat response. Keep large XML
    payloads in tool results and/or write them to files, and respond with a short summary.
    
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
            return _message_content_to_str(last_message.content)
    
    return "Error: Could not generate datamodel content"


@tool
def generate_testcase_from_datamodel(datamodel_path: str, description: str) -> str:
    """Generate testcase XML content from a .datamodel file and a description.

    Use this tool when you need to create a new testcase .xml based on an existing
    .datamodel file under the storage directory.

    The tool returns XML content that you should then save using write_file.
    IMPORTANT: Do NOT paste the full XML into the normal chat response. Keep large XML
    payloads in tool results and/or write them to files, and respond with a short summary.

    Args:
        datamodel_path: Path to the .datamodel file, relative to storage root.
        description: Requirements for the testcase content (what to include, values, etc.).

    Returns:
        XML content for a testcase .xml file, ready to be saved.
    """
    global _current_model
    model = _current_model or os.getenv("ANTHROPIC_MODEL", DEFAULT_MODEL)

    agent = create_testcase_from_datamodel_agent(model)
    request = f"""Datamodel path: {datamodel_path}

Description / Requirements:
{description}

Task:
- Read the datamodel XML from the given path using read_file.
- Generate ONE well-formed XML testcase instance matching the datamodel semantics.
- Return ONLY the XML content (no prose, no markdown fences).
"""
    result = agent.invoke({"messages": [{"role": "user", "content": request}]})

    messages = result.get("messages", [])
    if messages:
        last_message = messages[-1]
        if hasattr(last_message, "content"):
            return _message_content_to_str(last_message.content)

    return "Error: Could not generate testcase XML content"


@tool
def modify_testcase_xml(source_testcase_path: str, description: str) -> str:
    """Modify an existing testcase XML file while preserving structure.

    Use this tool when you need to update values inside an existing testcase .xml
    without changing element/attribute names or overall structure.

    The tool returns XML content that you should then save using write_file (new file)
    or edit_file (replace full contents), depending on user intent.
    IMPORTANT: Do NOT paste the full XML into the normal chat response. Keep large XML
    payloads in tool results and/or write them to files, and respond with a short summary.

    Args:
        source_testcase_path: Path to the source .xml testcase file, relative to storage root.
        description: What values should be changed and how.

    Returns:
        Updated XML content (structure preserved), ready to be saved.
    """
    global _current_model
    model = _current_model or os.getenv("ANTHROPIC_MODEL", DEFAULT_MODEL)

    agent = create_testcase_modifier_agent(model)
    request = f"""Source testcase path: {source_testcase_path}

Modify content according to the following description, but preserve the same XML structure and element/attribute names.

Description:
{description}

Task:
- Read the source testcase XML from the given path using read_file.
- Apply the requested changes by editing values only (text nodes / attribute values).
- Return ONLY the XML content (no prose, no markdown fences).
"""
    result = agent.invoke({"messages": [{"role": "user", "content": request}]})

    messages = result.get("messages", [])
    if messages:
        last_message = messages[-1]
        if hasattr(last_message, "content"):
            return _message_content_to_str(last_message.content)

    return "Error: Could not modify testcase XML content"


@tool
def generate_formio_json(
    description: str,
    datamodel_path: str = "",
    source_formio_path: str = "",
) -> str:
    """Generate or modify Form.io JSON content for .formio files.

    Use this tool when you need to create or edit .formio files (Form.io JSON schemas).

    The tool returns JSON content that you should then save using write_file (new file)
    or edit_file (replace full contents), depending on user intent.
    IMPORTANT: Do NOT paste the full JSON into the normal chat response. Keep large JSON
    payloads in tool results and/or write them to files, and respond with a short summary.

    Args:
        description: Requirements for the Form.io schema (what to include/change).
        datamodel_path: Optional path to a .datamodel file, relative to storage root.
                       If provided (and source_formio_path is empty), the subagent will
                       read and use the datamodel as input.
        source_formio_path: Optional path to an existing .formio file, relative to storage root.
                            If provided, the subagent will read and modify that JSON while
                            preserving structure (no add/remove components; no key renames).

    Returns:
        JSON content for a .formio file, ready to be saved.
    """
    global _current_model
    model = _current_model or os.getenv("ANTHROPIC_MODEL", DEFAULT_MODEL)

    agent = create_formio_agent(model)
    request = f"""Datamodel path: {datamodel_path or "(none)"}
Source formio path: {source_formio_path or "(none)"}

Description / Requirements:
{description}

Task:
- Decide mode automatically:
  - If Source formio path is provided: read it via read_file and modify it (preserve structure).
  - Else if Datamodel path is provided: read it via read_file and generate a Form.io JSON schema.
  - Else: generate a Form.io JSON schema from the description.
- Return ONLY the JSON content (no prose, no markdown fences).
"""
    result = agent.invoke({"messages": [{"role": "user", "content": request}]})

    messages = result.get("messages", [])
    if not messages:
        return "Error: Could not generate Form.io JSON content"

    last_message = messages[-1]
    if not hasattr(last_message, "content"):
        return "Error: Could not generate Form.io JSON content"

    content = _message_content_to_str(last_message.content)

    # Validate/normalize JSON (robust against accidental fenced output).
    try:
        parsed = json.loads(content)
    except Exception:
        m = re.search(r"```json\s*([\s\S]*?)```", content, re.IGNORECASE) or re.search(
            r"```([\s\S]*?)```", content
        )
        if not m:
            return "Error: Could not generate Form.io JSON content"
        try:
            parsed = json.loads(m.group(1).strip())
        except Exception:
            return "Error: Could not generate Form.io JSON content"

    if isinstance(parsed, list):
        parsed = {"display": "form", "components": parsed}

    if not isinstance(parsed, dict):
        return "Error: Could not generate Form.io JSON content"

    display = parsed.get("display", "form")
    components = parsed.get("components", [])
    if not isinstance(components, list):
        components = []

    normalized: dict = {"display": display, "components": components}
    for key, value in parsed.items():
        if key in ("display", "components"):
            continue
        normalized[key] = value

    return json.dumps(normalized, indent=2, ensure_ascii=False)


# System prompt for the supervisor agent
SYSTEM_PROMPT = """You are a helpful coding assistant with access to a local filesystem workspace and specialized capabilities for generating datamodel files, testcase XML files, and Form.io .formio JSON schemas.

IMPORTANT: File modifications (write_file, edit_file, delete_file) create PROPOSALS that the user must approve before changes are applied. When you use these tools, the changes are NOT immediately applied - they are queued for user review. The user will see a diff view and can approve or reject each proposal.

You can help users by:
- Browsing and exploring files in the workspace
- Reading file contents
- Creating and writing new files (creates a proposal for user approval)
- Editing existing files (creates a proposal for user approval)
- Deleting files and directories (creates a proposal for user approval)
- Generating .datamodel XML files using the datamodel subagent
- Generating and modifying testcase .xml files using the testcase subagent
- Generating and modifying Form.io .formio JSON files using the formio subagent

Available tools:
- ls: List directory contents
- read_file: Read a file's contents
- write_file: Create or overwrite a file (creates proposal pending approval)
- edit_file: Edit a file by replacing text (creates proposal pending approval)
- delete_file: Delete a file (creates proposal pending approval)
- delete_directory: Delete a directory (optionally with all contents)
- generate_datamodel: Generate XML content for .datamodel files (uses specialized subagent)
- generate_testcase_from_datamodel: Generate XML content for testcase .xml from an existing .datamodel
- modify_testcase_xml: Modify an existing testcase .xml (structure preserved; values only)
- generate_formio_json: Generate/modify JSON content for Form.io .formio files

All file operations are relative to the current workspace directory.

Output policy (important):
1. Tool results may contain large payloads (e.g. XML/JSON). Do NOT paste large tool outputs into the normal chat response.
2. Prefer writing generated content to files using write_file/edit_file when the user asked to create/update files.
3. In the chat response, provide a short summary (what was generated/changed and where it was saved). Remind the user that they need to approve the proposal in the "Pending Changes" panel for the changes to take effect.

When working with files:
1. Use ls to explore the directory structure first
2. Use read_file to understand existing code before making changes
3. Use write_file for new files or complete rewrites (creates proposal)
4. Use edit_file for targeted changes to existing files (creates proposal)
5. Use delete_file to remove files (creates proposal)
6. Use delete_directory to remove directories (use recursive=True for non-empty dirs)

After making changes:
- Inform the user that a proposal has been created
- Remind them to review and approve the changes in the "Pending Changes" panel
- The proposal_id is included in the tool response for reference

When creating or editing .datamodel files:
1. Use generate_datamodel to get the XML content - describe what fields and structure you need
2. Use write_file to save the generated content to a .datamodel file (creates proposal)
3. For edits to existing datamodels, first use read_file to see the current content, then use generate_datamodel with context about what to change

When creating or editing testcase .xml files:
1. If you have a .datamodel file as source, use generate_testcase_from_datamodel to get the XML content
2. If you need to update an existing testcase .xml (values only), use modify_testcase_xml
3. Use write_file to save a new testcase file (creates proposal), or edit_file to replace content in an existing file

When creating or editing .formio files:
1. Use generate_formio_json to get the JSON content (optionally provide datamodel_path or source_formio_path)
2. Use write_file to save a new .formio file (creates proposal), or edit_file to replace content in an existing .formio file

Be helpful, clear, and efficient in your responses. When showing code, explain what it does."""

# Tools available to the supervisor agent
TOOLS = [
    ls,
    read_file,
    write_file,
    edit_file,
    delete_file,
    delete_directory,
    generate_datamodel,
    generate_testcase_from_datamodel,
    modify_testcase_xml,
    generate_formio_json,
]


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
