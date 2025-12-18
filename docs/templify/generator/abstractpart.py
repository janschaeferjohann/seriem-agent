"""
Module for generating AbstractPart XML elements.
Handles creation of abstract part structures with visibility conditions and validation.
"""

from dataclasses import dataclass, field
from typing import List, Optional
from enum import Enum
from templify.utils.logger_setup import setup_logger
import logging

# Initialize logger
logger = setup_logger(__name__, log_level=logging.INFO)

@dataclass
class Script:
    """Represents a script element with CDATA content"""
    content: str

@dataclass
class AbstractPart:
    """Represents an abstract part element with visibility and validation conditions"""
    visible_if: Optional[Script] = None
    validation: Optional[Script] = None

def create_script_xml(script: Script) -> str:
    """Generate XML for a script element with CDATA content"""
    if not script:
        return ""
    return f'<![CDATA[{script.content}]]>'

def create_abstract_part_xml(part: AbstractPart) -> str:
    """Generate XML for an abstract part element"""
    elements = []
    
    if part.visible_if:
        elements.append(f'''<VisibleIf>
    {create_script_xml(part.visible_if)}
</VisibleIf>''')
        
    if part.validation:
        elements.append(f'''<Validation>
    {create_script_xml(part.validation)}
</Validation>''')
        
    if not elements:
        return "<AbstractPart/>"
        
    return f'''<AbstractPart>
    {"".join(elements)}
</AbstractPart>'''

def create_abstract_parts_xml(parts: List[AbstractPart]) -> str:
    """Generate XML for multiple abstract parts"""
    return "\n".join(create_abstract_part_xml(part) for part in parts)

def main():
    """Example usage of the abstract part generation functions."""
    # Create an abstract part with visibility condition
    part = AbstractPart(
        visible_if=Script(content="$document.FRW060.Dialog.Variable1.valueOf()==1"),
        validation=Script(content="$document.FRW060.Dialog.Variable2.valueOf()>0")
    )
    
    # Generate XML
    xml = create_abstract_part_xml(part)
    logger.info("Generated abstract part XML:")
    logger.info(xml)

if __name__ == "__main__":
    main() 