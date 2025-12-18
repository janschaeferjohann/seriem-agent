"""
Parameter definition generation module for templify.
"""

from typing import List, Dict, Optional, Any
from templify.utils.logger_setup import setup_logger
from templify.parser.get_data import get_relative_project_path


# Initialize logger
logger = setup_logger(__name__)

def create_paramdef(
    name: str, 
    ref: str, 
    data_source_name: Optional[str] = None,
    data_mapping_ref: Optional[str] = None,
    provided: Optional[bool] = None,
    description: str = "",
    input_prefix: Optional[str] = None,
    input_suffix: Optional[str] = None,
    output_prefix: Optional[str] = None,
    output_suffix: Optional[str] = None,
    **additional_attrs: Any
) -> str:
    """
    Creates a single ParamDef XML element with required and optional attributes.
    
    Args:
        name: Name of the parameter (required)
        ref: Reference path to the datamodel (required)
        data_source_name: Name of the data source (optional)
        data_mapping_ref: Reference to the data mapping file (optional)
        provided: Whether the parameter is provided (optional)
        description: Description of the parameter (optional)
        input_prefix: Prefix for input (optional)
        input_suffix: Suffix for input (optional)
        output_prefix: Prefix for output (optional)
        output_suffix: Suffix for output (optional)
        additional_attrs: Any additional attributes to include
        
    Returns:
        str: XML representation of the ParamDef element
        
    Examples:
        >>> create_paramdef("Konstanten", "\\_T_BW_Global\\Daten\\Konstanten.datamodel")
        '<ParamDef name="Konstanten" ref="\\_T_BW_Global\\Daten\\Konstanten.datamodel">
           <Description></Description>
         </ParamDef>'
        
        >>> create_paramdef("FRW110", "\\T_BW_PKM_13_24_KW\\FRW110\\Daten\\FRW110.datamodel", 
        ...                 data_source_name="Auftragssteuerung", 
        ...                 data_mapping_ref="FRW110\\Daten\\FRW110.mapping")
        '<ParamDef name="FRW110" ref="\\T_BW_PKM_13_24_KW\\FRW110\\Daten\\FRW110.datamodel" 
           dataSourceName="Auftragssteuerung" dataMappingRef="FRW110\\Daten\\FRW110.mapping">
           <Description></Description>
           <Input text-prefix="" text-suffix=""></Input>
           <Output text-prefix="" text-suffix=""></Output>
         </ParamDef>'
    """
    # Validate required parameters
    if not name:
        raise ValueError("Parameter name is required")
    if not ref:
        raise ValueError("Parameter ref is required")
    
    # Build attributes dictionary
    attrs = {
        'name': name,
        'ref': ref  # Assume ref is already in the correct format
    }
    
    # Add optional standard attributes if provided
    if data_source_name:
        attrs['dataSourceName'] = data_source_name
    if data_mapping_ref is not None:  # Allow empty strings
        attrs['dataMappingRef'] = data_mapping_ref  # Assume data_mapping_ref is already in the correct format
    if provided is not None:
        attrs['provided'] = str(provided).lower()
    
    # Handle special attribute mappings from additional_attrs
    mapped_attrs = {}
    for key, value in additional_attrs.items():
        # Map snake_case to camelCase for XML attributes
        if key == 'data_source_definition_ref' and value is not None:  # Allow empty strings
            mapped_attrs['dataSourceDefinitionRef'] = value
        elif key == 'constant_data_ref' and value is not None:  # Allow empty strings
            mapped_attrs['constantDataRef'] = value
        elif value is not None:  # Only add non-None values
            mapped_attrs[key] = value
    
    # Add any additional attributes
    attrs.update(mapped_attrs)
    
    # Format all attributes for XML
    formatted_attrs = [f'{key}="{value}"' for key, value in attrs.items()]
    attr_string = " ".join(formatted_attrs)
    
    # Build child elements
    description_element = f'<Description>{description}</Description>'
    
    # Add Input and Output elements if any input/output attributes were provided
    child_elements = [description_element]
    
    if any(x is not None for x in [input_prefix, input_suffix, output_prefix, output_suffix]):
        # Add Input element if needed
        input_attrs = []
        if input_prefix is not None:
            input_attrs.append(f'text-prefix="{input_prefix}"')
        if input_suffix is not None:
            input_attrs.append(f'text-suffix="{input_suffix}"')
        
        input_attr_string = " ".join(input_attrs) if input_attrs else 'text-prefix="" text-suffix=""'
        child_elements.append(f'<Input {input_attr_string}></Input>')
        
        # Add Output element if needed
        output_attrs = []
        if output_prefix is not None:
            output_attrs.append(f'text-prefix="{output_prefix}"')
        if output_suffix is not None:
            output_attrs.append(f'text-suffix="{output_suffix}"')
            
        output_attr_string = " ".join(output_attrs) if output_attrs else 'text-prefix="" text-suffix=""'
        child_elements.append(f'<Output {output_attr_string}></Output>')
    
    # Build the final XML
    indented_children = "\n   ".join(child_elements)
    return f'<ParamDef {attr_string}>\n   {indented_children}\n</ParamDef>'

