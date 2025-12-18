"""
Modification rights generation module for templify.
"""

from typing import List, Dict, Optional, Any
from templify.utils.logger_setup import setup_logger


# Initialize logger
logger = setup_logger(__name__)

def create_modificationright(
    role: str,
    operations: str,
    **additional_attrs: Any
) -> str:
    """
    Creates a single ModificationRight XML element.
    
    Args:
        role: Role name (required)
        operations: Comma-separated list of operations (required)
        additional_attrs: Any additional attributes to include
        
    Returns:
        str: XML representation of the ModificationRight element
        
    Examples:
        >>> create_modificationright("_EVERYONE_", "EDIT,INPUT")
        '<ModificationRight role="_EVERYONE_" operations="EDIT,INPUT"></ModificationRight>'
        
        >>> create_modificationright("admin", "EDIT,DELETE,VIEW")
        '<ModificationRight role="admin" operations="EDIT,DELETE,VIEW"></ModificationRight>'
    """
    # Validate required parameters
    if not role:
        raise ValueError("Role is required")
    if not operations:
        raise ValueError("Operations are required")
    
    # Build attributes dictionary
    attrs = {
        'role': role,
        'operations': operations
    }
    
    # Add any additional attributes
    attrs.update(additional_attrs)
    
    # Format all attributes for XML
    formatted_attrs = [f'{key}="{value}"' for key, value in attrs.items()]
    attr_string = " ".join(formatted_attrs)
    
    # Build the final XML
    return f'<ModificationRight {attr_string}></ModificationRight>'

def create_modificationrights(
    allowed_rights: Optional[List[Dict[str, Any]]] = None,
    denied_rights: Optional[List[Dict[str, Any]]] = None
) -> str:
    """
    Create a complete ModificationRights XML structure with Allowed and Denied sections.
    
    Args:
        allowed_rights: List of allowed modification right dictionaries with keys 
                       corresponding to create_modificationright parameters.
        denied_rights: Optional list of denied modification right dictionaries with keys
                      corresponding to create_modificationright parameters.
    
    Returns:
        str: Complete ModificationRights XML string.
        
    Examples:
        >>> create_modificationrights([{"role": "_EVERYONE_", "operations": "EDIT,INPUT"}])
        '<ModificationRights>
          <Allowed>
            <ModificationRight role="_EVERYONE_" operations="EDIT,INPUT"></ModificationRight>
          </Allowed>
          <Denied></Denied>
        </ModificationRights>'
        
        >>> create_modificationrights(
        ...     [
        ...         {"role": "_EVERYONE_", "operations": "EDIT,INPUT"},
        ...         {"role": "admin", "operations": "DELETE,MODIFY"}
        ...     ],
        ...     [
        ...         {"role": "guest", "operations": "EDIT"}
        ...     ]
        ... )
        '<ModificationRights>
          <Allowed>
            <ModificationRight role="_EVERYONE_" operations="EDIT,INPUT"></ModificationRight>
            <ModificationRight role="admin" operations="DELETE,MODIFY"></ModificationRight>
          </Allowed>
          <Denied>
            <ModificationRight role="guest" operations="EDIT"></ModificationRight>
          </Denied>
        </ModificationRights>'
    """
    
    # Generate Allowed elements
    allowed_elements = []
    if allowed_rights:
        for right in allowed_rights:
            # Create a copy of the dict to avoid modifying the original
            right_copy = right.copy()
            allowed_elements.append(create_modificationright(**right_copy))
    
    # Generate Denied elements
    denied_elements = []
    if denied_rights:
        for right in denied_rights:
            # Create a copy of the dict to avoid modifying the original
            right_copy = right.copy()
            denied_elements.append(create_modificationright(**right_copy))
    
    # Build Allowed section
    if allowed_elements:
        allowed_xml = "\n    ".join(allowed_elements)
        allowed_section = f'<Allowed>\n    {allowed_xml}\n  </Allowed>'
    else:
        allowed_section = '<Allowed></Allowed>'
    
    # Build Denied section
    if denied_elements:
        denied_xml = "\n    ".join(denied_elements)
        denied_section = f'<Denied>\n    {denied_xml}\n  </Denied>'
    else:
        denied_section = '<Denied></Denied>'
    
    # Combine sections
    return f'<ModificationRights>\n  {allowed_section}\n  {denied_section}\n</ModificationRights>'

def create_default_modificationrights() -> str:
    """
    Create default ModificationRights with _EVERYONE_ having EDIT,INPUT operations.
    
    Returns:
        str: Default ModificationRights XML string.
        
    Example:
        >>> create_default_modificationrights()
        '<ModificationRights>
          <Allowed>
            <ModificationRight role="_EVERYONE_" operations="EDIT,INPUT"></ModificationRight>
          </Allowed>
          <Denied></Denied>
        </ModificationRights>'
    """
    default_allowed = [
        {
            'role': '_EVERYONE_',
            'operations': 'EDIT,INPUT'
        }
    ]
    
    return create_modificationrights(allowed_rights=default_allowed)

def main():
    """Example usage of the modification rights generation functions."""
    logger.debug("Demonstrating ModificationRights generation functions")
    
    # Example 1: Default rights
    default_rights = create_default_modificationrights()
    logger.debug("Generated Default ModificationRights XML: %s", default_rights)
    
    # Example 2: Custom rights with multiple allowed and denied
    allowed_rights = [
        {
            'role': '_EVERYONE_',
            'operations': 'EDIT,INPUT'
        },
        {
            'role': 'admin',
            'operations': 'EDIT,DELETE,MODIFY,VIEW'
        }
    ]
    
    denied_rights = [
        {
            'role': 'guest',
            'operations': 'DELETE,MODIFY'
        }
    ]
    
    custom_rights = create_modificationrights(allowed_rights, denied_rights)
    logger.debug("Generated Custom ModificationRights XML: %s", custom_rights)
    
    # Example 3: Single modification right
    single_right = create_modificationright('user', 'VIEW,EDIT')
    logger.debug("Generated Single ModificationRight XML: %s", single_right)

if __name__ == "__main__":
    main()
