"""
Script generation module for templify.
Handles generation of JavaScript scripts using Claude API.
"""

import json
import logging
import requests
import time
from typing import Dict, List, Optional

from templify.utils.logger_setup import setup_logger
from templify.utils.config import get_default_headers, get_default_payload, CLAUDE_API_URL, REQUEST_TIMEOUT

# Initialize logger
logger = setup_logger(__name__, log_level=logging.INFO)

def generate_scripts(
    script_descriptions: Dict[str, str],
    template_name: str,
    variant_number: str = "0001"
) -> Dict[str, str]:
    """
    Generate JavaScript scripts for multiple variables using Claude API.
    
    Args:
        script_descriptions (Dict[str, str]): Dictionary mapping variable names to their script descriptions
        template_name (str): The template name (e.g., 'FRW060')
        variant_number (str): The variant number (e.g., '0001')
        
    Returns:
        Dict[str, str]: Dictionary mapping variable names to their generated scripts
    """
    if not script_descriptions:
        logger.info("No script descriptions provided")
        return {}
    
    logger.info(f"Generating scripts for {len(script_descriptions)} variables")
    
    # Prepare the prompt content for Claude
    prompt_content = f"""
    I need you to write JavaScript scripts for use in a document template system. 
    
    The scripts need to be compatible with the .rhino.1.2 JavaScript engine.
    
    REQUIREMENTS:
    - Use only basic JavaScript features: var, if/else, return, basic math
    - NO ternary operators (? :), NO arrow functions, NO template literals
    - NO array methods (map, filter, etc.), NO object destructuring
    - NO try/catch blocks, NO async/await
    - Keep scripts as simple as possible
    - Use clear variable names
    - Always declare variables with 'var'
    - Always use explicit if/else statements
    - Always return the final result at the end
    - Variables from the document are accessed through $document.{template_name}.Dialog._{variant_number}.[Variable_Name]
    - For date values, use .valueOf().getTime() to get the timestamp
    - For date calculations, use basic math with milliseconds (e.g., 1000 * 60 * 60 * 24 for days)
    
    Here are the script descriptions to process:
    {json.dumps(script_descriptions, indent=2)}
    
    Return the data as a JSON object where each key is the variable name and the value is the generated script.
    Only include the JSON in your response, no other text.
    
    EXAMPLES OF GOOD SCRIPTS:
    
    Example 1 (Date difference calculation):
    ```javascript
    var datum1 = $document.FRW060.Dialog._0002.Dialog_Variable5.valueOf().getTime();
    var datum2 = $document.FRW060.Dialog._0002.Dialog_Variable4.valueOf().getTime();
    var diff = datum1 - datum2;
    var tage = diff / (1000 * 60 * 60 * 24) + 1;
    return tage;
    ```
    
    Example 2 (Conditional text):
    ```javascript
    var text = "";
    if ($Variable1_Tage1 == 1) {{
        text = "Tag";
    }} else if ($Variable1_Tage1 > 1) {{
        text = "Tage";
    }}
    return text;
    ```
    
    Example 3 (Simple condition):
    ```javascript
    var result = "";
    if ($document.FRW060.Dialog._0001.Dialog_Variable1 == "Ja") {{
        result = "freiwillig";
    }}
    return result;
    ```
    """
    
    try:
        # Prepare the API request
        headers = get_default_headers()
        payload = get_default_payload(prompt_content)
        
        # Add extra time for the API call
        time.sleep(1.3)
        
        # Make the API request
        logger.debug("Sending request to Claude API for script generation")
        response = requests.post(
            CLAUDE_API_URL,
            headers=headers,
            json=payload,
            timeout=REQUEST_TIMEOUT
        )
        
        # Check if the request was successful
        response.raise_for_status()
        
        # Parse the response
        claude_response = response.json()
        result_text = claude_response['content'][0]['text']
        
        logger.debug("Received response from Claude API")
        
        # Extract the JSON part from Claude's response
        try:
            # Try to find JSON in the response
            start_idx = result_text.find('{')
            end_idx = result_text.rfind('}') + 1
            
            if start_idx >= 0 and end_idx > start_idx:
                json_str = result_text[start_idx:end_idx]
                generated_scripts = json.loads(json_str)
            else:
                # If no JSON object found, try parsing the whole response
                generated_scripts = json.loads(result_text)
                
            logger.info(f"Successfully generated scripts for {len(generated_scripts)} variables")
            for var_name in generated_scripts:
                logger.debug(f"Generated script for {var_name}")
                
            return generated_scripts
                
        except json.JSONDecodeError:
            logger.error("Error parsing Claude's response as JSON")
            logger.debug(f"Raw response: {result_text}")
            return {}
        
    except Exception as e:
        logger.error(f"Error calling Claude API for script generation: {str(e)}")
        return {}

def main():
    """Test function to demonstrate script generation."""
    # Example script descriptions
    script_descriptions = {
        "Variable1": "Return 'freiwillig' if Dialog-Variable1 is 'Ja', otherwise return empty string",
        "Variable2": "Calculate the difference in days between Dialog-Variable3 and Dialog-Variable4",
        "Variable3": "Return 'Tag' if the value is 1, 'Tage' if greater than 1"
    }
    
    # Generate scripts
    generated_scripts = generate_scripts(
        script_descriptions,
        template_name="FRWT100",
        variant_number="0001"
    )
    
    # Print results
    print("\nGenerated Scripts:")
    print("-" * 50)
    for var_name, script in generated_scripts.items():
        print(f"\n{var_name}:")
        print(script)
        print("-" * 50)

if __name__ == "__main__":
    main()
