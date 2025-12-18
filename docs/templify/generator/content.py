"""
Content generation module for templify.
Handles generation of content part XML for model files.
"""

import re
import logging
from typing import List, Dict, Any, Optional

from templify.utils.logger_setup import setup_logger
from templify.generator.par import Span, SpanStyle, create_span_xml
from templify.generator.condition import generate_condition, generate_conditions_batch

# Initialize logger
logger = setup_logger(__name__)

def combine_spans_xml(spans: List[Span]) -> str:
    """
    Create XML for a list of spans by joining their XML representations.
    
    Args:
        spans (List[Span]): List of spans to convert to XML
        
    Returns:
        str: Combined XML for all spans
    """
    return "\n".join(create_span_xml(span) for span in spans)

def process_span_text(text: str, template_name: str, variant_number: str) -> List[Dict[str, Any]]:
    """
    Process text in a span. The input text is assumed to have $Dialog-Variable references already resolved by Claude.
    This function now primarily ensures any remaining variable-like patterns (e.g., $some_other_variable)
    are correctly formatted for <Data> tags with the appropriate path structure.
    It infers the section ('Dialog' or 'Aufbereitet') based on the variable name convention.
    Textbaustein references are expected to be handled by the extractor as separate 'model' type content parts.
    
    Args:
        text (str): Text content from a span
        template_name (str): Name of the template (e.g., FRW060)
        variant_number (str): Variant number (e.g., 0001)
        
    Returns:
        list: List of text and data elements
    """
    elements = []
    last_end = 0
    for match in re.finditer(r'\$((?:Dialog-Variable\s+\S+)|[A-Za-z0-9_-]+)', text):
        start, end = match.span()
        var_name_with_prefix = match.group(1) 
        
        if start > last_end:
            elements.append({"type": "text", "content": text[last_end:start]})
        
        section_name = ""
        var_name_formatted = ""
        if var_name_with_prefix.startswith("Dialog-"):
            section_name = "Dialog"
            var_name_formatted = var_name_with_prefix.replace(' ', '_').replace('-', '_') 
        else:
            section_name = "Aufbereitet"
            var_name_formatted = var_name_with_prefix.replace(' ', '_').replace('-', '_')

        full_path = f"${template_name}.{section_name}._{variant_number}.{var_name_formatted}"
        
        elements.append({
            "type": "data", 
            "content": full_path
        })
        last_end = end
        
    # Add any remaining text after the last variable
    if last_end < len(text):
        elements.append({"type": "text", "content": text[last_end:]})
        
    # If no variables were found, the whole text is a single text element
    if not elements and text:
        elements.append({"type": "text", "content": text})
        
    logger.debug(f"Processed span text '{text[:50]}...' into elements: {elements}")
    return elements

