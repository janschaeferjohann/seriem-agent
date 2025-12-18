"""
Model generation module for templify.
Handles generation of model XML content with data definitions, UI contributions, and content parts.
"""

import sys
import logging
from typing import Optional, Dict, List, Any

from templify.utils.logger_setup import setup_logger
from templify.generator.paramdef import create_datadefinition
from templify.generator.uicontribution import create_ui_contributions
from templify.generator.content import create_content

# Initialize logger
logger = setup_logger(__name__)

def create_datadefinition_xml(
    paramdefs: List[Dict[str, Any]], 
    datanodedefs: Optional[List[Dict[str, Any]]] = None
) -> str:
    """
    Create the DataDefinition XML part of the model using the parameter definition functions.
    
    Args:
        paramdefs: List of parameter definition dictionaries, each containing:
                  - name: Name of the parameter (required)
                  - ref: Reference path to the datamodel (required)
                  - data_source_name: Name of the data source (optional)
                  - data_mapping_ref: Reference to data mapping file (optional)
                  - provided: Whether parameter is provided (optional)
                  - description: Description text (optional)
                  - input_prefix/suffix: Input formatting (optional)
                  - output_prefix/suffix: Output formatting (optional)
                  
        datanodedefs: Optional list of data node definition dictionaries, each containing:
                     - name: Name of the data node (required)
                     - ref: Reference path to the datamodel (required)
                     - description: Description text (optional)
        
    Returns:
        str: The DataDefinition XML content
    """
    logger.debug(f"Creating DataDefinition XML with {len(paramdefs)} params and {len(datanodedefs) if datanodedefs else 0} datanodes")
    
    # Directly use the create_datadefinition function from paramdef module
    return create_datadefinition(paramdefs, datanodedefs)

def create_uicontributions_xml(
    ui_contributions: List[Dict[str, Any]],
    template_name: str,
    variant_number: Optional[str] = None
) -> str:
    """
    Create the UI Contributions XML part of the model using the create_ui_contributions function.
    
    Args:
        ui_contributions: List of UI contribution dictionaries, each containing:
                         - feldgruppe: Group name (optional, defaults to 'Allgemein')
                         - dialog_variable: Variable name (required)
                         - condition: Visibility condition (optional)
                         - label: Display label (required)
        template_name: Name of the template
        variant_number: Optional variant number
        
    Returns:
        str: The UI Contributions XML content
    """
    logger.debug(f"Creating UI Contributions XML for {template_name} with {len(ui_contributions)} contributions")
    
    # Ensure variant_number is a string if provided
    variant_str = str(variant_number) if variant_number is not None else "0001"
    
    # Directly use the create_ui_contributions function
    return create_ui_contributions(ui_contributions, template_name, variant_str)

def create_contentpart_xml(
    content_parts: List[Dict[str, Any]],
    template_name: str,
    variant_number: Optional[str] = None
) -> str:
    """
    Create the Content Part XML of the model by using the content generator.
    
    Args:
        content_parts: List of content part dictionaries
        template_name: Name of the template
        variant_number: Optional variant number
        
    Returns:
        str: The Content Part XML content
    """
    logger.debug(f"Creating Content Part XML for {template_name} with {len(content_parts)} parts")
    
    # Call the specialized content creation function
    return create_content(content_parts, template_name, variant_number)

def create_model_xml(
    template_name: str,
    variant_number: Optional[str] = None,
    paramdefs: Optional[List[Dict[str, Any]]] = None,
    datanodedefs: Optional[List[Dict[str, Any]]] = None,
    ui_contributions: Optional[List[Dict[str, Any]]] = None,
    content_parts: Optional[List[Dict[str, Any]]] = None,
    datadef_xml: Optional[str] = None,
    ui_contributions_xml: Optional[str] = None,
    contentpart_xml: Optional[str] = None
) -> str:
    """
    Create the complete model XML by combining data definitions, UI contributions, and content parts.
    
    This function can either:
    1. Generate each part from input data (paramdefs, ui_contributions, content_parts)
    2. Use pre-generated XML strings (datadef_xml, ui_contributions_xml, contentpart_xml)
    3. Any combination of the above
    
    Args:
        template_name: Name of the template (required)
        variant_number: Optional variant number (defaults to "0001")
        
        # For generating component parts:
        paramdefs: Optional list of parameter definitions to create data definitions
        datanodedefs: Optional list of data node definitions to create data definitions
        ui_contributions: Optional list of UI contributions
        content_parts: Optional list of content parts
        
        # For using pre-generated XML:
        datadef_xml: Optional pre-generated DataDefinition XML
        ui_contributions_xml: Optional pre-generated UI Contributions XML
        contentpart_xml: Optional pre-generated Content Part XML
        
    Returns:
        str: The complete model XML content
    """
    logger.info(f"Creating model XML for {template_name}")
    variant_str = str(variant_number) if variant_number is not None else "0001"
    
    # Generate DataDefinition XML if needed
    final_datadef_xml = datadef_xml
    if final_datadef_xml is None and paramdefs:
        final_datadef_xml = create_datadefinition_xml(paramdefs, datanodedefs)
    if final_datadef_xml is None:
        logger.debug("No DataDefinition provided or generated")
        final_datadef_xml = "<!-- No DataDefinition specified -->"
    
    # Generate UI Contributions XML if needed
    final_ui_xml = ui_contributions_xml
    if final_ui_xml is None and ui_contributions:
        final_ui_xml = create_uicontributions_xml(ui_contributions, template_name, variant_str)
    if final_ui_xml is None:
        logger.debug("No UI Contributions provided or generated")
        final_ui_xml = "<!-- No UI Contributions specified -->"
    
    # Generate Content Part XML if needed
    final_content_xml = contentpart_xml
    if final_content_xml is None and content_parts:
        final_content_xml = create_contentpart_xml(content_parts, template_name, variant_str)
    if final_content_xml is None:
        logger.debug("No Content Parts provided or generated")
        final_content_xml = "<!-- No Content Parts specified -->"
    
    # Combine into final model XML
    model_content = f"""<ContainerPart xmlns="urn:kwsoft:mtext:tonic:dom">
{final_datadef_xml}
{final_ui_xml}
{final_content_xml}
</ContainerPart>"""
    
    logger.info(f"Successfully created model XML for {template_name}")
    return model_content

