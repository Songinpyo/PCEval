"""
Converter from Wokwi diagram format to Standardized Hardware Description Format (SHDF).

This module provides functions to convert Wokwi-specific hardware diagrams into
the platform-independent SHDF format, making them suitable for use in LLM prompts.

Terminology used in this module:
- shdf_component_type: Component type in SHDF format (e.g., "arduino uno")
- wokwi_component_type: Component type in Wokwi format (e.g., "wokwi-arduino-uno")
- shdf_component_id: Component ID in SHDF format (e.g., "arduino1")
- wokwi_component_id: Component ID in Wokwi format (same as SHDF, e.g., "arduino1")
- shdf_pin: Pin name in SHDF format (e.g., "pin13")
- wokwi_pin: Pin name in Wokwi format (e.g., "13")
"""

from .pin_mappings import wokwi_to_shdf_pin
from .type_mappings import wokwi_to_shdf_type


def convert_wokwi_to_standard(wokwi_diagram, mode="logical"):
    """
    Convert a Wokwi diagram to the Standardized Hardware Description Format (SHDF).

    Args:
        wokwi_diagram: A dictionary containing the Wokwi diagram
        mode: "logical" for abstract circuit or "physical" for breadboard layout

    Returns:
        A dictionary in the SHDF format
    """
    standard_format = {
        "components": [],
        "connections": []
    }

    # Process components
    for part in wokwi_diagram.get("parts", []):
        # Skip breadboard in logical mode
        if mode == "logical" and part["type"] == "wokwi-breadboard":
            continue

        # Convert Wokwi component type to SHDF type
        component_id = part["id"]
        wokwi_component_type = part["type"]
        
        if wokwi_component_type == "wokwi-7segment" and part.get("attrs", {}).get("digits", "") == "4":
            wokwi_component_type = "4-digit wokwi-7segment"
            part["attrs"] = {}
        
        shdf_component_type = wokwi_to_shdf_type(wokwi_component_type)

        # Create standardized component
        component = {
            "id": component_id,  # Component ID stays the same
            "type": shdf_component_type
        }

        # Extract relevant properties
        if "attrs" in part:
            properties = {}
            for key, value in part["attrs"].items():
                if key == "color":
                    properties["color"] = value.lower()
                elif key == "value" and shdf_component_type == "resistor":
                    # Standardize resistor values
                    if not value.endswith("ohm") and not value.endswith("Ω"):
                        properties["value"] = f"{value} ohm"
                    else:
                        properties["value"] = value
                elif key in ["label", "frequency", "threshold"]:
                    # Include other relevant properties
                    properties[key] = value

            if properties:
                component["properties"] = properties

        standard_format["components"].append(component)

    # Process connections
    for conn in wokwi_diagram.get("connections", []):
        if len(conn) >= 2:
            wokwi_from_point = conn[0]
            wokwi_to_point = conn[1]

            # Skip breadboard-only connections in logical mode
            if mode == "logical" and ("breadboard" in wokwi_from_point and "breadboard" in wokwi_to_point):
                continue

            # Process the connection points
            shdf_from_point = _convert_connection_point(wokwi_from_point, mode)
            shdf_to_point = _convert_connection_point(wokwi_to_point, mode)

            if shdf_from_point and shdf_to_point:
                standard_format["connections"].append([shdf_from_point, shdf_to_point])

    return standard_format


def _convert_connection_point(wokwi_point, mode):
    """
    Convert a Wokwi connection point to the SHDF format.

    Args:
        wokwi_point: The Wokwi connection point (e.g., "arduino uno1:13")
        standard format: SHDF
        mode: "logical" or "physical"

    Returns:
        SHDF connection point or None if it should be skipped
    """
    
    # Handle breadboard connections
    if "breadboard" in wokwi_point:
        if mode == "logical":
            return None  # Skip breadboard in logical mode
        else:
            # if p or n is in the point
            if "p" in wokwi_point or "n" in wokwi_point: # top, bottom rail
                
                bb_parts = wokwi_point.split(":", 1)[1].split(".") # ['breadboard', 'tn.1']
                if len(bb_parts) == 2:
                    row, col_side = bb_parts
                    col = ''.join(c for c in col_side if c.isdigit())
                    return f"breadboard.{col}{row}"
                else:
                    raise ValueError(f"Invalid breadboard point: {wokwi_point}")
            
            else: # column side
                bb_parts = wokwi_point.split(":", 1)[1].split(".", 1) # ['breadboard', '10t.a']
                if len(bb_parts) == 2:
                    col_side, row = bb_parts
                    col = ''.join(c for c in col_side if c.isdigit())
                    return f"breadboard.{col}{row}" # breadbaord:10t.a -> 
                else:
                    raise ValueError(f"Invalid breadboard point: {wokwi_point}")

    # Handle component pins
    elif ":" in wokwi_point:
        component_id, wokwi_pin = wokwi_point.split(":", 1)

        # Standardize pin names using the mapping and convert to lowercase
        shdf_pin = wokwi_to_shdf_pin(component_id, wokwi_pin).lower()
        return f"{component_id}.{shdf_pin}"

    return wokwi_point  # Return as-is if no conversion needed


if __name__ == "__main__":
    # Simple test case
    test_wokwi = {
        "version": 1,
        "parts": [
            {"id": "uno1", "type": "wokwi-arduino-uno", "top": 200, "left": 20},
            {"id": "led1", "type": "wokwi-led", "top": 100, "left": 150, "attrs": {"color": "red"}}
        ],
        "connections": [
            ["uno1:13", "led1:A", "green", []],
            ["led1:C", "uno1:GND.1", "black", []]
        ]
    }

    result = convert_wokwi_to_standard(test_wokwi)
    import json
    print(json.dumps(result, indent=2))
