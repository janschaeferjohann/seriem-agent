"""
Template generation module for templify.
Handles generation of complete template XML content with RootPart containing
DataDefinition, ModificationRights, and Document sections.
"""

import sys
import logging
from typing import Optional, Dict, List, Any

from templify.utils.logger_setup import setup_logger
from templify.generator.paramdef import create_datadefinition
from templify.generator.modificationrights import create_default_modificationrights, create_modificationrights
from templify.generator.document import create_document

# Initialize logger
logger = setup_logger(__name__)

def create_rootpart(
    template_id: str,
    title: str,
    description: Optional[str] = None,
    content: str = ""
) -> str:
    """
    Create the RootPart XML wrapper element.
    
    Args:
        template_id: ID for the template (e.g., "\\library\\T_BW_PKM_13_24_KW\\FRW025\\Vorlagen\\FRW025.template")
        title: Title of the template (e.g., "FRW025")
        description: Optional description (e.g., "#Aenderung_FM_Auslandsaufenthalt")
        content: Inner XML content to wrap
        
    Returns:
        str: Complete RootPart XML with content
        
    Example:
        >>> create_rootpart(
        ...     "\\library\\T_BW_PKM_13_24_KW\\FRW025\\Vorlagen\\FRW025.template",
        ...     "FRW025",
        ...     "#Aenderung_FM_Auslandsaufenthalt",
        ...     "<DataDefinition></DataDefinition>"
        ... )
    """
    # Build attributes
    attrs = [
        'xmlns="urn:kwsoft:mtext:tonic:dom"',
        f'id="{template_id}"',
        f'title="{title}"'
    ]
    
    if description:
        attrs.append(f'description="{description}"')
    
    attr_string = " ".join(attrs)
    
    if content.strip():
        return f'<RootPart {attr_string}>\n{content}\n</RootPart>'
    else:
        return f'<RootPart {attr_string}></RootPart>'

