"""
Data node XML generation module for templify.
Handles generation of XML for different types of nodes in the datamodel.
"""

from enum import Enum
from typing import List, Optional
from templify.utils.logger_setup import setup_logger
import logging

# Initialize logger
logger = setup_logger(__name__, log_level=logging.INFO)

class DataType(Enum):
    TEXT = "TEXT"
    BOOLEAN = "BOOLEAN"
    NUMBER = "NUMBER"
    DATE = "DATE"
    DATETIME = "DATETIME"  # Added for compatibility with old implementation

def get_data_type(field_type: str) -> str:
    """
    Determine the data-type based on the field type.
    
    Args:
        field_type (str): Description of field type from the Steuerung file
        
    Returns:
        str: The corresponding XML data-type
    """
    field_type = field_type.lower() if field_type else ""
    
    if "checkbox" in field_type:
        return DataType.BOOLEAN.value
    elif "datum" in field_type:
        return DataType.DATETIME.value  # Using DATETIME instead of DATE which causes errors
    elif "dropdown" in field_type:
        return DataType.TEXT.value  # Dropdown fields are stored as text
    elif "freitext" in field_type:
        return DataType.TEXT.value
    elif "zahl" in field_type or "numeric" in field_type:
        return DataType.NUMBER.value
    else:
        return DataType.TEXT.value  # Default to TEXT for unknown types

def create_validation_xml(
    label: str,
    allow_empty_value: str = "true",
    dialog_field: str = "",
    operator: str = "ANY",
    validation_type: str = "ANY_VALUE",
    field_type: str = "",
    values: List[dict] = None,
    max_length: int = 0
) -> str:
    """
    Generate XML for validation settings.
    
    Args:
        label (str): The validation label
        allow_empty_value (str): Whether empty values are allowed
        dialog_field (str): The dialog field name
        operator (str): The validation operator
        validation_type (str): The type of validation
        field_type (str): The type of field (e.g., "DATETIME", "TEXT", "NUMBER")
        values (List[dict]): List of value dictionaries for combobox, each with:
            - content: The value content
            - description: The display text
            - valId: The value ID
        max_length (int): Maximum character length (0 if not specified)
            
    Returns:
        str: XML string for validation settings
    """
    # Get error message based on field type
    error_message = ""
    if values and dialog_field == "COMBOBOX":
        error_message = "Bitte einen Wert aus der Liste auswählen"
    elif field_type == "DATETIME":
        error_message = "Bitte Datum eingeben!"
    elif field_type == "TEXT":
        error_message = "Bitte ausfüllen"
    elif field_type == "NUMBER":
        error_message = "Bitte eine Zahl eingeben"
    elif field_type == "DROPDOWN" or dialog_field == "COMBOBOX":
        error_message = "Bitte auswählen!"
    
    # Add error message if we have one
    error_xml = f'<ErrorMessage>{error_message}</ErrorMessage>' if error_message else ""
    
    # Determine validation type and operator based on max_length and values
    if max_length > 0:
        validation_type = "TEXT_LENGTH"
        operator = "LESS_OR_EQUAL"
    elif values and dialog_field == "COMBOBOX":
        validation_type = "LIST"
        operator = "ANY"
    
    # Generate values XML for combobox or max_length
    values_xml = ""
    if values and dialog_field == "COMBOBOX":
        values_list = []
        for val in values:
            values_list.append(f'''                  <Value content="{val['content']}" description="{val['description']}" valId="{val['valId']}"/>''')
        values_xml = f'''               <Values>
{chr(10).join(values_list)}
               </Values>'''
    elif max_length > 0:
        # Create TEXT_LENGTH validation with max_length value
        values_xml = f'''               <Values>
                  <Value content="{max_length}"/>
                  <Value/>
               </Values>'''
    else:
        values_xml = "<Values/>"
    
    return f'''<Validation allow-empty-value="{allow_empty_value}"
                        dialog-field="{dialog_field}"
                        label="{label}"
                        operator="{operator}"
                        validation-type="{validation_type}">
               {values_xml}
               {error_xml}
            </Validation>'''

def create_format_xml(field_type: str) -> str:
    """
    Generate XML for format settings based on field type.
    
    Args:
        field_type (str): The type of field (e.g., "DATETIME", "TEXT", "NUMBER")
        
    Returns:
        str: XML string for format settings
    """
    if field_type == "DATETIME":
        return '''<Format>
               <Output date-format="dd.MM.yyyy HH:mm:ss"
                       date-style="2"
                       date-type="DATE"
                       use-current-locale="true"/>
            </Format>'''
    elif field_type == "NUMBER":
        return '''<Format>
               <Output type="NUMBER"/>
            </Format>'''
    return ""

