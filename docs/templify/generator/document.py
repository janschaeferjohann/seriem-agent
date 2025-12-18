"""
Document generation module for templify.
"""

from typing import List, Dict, Optional, Any
from templify.utils.logger_setup import setup_logger
from templify.generator.paramdef import create_param


# Initialize logger
logger = setup_logger(__name__)

def create_visibleif(condition: Optional[str] = None, default_condition: str = '$FRW025.Dialog.Dialog_Variable1 == "Ende"') -> str:
    """
    Create a VisibleIf XML element.
    
    Args:
        condition: Optional condition description to generate JS condition via condition.py
        default_condition: Default JavaScript condition to use if condition is None/empty
        
    Returns:
        str: XML representation of the VisibleIf element
        
    Examples:
        >>> create_visibleif()
        '<VisibleIf><![CDATA[$FRW025.Dialog.Dialog_Variable1 == "Ende"]]></VisibleIf>'
        
        >>> create_visibleif(default_condition='$Template.Dialog.Variable1 == "Test"')
        '<VisibleIf><![CDATA[$Template.Dialog.Variable1 == "Test"]]></VisibleIf>'
    """
    # IMPROVE: Implement condition.py integration when condition is provided
    # For now, use the default_condition
    if condition and condition.strip():
        # Future: Call condition.py to generate JavaScript condition
        # js_condition = generate_condition([condition], template_name, variant_number)[0]
        # For now, use the provided condition as-is
        js_condition = condition
    else:
        js_condition = default_condition
    
    return f'<VisibleIf><![CDATA[{js_condition}]]></VisibleIf>'



def create_style(section_style_parent: Optional[str] = None, **additional_style_attrs: Any) -> str:
    """
    Create a Style XML section with SectionStyle.
    
    Args:
        section_style_parent: Parent name for SectionStyle (optional)
        additional_style_attrs: Additional style attributes
        
    Returns:
        str: XML representation of the Style section
        
    Examples:
        >>> create_style("Anschreiben")
        '<Style>
          <SectionStyle parentName="Anschreiben"></SectionStyle>
        </Style>'
        
        >>> create_style()
        '<Style>
          <SectionStyle></SectionStyle>
        </Style>'
    """
    # Build SectionStyle attributes
    section_attrs = {}
    if section_style_parent:
        section_attrs['parentName'] = section_style_parent
    
    # Add additional style attributes
    section_attrs.update(additional_style_attrs)
    
    # Format attributes
    if section_attrs:
        formatted_attrs = [f'{key}="{value}"' for key, value in section_attrs.items()]
        attr_string = " ".join(formatted_attrs)
        section_style = f'<SectionStyle {attr_string}></SectionStyle>'
    else:
        section_style = '<SectionStyle></SectionStyle>'
    
    return f'<Style>\n  {section_style}\n</Style>'

def create_containerextension(extension_id: str, container_part_refs: List[Dict[str, Any]]) -> str:
    """
    Create a ContainerExtension with ContainerPartRef elements.
    
    Args:
        extension_id: ID for the ContainerExtension
        container_part_refs: List of ContainerPartRef configurations. Each config can contain:
                            - uri: URI for the ContainerPartRef (required)
                            - params: List of parameter dicts with name, value, param_type, etc.
        
    Returns:
        str: XML representation of the ContainerExtension
        
    Example:
        >>> create_containerextension("Brieftext Inhalt", [
        ...     {
        ...         "uri": "FRW025\\Bausteine\\FRW025_Fachtext.model",
        ...         "params": [
        ...             {"name": "FRW025", "value": "$FRW025"},
        ...             {"name": "Konstanten", "value": "$Konstanten"},
        ...             {"name": "Auftragssteuerung", "param_type": "datanoderef"}
        ...         ]
        ...     }
        ... ])
        '<ContainerExtension id="Brieftext Inhalt">
          <ContainerPartRef uri="FRW025\\Bausteine\\FRW025_Fachtext.model">
            <Param name="FRW025">$FRW025</Param>
            <Param name="Konstanten">$Konstanten</Param>
            <Param name="Auftragssteuerung" type="datanoderef">$Auftragssteuerung</Param>
          </ContainerPartRef>
        </ContainerExtension>'
    """
    # Validate required parameters
    if not extension_id:
        raise ValueError("Extension ID is required")
    
    container_parts = []
    for ref_config in container_part_refs:
        uri = ref_config.get('uri', '')
        if not uri:
            continue
            
        # Create params for this ContainerPartRef
        params = ref_config.get('params', [])
        param_elements = []
        for param in params:
            if isinstance(param, dict):
                param_elements.append(create_param(**param))
            else:
                # Fallback for simple string params
                param_elements.append(create_param(str(param)))
        
        # Build ContainerPartRef
        if param_elements:
            param_xml = "\n    ".join(param_elements)
            container_part = f'<ContainerPartRef uri="{uri}">\n    {param_xml}\n  </ContainerPartRef>'
        else:
            container_part = f'<ContainerPartRef uri="{uri}"></ContainerPartRef>'
        
        container_parts.append(container_part)
    
    # Combine all ContainerPartRef elements
    if container_parts:
        parts_xml = "\n  ".join(container_parts)
        return f'<ContainerExtension id="{extension_id}">\n  {parts_xml}\n</ContainerExtension>'
    else:
        return f'<ContainerExtension id="{extension_id}"></ContainerExtension>'

