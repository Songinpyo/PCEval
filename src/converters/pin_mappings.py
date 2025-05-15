"""
Pin name mappings between Wokwi and SHDF formats.

This module provides bidirectional mappings for converting pin names between Wokwi's format
and the Standardized Hardware Description Format (SHDF).

The mappings are loaded from module_info.json, which contains information about all supported
components, including their pins and pin aliases.

Terminology used in this module:
- shdf_component_type: Component type in SHDF format (e.g., "arduino uno")
- wokwi_component_type: Component type in Wokwi format (e.g., "wokwi-arduino-uno")
- shdf_pin: Pin name in SHDF format (e.g., "pin13")
- wokwi_pin: Pin name in Wokwi format (e.g., "13")
"""

import json
import re
from pathlib import Path

# Bidirectional pin mappings
# Format: {shdf_component_type: {wokwi_pin: shdf_pin, ...}}
PIN_MAPPINGS = {}

# Initialize aliases for pin names (different ways to express the same pin)
PIN_NAME_ALIASES = {}

# Initialize reverse mappings
REVERSE_PIN_MAPPINGS = {}

# Initialize aliases for component types (different ways to express the same component type)
COMPONENT_TYPE_ALIASES = {}

def load_module_info():
    """
    Load component information from the module_info.json file.

    Returns:
        A dictionary mapping shdf_component_type to their pin information.
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
                shdf_component_type = component.get("shdf_type", "").lower()
                component_dict[shdf_component_type] = component

        return component_dict
    except Exception as e:
        print(f"Error loading module info: {e}")
        return {}

def update_pin_mappings_from_module_info():
    """
    Update the PIN_MAPPINGS, PIN_NAME_ALIASES, REVERSE_PIN_MAPPINGS, COMPONENT_TYPE_ALIASES dictionaries with information from module_info.json.
    """
    global PIN_MAPPINGS, PIN_NAME_ALIASES, REVERSE_PIN_MAPPINGS, COMPONENT_TYPE_ALIASES

    # Clear existing mappings
    PIN_MAPPINGS = {}

    # Initialize PIN_NAME_ALIASES with common aliases
    PIN_NAME_ALIASES = {}

    component_info = load_module_info()

    # Update pin mappings based on component info
    for shdf_component_type, component in component_info.items():
        # Create a new mapping for this component type
        PIN_MAPPINGS[shdf_component_type] = {}
        PIN_NAME_ALIASES[shdf_component_type] = {}
        REVERSE_PIN_MAPPINGS[shdf_component_type] = {}

        COMPONENT_TYPE_ALIASES[shdf_component_type] = shdf_component_type
        for alias in component.get("shdf_type_aliases", []):
            COMPONENT_TYPE_ALIASES[alias.lower()] = shdf_component_type

        # Add pin mappings based on the component info
        for pin_info in component.get("pins", []):
            wokwi_pin = pin_info.get("pin_name", "")
            description = pin_info.get("description", "")
            pin_aliases = pin_info.get("pin_aliases", [])

            if wokwi_pin and description:
                # Convert the pin name to a standardized format for SHDF
                
                if wokwi_pin.isdigit():
                    shdf_pin = f"pin{wokwi_pin}"
                elif shdf_component_type in ["arduino uno", "7-segment display"]:
                    result = ""
                    for char in wokwi_pin:
                        if char.isdigit():
                            result += char
                        elif char == '.':
                            continue
                        else:
                            result += char.lower()
                    shdf_pin = result
                elif "." in wokwi_pin:
                    prefix, suffix = wokwi_pin.split(".")
                    prefix = "pin" + prefix if prefix.isdigit() else prefix.lower()
                    suffix = "pin" + suffix if suffix.isdigit() else suffix.lower()
                    shdf_pin = f"{prefix}.{suffix}"
                else:
                    shdf_pin = wokwi_pin.lower()
                    
                # Add the mapping
                PIN_MAPPINGS[shdf_component_type][wokwi_pin] = shdf_pin
                REVERSE_PIN_MAPPINGS[shdf_component_type][shdf_pin] = wokwi_pin

                # Add aliases to PIN_NAME_ALIASES
                PIN_NAME_ALIASES[shdf_component_type][shdf_pin.lower()] = shdf_pin
                for alias in pin_aliases:
                    PIN_NAME_ALIASES[shdf_component_type][alias.lower()] = shdf_pin

def wokwi_to_shdf_pin(component_id, wokwi_pin):
    """
    Convert a Wokwi pin name to SHDF format.

    Args:
        component_id: Component id (e.g., "arduino uno1")
        wokwi_pin: The Wokwi pin name (e.g., "13")

    Returns:
        The SHDF pin name (e.g., "pin13")
    """
    # Convert to lowercase for case-insensitive lookup
    wokwi_pin_lower = wokwi_pin.lower()
    wokwi_component_type = re.sub(r'\d+$', '', component_id)

    try:
        shdf_component_type = COMPONENT_TYPE_ALIASES[wokwi_component_type.lower()]
    except Exception as e:
        print("Component type is not in aliases (wokwi to shdf):", shdf_component_type)
    
    # Check component-specific mappings if provided
    if shdf_component_type in PIN_MAPPINGS:
        component_mappings = PIN_MAPPINGS[shdf_component_type]
        if wokwi_pin in component_mappings or wokwi_pin_lower in component_mappings:
            # Try with original pin name first, then with lowercase
            pin_to_use = wokwi_pin if wokwi_pin in component_mappings else wokwi_pin_lower
            shdf_pin = component_mappings[pin_to_use]
            return shdf_pin

    # If no mapping found, return as is
    return wokwi_pin

def shdf_to_wokwi_pin(shdf_pin, shdf_component_type):
    """
    Convert an SHDF pin name to Wokwi format.

    Args:
        shdf_pin: The SHDF pin name (e.g., "pin13")
        shdf_component_type: The SHDF component type (e.g., "arduino uno")

    Returns:
        The Wokwi pin name (e.g., "13")
    """
    # Convert to lowercase for case-insensitive lookup
    shdf_pin_lower = shdf_pin.lower()

    try:
        shdf_component_type = COMPONENT_TYPE_ALIASES[shdf_component_type.lower()]
    except Exception as e:
        print("\033[91mComponent type is not in aliases (shdf to wokwi):", shdf_component_type, "\033[0m")

    # Check if this is an alias and convert to standard form
    try:
        shdf_pin_lower = PIN_NAME_ALIASES[shdf_component_type][shdf_pin_lower]
    except Exception as e:
        print("\033[91mPin name is not in aliases (shdf to wokwi):", shdf_component_type, shdf_pin_lower, "\033[0m")

    # Check component-specific mappings if provided
    component_mappings = REVERSE_PIN_MAPPINGS[shdf_component_type]
    return component_mappings[shdf_pin_lower]

def get_all_pin_patterns():
    """
    Get all pin patterns for all component types.

    Returns:
        A dictionary mapping component types to lists of regex patterns for valid pin names.
    """
    import re
    pin_patterns = {}

    # Add patterns for all component types in PIN_MAPPINGS (SHDF)
    for shdf_component_type, mappings in PIN_MAPPINGS.items():
        pin_patterns[shdf_component_type] = []

        # Add patterns for all pins
        for _, shdf_pin in mappings.items():
            pattern = f"^{re.escape(shdf_pin.lower())}$"
            if pattern not in pin_patterns[shdf_component_type]:
                pin_patterns[shdf_component_type].append(pattern)

    # Add patterns for all pins in PIN_NAME_ALIASES
    for shdf_component_type, mappings in PIN_NAME_ALIASES.items():
        if shdf_component_type not in pin_patterns:
            pin_patterns[shdf_component_type] = []

        for alias, _ in mappings.items():
            pattern = f"^{re.escape(alias.lower())}$"
            if pattern not in pin_patterns[shdf_component_type]:
                pin_patterns[shdf_component_type].append(pattern)

    return pin_patterns

# Update pin mappings with module info
update_pin_mappings_from_module_info()

# Export the mappings
__all__ = ["PIN_MAPPINGS", "REVERSE_PIN_MAPPINGS", "PIN_NAME_ALIASES", "COMPONENT_TYPE_ALIASES",
           "wokwi_to_shdf_pin", "shdf_to_wokwi_pin", "get_all_pin_patterns"]