def create_settings_xml(data_type: str, script: Optional[str] = None, use_cdata: bool = False, use_current_date: bool = False) -> str:
    """
    Create the settings XML section for a node.
    
    Args:
        data_type (str): The data type of the node
        script (Optional[str]): Optional script content
        use_cdata (bool): Whether to wrap script in CDATA
        use_current_date (bool): Whether to use current date for date fields
        
    Returns:
        str: XML string for the settings section
    """
    
    if use_cdata and script:
        return f'''<Settings>
            <Script><![CDATA[{script}]]></Script>
        </Settings>'''
    elif use_current_date and data_type == "DATETIME":
        return '''<Settings>
            <Script>new Date();</Script>
        </Settings>'''
    elif script and script.strip():
        return f'''<Settings>
            <Script>{script}</Script>
        </Settings>'''
    else:
        return "<Settings/>"

def create_normal_node_xml(
    name: str,
    data_type: str,
    script: str = "",
    validation_label: str = "",
    hierarchical: str = "FLAT",
    multiple: str = "false",
    searchable: str = "false",
    use_cdata: bool = False,
    dialog_field: str = "",
    validation_values: List[dict] = None,
    use_current_date: bool = False,
    is_required: bool = False,
    max_length: int = 0
) -> str:
    """
    Generate XML for a normal node.
    
    Args:
        name (str): The node name
        data_type (str): The data type (TEXT, BOOLEAN, etc.)
        script (str): The script content
        validation_label (str): The validation label
        hierarchical (str): The hierarchical setting
        multiple (str): Whether multiple values are allowed
        searchable (str): Whether the node is searchable
        use_cdata (bool): Whether to wrap the script in CDATA tags
        dialog_field (str): The dialog field type (e.g., "COMBOBOX")
        validation_values (List[dict]): List of value dictionaries for combobox validation
        use_current_date (bool): Whether to use current date for date fields
        is_required (bool): Whether the field is required (affects allow_empty_value)
        max_length (int): Maximum character length (0 if not specified)
        
    Returns:
        str: XML string for a normal node
    """
    # Convert is_required to allow_empty_value (inverse logic)
    allow_empty_value = "false" if is_required else "true"
    
    # Create validation XML if we have a label, or if field is required, or if max_length is specified, or if we have validation_values
    should_create_validation = validation_label or is_required or max_length > 0 or (validation_values and len(validation_values) > 0)
    
    validation_xml = create_validation_xml(
        validation_label or "",  # Use empty string if no label
        allow_empty_value=allow_empty_value,
        field_type=data_type,
        dialog_field=dialog_field,
        values=validation_values,
        max_length=max_length
    ) if should_create_validation else ""
    
    settings_xml = create_settings_xml(data_type, script, use_cdata, use_current_date)
    
    return f'''<Node data-type="{data_type}"
                            hierarchical="{hierarchical}"
                            multiple="{multiple}"
                            name="{name}"
                            searchable="{searchable}">
                            {validation_xml}
                            {settings_xml}
                        </Node>'''

def create_reference_node_xml(
    name: str,
    ref_path: str,
    multiple: str = "false"
) -> str:
    """
    Generate XML for a reference node.
    
    Args:
        name (str): The node name
        ref_path (str): The path to the referenced datamodel
        multiple (str): Whether multiple values are allowed
        
    Returns:
        str: XML string for a reference node
    """
    settings_xml = create_settings_xml(data_type="TEXT")
    
    return f'''<Node multiple="{multiple}"
         name="{name}"
         ref="{ref_path}">
      {settings_xml}
   </Node>'''

def create_hierarchy_node_xml(
    name: str,
    child_nodes_xml: List[str],
    multiple: str = "false"
) -> str:
    """
    Generate XML for a hierarchy node containing other nodes.
    
    Args:
        name (str): The node name
        child_nodes_xml (List[str]): List of XML strings for child nodes
        multiple (str): Whether multiple values are allowed
        
    Returns:
        str: XML string for a hierarchy node
    """
    settings_xml = create_settings_xml(data_type="TEXT")
    child_nodes = "\n".join(child_nodes_xml)
    
    return f'''<Node multiple="{multiple}" name="{name}">
         {settings_xml}
         {child_nodes}
   </Node>'''

def main():
    """Example usage of the XML generation functions."""
    # Example 1: Normal node with field type mapping
    field_type = "Checkbox"
    data_type = get_data_type(field_type)
    normal_node = create_normal_node_xml(
        name="Variable1_FM",
        data_type=data_type,
        script="//if ($Dialog-Variable1 = Ja) then return 'freiwillig' else return ''",
        validation_label="Kosten und Gebühren"
    )


    # Example 2: Reference node
    ref_node = create_reference_node_xml(
        name="WRK5",
        ref_path="\\T_BW_PKM_13_24_KW\\Daten\\CMPR_W5_22_GAA_T22B.datamodel"
    )


    # Example 3: Hierarchy node with CDATA script
    child_node = create_normal_node_xml(
        name="Dialog_Variable1",
        data_type="BOOLEAN",
        script="// Auto-generated script for Dialog_Variable1",
        validation_label="Freiwilliges Mitglied",
        use_cdata=True
    )
    hierarchy_node = create_hierarchy_node_xml(
        name="_0001",
        child_nodes_xml=[child_node]
    )


if __name__ == "__main__":
    main()