def create_datanodedef(
    name: str,
    ref: str,
    description: str = "",
    **additional_attrs: Any
) -> str:
    """
    Creates a DataNodeDef XML element.
    
    Args:
        name: Name of the data node (required)
        ref: Reference path to the datamodel (required)
        description: Description of the data node (optional)
        additional_attrs: Any additional attributes to include
        
    Returns:
        str: XML representation of the DataNodeDef element
        
    Example:
        >>> create_datanodedef("omaui", "\\\\__T_Common\\Daten\\OscareAdapterUI.datamodel")
        '<DataNodeDef name="omaui" ref="\\\\__T_Common\\Daten\\OscareAdapterUI.datamodel">
           <Description></Description>
         </DataNodeDef>'
    """
    # Validate required parameters
    if not name:
        raise ValueError("Parameter name is required")
    if not ref:
        raise ValueError("Parameter ref is required")
    
    # Build attributes dictionary
    attrs = {
        'name': name,
        'ref': ref  # Assume ref is already in the correct format
    }
    
    # Add any additional attributes
    attrs.update(additional_attrs)
    
    # Format all attributes for XML
    formatted_attrs = [f'{key}="{value}"' for key, value in attrs.items()]
    attr_string = " ".join(formatted_attrs)
    
    # Build description element
    description_element = f'<Description>{description}</Description>'
    
    # Build the final XML
    return f'<DataNodeDef {attr_string}>\n   {description_element}\n</DataNodeDef>'

def create_datadefinition(
    paramdefs: List[Dict[str, Any]], 
    datanodedefs: Optional[List[Dict[str, Any]]] = None
) -> str:
    """
    Create a complete DataDefinition XML structure using ParamDef and DataNodeDef elements.
    
    Args:
        paramdefs: List of parameter definition dictionaries with keys corresponding 
                   to create_paramdef parameters.
        datanodedefs: Optional list of data node definition dictionaries with keys
                     corresponding to create_datanodedef parameters.
    
    Returns:
        str: Complete DataDefinition XML string.
        
    Example:
        >>> create_datadefinition(
        ...     [
        ...         {
        ...             "name": "Auftragssteuerung",
        ...             "ref": "\\_T_BW_Global\\Daten\\FW_Auftragssteuerung.datamodel",
        ...             "data_mapping_ref": "\\_T_BW_Global\\Daten\\FW_Auftragssteuerung.mapping"
        ...         }
        ...     ],
        ...     [
        ...         {
        ...             "name": "omaui",
        ...             "ref": "\\__T_Common\\Daten\\OscareAdapterUI.datamodel"
        ...         }
        ...     ]
        ... )
        '<DataDefinition>
          <ParamDef name="Auftragssteuerung" ref="\\_T_BW_Global\\Daten\\FW_Auftragssteuerung.datamodel" dataMappingRef="\\_T_BW_Global\\Daten\\FW_Auftragssteuerung.mapping">
             <Description></Description>
          </ParamDef>
          <DataNodeDef name="omaui" ref="\\__T_Common\\Daten\\OscareAdapterUI.datamodel">
             <Description></Description>
          </DataNodeDef>
        </DataDefinition>'
    """
    # Generate ParamDef elements
    paramdef_elements = []
    for pd in paramdefs:
        # Create a copy of the dict to avoid modifying the original
        pd_copy = pd.copy()
        paramdef_elements.append(create_paramdef(**pd_copy))
    
    # Generate DataNodeDef elements if provided
    datanodedef_elements = []
    if datanodedefs:
        for dn in datanodedefs:
            # Create a copy of the dict to avoid modifying the original
            dn_copy = dn.copy()
            datanodedef_elements.append(create_datanodedef(**dn_copy))
    
    # Combine all elements with proper indentation
    elements = []
    
    # Add ParamDef elements
    if paramdef_elements:
        elements.extend(paramdef_elements)
    
    # Add DataNodeDef elements
    if datanodedef_elements:
        elements.extend(datanodedef_elements)
    
    # Join all elements with newlines and indentation
    elements_xml = "\n  ".join(elements)
    
    # Wrap in DataDefinition tags
    return f'<DataDefinition>\n  {elements_xml}\n</DataDefinition>'