def create_datadefinition_xml(
    paramdefs: List[Dict[str, Any]], 
    datanodedefs: Optional[List[Dict[str, Any]]] = None
) -> str:
    """
    Create the DataDefinition XML part of the template using the parameter definition functions.
    
    Args:
        paramdefs: List of parameter definition dictionaries, each containing:
                  - name: Name of the parameter (required)
                  - ref: Reference path to the datamodel (required)
                  - data_source_name: Name of the data source (optional)
                  - data_mapping_ref: Reference to data mapping file (optional)
                  - constant_data_ref: Reference to constant data (optional)
                  - data_source_definition_ref: Reference to data source definition (optional)
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
    logger.debug("Creating DataDefinition XML with %d params and %d datanodes", 
                len(paramdefs), len(datanodedefs) if datanodedefs else 0)
    
    # Directly use the create_datadefinition function from paramdef module
    return create_datadefinition(paramdefs, datanodedefs)

def create_modificationrights_xml(
    allowed_rights: Optional[List[Dict[str, Any]]] = None,
    denied_rights: Optional[List[Dict[str, Any]]] = None
) -> str:
    """
    Create the ModificationRights XML part of the template.
    
    Args:
        allowed_rights: Optional list of allowed modification rights. Each dict contains:
                       - role: Role name (required)
                       - operations: Operations string (required)
        denied_rights: Optional list of denied modification rights with same structure
        
    Returns:
        str: The ModificationRights XML content
    """
    logger.debug("Creating ModificationRights XML")
    
    if allowed_rights is None and denied_rights is None:
        # Use default modification rights
        return create_default_modificationrights()
    else:
        # Use provided rights
        return create_modificationrights(allowed_rights or [], denied_rights or [])

def create_document_xml(
    document_id: Optional[str] = None,
    style_config: Optional[Dict[str, Any]] = None,
    document_part_refs: Optional[List[Dict[str, Any]]] = None,
    document_parts: Optional[List[Dict[str, Any]]] = None
) -> str:
    """
    Create the Document XML part of the template using the document generator.
    
    Args:
        document_id: Optional ID attribute for the Document
        style_config: Optional style configuration
        document_part_refs: Optional list of DocumentPartRef configurations
        document_parts: Optional list of DocumentPart configurations
        
    Returns:
        str: The Document XML content
    """
    logger.debug("Creating Document XML")
    
    # Directly use the create_document function from document module
    return create_document(
        document_id=document_id,
        style_config=style_config,
        document_part_refs=document_part_refs,
        document_parts=document_parts
    )

def create_template_xml(
    template_id: str,
    title: str,
    description: Optional[str] = None,
    
    # For generating component parts:
    paramdefs: Optional[List[Dict[str, Any]]] = None,
    datanodedefs: Optional[List[Dict[str, Any]]] = None,
    allowed_rights: Optional[List[Dict[str, Any]]] = None,
    denied_rights: Optional[List[Dict[str, Any]]] = None,
    document_config: Optional[Dict[str, Any]] = None,
    
    # For using pre-generated XML:
    datadef_xml: Optional[str] = None,
    modificationrights_xml: Optional[str] = None,
    document_xml: Optional[str] = None
) -> str:
    """
    Create the complete template XML by combining all sections within a RootPart.
    
    This function can either:
    1. Generate each part from input data (paramdefs, document_config, etc.)
    2. Use pre-generated XML strings (datadef_xml, modificationrights_xml, document_xml)
    3. Any combination of the above
    
    Args:
        template_id: ID for the template (required)
        title: Title of the template (required)
        description: Optional description
        
        # For generating component parts:
        paramdefs: Optional list of parameter definitions to create DataDefinition
        datanodedefs: Optional list of data node definitions to create DataDefinition
        allowed_rights: Optional list of allowed modification rights
        denied_rights: Optional list of denied modification rights
        document_config: Optional document configuration dict containing:
                        - document_id: Optional document ID
                        - style_config: Optional style configuration
                        - document_part_refs: Optional list of DocumentPartRef configs
                        - document_parts: Optional list of DocumentPart configs
        
        # For using pre-generated XML:
        datadef_xml: Optional pre-generated DataDefinition XML
        modificationrights_xml: Optional pre-generated ModificationRights XML
        document_xml: Optional pre-generated Document XML
        
    Returns:
        str: The complete template XML content
    """
    logger.info("Creating template XML for %s", title)
    
    # Generate DataDefinition XML if needed
    final_datadef_xml = datadef_xml
    if final_datadef_xml is None and paramdefs:
        final_datadef_xml = create_datadefinition_xml(paramdefs, datanodedefs)
    if final_datadef_xml is None:
        logger.debug("No DataDefinition provided or generated")
        final_datadef_xml = "<!-- No DataDefinition specified -->"
    
    # Generate ModificationRights XML if needed
    final_rights_xml = modificationrights_xml
    if final_rights_xml is None:
        final_rights_xml = create_modificationrights_xml(allowed_rights, denied_rights)
    
    # Generate Document XML if needed
    final_document_xml = document_xml
    if final_document_xml is None and document_config:
        final_document_xml = create_document_xml(**document_config)
    if final_document_xml is None:
        logger.debug("No Document provided or generated")
        final_document_xml = "<!-- No Document specified -->"
    
    # Combine all sections
    sections = []
    if final_datadef_xml and final_datadef_xml.strip() and "<!-- No DataDefinition" not in final_datadef_xml:
        sections.append(f" {final_datadef_xml}")
    if final_rights_xml and final_rights_xml.strip():
        sections.append(f" {final_rights_xml}")
    if final_document_xml and final_document_xml.strip() and "<!-- No Document" not in final_document_xml:
        sections.append(f" {final_document_xml}")
    
    content = "\n".join(sections)
    
    # Create the complete template within RootPart
    template_content = create_rootpart(template_id, title, description, content)
    
    logger.info("Successfully created template XML for %s", title)
    return template_content

def main(template_name: str) -> bool:
    """
    Main function that demonstrates the template XML generation process.
    
    Args:
        template_name: Name of the template to process
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        logger.info("Starting template generation for %s", template_name)
        
        # Example template configuration based on provided example
        template_id = f"\\library\\T_BW_PKM_13_24_KW\\{template_name}\\Vorlagen\\{template_name}.template"
        title = template_name
        description = "#Aenderung_FM_Auslandsaufenthalt"
        
        # Example parameter definitions
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
                 'name': '_13_B_FM_MERKBLAETTER_T_M010',
                 'ref': '\\T_AOK_BW_TB\\Anlagen\\13_B_FM_MERKBLAETTER_T\\Daten\\_13_B_FM_MERKBLAETTER_T_M010.datamodel',
                 'data_source_name': 'Auftragssteuerung',
                 'data_mapping_ref': '',
                 'constant_data_ref': ''
             },
                         {
                 'name': 'Konstanten',
                 'ref': '\\\\_T_BW_Global\\Daten\\Konstanten.datamodel',
                 'data_source_name': 'Konstanten',
                 'data_source_definition_ref': '\\\\_T_BW_Global\\Konstanten.datasource',
                 'data_mapping_ref': '\\\\_T_BW_Global\\Daten\\Konstanten.mapping',
                 'constant_data_ref': ''
             },
                         {
                 'name': template_name,
                 'ref': f'\\T_BW_PKM_13_24_KW\\{template_name}\\Daten\\{template_name}.datamodel',
                 'data_source_name': 'auftragssteuerung',
                 'data_mapping_ref': f'\\T_BW_PKM_13_24_KW\\{template_name}\\Daten\\{template_name}.mapping',
                 'constant_data_ref': ''
             }
        ]
        
        # Example datanode definitions
        datanodedefs = [
            {
                'name': 'omaui',
                'ref': '\\\\__T_Common\\Daten\\OscareAdapterUI.datamodel'
            }
        ]
        
        # Document configuration - For Testing
        document_config = {
            'style_config': {'section_style_parent': 'Anschreiben'},
            'document_part_refs': [
                {
                    'uri': '\\\\_T_BW_Global\\Dokumentsteuerung\\Brief.model',
                    'extensions': [
                        {
                            'id': 'Brieftext Inhalt',
                            'container_part_refs': [
                                {
                                    'uri': f'{template_name}\\Bausteine\\{template_name}_Fachtext.model',
                                    'params': [
                                        {'name': template_name, 'value': f'${template_name}'},
                                        {'name': 'Konstanten', 'value': '$Konstanten'}
                                    ]
                                }
                            ]
                        }
                    ],
                    'params': [
                        {'name': 'Auftragssteuerung', 'value': '$Auftragssteuerung'},
                        {'name': 'Brief', 'value': '$Auftragssteuerung.Steuerdaten.Vorlage.Brief'},
                        {'name': 'Betreff1', 'value': f'${template_name}.Aufbereitet.Variable1_Betreff'},
                        {'name': 'Betreff2', 'value': '""'},
                        {'name': 'AnzahlAnlagen', 'value': f'${template_name}.Aufbereitet.AnlagenAnzahl'},
                        {'name': 'Ausgabesteuerung', 'value': '$Auftragssteuerung.Steuerdaten.Vorlage.Brief.instance(0).OMS'},
                        {'name': 'VertikaleZeileAnschreiben', 'value': '$Auftragssteuerung.Fachdaten.CORC.KUND_ID'},
                        {'name': 'Betreff3', 'value': '""'},
                        {'name': 'Briefdatum', 'value': '$Auftragssteuerung.Fachdaten.HEADER.OUTPUT_DATE.toString()'},
                        {'name': 'Anlagen', 'value': f'${template_name}.Aufbereitet.Variable4_Anlage'}
                    ]
                },
                {
                    'uri': '\\\\_T_BW_Global\\Framework\\Bausteine\\OscareAdapterDocumentToolbarOnlyUI.model',
                    'params': [
                        {'name': 'FW_Daten', 'value': '$FW_Daten'},
                        {'name': 'oai', 'value': '$omaui'}
                    ]
                }
            ],
            'document_parts': [
                {
                    'visible_if_condition': f'${template_name}.Dialog.Dialog_Variable1 == "Ende"',
                    'document_part_refs': [
                        {
                            'uri': 'Anlagen\\13_B_FM_MERKBLAETTER_T\\13_B_FM_MERKBLAETTER_T_M010.model',
                            'params': [
                                {'name': 'Auftragssteuerung', 'param_type': 'datanoderef', 'value': '$Auftragssteuerung'},
                                {'name': '_13_B_FM_MERKBLAETTER_T_M010', 'value': '$_13_B_FM_MERKBLAETTER_T_M010'}
                            ]
                        }
                    ]
                }
            ]
        }
        
        # Generate the complete template XML
        template_xml = create_template_xml(
            template_id=template_id,
            title=title,
            description=description,
            paramdefs=paramdefs,
            datanodedefs=datanodedefs,
            document_config=document_config
        )
        
        # Log the results
        xml_length = len(template_xml)
        logger.info("Successfully generated template XML for %s (%d bytes)", template_name, xml_length)
        
        # Display the generated XML
        print(template_xml)
        
        return True
        
    except Exception as e:
        logger.error("Error generating template XML for %s: %s", template_name, str(e))
        return False

if __name__ == "__main__":
    # Execute with template_name argument
    if len(sys.argv) > 1:
        template_to_run = sys.argv[1]
        logger.info("Running template generation for: %s", template_to_run)
        if not main(template_to_run):
            sys.exit(1)
    else:
        logger.warning("No template name provided. Exiting.")
        sys.exit(1)
