"""
Converter from Standardized Hardware Description Format (SHDF) to Wokwi diagram format.

This module provides functions to convert platform-independent SHDF hardware diagrams
into Wokwi-specific format for simulation and testing.

Terminology used in this module:
- shdf_component_type: Component type in SHDF format (e.g., "arduino uno")
- wokwi_component_type: Component type in Wokwi format (e.g., "wokwi-arduino-uno")
- shdf_component_id: Component ID in SHDF format (e.g., "arduino1")
- wokwi_component_id: Component ID in Wokwi format (same as SHDF, e.g., "arduino1")
- shdf_pin: Pin name in SHDF format (e.g., "pin13")
- wokwi_pin: Pin name in Wokwi format (e.g., "13")
"""

import json
import hashlib
import re
import sys
from .pin_mappings import shdf_to_wokwi_pin
from .type_mappings import shdf_to_wokwi_type, shdf_alias_check


def convert_standard_to_wokwi(standard_diagram, mode="logical"):
    """
    Convert a standardized hardware description to Wokwi format.

    Args:
        standard_diagram: A dictionary in the SHDF format
        mode: "logical" for abstract circuit or "physical" for breadboard layout

    Returns:
        A Wokwi-compatible diagram as a dictionary
    """
    # Initialize Wokwi diagram
    wokwi_diagram = {
        "version": 1,
        "author": "Arduino-LLM",
        "editor": "Inpyo Song and Eunji Jeon",
        "parts": [],
        "connections": []
    }

    # Component mapping (shdf_component_id -> shdf_component_type)
    component_type_map = {}

    # Process components
    for i, component in enumerate(standard_diagram.get("components", [])):
        shdf_component_id = component.get("id")
        shdf_component_type = component.get("type")
        
        shdf_component_type = shdf_alias_check(shdf_component_type)
        if shdf_component_type is None:
            print("\033[91mno component type during convert_standard_to_wokwi\033[0m", file=sys.stderr)
            continue
        
        if shdf_component_type == "4-digit 7-segment display":
            print(shdf_component_type)
            shdf_component_type = "7-segment display"
            component["properties"] = { "digits" : "4" }

        # Map component type to Wokwi type
        wokwi_component_type = _get_wokwi_type(shdf_component_type)
        wokwi_component_id = _get_wokwi_id(shdf_component_id, shdf_component_type)

        # Store mapping
        component_type_map[shdf_component_id] = shdf_component_type

        # Extract properties
        attrs = {}
        if "properties" in component:
            for key, value in component["properties"].items():
                if key in ["color", "digits"]:
                    attrs[key] = value
                elif key == "value" and shdf_component_type=='resistor':
                    # Extract numeric part of resistor value
                    value = value.replace("ohm", "")
                    value = value.replace("k", "000").strip()
                    if not value.isdigit():
                        raise ValueError("Resistor attribute should be an integer.")
                    attrs["value"] = value
                else:
                    print("invalid property: ", key)

        # Calculate position based on component type and mode
        position = _calculate_position(wokwi_component_type, i, mode)

        # Add to parts list
        wokwi_part = {
            "type": wokwi_component_type,
            "id": wokwi_component_id,
            "top": position["top"],
            "left": position["left"],
            "attrs": attrs
        }

        # Add rotation if needed
        if "rotate" in position:
            wokwi_part["rotate"] = position["rotate"]

        wokwi_diagram["parts"].append(wokwi_part)

    # Process connections
    # print(standard_diagram["connections"])
    for connection in standard_diagram.get("connections", []):
        # Each connection is a direct array of two endpoints
        if isinstance(connection, list) and len(connection) == 2:
            endpoints = connection
        else:
            # For backward compatibility with older format
            endpoints = connection.get("endpoints", [])
            if len(endpoints) != 2:
                continue

        # Convert to Wokwi connection format

        endpoint1_wokwi = _convert_to_wokwi_point(endpoints[0], component_type_map)
        endpoint2_wokwi = _convert_to_wokwi_point(endpoints[1], component_type_map)

        if endpoint1_wokwi and endpoint2_wokwi:
            # Add wire color based on connection type
            wire_color = _determine_wire_color(endpoints[0], endpoints[1])

            wokwi_diagram["connections"].append([
                endpoint1_wokwi,
                endpoint2_wokwi,
                wire_color,
                []  # Empty routing information
            ])

    return wokwi_diagram


