"""
Condition generation module for templify.
"""

import os
import time
import re
import xml.etree.ElementTree as ET
from typing import List, Dict, Optional
from pathlib import Path
from templify.utils.logger_setup import setup_logger
from templify.utils.claude_call import call_claude
from templify.parser.get_data import get_output_dir

# Initialize logger
logger = setup_logger(__name__)

def load_datamodel(template_name: str) -> Dict[str, List[str]]:
    """
    Load the datamodel file for the given template and extract variable paths.
    
    Args:
        template_name (str): The name of the template (e.g., 'FRW060')
        
    Returns:
        Dict[str, List[str]]: Dictionary mapping variant numbers to lists of variable paths
    """
    result = {}
    try:
        # Construct the path to the datamodel file
        output_dir = get_output_dir(template_name)
        datamodel_path = output_dir / "Daten" / f"{template_name}.datamodel"
        # Parse the XML file
        tree = ET.parse(datamodel_path)
        root = tree.getroot()
        
        # Find the Dialog and Aufbereitet nodes
        dialog_node = root.find(".//Node[@name='Dialog']")
        aufbereitet_node = root.find(".//Node[@name='Aufbereitet']")
        
        if dialog_node is not None:
            # Extract variant nodes (e.g., _0001, _0002, etc.)
            for variant_node in dialog_node.findall("./Node"):
                variant_number = variant_node.get("name", "").strip("_")
                if not variant_number or not re.match(r'^\d{4}$', variant_number):
                    continue
                    
                dialog_variables = []
                # Extract dialog variable names
                for var_node in variant_node.findall("./Node"):
                    var_name = var_node.get("name", "")
                    if var_name:
                        # Format as template_name.Dialog._variant.var_name
                        path = f"${template_name}.Dialog._{variant_number}.{var_name.replace('$Dialog-', 'Dialog_')}"
                        dialog_variables.append(path)
                
                if variant_number not in result:
                    result[variant_number] = []
                result[variant_number].extend(dialog_variables)
        
        if aufbereitet_node is not None:
            # Extract variant nodes for Aufbereitet
            for variant_node in aufbereitet_node.findall("./Node"):
                variant_number = variant_node.get("name", "").strip("_")
                if not variant_number or not re.match(r'^\d{4}$', variant_number):
                    continue
                    
                aufbereitet_variables = []
                # Extract aufbereitet variable names
                for var_node in variant_node.findall("./Node"):
                    var_name = var_node.get("name", "")
                    if var_name:
                        # Format as template_name.Aufbereitet._variant.var_name
                        path = f"${template_name}.Aufbereitet._{variant_number}.{var_name}"
                        aufbereitet_variables.append(path)
                
                if variant_number not in result:
                    result[variant_number] = []
                result[variant_number].extend(aufbereitet_variables)
                
        logger.info(f"Loaded {sum(len(vars) for vars in result.values())} variable paths from datamodel")
        return result
        
    except Exception as e:
        logger.error(f"Error loading datamodel for {template_name}: {e}")
        return {}

