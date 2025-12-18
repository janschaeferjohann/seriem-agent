"""
UI contribution XML generation module for templify.
Handles generation of XML for UI contributions including InputArea and GuideArea.
IMPROVE: Are xsd available for ui contributions?
"""

import logging
from typing import List, Dict, Optional
from xml.sax.saxutils import escape
from templify.utils.logger_setup import setup_logger
from templify.generator.condition import generate_condition
from templify.parser.extract_uicontributions import extract_ui_contributions

# Initialize logger
logger = setup_logger(__name__)

def _format_variable_path(raw_variable_name: str, template_name: str, variant_number: str) -> str:
    """
    Formats the variable path based on naming conventions.
    Example: $Dialog-Variable1 -> $FRW060.Dialog._0001.Dialog_Variable1
    Example: $Some_Var -> $FRW060.Aufbereitet._0001.Some_Var
    """
    if not raw_variable_name.startswith('$'):
        logger.warning(f"Variable '{raw_variable_name}' does not start with $. Path formatting might be incorrect.")
        # Attempt basic formatting anyway
        var_name_only = raw_variable_name
    else:
        var_name_only = raw_variable_name[1:] # Remove leading $

    section_name = ""
    var_name_formatted = ""
    # Check if it follows the Dialog variable pattern
    if var_name_only.startswith("Dialog-"):
        section_name = "Dialog"
        # Format name: keep prefix, replace space/hyphen with underscore
        var_name_formatted = var_name_only.replace(' ', '_').replace('-', '_')
    else:
        # Assume Aufbereitet for others
        section_name = "Aufbereitet"
        # Format name: replace space/hyphen with underscore
        var_name_formatted = var_name_only.replace(' ', '_').replace('-', '_')

    # Construct the correct path
    full_path = f"${template_name}.{section_name}._{variant_number}.{var_name_formatted}"
    return full_path

def create_ui_contributions(contributions: List[Dict[str, str]], template_name: str, variant_number: str) -> str:
    """
    Create the UIContribution XML structure from a list of contribution dictionaries.
    Handles GuideArea (Folders, ContentLinks) and InputArea (Groups, Fields).
    Correctly formats dataNode paths.

    Args:
        contributions (list): List of dictionaries, each with 'feldgruppe', 'dialog_variable', 'condition', 'label'.
        template_name (str): The template name (e.g., FRW060).
        variant_number (str): The variant number (e.g., 0001).

    Returns:
        str: The complete UIContribution XML string.
    """
    if not contributions:
        return "<UIContribution/>" # Return empty element if no contributions

    guide_folders: Dict[str, List[str]] = {}
    input_groups: Dict[str, List[str]] = {}

    for contrib in contributions:
        feldgruppe = contrib.get('feldgruppe', 'Allgemein')
        variable = contrib.get('dialog_variable', '')
        label = contrib.get('label', '')
        raw_condition = contrib.get('condition', '')

        if not variable or not label:
            logger.warning(f"Skipping contribution due to missing variable or label: {contrib}")
            continue

        # Format the dataNode path correctly
        data_node_path = _format_variable_path(variable, template_name, variant_number)

        # Generate condition XML part if a condition exists
        condition_xml = ""
        if raw_condition:
            # Pass the raw condition to generate_condition, along with context
            # generate_condition should now handle full path generation
            js_conditions = generate_condition([raw_condition], template_name, variant_number)
            if js_conditions and js_conditions[0]: # Check if list is not empty and first element is truthy
                condition_xml = f'\n     <VisibleIf><![CDATA[{js_conditions[0]}]]></VisibleIf>'
            else:
                logger.warning(f"Condition generation failed for contribution: {contrib}")

        # Escape label for XML safety
        escaped_label = escape(label)

        # Prepare ContentLink and Field XML parts
        content_link_xml = f'''    <ContentLink title="{escaped_label}" targetId="" dataNode="{data_node_path}">{condition_xml}
    </ContentLink>'''
        field_xml = f'''    <Field title="{escaped_label}" dataNode="{data_node_path}">{condition_xml}
    </Field>'''

        # Add to respective dictionaries
        if feldgruppe not in guide_folders:
            guide_folders[feldgruppe] = []
            input_groups[feldgruppe] = []
        guide_folders[feldgruppe].append(content_link_xml)
        input_groups[feldgruppe].append(field_xml)

    # Build GuideArea XML
    guide_area_parts = []
    for title, links in guide_folders.items():
        escaped_title = escape(title)
        links_str = '\n'.join(links)
        guide_area_parts.append(f'   <Folder title="{escaped_title}">\n{links_str}\n   </Folder>')
    guide_area_xml = "<GuideArea>\n" + '\n'.join(guide_area_parts) + "\n </GuideArea>"

    # Build InputArea XML
    input_area_parts = []
    for title, fields in input_groups.items():
        escaped_title = escape(title)
        fields_str = '\n'.join(fields)
        input_area_parts.append(f'   <Group title="{escaped_title}">\n{fields_str}\n   </Group>')
    input_area_xml = "<InputArea>\n" + '\n'.join(input_area_parts) + "\n </InputArea>"

    # Combine into final UIContribution XML
    ui_contribution_xml = f"<UIContribution>\n{guide_area_xml}\n{input_area_xml}\n</UIContribution>"

    logger.info(f"Generated UIContribution XML for {len(contributions)} contributions.")
    return ui_contribution_xml

def main():
    """Example usage of the UI contribution generation functions."""
    # Example UI contributions
    ui_contributions = [
        {
            'feldgruppe': 'Mitglied',
            'dialog_variable': '$Dialog-Var1',
            'condition': '$Dialog-Var2 = Ja',
            'label': 'Name'
        },
        {
            'feldgruppe': 'Beitrag',
            'dialog_variable': '$Dialog-Var3',
            'condition': '',
            'label': 'Betrag'
        }
    ]
    
    # Generate UI contribution XML
    ui_contribution_xml = create_ui_contributions(ui_contributions, "Template", "0001")
    print("Generated UI Contribution XML:")
    print(ui_contribution_xml)

if __name__ == "__main__":
    main() 