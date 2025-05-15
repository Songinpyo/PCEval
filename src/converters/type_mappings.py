#!/usr/bin/env python3
"""
Component type mappings between Wokwi and SHDF formats.

This module provides bidirectional mappings for converting component types between Wokwi's format
and the Standardized Hardware Description Format (SHDF).

The mappings are loaded from module_info.json, which contains information about all supported
components, including their Wokwi types, SHDF types, and aliases.

Terminology used in this module:
- shdf_component_type: Component type in SHDF format (e.g., "arduino uno")
- wokwi_component_type: Component type in Wokwi format (e.g., "wokwi-arduino-uno")
"""

import json
from pathlib import Path

# Initialize empty mappings
# Format: {wokwi_component_type: shdf_component_type}
TYPE_MAPPINGS = {}
SHDF_TYPE_ALIASES = {}

# Build reverse mappings
# Format: {shdf_component_type: wokwi_component_type}
REVERSE_TYPE_MAPPINGS = {shdf_component_type: wokwi_component_type for wokwi_component_type, shdf_component_type in TYPE_MAPPINGS.items()}

def load_module_info():
    """
    Load component information from the module_info.json file.

    Returns:
        A dictionary mapping wokwi_component_type to their information.
    """
    # Find the module_info.json file
    current_dir = Path(__file__).resolve().parent
    module_info_path = current_dir / "module_info.json"

    if not module_info_path.exists():
        print(f"Warning: Module info file not found at {module_info_path}")
        return {}

    try:
        with open(module_info_path, "r") as f:
            module_info = json.load(f)

        # Convert to a dictionary for easier lookup
        component_dict = {}
        for component in module_info:
            wokwi_component_type = component.get("wokwi_type", "")
            if wokwi_component_type:
                component_dict[wokwi_component_type] = component

        return component_dict
    except Exception as e:
        print(f"Error loading module info: {e}")
        return {}

def update_type_mappings_from_module_info():
    """
    Update the TYPE_MAPPINGS and SHDF_TYPE_ALIASES dictionaries with information from module_info.json.
    """
    global TYPE_MAPPINGS, SHDF_TYPE_ALIASES, REVERSE_TYPE_MAPPINGS

    # Clear existing mappings
    TYPE_MAPPINGS = {}
    SHDF_TYPE_ALIASES = {}

    component_info = load_module_info()

    # Update type mappings based on component info
    for wokwi_component_type, component in component_info.items():
        # Get the component name (SHDF type)
        shdf_component_type = component.get("shdf_type", "").lower()

        # Add the mapping
        TYPE_MAPPINGS[wokwi_component_type] = shdf_component_type

        # Add aliases if available
        SHDF_TYPE_ALIASES[shdf_component_type] = shdf_component_type
        aliases = component.get("shdf_type_aliases", [])
        for alias in aliases:
            SHDF_TYPE_ALIASES[alias.lower()] = shdf_component_type

    # Rebuild reverse mappings
    REVERSE_TYPE_MAPPINGS = {shdf_component_type: wokwi_component_type for wokwi_component_type, shdf_component_type in TYPE_MAPPINGS.items()}

# Update type mappings with module info
update_type_mappings_from_module_info()

def wokwi_to_shdf_type(wokwi_component_type):
    """
    Convert a Wokwi component type to SHDF type.

    Args:
        wokwi_component_type: The Wokwi component type (e.g., "wokwi-arduino-uno")

    Returns:
        The corresponding SHDF type (e.g., "arduino uno")
    """
    # Check if the type is in our mappings
    if wokwi_component_type in TYPE_MAPPINGS:
        return TYPE_MAPPINGS[wokwi_component_type]

    # If not, create a standardized type name
    return wokwi_component_type.replace("wokwi-", "").lower().replace("-", " ")

def shdf_to_wokwi_type(shdf_component_type):
    """
    Convert an SHDF component type to Wokwi type.

    Args:
        shdf_component_type: The SHDF component type (e.g., "arduino uno")

    Returns:
        The corresponding Wokwi type (e.g., "wokwi-arduino-uno")
    """

    # Check if the type is in our mappings
    if shdf_component_type in REVERSE_TYPE_MAPPINGS:
        return REVERSE_TYPE_MAPPINGS[shdf_component_type]

    # If not, create a Wokwi type name
    return f"wokwi-{shdf_component_type.replace(' ', '-')}"

def shdf_alias_check(shdf_component_type):
    try:
        return SHDF_TYPE_ALIASES[shdf_component_type]
    except Exception as e:
        return shdf_component_type

def get_all_component_types():
    """
    Get all component types from TYPE_MAPPINGS and SHDF_TYPE_ALIASES.

    Returns:
        A set of all shdf_component_type values in lowercase.
    """
    component_types = set()

    # Add all SHDF types from TYPE_MAPPINGS
    for _, shdf_component_type in TYPE_MAPPINGS.items():
        component_types.add(shdf_component_type.lower())

    # Add all aliases
    for alias, _ in SHDF_TYPE_ALIASES.items():
        component_types.add(alias.lower())

    return component_types


# Export the mappings
__all__ = ["TYPE_MAPPINGS", "REVERSE_TYPE_MAPPINGS", "SHDF_TYPE_ALIASES",
           "wokwi_to_shdf_type", "shdf_to_wokwi_type", "get_all_component_types"]