def generate_condition(raw_conditions: List[str], template_name: str, variant_number: str) -> List[str]:
    """
    Convert raw condition strings into JavaScript conditions using Claude.
    
    Args:
        raw_conditions (List[str]): List of raw condition strings
        template_name (str): The template name (e.g., 'FRW060')
        variant_number (str): The variant number (e.g., '0001')
        
    Returns:
        List[str]: List of JavaScript conditions
    """
    js_conditions = []
    if not raw_conditions:
        return js_conditions

    # Load variable paths from datamodel for context
    all_variable_paths = load_datamodel(template_name)
    variable_paths = all_variable_paths.get(variant_number, [])
    
    # Generate conditions one by one
    for raw_condition in raw_conditions:
        if not raw_condition or not isinstance(raw_condition, str):
            js_conditions.append(f"// Skipped empty/invalid condition\nfalse;")
            continue
            
        # Create the prompt for Claude
        prompt_template = f"""
I need you to write a JavaScript condition for use in a document template system.

The condition needs to be compatible with the .rhino.1.2 JavaScript engine.

REQUIREMENTS:
- Generate valid JavaScript code, focused on simplicity
- Variables from the document are accessed through ${template_name}.Dialog._{variant_number}.[Variable_Name]
- DO NOT use $document prefix, start directly with the variable path
- For Dialog variables (those mentioned as "$Dialog-Something" in the condition):
  * ALWAYS use the format: ${template_name}.Dialog._{variant_number}.Dialog_VariableName
  * Note that "Dialog_" must be part of the variable name
- For other variables (those not starting with "$Dialog-"):
  * Use the format: ${template_name}.Aufbereitet._{variant_number}.VariableName
- Return date values with .valueOf().getTime() to get the timestamp
- For calculations with dates, use milliseconds (e.g., 1000 * 60 * 60 * 24 for days)
- When the condition description mentions a variable equals "Ja", this means the variable should be checked for true
- Create a single line condition which is a logical condition, typically ending with a semicolon.

AVAILABLE VARIABLES FROM DATAMODEL:
{', '.join(variable_paths)}

Here are some examples of good conditions:

Example 1 (Multiple value check):
```javascript
$FRW060.Dialog._0002.Dialog_Variable3.valueOf()==2 || $FRW060.Dialog._0002.Dialog_Variable3.valueOf()==3 || $FRW060.Dialog._0002.Dialog_Variable3.valueOf()==4 || $FRW060.Dialog._0002.Dialog_Variable3.valueOf()==5;
```

Example 2 (Boolean check with "Ja"):
```javascript
$FRW060.Dialog._0002.Dialog_Variable14.valueOf()==true;
```

Here's the condition description to implement:
{raw_condition}

Only provide the JavaScript code in your response, nothing else.
"""
        
        try:
            # Simple rate limiting
            time.sleep(1.0)
            
            # Call Claude with the prompt
            result_text = call_claude(prompt=prompt_template)

            # Clean up the response
            if "```" in result_text:
                if "```javascript" in result_text:
                    result_text = result_text.split("```javascript")[1].split("```")[0]
                elif "```js" in result_text:
                    result_text = result_text.split("```js")[1].split("```")[0]
                else:
                    parts = result_text.split("```", 2)
                    if len(parts) > 1:
                        result_text = parts[1].split("```")[0]
            
            result_text = result_text.strip()
            result_text = result_text.replace('$document.', '$')
            
            # Handle empty results
            if not result_text:
                js_conditions.append(f"false;")
                continue

            # Ensure the condition ends with a semicolon
            if not result_text.endswith(';') and not result_text.endswith('}'):
                result_text += ';'
                
            js_conditions.append(result_text)
            logger.debug(f"Generated condition: {result_text}")

        except Exception as e:
            # Simple fallback on error
            logger.warning(f"Error generating condition: {str(e)}")
            js_conditions.append("false;")
            
    return js_conditions