def create_extensions(container_extensions: List[Dict[str, Any]]) -> str:
    """
    Create the complete Extensions section.
    
    Args:
        container_extensions: List of ContainerExtension configurations
        
    Returns:
        str: XML representation of the Extensions section
        
    Example:
        >>> create_extensions([
        ...     {
        ...         "id": "Brieftext Inhalt",
        ...         "container_part_refs": [{"uri": "test.model", "params": []}]
        ...     }
        ... ])
        '<Extensions>
          <ContainerExtension id="Brieftext Inhalt">
            <ContainerPartRef uri="test.model"></ContainerPartRef>
          </ContainerExtension>
        </Extensions>'
    """
    extension_elements = []
    for ext_config in container_extensions:
        extension_id = ext_config.get('id', '')
        container_part_refs = ext_config.get('container_part_refs', [])
        
        if extension_id:
            extension_elements.append(create_containerextension(extension_id, container_part_refs))
    
    if extension_elements:
        extensions_xml = "\n  ".join(extension_elements)
        return f'<Extensions>\n  {extensions_xml}\n</Extensions>'
    else:
        return '<Extensions></Extensions>'

def create_documentpartref(
    uri: str, 
    params: Optional[List[Dict[str, Any]]] = None,
    extensions: Optional[List[Dict[str, Any]]] = None,
    **additional_attrs: Any
) -> str:
    """
    Create a DocumentPartRef XML element.
    
    Args:
        uri: URI for the DocumentPartRef (required)
        params: Optional list of parameter configurations. Each param dict can contain:
               - name: Parameter name (required)
               - value: Custom value (optional, defaults to "${name}")
               - param_type: Type attribute (optional, e.g., "datanoderef")
               - Any additional attributes for the Param element
        extensions: Optional list of extension configurations
        additional_attrs: Any additional attributes to include
        
    Returns:
        str: XML representation of the DocumentPartRef element
        
    Examples:
        >>> create_documentpartref(
        ...     "\\_T_BW_Global\\Dokumentsteuerung\\Brief.model",
        ...     params=[
        ...         {"name": "Brief", "value": "$Auftragssteuerung.Steuerdaten.Vorlage.Brief"},
        ...         {"name": "Auftragssteuerung", "param_type": "datanoderef"},
        ...         {"name": "Betreff1", "value": '"Custom Subject"'}
        ...     ],
        ...     extensions=[{"id": "Brieftext Inhalt", "container_part_refs": []}]
        ... )
    """
    # Validate required parameters
    if not uri:
        raise ValueError("URI is required")
    
    # Build attributes dictionary
    attrs = {'uri': uri}
    attrs.update(additional_attrs)
    
    # Format all attributes for XML
    formatted_attrs = [f'{key}="{value}"' for key, value in attrs.items()]
    attr_string = " ".join(formatted_attrs)
    
    # Build child elements
    child_elements = []
    
    # Add Extensions if provided
    if extensions:
        child_elements.append(create_extensions(extensions))
    
    # Add Param elements if provided
    if params:
        for param in params:
            if isinstance(param, dict):
                child_elements.append(create_param(**param))
            else:
                child_elements.append(create_param(str(param)))
    
    # Build the final XML
    if child_elements:
        children_xml = "\n   ".join(child_elements)
        return f'<DocumentPartRef {attr_string}>\n   {children_xml}\n  </DocumentPartRef>'
    else:
        return f'<DocumentPartRef {attr_string}></DocumentPartRef>'

def create_documentpart(
    visible_if_condition: Optional[str] = None,
    document_part_refs: Optional[List[Dict[str, Any]]] = None,
    **additional_attrs: Any
) -> str:
    """
    Create a DocumentPart XML element.
    
    Args:
        visible_if_condition: Optional condition for VisibleIf element
        document_part_refs: Optional list of DocumentPartRef configurations
        additional_attrs: Any additional attributes
        
    Returns:
        str: XML representation of the DocumentPart element
        
    Example:
        >>> create_documentpart(
        ...     visible_if_condition='$FRW025.Dialog.Dialog_Variable1 == "Ende"',
        ...     document_part_refs=[{"uri": "test.model"}]
        ... )
    """
    # Build child elements
    child_elements = []
    
    # Add VisibleIf if condition provided
    if visible_if_condition:
        child_elements.append(create_visibleif(condition=visible_if_condition))
    
    # Add DocumentPartRef elements if provided
    if document_part_refs:
        for ref_config in document_part_refs:
            if isinstance(ref_config, dict):
                child_elements.append(create_documentpartref(**ref_config))
    
    # Build the final XML
    if child_elements:
        children_xml = "\n   ".join(child_elements)
        return f'<DocumentPart>\n   {children_xml}\n  </DocumentPart>'
    else:
        return '<DocumentPart></DocumentPart>'

