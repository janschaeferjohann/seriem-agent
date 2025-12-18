"""
Module for generating ISYText metadata XML files dynamically.
Creates XML structure based on extracted metadata parameters.
"""

import logging
import uuid
from typing import Dict, Any, Optional, List
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom import minidom

from templify.utils.logger_setup import setup_logger

logger = setup_logger(__name__, log_level=logging.INFO)

def create_metadata_xml(metadata: Dict[str, Any]) -> str:
    """
    Create metadata XML from extracted metadata parameters.
    
    Args:
        metadata (Dict[str, Any]): Extracted metadata parameters
        
    Returns:
        str: Complete XML string for .template.metadata file
    """
    logger.info(f"Creating metadata XML with {len(metadata)} parameters")
    
    # Create root structure
    root = Element("content")
    entry = SubElement(root, "entry", name="/dataProviders/Metadata")
    provider = SubElement(entry, "SerializedDataProvider", 
                         providerClass="de.kwsoft.mtext.format.dataprovider.MetadataNodeInstance")
    SubElement(provider, "DataModelResourceName", name="")
    
    # Create main Metadata node
    metadata_node = SubElement(provider, "NodeInst", name="Metadata", value="")
    metadata_children = SubElement(metadata_node, "Children")
    
    # Add oscare_Adapter section if mapping_ident exists
    if 'mapping_ident' in metadata:
        add_oscare_adapter_section(metadata_children, metadata['mapping_ident'])
    
    # Add Vorlage section
    add_vorlage_section(metadata_children, metadata)
    
    # Convert to pretty-printed XML string
    xml_str = prettify_xml(root)
    logger.info("Successfully created metadata XML")
    return xml_str

def add_oscare_adapter_section(parent: Element, mapping_ident: str) -> None:
    """Add oscare_Adapter section to metadata XML."""
    oscare_node = SubElement(parent, "NodeInst", name="oscare_Adapter", value="")
    oscare_children = SubElement(oscare_node, "Children")
    
    SubElement(oscare_children, "NodeInst", 
               name="mapping_ident",
               uuid="901667f4-338a-4e3c-a4af-d62fcd58f131",
               value=mapping_ident)

def add_vorlage_section(parent: Element, metadata: Dict[str, Any]) -> None:
    """Add Vorlage section to metadata XML."""
    vorlage_node = SubElement(parent, "NodeInst", name="Vorlage", value="")
    vorlage_children = SubElement(vorlage_node, "Children")
    
    # Add basic Vorlage fields
    add_if_exists(vorlage_children, "Document_ID", metadata.get('document_id'))
    add_if_exists(vorlage_children, "Document_Title", metadata.get('document_title'))
    add_if_exists(vorlage_children, "Nachbearbeitung", metadata.get('nachbearbeitung'))
    add_if_exists(vorlage_children, "Ausgabesteuerung", metadata.get('ausgabesteuerung'))
    add_if_exists(vorlage_children, "Freigabe_User", metadata.get('freigabe_user'))
    add_if_exists(vorlage_children, "Freigabe", metadata.get('freigabe'))
    add_if_exists(vorlage_children, "LVIN_channel_opt", metadata.get('lvin_channel_opt'))
    
    # Add Brief section
    add_brief_section(vorlage_children, metadata)
    
    # Add Sonderfunktionen section if needed
    if metadata.get('berechnetes_datum'):
        add_sonderfunktionen_section(vorlage_children, metadata)

def add_brief_section(parent: Element, metadata: Dict[str, Any]) -> None:
    """Add Brief section to Vorlage."""
    brief_node = SubElement(parent, "NodeInst", 
                           name="Brief", 
                           uuid="ac07e78e-22f2-4271-aa3d-b563ce9a624e", 
                           value="")
    brief_children = SubElement(brief_node, "Children")
    
    # Basic Brief fields
    add_if_exists(brief_children, "Beschreibung", metadata.get('beschreibung'))
    add_if_exists(brief_children, "Empf_Mindestalter", metadata.get('empf_mindestalter'))
    add_if_exists(brief_children, "Empf_Quelle", metadata.get('empf_quelle'))
    add_if_exists(brief_children, "Empf_Rolle", metadata.get('empf_rolle'))
    add_if_exists(brief_children, "Empf_Typ", metadata.get('empf_typ'))
    add_if_exists(brief_children, "Absender_Typ", metadata.get('absender_typ'))
    add_if_exists(brief_children, "Briefkopf_Auswahl", metadata.get('briefkopf_auswahl'))
    
    # SB_Info_anzeigen with valueDesc
    if 'sb_info_anzeigen' in metadata:
        SubElement(brief_children, "NodeInst",
                   name="SB_Info_anzeigen",
                   value=metadata['sb_info_anzeigen'],
                   valueDesc="Sachbearbeiterinformationen im Briefkopf anzeigen?")
    
    add_if_exists(brief_children, "ORGA_anzeigen", metadata.get('orga_anzeigen'))
    add_if_exists(brief_children, "Postzustellungsurkunde", metadata.get('postzustellungsurkunde'))
    add_if_exists(brief_children, "Unterschrift_Typ", metadata.get('unterschrift_typ'))
    add_if_exists(brief_children, "Schlusssatz", metadata.get('schlusssatz'))
    
    # postscriptum with uuid
    if 'postscriptum' in metadata:
        SubElement(brief_children, "NodeInst",
                   name="postscriptum",
                   uuid="acc87c19-312b-4cd8-bf1a-bdf8c653c058",
                   value=metadata['postscriptum'])
    
    # Hinweistexte with uuid
    if 'hinweistexte' in metadata:
        SubElement(brief_children, "NodeInst",
                   name="Hinweistexte",
                   uuid="d4e018f2-b4b6-438c-9f77-d40fc5d2a68b",
                   value=metadata['hinweistexte'])
    
    add_if_exists(brief_children, "Dokumentenart", metadata.get('dokumentenart'))
    
    # Add Dialoge section
    add_dialoge_section(brief_children, metadata)
    
    # Add OMS section
    add_oms_section(brief_children, metadata)
    
    # Add Marketing section
    add_marketing_section(brief_children, metadata)