def generate_conditions_batch(
    condition_map: Dict[str, str], 
    template_name: str, 
    variant_number: str
) -> Dict[str, str]:
    """
    Generate JavaScript conditions for multiple conditions using Claude API.
    
    Args:
        condition_map (Dict[str, str]): Dictionary mapping condition IDs to raw condition strings
        template_name (str): The template name (e.g., 'FRW060')
        variant_number (str): The variant number (e.g., '0001')
        
    Returns:
        Dict[str, str]: Dictionary mapping condition IDs to generated JavaScript conditions
    """
    if not condition_map:
        logger.info("No conditions provided for batch processing")
        return {}
    
    logger.info(f"Batch processing {len(condition_map)} conditions for {template_name} variant {variant_number}")
    
    # Load variable paths from datamodel for context
    all_variable_paths = load_datamodel(template_name)
    variable_paths = all_variable_paths.get(variant_number, [])
    
    # Prepare the prompt content for Claude
    variable_paths_str = '\n'.join(variable_paths)
    newline = '\n'
    double_newline = '\n\n'
    prompt_content = f"""
I need you to convert multiple condition descriptions into JavaScript conditions for use in a document template system.

The conditions need to be compatible with the .rhino.1.2 JavaScript engine.

REQUIREMENTS:
- Generate valid JavaScript code, focused on simplicity
- Use only basic JavaScript features: if/else, comparisons, logical operators (&&, ||)
- Variables from the document are accessed through their full path
- DO NOT use $document prefix, start directly with the variable path
- For Dialog variables (those mentioned as "$Dialog-Something" in the condition):
  * ALWAYS use the format: ${template_name}.Dialog._{variant_number}.Dialog_VariableName
  * Note that "Dialog_" must be part of the variable name
- For other variables (those not starting with "$Dialog-"):
  * Use the format: ${template_name}.Aufbereitet._{variant_number}.VariableName
- Return date values with .valueOf().getTime() to get the timestamp
- For calculations with dates, use milliseconds (e.g., 1000 * 60 * 60 * 24 for days)
- When the condition description mentions a variable equals "Ja", this means the variable should be checked for true
- Create a single line condition which is a logical condition, always ending with a semicolon

AVAILABLE VARIABLES FROM DATAMODEL:
{variable_paths_str}

Here are the condition descriptions to convert:
{
    double_newline.join([f"ID: {cond_id}{newline}Description: {raw_cond}" for cond_id, raw_cond in condition_map.items()])
}

Return the result as a JSON object where:
- Each key is the condition ID from the input
- Each value is the corresponding JavaScript condition code

Only include the JSON in your response, no other text.

EXAMPLES OF GOOD CONDITIONS:

Example 1 (Multiple value check):
```javascript
$FRW060.Dialog._0002.Dialog_Variable3.valueOf()==2 || $FRW060.Dialog._0002.Dialog_Variable3.valueOf()==3 || $FRW060.Dialog._0002.Dialog_Variable3.valueOf()==4 || $FRW060.Dialog._0002.Dialog_Variable3.valueOf()==5;
```

Example 2 (Boolean check with "Ja"):
```javascript
$FRW060.Dialog._0002.Dialog_Variable14.valueOf()==true;
```

Example 3 (Date comparison):
```javascript
$FRW060.Dialog._0002.Dialog_Variable5.valueOf().getTime() > $FRW060.Dialog._0002.Dialog_Variable4.valueOf().getTime();
```
"""
    
    try:
        # Simple rate limiting
        time.sleep(1.0)
        
        # Call Claude API
        result_text = call_claude(prompt=prompt_content)
        
        # Extract JSON from response
        try:
            # Look for JSON content
            json_start = result_text.find('{')
            json_end = result_text.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = result_text[json_start:json_end]
                generated_conditions = eval(json_str)  # Using eval since it's from Claude
            else:
                # Try the whole response
                generated_conditions = eval(result_text)
                
            # Process each condition to ensure it's formatted correctly
            for cond_id, condition in generated_conditions.items():
                condition = condition.strip()
                # Replace any $document. prefix
                condition = condition.replace('$document.', '$')
                # Ensure it ends with semicolon
                if not condition.endswith(';') and not condition.endswith('}'):
                    condition += ';'
                generated_conditions[cond_id] = condition
                
            logger.info(f"Successfully batch processed {len(generated_conditions)} conditions")
            return generated_conditions
                
        except Exception as e:
            logger.error(f"Error parsing batch conditions response: {str(e)}")
            logger.debug(f"Raw response: {result_text}")
            
            # Fallback to individual processing
            logger.info("Falling back to individual condition processing")
            result = {}
            for cond_id, raw_cond in condition_map.items():
                js_conditions = generate_condition([raw_cond], template_name, variant_number)
                if js_conditions:
                    result[cond_id] = js_conditions[0]
                else:
                    result[cond_id] = "false;"
            return result
            
    except Exception as e:
        logger.error(f"Error in batch condition generation: {str(e)}")
        # Fallback to individual processing
        logger.info("Falling back to individual condition processing after error")
        result = {}
        for cond_id, raw_cond in condition_map.items():
            try:
                js_conditions = generate_condition([raw_cond], template_name, variant_number)
                if js_conditions:
                    result[cond_id] = js_conditions[0]
                else:
                    result[cond_id] = "false;"
            except:
                result[cond_id] = "false;"
        return result

def main():
    """Example usage of the condition generation function."""
    example_conditions = {
        "cond1": "$Dialog-Variable1 = Ja",
        "cond2": "$Dialog-Variable2 = Nein",
        "cond3": "$AufbereitetVar > 5 AND $Dialog-Checkbox = Ja",
        "cond4": "$Dialog-Datum < today"
    }
    
    # Test batch processing
    print("\nBatch processing example:")
    batch_results = generate_conditions_batch(example_conditions, "FRW060", "0001")
    for cond_id, js_condition in batch_results.items():
        print(f"\nID: {cond_id}")
        print(f"Original: {example_conditions[cond_id]}")
        print(f"Generated: {js_condition}")
    
    # Also demonstrate the original function
    print("\nIndividual processing example:")
    individual_results = generate_condition(list(example_conditions.values()), "FRW060", "0001")
    for i, (orig, js) in enumerate(zip(example_conditions.values(), individual_results)):
        print(f"\nOriginal {i+1}: {orig}")
        print(f"Generated: {js}")

if __name__ == "__main__":
    main()