def create_document(
    document_id: Optional[str] = None,
    style_config: Optional[Dict[str, Any]] = None,
    document_part_refs: Optional[List[Dict[str, Any]]] = None,
    document_parts: Optional[List[Dict[str, Any]]] = None
) -> str:
    """
    Create the complete Document XML structure.
    
    Args:
        document_id: Optional ID attribute for the Document
        style_config: Optional style configuration
        document_part_refs: Optional list of DocumentPartRef configurations
        document_parts: Optional list of DocumentPart configurations
        
    Returns:
        str: Complete Document XML string
        
    Example:
        >>> create_document(
        ...     document_id="FRW025_0001",
        ...     style_config={"section_style_parent": "Anschreiben"},
        ...     document_part_refs=[{"uri": "Brief.model", "params": []}]
        ... )
    """
    # Build attributes
    attrs = {}
    if document_id:
        attrs['id'] = document_id
    
    attr_string = ""
    if attrs:
        formatted_attrs = [f'{key}="{value}"' for key, value in attrs.items()]
        attr_string = " " + " ".join(formatted_attrs)
    
    # Build child elements
    child_elements = []
    
    # Add Style section
    if style_config:
        child_elements.append(create_style(**style_config))
    else:
        child_elements.append(create_style())
    
    # Add DocumentPartRef elements
    if document_part_refs:
        for ref_config in document_part_refs:
            if isinstance(ref_config, dict):
                child_elements.append(create_documentpartref(**ref_config))
    
    # Add DocumentPart elements
    if document_parts:
        for part_config in document_parts:
            if isinstance(part_config, dict):
                child_elements.append(create_documentpart(**part_config))
    
    # Build the final XML
    if child_elements:
        children_xml = "\n  ".join(child_elements)
        return f'<Document{attr_string}>\n  {children_xml}\n </Document>'
    else:
        return f'<Document{attr_string}></Document>'

def main():
    """Example usage of the document generation functions."""
    logger.debug("Demonstrating Document generation functions")
    
    # Example 1: Simple VisibleIf
    visible_if_xml = create_visibleif()
    logger.debug("Generated VisibleIf XML: %s", visible_if_xml)
    
    # Example 2: Param with type
    param_xml = create_param("Auftragssteuerung", param_type="datanoderef")
    logger.debug("Generated Param with type XML: %s", param_xml)
    
    # Example 3: Style section
    style_xml = create_style("Anschreiben")
    logger.debug("Generated Style XML: %s", style_xml)
    
    # Example 4: Complete Document
    document_xml = create_document(
        document_id="FRW025_0001",
        style_config={"section_style_parent": "Anschreiben"},
        document_part_refs=[
            {
                "uri": "\\_T_BW_Global\\Dokumentsteuerung\\Brief.model",
                "extensions": [
                    {
                        "id": "Brieftext Inhalt",
                        "container_part_refs": [
                            {
                                "uri": "FRW025\\Bausteine\\FRW025_Fachtext.model",
                                "params": [
                                    {"name": "FRW025", "value": "$FRW025"},
                                    {"name": "Konstanten", "value": "$Konstanten"}
                                ]
                            }
                        ]
                    }
                ],
                "params": [
                    {"name": "Auftragssteuerung", "value": "$Auftragssteuerung"},
                    {"name": "Brief", "value": "$Auftragssteuerung.Steuerdaten.Vorlage.Brief"},
                    {"name": "Betreff1", "value": "$FRW025.Aufbereitet.Variable1_Betreff"}
                ]
            }
        ],
        document_parts=[
            {
                "visible_if_condition": '$FRW025.Dialog.Dialog_Variable1 == "Ende"',
                "document_part_refs": [
                    {
                        "uri": "Anlagen\\13_B_FM_MERKBLAETTER_T\\13_B_FM_MERKBLAETTER_T_M010.model",
                        "params": [
                            {"name": "Auftragssteuerung", "param_type": "datanoderef", "value": "$Auftragssteuerung"},
                            {"name": "_13_B_FM_MERKBLAETTER_T_M010", "value": "$_13_B_FM_MERKBLAETTER_T_M010"}
                        ]
                    }
                ]
            }
        ]
    )
    logger.debug("Generated complete Document XML: %s", document_xml)
    print(document_xml)
if __name__ == "__main__":
    main()
