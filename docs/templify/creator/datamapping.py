"""
Module for generating ISYText DataMapping XML content.
"""
import logging
from datetime import datetime
from templify.parser.get_data import get_xsd_path, get_steuerung_formkey
from templify.utils.logger_setup import setup_logger

# Initialize logger
logger = setup_logger(__name__, log_level=logging.INFO)

def create_datamapping_xml(template_name: str) -> str:
    """
    Creates the XML content for a .mapping file.
    This typically defines how data sources map to parameters.
    In this common case, it maps the Auftragssteuerung source to the template-specific node.

    Args:
        template_name (str): The name of the template (e.g., FRW060).

    Returns:
        str: The XML content for the .mapping file.
    """
    try:
        # Get the XSD path and formkey
        xsd_path = get_xsd_path()
        formkey = get_steuerung_formkey(template_name)
        
        if not formkey:
            logger.warning(f"Failed to get formkey for {template_name}, using template name as fallback")
            formkey = template_name  # Use template name as fallback
        
        # Create the mapping properties content
        mapping_content = f"""<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<!DOCTYPE properties SYSTEM "http://java.sun.com/dtd/properties.dtd">
<properties>
<comment>Erstellt am {datetime.now().strftime('%d.%m.%y, %H:%M')}</comment>
<entry key="DataMappingEditor.XSD_FILE_NAME">\\Z_Entwicklung_XSD\\{xsd_path}.xsd</entry>
<entry key="DataMappingEditor.XSD_ROOT_ELEMENT">abap</entry>
<entry key="DataMappingResult.FILE_NAME">\\Z_Entwicklung_XML\\XML_KWSOFT\\{template_name}\\{formkey}.xml</entry>
</properties>"""
        
        return mapping_content
    except Exception as e:
        logger.error(f"Error creating datamapping XML for {template_name}: {str(e)}")
        # Return a minimal valid XML as fallback
        return f"""<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<!DOCTYPE properties SYSTEM "http://java.sun.com/dtd/properties.dtd">
<properties>
<comment>Error creating mapping file</comment>
</properties>"""