def _get_wokwi_type(shdf_component_type):
    """Map SHDF component type to Wokwi component type."""
    # Use the centralized type mapping function
    return shdf_to_wokwi_type(shdf_component_type)

def _get_wokwi_id(shdf_component_id, shdf_component_type):
    
    match = re.search(r'(\d+)$', shdf_component_id)
    
    if shdf_alias_check(shdf_component_id) == shdf_component_type and match:
        return shdf_component_type + "1"

    if match:
        number = match.group(1)
        return shdf_component_type + number
    else:
        print("No number at the end:", shdf_component_id)
        return shdf_component_id

def _calculate_position(wokwi_component_type, index, mode):
    """Calculate component position based on type and index."""
    # Default positions
    if wokwi_component_type == "wokwi-arduino-uno":
        return {"top": 200, "left": 20}
    elif wokwi_component_type == "wokwi-breadboard":
        return {"top": 0, "left": 100}
    elif wokwi_component_type == "wokwi-resistor":
        return {"top": 100, "left": 150 + (index * 50), "rotate": 90}
    elif wokwi_component_type == "wokwi-led":
        return {"top": 50, "left": 150 + (index * 50)}
    elif wokwi_component_type == "wokwi-pushbutton":
        return {"top": 150, "left": 150 + (index * 50), "rotate": 90}
    elif mode == "logical":
        return {"top": 100, "left": 200 + (index * 80)}
    else:  # physical mode
        return {"top": 50 + (index * 30), "left": 150 + (index * 40)}


def _convert_to_wokwi_point(shdf_point, component_type_map):
    """Convert SHDF connection point to Wokwi format."""
    if "breadboard" in shdf_point:
        parts = shdf_point.split(".", 1)
        if len(parts) != 2:
            raise ValueError(f"Invalid SHDF point: {shdf_point}")
        
        bb_id, position = parts
        
        # Check if this is a power rail point (contains 'p' or 'n')
        if "p" in position or "n" in position:
            # Handle power rail format (breadboard.50tn -> bb1:tn.50)
            # Extract rail type (tn, tp, bn, bp) and column number
            rail_type = ''.join(c for c in position if c.isalpha())
            col = ''.join(c for c in position if c.isdigit())
            
            # Return Wokwi format for power rail
            return f"{bb_id}:{rail_type}.{col}"
        else:
            # Handle regular position format (breadboard.10a -> bb1:10t.a)
            # Extract column number and row letter
            col = ''.join(c for c in position if c.isdigit())
            row = ''.join(c for c in position if c.isalpha())
            
            # Determine side (t or b) based on row letter
            # Rows a-e are on the top half (t), rows f-j are on the bottom half (b)
            side = "t" if row.lower() in "abcde" else "b"
            
            # Return Wokwi format for regular position
            return f"{bb_id}:{col}{side}.{row}"
        
    elif "." in shdf_point:
        # Convert component.pin to component:pin
        shdf_component_id, shdf_pin = shdf_point.split(".", 1)

        # Standardize pin names using the mapping
        wokwi_pin = shdf_to_wokwi_pin(shdf_pin, component_type_map[shdf_component_id])
        wokwi_component_id = _get_wokwi_id(shdf_component_id, component_type_map[shdf_component_id])

        return f"{wokwi_component_id}:{wokwi_pin}"

    return shdf_point


def _determine_wire_color(from_point, to_point):
    """Determine wire color based on connection type."""
    points = from_point + to_point

    if "gnd" in points.lower():
        return "black"
    elif "5v" in points.lower() or "3.3v" in points.lower():
        return "red"
    elif "anode" in points or "cathode" in points:
        return "green"
    else:
        # Use a hash of the connection to get a consistent color
        colors = ["blue", "green", "yellow", "orange", "purple"]
        hash_val = int(hashlib.md5(points.encode()).hexdigest(), 16) % len(colors)
        return colors[hash_val]


if __name__ == "__main__":
    # Simple test case
    test_shdf = {
        "components": [
            {"id": "arduino", "type": "Arduino Uno"},
            {"id": "led1", "type": "LED", "properties": {"color": "red"}}
        ],
        "connections": [
            ["arduino.pin13", "led1.anode"],
            ["led1.cathode", "arduino.gnd"]
        ]
    }

    result = convert_standard_to_wokwi(test_shdf)
    print(json.dumps(result, indent=2))
