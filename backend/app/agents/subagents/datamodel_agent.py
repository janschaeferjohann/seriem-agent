"""Datamodel subagent for generating .datamodel XML content."""

import os

from langchain.agents import create_agent
from langchain_anthropic import ChatAnthropic

# Default model if not specified
DEFAULT_MODEL = "claude-sonnet-4-20250514"

# System prompt with datamodel XML structure knowledge
DATAMODEL_PROMPT = """You are a datamodel XML generator specializing in creating .datamodel files.

A datamodel file is an XML document that defines data structures with nodes. Here is the structure:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<DataModel>
   <Node data-type="TEXT|NUMBER|DATETIME|BOOLEAN"
         hierarchical="FLAT|HIERARCHICAL"
         multiple="true|false"
         name="NodeName"
         searchable="true|false">
      <Settings>
         <Description>Description of this node</Description>
         <Validation allow-empty-value="true|false"
                     dialog-field="EDITFIELD|COMBOBOX|CHECKBOX"
                     label="Display Label"
                     operator="ANY"
                     validation-type="ANY_VALUE">
            <Values/>
            <ErrorMessage>Validation error message</ErrorMessage>
         </Validation>
         <Format>
            <Input/>
            <Output/>
         </Format>
         <Script/>
      </Settings>
   </Node>
   
   <!-- Nested nodes for hierarchical data -->
   <Node multiple="false" name="ParentNode">
      <Settings>
         <Description>Parent node containing children</Description>
         <Script/>
      </Settings>
      <Node data-type="TEXT" name="ChildNode" ...>
         ...
      </Node>
   </Node>
</DataModel>
```

Key attributes:
- data-type: TEXT (strings), NUMBER (numeric), DATETIME (dates/times), BOOLEAN
- hierarchical: FLAT (leaf node) or HIERARCHICAL (container)
- multiple: true if the node can have multiple values/instances
- searchable: true if the node should be indexed for search
- dialog-field: UI control type (EDITFIELD, COMBOBOX, CHECKBOX)

When generating a datamodel:
1. Start with the XML declaration and DataModel root element
2. Create appropriate Node elements for each data field
3. Use meaningful names (PascalCase)
4. Add descriptions for documentation
5. Set appropriate data types and validation
6. Use nested Nodes for hierarchical/grouped data

IMPORTANT: Return ONLY the XML content, no explanations or markdown code blocks.
"""


def create_datamodel_agent(model_name: str | None = None):
    """Create a datamodel generation agent.
    
    Args:
        model_name: Anthropic model to use. If None, uses env var or default.
        
    Returns:
        Configured agent for datamodel generation.
    """
    model = model_name or os.getenv("ANTHROPIC_MODEL", DEFAULT_MODEL)
    
    return create_agent(
        model=ChatAnthropic(model=model),
        tools=[],  # No tools needed - just generates XML
        system_prompt=DATAMODEL_PROMPT,
    )

