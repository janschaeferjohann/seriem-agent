"""
Data model XML generation module for templify.
Handles generation of XML for complex node structures in the datamodel.
"""

import logging
from dataclasses import dataclass
from typing import List, Optional, Union, Dict, Tuple
from enum import Enum
from .datanode import (
    create_normal_node_xml,
    create_reference_node_xml,
    create_hierarchy_node_xml,
    get_data_type
)
from templify.utils.logger_setup import setup_logger

# Initialize logger
logger = setup_logger(__name__, log_level=logging.INFO)

class NodeType(Enum):
    """Types of nodes that can be created"""
    NORMAL = "normal"
    REFERENCE = "reference"
    HIERARCHY = "hierarchy"

@dataclass
class NodeConfig:
    """Configuration for a single node"""
    name: str
    node_type: NodeType
    data_type: Optional[str] = None  # For normal nodes
    ref_path: Optional[str] = None   # For reference nodes
    script_description: Optional[str] = None  # Description of what the script should do
    script_function: Optional[str] = None    # The actual script function
    validation_label: Optional[str] = None
    hierarchical: str = "FLAT"
    multiple: str = "false"
    searchable: str = "false"
    use_cdata: bool = False
    use_current_date: bool = False  # Whether to use current date for date fields
    is_required: bool = False  # Whether the field is required (from Pflichtfeld)
    max_length: int = 0  # Maximum character length (from "mit X Zeichen")
    validation_values: List[Dict[str, str]] = None  # List of enumerated values for dropdowns
    dialog_field: str = ""  # Dialog field type (e.g., "COMBOBOX")
    children: List['NodeConfig'] = None  # For hierarchy nodes

def collect_script_descriptions(config: NodeConfig) -> Dict[str, str]:
    """
    Collect all script descriptions from the node configuration.
    
    Args:
        config (NodeConfig): The node configuration to process
        
    Returns:
        Dict[str, str]: Dictionary mapping node names to their script descriptions
    """
    descriptions = {}
    
    # Add description for current node if it has one
    if config.script_description:
        descriptions[config.name] = config.script_description
    
    # Process children if this is a hierarchy node
    if config.node_type == NodeType.HIERARCHY and config.children:
        for child in config.children:
            descriptions.update(collect_script_descriptions(child))
    
    return descriptions

def replace_script_descriptions(config: NodeConfig, script_functions: Dict[str, str]) -> NodeConfig:
    """
    Replace script descriptions with actual script functions.
    
    Args:
        config (NodeConfig): The node configuration to update
        script_functions (Dict[str, str]): Dictionary mapping node names to their script functions
        
    Returns:
        NodeConfig: Updated node configuration with script functions
    """
    # Create a copy of the config to avoid modifying the original
    updated_config = NodeConfig(
        name=config.name,
        node_type=config.node_type,
        data_type=config.data_type,
        ref_path=config.ref_path,
        script_description=config.script_description,
        script_function=script_functions.get(config.name, config.script_function),
        validation_label=config.validation_label,
        hierarchical=config.hierarchical,
        multiple=config.multiple,
        searchable=config.searchable,
        use_cdata=config.use_cdata,
        use_current_date=config.use_current_date,
        is_required=config.is_required,
        max_length=config.max_length,
        validation_values=config.validation_values,
        dialog_field=config.dialog_field,
        children=None
    )
    
    # Process children if this is a hierarchy node
    if config.node_type == NodeType.HIERARCHY and config.children:
        updated_config.children = [
            replace_script_descriptions(child, script_functions)
            for child in config.children
        ]
    
    return updated_config

def process_scripts(config: NodeConfig, template_name: str, variant_number: str = "0001") -> NodeConfig:
    """
    Process all scripts in the node configuration by generating and replacing them.
    
    Args:
        config (NodeConfig): The node configuration to process
        template_name (str): The template name (e.g., 'FRW060')
        variant_number (str): The variant number (e.g., '0001')
        
    Returns:
        NodeConfig: Updated node configuration with generated scripts
    """
    from templify.generator.script import generate_scripts
    
    # Collect all script descriptions
    script_descriptions = collect_script_descriptions(config)
    
    if not script_descriptions:
        logger.info("No scripts to generate")
        return config
    
    # Generate scripts for all descriptions at once
    generated_scripts = generate_scripts(
        script_descriptions,
        template_name,
        variant_number
    )
    
    if not generated_scripts:
        logger.warning("No scripts were generated")
        return config
    
    # Replace descriptions with generated scripts
    return replace_script_descriptions(config, generated_scripts)

def build_node(config: NodeConfig) -> str:
    """
    Build a single node based on its configuration.
    This is the main entry point for node creation.
    
    Args:
        config (NodeConfig): Configuration for the node to build
        
    Returns:
        str: XML string representing the node and its children
    """
    # Use script_function if available, otherwise use script_description
    script = config.script_function if config.script_function else config.script_description
    
    if config.node_type == NodeType.NORMAL:
        return create_normal_node_xml(
            name=config.name,
            data_type=config.data_type,
            script=script,
            validation_label=config.validation_label,
            hierarchical=config.hierarchical,
            multiple=config.multiple,
            searchable=config.searchable,
            use_cdata=config.use_cdata,
            use_current_date=config.use_current_date,
            is_required=config.is_required,
            max_length=config.max_length,
            dialog_field=config.dialog_field,
            validation_values=config.validation_values
        )
    elif config.node_type == NodeType.REFERENCE:
        return create_reference_node_xml(
            name=config.name,
            ref_path=config.ref_path,
            multiple=config.multiple
        )
    elif config.node_type == NodeType.HIERARCHY:
        child_nodes = [build_node(child) for child in config.children]
        return create_hierarchy_node_xml(
            name=config.name,
            child_nodes_xml=child_nodes,
            multiple=config.multiple
        )