def main(template_name: str) -> bool:
    """
    Main function that demonstrates the model XML generation process.
    
    Args:
        template_name: Name of the template to process
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        logger.info(f"Starting model generation for {template_name}")
        
        # Example parameter definitions for demonstration
        paramdefs = [
            {
                'name': 'Auftragssteuerung',
                'ref': '\\\\_T_BW_Global\\Daten\\FW_Auftragssteuerung.datamodel',
                'data_mapping_ref': '\\\\_T_BW_Global\\Daten\\FW_Auftragssteuerung.mapping'
            },
            {
                'name': template_name,
                'ref': f'\\T_BW_PKM_13_24_KW\\{template_name}\\Daten\\{template_name}.datamodel',
                'data_source_name': 'Auftragssteuerung',
                'data_mapping_ref': f'\\T_BW_PKM_13_24_KW\\{template_name}\\Daten\\{template_name}.mapping'
            }
        ]
        
        # Example datanode definitions for demonstration
        datanodedefs = [
            {
                'name': 'omaui',
                'ref': '\\\\__T_Common\\Daten\\OscareAdapterUI.datamodel'
            }
        ]
        
        # Example UI contributions
        ui_contributions = [
            {
                'feldgruppe': 'Persönliche Daten',
                'dialog_variable': 'Vorname',
                'label': 'Vorname',
                'condition': ''
            },
            {
                'feldgruppe': 'Persönliche Daten',
                'dialog_variable': 'Nachname',
                'label': 'Nachname',
                'condition': ''
            },
            {
                'feldgruppe': 'Adresse',
                'dialog_variable': 'Strasse',
                'label': 'Straße',
                'condition': ''
            }
        ]
        
        # Example content parts
        content_parts = [
            {'type': 'paragraph', 'content': 'Example content'},
            {'type': 'model', 'content': '\\T_BW_Global\\Templates\\Header.model'}
        ]
        
        # Method 1: Use the updated create_model_xml to generate everything
        model_xml = create_model_xml(
            template_name=template_name,
            variant_number="0001",
            paramdefs=paramdefs,
            datanodedefs=datanodedefs,
            ui_contributions=ui_contributions,
            content_parts=content_parts
        )
        
        # Method 2: Generate each part separately and then combine
        # (This is just to demonstrate the alternative approach)
        datadef_xml = create_datadefinition_xml(paramdefs, datanodedefs)
        ui_contributions_xml = create_uicontributions_xml(ui_contributions, template_name, "0001")
        contentpart_xml = create_contentpart_xml(content_parts, template_name, "0001")
        
        model_xml_alt = create_model_xml(
            template_name=template_name,
            variant_number="0001",
            datadef_xml=datadef_xml,
            ui_contributions_xml=ui_contributions_xml,
            contentpart_xml=contentpart_xml
        )
        
        # Log the results
        xml_length = len(model_xml)
        logger.info(f"Successfully generated model XML for {template_name} ({xml_length} bytes)")
        logger.info(f"Model XML: {model_xml}")
        
        # Optionally display a sample or preview
        preview_length = min(100, xml_length)
        logger.debug(f"Model XML preview: {model_xml[:preview_length]}...")
        
        return True
        
    except Exception as e:
        logger.error(f"Error generating model XML for {template_name}: {str(e)}")
        return False

if __name__ == "__main__":
    # Updated for standalone execution with template_name argument
    if len(sys.argv) > 1:
        template_to_run = sys.argv[1]
        logger.info(f"Running directly for template: {template_to_run}")
        if not main(template_to_run):
            sys.exit(1)
    else:
        logger.warning("No template name provided for direct execution. Exiting.")
        sys.exit(1)