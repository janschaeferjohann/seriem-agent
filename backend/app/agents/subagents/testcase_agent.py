"""Testcase subagent for generating and modifying testcase XML content.

This subagent is read-only: it may call filesystem read/list tools to load
datamodels or existing XML, but it must only return XML content. The main
supervisor agent is responsible for persisting changes via write_file/edit_file.
"""

import os

from langchain.agents import create_agent
from langchain_anthropic import ChatAnthropic

from app.tools import ls, read_file

# Default model if not specified
DEFAULT_MODEL = "claude-sonnet-4-20250514"


TESTCASE_FROM_DATAMODEL_PROMPT = """You generate XML testcases from Seriem datamodels.

You have access to tools:
- ls(path): list directory contents under the storage root
- read_file(path): read a file under the storage root

Input you will receive:
- A datamodel file path (relative to storage root)
- A natural-language description of the testcase to generate

Rules:
1) You MUST call read_file(datamodel_path) and base your output on the actual XML you read.
2) Output MUST be a single well-formed XML document.
3) Return ONLY the XML content. No explanations. No markdown fences.
4) Keep the XML concise while still matching the datamodel semantics and the user requirements.
5) Map datamodel Nodes to XML elements:
   - Use Node @name as the XML element name.
   - Nested Nodes become nested XML elements.
   - For Node multiple=\"true\": include exactly one representative occurrence unless the user explicitly requests more.
6) Root element selection:
   - If the datamodel has exactly one top-level Node, use that Node's name as the root element.
   - If it has multiple top-level Nodes, wrap them in a <Testcase> root element.

If the datamodel contains fields you cannot infer from the description, populate them with realistic placeholder values.
"""


TESTCASE_MODIFIER_PROMPT = """You modify existing XML testcase instances while preserving structure.

You have access to tools:
- ls(path): list directory contents under the storage root
- read_file(path): read a file under the storage root

Input you will receive:
- A source testcase XML file path (relative to storage root)
- A natural-language description of the changes to apply

Rules:
1) You MUST call read_file(source_testcase_path) and base your output on the XML you read.
2) Output MUST be a single well-formed XML document.
3) Return ONLY the XML content. No explanations. No markdown fences.
4) Preserve structure:
   - Do not rename elements or attributes.
   - Do not add or remove elements/attributes.
   - Do not reorder elements unless required for well-formedness.
5) Only modify text nodes and attribute values as needed to satisfy the description.
"""


def create_testcase_from_datamodel_agent(model_name: str | None = None):
    """Create a testcase generation agent (from datamodel).

    Args:
        model_name: Anthropic model to use. If None, uses env var or default.

    Returns:
        Configured agent for testcase generation from datamodel.
    """
    model = model_name or os.getenv("ANTHROPIC_MODEL", DEFAULT_MODEL)

    return create_agent(
        model=ChatAnthropic(model=model),
        tools=[ls, read_file],
        system_prompt=TESTCASE_FROM_DATAMODEL_PROMPT,
    )


def create_testcase_modifier_agent(model_name: str | None = None):
    """Create a testcase modification agent (preserve structure).

    Args:
        model_name: Anthropic model to use. If None, uses env var or default.

    Returns:
        Configured agent for testcase modification.
    """
    model = model_name or os.getenv("ANTHROPIC_MODEL", DEFAULT_MODEL)

    return create_agent(
        model=ChatAnthropic(model=model),
        tools=[ls, read_file],
        system_prompt=TESTCASE_MODIFIER_PROMPT,
    )