def create_variable_section(name: str, variables: List[dict], template_name: str, variant_number: str = "0001") -> NodeConfig:
    """
    Create a hierarchy node containing variable nodes.
    
    Args:
        name (str): Name of the section
        variables (List[dict]): List of variable configurations
        template_name (str): The template name (e.g., 'FRW060')
        variant_number (str): The variant number (e.g., '0001')
        
    Returns:
        NodeConfig: Configuration for a hierarchy node containing the variables
    """
    children = []
    for var in variables:
        # Get data type from field_type if available, otherwise use data_type
        field_type = var.get('field_type', '')
        data_type = var.get('data_type', '')
        
        # If we have a field_type, use get_data_type to map it
        if field_type:
            data_type = get_data_type(field_type)
        elif not data_type:
            data_type = 'TEXT'  # Default to TEXT if neither is available
            
        # Get script content if available
        script = var.get('script', '')
        script_description = None
        
        # Only set script_description if we have a script
        if script:
            script_description = str(script).strip()
            if not script_description:
                script_description = None
        
        # Check if this is a date field that should use current date
        use_current_date = var.get('use_current_date', False)
        
        # Get validation settings from extracted variable data
        is_required = var.get('is_required', False)
        max_length = var.get('max_length', 0)
        validation_values = var.get('validation_values', [])
        
        # Determine dialog field type based on field_type and validation_values
        dialog_field = ""
        if validation_values:  # If we have enumerated values, it's a combobox
            dialog_field = "COMBOBOX"
        elif field_type and "dropdown" in field_type.lower():  # Dropdown without enumerated values
            dialog_field = "COMBOBOX"
        
        logger.info(f"Creating node for {var['name']} with use_current_date={use_current_date}, field_type={field_type}, data_type={data_type}, is_required={is_required}, max_length={max_length}, dialog_field={dialog_field}, validation_values_count={len(validation_values)}")
            
        children.append(NodeConfig(
            name=var['name'],
            node_type=NodeType.NORMAL,
            data_type=data_type,
            validation_label=var.get('label', ''),
            script_description=script_description,
            script_function=var.get('script_function', ''),
            use_cdata=False,  # Set to False to match original implementation
            use_current_date=use_current_date,
            is_required=is_required,
            max_length=max_length,
            validation_values=validation_values,
            dialog_field=dialog_field
        ))
    
    # Create the section node
    section = NodeConfig(
        name=name,
        node_type=NodeType.HIERARCHY,
        children=children
    )
    
    # Process scripts for all nodes in the section
    return process_scripts(section, template_name, variant_number)

def create_reference_section(name: str, ref_path: str) -> NodeConfig:
    """
    Create a reference node section.
    
    Args:
        name (str): Name of the reference node
        ref_path (str): Path to the referenced datamodel
        
    Returns:
        NodeConfig: Configuration for a reference node
    """
    return NodeConfig(
        name=name,
        node_type=NodeType.REFERENCE,
        ref_path=ref_path
    )

def wrap_datamodel_xml(nodes_xml: str) -> str:
    """
    Wrap the nodes XML with proper XML declaration and DataModel tags.
    
    Args:
        nodes_xml (str): The XML string containing the nodes
        
    Returns:
        str: Complete XML document with proper wrapping
    """
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<DataModel>
{nodes_xml}
</DataModel>'''

# IMPROVE: Saving files is handled in the core module
def save_datamodel_xml(xml: str, output_path: str) -> None:
    """
    Save the generated XML to a file.
    
    Args:
        xml (str): The XML string to save
        output_path (str): Path where to save the file
    """
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(xml)

def main():
    """Example usage of the XML generation functions."""
    # Create a structure with a reference node and variable section
    structure = NodeConfig(
        name="Root",
        node_type=NodeType.HIERARCHY,
        children=[
            # Reference section
            create_reference_section(
                "Model1",
                "\\path\\to\\model1.datamodel"
            ),
            # Variable section
            create_variable_section("Section1", [
                {
                    "name": "Variable1",
                    "field_type": "Checkbox",
                    "label": "Some Label",
                    "script_description": "Return 'freiwillig' if Dialog-Variable1 is 'Ja', otherwise return empty string"
                },
                {
                    "name": "Variable2",
                    "field_type": "Freitext",
                    "label": "Another Label",
                    "script_description": "Process the input text and return formatted result"
                }
            ], "FRW060"),
            # Nested hierarchy
            NodeConfig(
                name="Section2",
                node_type=NodeType.HIERARCHY,
                children=[
                    create_reference_section(
                        "Model2",
                        "\\path\\to\\model2.datamodel"
                    ),
                    NodeConfig(
                        name="Variable3",
                        node_type=NodeType.NORMAL,
                        data_type="BOOLEAN",
                        validation_label="Nested Label",
                        script_description="Check if the value is valid and return appropriate result"
                    )
                ]
            )
        ]
    )
    
    # Step 1: Collect script descriptions
    script_descriptions = collect_script_descriptions(structure)
    
    # Step 2: Generate script functions (this would be done by another module)
    script_functions = {
        "Variable1": "//if ($Dialog-Variable1 = Ja) then return 'freiwillig' else return ''",
        "Variable2": "// Process input text\nreturn $input.toUpperCase()",
        "Variable3": "// Validate boolean value\nreturn $value ? 'true' : 'false'"
    }
    
    # Step 3: Replace descriptions with functions
    updated_structure = replace_script_descriptions(structure, script_functions)
    
    # Step 4: Generate final XML
    nodes_xml = build_node(updated_structure)
    complete_xml = wrap_datamodel_xml(nodes_xml)

if __name__ == "__main__":
    main()
