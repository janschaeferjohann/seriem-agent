"""
Module for generating ContainerPart XML elements.
Handles creation of container part structures with child elements.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Union, Dict, Any
from enum import Enum
from templify.utils.logger_setup import setup_logger
import logging
from .abstractpart import AbstractPart, Script

# Initialize logger
logger = setup_logger(__name__, log_level=logging.INFO)

@dataclass
class ChildElement:
    """Represents a child element in the container part"""
    type: str  # One of: Container, Image, Numbering, Par, Table
    content: Union[str, Dict[str, Any]]

@dataclass
class ContainerPart(AbstractPart):
    """Represents a container part element with child elements"""
    children: List[ChildElement] = field(default_factory=list)

def create_child_element_xml(child: ChildElement) -> str:
    """Generate XML for a child element"""
    if not child:
        return ""
        
    # Handle string content directly
    if isinstance(child.content, str):
        # For ContainerPartRef, preserve the exact XML structure
        if child.type == "ContainerPartRef":
            return child.content
        return f'''<{child.type}>
    {child.content}
</{child.type}>'''
        
    # Handle dictionary content
    content_xml = ""
    for key, value in child.content.items():
        if isinstance(value, dict):
            content_xml += f"<{key}>{create_child_element_xml(ChildElement(type=key, content=value))}</{key}>"
        else:
            content_xml += f"<{key}>{value}</{key}>"
            
    return f'''<{child.type}>
    {content_xml}
</{child.type}>'''

def create_container_part_xml(part: ContainerPart) -> str:
    """Generate XML for a container part element"""
    elements = []
    
    # Add AbstractPart elements
    if part.visible_if:
        elements.append(f'''<VisibleIf>
    <![CDATA[{part.visible_if.content}]]>
</VisibleIf>''')
        
    if part.validation:
        elements.append(f'''<Validation>
    <![CDATA[{part.validation.content}]]>
</Validation>''')
        
    # Add child elements
    for child in part.children:
        elements.append(create_child_element_xml(child))
        
    if not elements:
        return "<ContainerPart/>"
        
    return f'''<ContainerPart>
    {"".join(elements)}
</ContainerPart>'''

def create_container_parts_xml(parts: List[ContainerPart]) -> str:
    """Generate XML for multiple container parts"""
    return "\n".join(create_container_part_xml(part) for part in parts)

def main():
    """Example usage of the container part generation functions."""
    # Create a container part with child elements
    part = ContainerPart(
        visible_if=Script(content="$document.FRW060.Dialog.Variable1.valueOf()==1"),
        validation=Script(content="$document.FRW060.Dialog.Variable2.valueOf()>0"),
        children=[
            ChildElement(
                type="Par",
                content={
                    "Text": "Example paragraph",
                    "Style": {
                        "FontSize": "12pt",
                        "FontFamily": "Arial"
                    }
                }
            ),
            ChildElement(
                type="Container",
                content={
                    "Style": {
                        "BackgroundColor": "#FFFFFF"
                    }
                }
            )
        ]
    )
    
    # Generate XML
    xml = create_container_part_xml(part)
    logger.info("Generated container part XML:")
    logger.info(xml)

if __name__ == "__main__":
    main() 