def add_dialoge_section(parent: Element, metadata: Dict[str, Any]) -> None:
    """Add Dialoge section to Brief."""
    dialoge_node = SubElement(parent, "NodeInst", name="Dialoge", value="")
    dialoge_children = SubElement(dialoge_node, "Children")
    
    add_if_exists(dialoge_children, "Dialoge_in_Anlagen_verwenden", metadata.get('dialoge_in_anlagen_verwenden'))
    add_if_exists(dialoge_children, "Manuellen_Adressdialog_anzeigen", metadata.get('manuellen_adressdialog_anzeigen'))
    add_if_exists(dialoge_children, "Sonder_Dialog", metadata.get('sonder_dialog'))
    
    # OSCARE_Anlagen subsection
    if metadata.get('oscare_anlagen_vorbelegung'):
        oscare_anlagen_node = SubElement(dialoge_children, "NodeInst", name="OSCARE_Anlagen", value="")
        oscare_anlagen_children = SubElement(oscare_anlagen_node, "Children")
        add_if_exists(oscare_anlagen_children, "Vorbelegung", metadata.get('oscare_anlagen_vorbelegung'))

def add_oms_section(parent: Element, metadata: Dict[str, Any]) -> None:
    """Add OMS section to Brief."""
    oms_node = SubElement(parent, "NodeInst", name="OMS", value="")
    oms_children = SubElement(oms_node, "Children")
    
    add_if_exists(oms_children, "StandardZustellMedium", metadata.get('standard_zustellmedium'))
    
    # ErlaubteZustellMedien - can be multiple entries
    if 'erlaubte_zustellmedien' in metadata:
        zustellmedien = metadata['erlaubte_zustellmedien']
        if isinstance(zustellmedien, list):
            for medium in zustellmedien:
                SubElement(oms_children, "NodeInst",
                          name="ErlaubteZustellMedien",
                          uuid=str(uuid.uuid4()),
                          value=medium)
        elif isinstance(zustellmedien, str):
            SubElement(oms_children, "NodeInst",
                      name="ErlaubteZustellMedien",
                      uuid=str(uuid.uuid4()),
                      value=zustellmedien)
    
    add_if_exists(oms_children, "Brief_archivieren", metadata.get('brief_archivieren'))
    add_if_exists(oms_children, "Beilage1", metadata.get('beilage1'))
    add_if_exists(oms_children, "OGS_Anzeigename", metadata.get('ogs_anzeigename'))

def add_marketing_section(parent: Element, metadata: Dict[str, Any]) -> None:
    """Add Marketing section to Brief."""
    marketing_node = SubElement(parent, "NodeInst", name="Marketing", value="")
    marketing_children = SubElement(marketing_node, "Children")
    
    add_if_exists(marketing_children, "WSM_Typ", metadata.get('wsm_typ'))

def add_sonderfunktionen_section(parent: Element, metadata: Dict[str, Any]) -> None:
    """Add Sonderfunktionen section to Vorlage."""
    sonder_node = SubElement(parent, "NodeInst", name="Sonderfunktionen", value="")
    sonder_children = SubElement(sonder_node, "Children")
    
    add_if_exists(sonder_children, "Berechnetes_Datum", metadata.get('berechnetes_datum'))

def add_if_exists(parent: Element, name: str, value: Any) -> None:
    """Add a NodeInst element only if value exists and is not None."""
    if value is not None and value != "":
        SubElement(parent, "NodeInst", name=name, value=str(value))

def prettify_xml(elem: Element) -> str:
    """Return a pretty-printed XML string for the Element."""
    rough_string = tostring(elem, encoding='unicode')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="   ").replace('<?xml version="1.0" ?>\n', '<?xml version="1.0" encoding="UTF-8"?>\n')

def save_metadata_xml(xml_content: str, output_path: str) -> bool:
    """
    Save metadata XML to file.
    
    Args:
        xml_content (str): XML content to save
        output_path (str): Path where to save the file
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(xml_content)
        logger.info(f"Successfully saved metadata XML to {output_path}")
        return True
    except Exception as e:
        logger.error(f"Error saving metadata XML to {output_path}: {e}", exc_info=True)
        return False 