def generate_content_elements(content_parts: List[Dict[str, Any]], template_name: str, variant_number: str) -> str:
    """
    Generate XML elements for content parts.
    Handles paragraphs, model references, and conditional container parts.
    
    Args:
        content_parts: List of content part dictionaries, where each can be:
                      - paragraph: with 'spans', 'style', 'visible_if' attributes
                      - model: with 'content' (model URI) and 'visible_if' attributes 
                      - conditional_container: with 'content_parts' and 'visible_if' attributes
        template_name: Name of the template
        variant_number: Variant number (e.g., '0001')
        
    Returns:
        str: XML string with all content elements
    """
    logger.debug(f"Generating content elements for {template_name} variant {variant_number} ({len(content_parts)} parts)")
    
    # Collect all conditions for batch processing
    conditions_map = {}
    for i, part in enumerate(content_parts):
        raw_condition = part.get("visible_if")
        if raw_condition:
            conditions_map[f"cond_{i}"] = raw_condition
    
    # Process all conditions in batch if there are any
    js_conditions = {}
    if conditions_map:
        js_conditions = generate_conditions_batch(conditions_map, template_name, variant_number)
    
    xml_output_parts = []
    for i, part in enumerate(content_parts):
        part_type = part.get('type')

        # Get condition if present for the part
        part_visibility_xml = "" 
        raw_condition = part.get("visible_if")
        if raw_condition:
            condition_id = f"cond_{i}"
            if condition_id in js_conditions and js_conditions[condition_id]:
                part_visibility_xml = f'\n   <VisibleIf><![CDATA[{js_conditions[condition_id]}]]></VisibleIf>'
            else:
                # Fallback to individual processing if batch failed for this condition
                individual_js_cond = generate_condition([raw_condition], template_name, variant_number)
                if individual_js_cond and isinstance(individual_js_cond, list) and individual_js_cond[0]:
                    part_visibility_xml = f'\n   <VisibleIf><![CDATA[{individual_js_cond[0]}]]></VisibleIf>'
        
        # --- Paragraph Handling ---
        if part_type == "paragraph":
            paragraph_style = part.get('style', 'Standard')
            if paragraph_style.lower() in ['überschrift 1', 'überschrift 2', 'list', 'strikethrough']:
                logger.debug(f"Normalizing style '{paragraph_style}' to 'Standard'")
                paragraph_style = 'Standard'
            
            spans_data = part.get("spans", [])
            processed_spans_xml_list = []
            if not spans_data:
                 processed_spans_xml_list.append('<Span><Text></Text></Span>')
            else:
                for span_idx, span_item in enumerate(spans_data):
                    if isinstance(span_item.get("text"), str):
                        elements = process_span_text(span_item["text"], template_name, variant_number)
                        for el_span_data in elements:
                            style_name = span_item.get("style")
                            if style_name and style_name.lower() == 'strikethrough': style_name = None
                            span_obj_style = SpanStyle(parent_name=style_name)
                            
                            span_obj = None
                            if el_span_data["type"] == "text":
                                span_obj = Span(text=el_span_data["content"], style=span_obj_style)
                            elif el_span_data["type"] == "data":
                                span_obj = Span(data_ref=el_span_data["content"], style=span_obj_style)
                            
                            if span_obj:
                                processed_spans_xml_list.append(create_span_xml(span_obj))
                    else:
                        logger.warning(f"Invalid span text in paragraph {i+1}, span {span_idx+1}")

            final_par_content_xml = "\n".join(processed_spans_xml_list)
            
            xml_output_parts.append(f'''  <Par>
   <Style parentName="{paragraph_style}"><SpaceAfter resolution="combine">0.5cm</SpaceAfter></Style>{part_visibility_xml} 
{final_par_content_xml}
  </Par>''')

        # --- Model Handling ---
        elif part_type == "model":
            model_name_or_uri = part.get('content')
            
            if model_name_or_uri and '\\\\' in model_name_or_uri: 
                container_ref_xml_content = f'''<ContainerPartRef uri="{model_name_or_uri}">
  <Param name="Auftragssteuerung" type="datanoderef">$Auftragssteuerung</Param>
</ContainerPartRef>'''
                
                if part_visibility_xml: 
                    xml_output_parts.append(f'''<ContainerPart>{part_visibility_xml}
  {container_ref_xml_content}
</ContainerPart>''')
                else:
                    xml_output_parts.append(container_ref_xml_content)
            else:
                 xml_output_parts.append(f'<!-- ERROR: Invalid model path: {model_name_or_uri} -->')
        
        # --- Conditional Container Handling ---
        elif part_type == "conditional_container":
            nested_content = part.get('content_parts', [])

            if part_visibility_xml:
                nested_content_xml = generate_content_elements(nested_content, template_name, variant_number) 
                xml_output_parts.append(f'''<ContainerPart>{part_visibility_xml}
{nested_content_xml}
</ContainerPart>''')
            else:
                if nested_content:
                    nested_content_xml = generate_content_elements(nested_content, template_name, variant_number)
                    xml_output_parts.append(nested_content_xml)

        # --- Unknown Type Handling ---
        else:
            logger.warning(f"Unknown part type: '{part_type}' at index {i}")

    return "\n".join(xml_output_parts)

def create_content(
    content_parts: List[Dict[str, Any]],
    template_name: str,
    variant_number: Optional[str] = None
) -> str:
    """
    Main function to create the content XML for a model file.
    
    Args:
        content_parts: List of content part dictionaries
        template_name: Name of the template
        variant_number: Optional variant number, defaults to "0001" if not provided
        
    Returns:
        str: The content XML as a properly formatted string
    """
    logger.info(f"Creating content XML for {template_name}")
    
    # Ensure variant_number is a string
    variant_str = str(variant_number) if variant_number is not None else "0001"
    
    # Check if content_parts is empty
    if not content_parts:
        logger.warning(f"No content parts provided for {template_name}")
        return "<!-- No content parts defined -->"
    
    # Use the core function to generate the content XML
    content_xml = generate_content_elements(content_parts, template_name, variant_str)
    
    logger.info(f"Generated content XML with {len(content_parts)} parts for {template_name}")
    return content_xml

def main(template_name: str) -> bool:
    """Example function demonstrating content generation."""
    try:
        logger.info(f"Testing content generation for {template_name}")
        
        # Example content parts
        content_parts = [
            {
                'type': 'paragraph',
                'style': 'Standard',
                'spans': [
                    {'text': 'This is a test paragraph with a $Dialog-Variable Vorname.'}
                ]
            },
            {
                'type': 'model',
                'content': '\\\\T_BW_Global\\Templates\\Footer.model'
            }
        ]
        
        # Generate content XML
        content_xml = create_content(content_parts, template_name, "0001")
        
        # Log some diagnostic information
        xml_length = len(content_xml)
        logger.info(f"Generated {xml_length} bytes of content XML")
        
        return True
        
    except Exception as e:
        logger.error(f"Error generating content XML: {str(e)}")
        return False

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        template_to_run = sys.argv[1]
        logger.info(f"Running content generation for template: {template_to_run}")
        if not main(template_to_run):
            sys.exit(1)
    else:
        logger.warning("No template name provided for direct execution. Exiting.")
        sys.exit(1)