def create_param(name: str, value: Optional[str] = None, param_type: Optional[str] = None, **additional_attrs: Any) -> str:
    """
    Creates a single Param XML element.
    
    Args:
        name: Name of the parameter (required)
        value: Custom value for the parameter (defaults to "${name}")
        param_type: Type attribute (e.g., "datanoderef")
        additional_attrs: Any additional attributes to include
        
    Returns:
        str: Param XML element
        
    Examples:
        >>> create_param("Auftragssteuerung")
        '<Param name="Auftragssteuerung">$Auftragssteuerung</Param>'
        
        >>> create_param("Auftragssteuerung", param_type="datanoderef")
        '<Param name="Auftragssteuerung" type="datanoderef">$Auftragssteuerung</Param>'
        
        >>> create_param("Betreff1", value='"Custom Subject"')
        '<Param name="Betreff1">"Custom Subject"</Param>'
    """
    # Validate required parameters
    if not name:
        raise ValueError("Parameter name is required")
    
    # Build attributes dictionary
    attrs = {'name': name}
    
    # Add type if provided
    if param_type:
        attrs['type'] = param_type
    
    # Add any additional attributes
    attrs.update(additional_attrs)
    
    # Format all attributes for XML
    formatted_attrs = [f'{key}="{attr_value}"' for key, attr_value in attrs.items()]
    attr_string = " ".join(formatted_attrs)
    
    # Determine value
    param_value = value if value is not None else f'${name}'
    
    return f'<Param {attr_string}>{param_value}</Param>'

def main():
    """Example usage of the parameter definition generation functions."""
    paramdefs = [
        {
            'name': 'Auftragssteuerung',
            'ref': '\\\\_T_BW_Global\\Daten\\FW_Auftragssteuerung.datamodel',
            'data_mapping_ref': '\\\\_T_BW_Global\\Daten\\FW_Auftragssteuerung.mapping'
        },
        {
            'name': 'FW_Daten',
            'ref': '\\\\__T_Common\\Daten\\FW_Daten.datamodel',
            'data_source_name': 'Auftragssteuerung',
            'data_mapping_ref': '\\\\__T_Common\\Daten\\FW_Daten.mapping'
        },
        {
            'name': 'FRWT100',
            'ref': '\\T_BW_PKM_13_24_KW\\FRWT100\\Daten\\FRWT100.datamodel',
            'data_source_name': 'Auftragssteuerung',
            'data_mapping_ref': '\\T_BW_PKM_13_24_KW\\FRWT100\\Daten\\FRWT100.mapping'
        }
    ]
    
    datanode_defs = [
        {
            'name': 'omaui',
            'ref': '\\\\__T_Common\\Daten\\OscareAdapterUI.datamodel'
        }
    ]
    
    datadef_xml = create_datadefinition(paramdefs, datanode_defs)
    print("Generated DataDefinition XML:")
    print(datadef_xml)
    
    param_xml = create_param('Auftragssteuerung')
    print("\nGenerated Param XML:")
    print(param_xml)

if __name__ == "__main__":
    main() 