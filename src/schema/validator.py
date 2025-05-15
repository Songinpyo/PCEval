"""
Validator for Standardized Hardware Description Format (SHDF).

This module provides functions to validate SHDF documents against the JSON schema.
"""

import os
import json
import re
from jsonschema import validate, ValidationError, SchemaError
from converters.type_mappings import TYPE_MAPPINGS, SHDF_TYPE_ALIASES
from converters.pin_mappings import get_all_pin_patterns

# Path to the schema file
SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "shdf_schema.json")

def load_schema():
    """
    Load the SHDF JSON schema.

    Returns:
        The JSON schema as a dictionary
    """
    with open(SCHEMA_PATH, "r") as f:
        schema = json.load(f)
    return schema

def validate_shdf(shdf_data):
    """
    Validate an SHDF document against the JSON schema.

    Args:
        shdf_data: The SHDF document as a dictionary

    Returns:
        A tuple (is_valid, errors) where:
        - is_valid is a boolean indicating whether the document is valid
        - errors is a list of validation error messages (empty if valid)
    """
    schema = load_schema()
    errors = []

    # Create a copy of the data with lowercase component types for validation
    normalized_data = shdf_data.copy()

    # Convert component types to lowercase
    if "components" in normalized_data:
        for component in normalized_data["components"]:
            if "type" in component:
                component["type"] = component["type"].lower()

                # Validate component type against module_info.json
                comp_type = component["type"]
                if comp_type not in SHDF_TYPE_ALIASES and comp_type not in TYPE_MAPPINGS.values():
                    errors.append(f"Invalid component type: {comp_type}")

    # If we already found errors, return them
    if errors:
        return False, errors

    try:
        validate(instance=normalized_data, schema=schema)
        return True, []
    except ValidationError as e:
        errors.append(f"Validation error: {e.message}")
        return False, errors
    except SchemaError as e:
        errors.append(f"Schema error: {e.message}")
        return False, errors
    except Exception as e:
        errors.append(f"Unexpected error: {str(e)}")
        return False, errors

def validate_component_ids(shdf_data):
    """
    Validate that component IDs are unique and referenced correctly in connections.

    Args:
        shdf_data: The SHDF document as a dictionary

    Returns:
        A tuple (is_valid, errors) where:
        - is_valid is a boolean indicating whether the document is valid
        - errors is a list of validation error messages (empty if valid)
    """
    errors = []

    # Check that component IDs are unique
    component_ids = [comp["id"] for comp in shdf_data.get("components", [])]
    if len(component_ids) != len(set(component_ids)):
        errors.append("Component IDs must be unique")

    # Check that connections reference valid component IDs
    valid_ids = set(component_ids)
    for i, connection in enumerate(shdf_data.get("connections", [])):
        for j, endpoint in enumerate(connection):
            # Extract component ID from endpoint (format: component.pin)
            if "." in endpoint:
                comp_id = endpoint.split(".", 1)[0]
                if comp_id not in valid_ids and comp_id != "breadboard":
                    errors.append(f"Connection {i} endpoint {j} references unknown component ID: {comp_id}")

    return len(errors) == 0, errors

def validate_pin_names(shdf_data):
    """
    Validate that pin names follow the conventions for each component type.

    Args:
        shdf_data: The SHDF document as a dictionary

    Returns:
        A tuple (is_valid, errors) where:
        - is_valid is a boolean indicating whether the document is valid
        - errors is a list of validation error messages (empty if valid)
    """
    errors = []

    # Load pin patterns from module_info.json
    pin_patterns = get_all_pin_patterns()

    # Add default pattern for breadboard
    pin_patterns["breadboard"] = [
        r"^[a-zA-Z0-9_.]+$",  # Any pin name is valid for breadboard
        r"^pin\d+[a-z]\.[a-z]$",  # Format like pin30t.c
        r"^bn\.\d+$"  # Format like bn.18
    ]
    
    # # Add common power pins to all component types
    # for comp_type in pin_patterns.keys():
    #     if comp_type != "breadboard":
    #         pin_patterns[comp_type].extend([
    #             r"^gnd\d*$",   # Ground (with or without number)
    #             r"^5v$",      # 5V
    #             r"^3.3v$",    # 3.3V
    #             r"^vin$",     # VIN
    #             r"^vcc$",     # VCC
    #             r"^power$",   # Power
    #             r"^ground$"   # Ground
    #         ])

    # Default pattern for components not explicitly listed
    default_pattern = [r"^[a-zA-Z0-9_.]+$"]

    # Build a map of component IDs to types
    comp_types = {comp["id"]: comp["type"] for comp in shdf_data.get("components", [])}

    # Check that connections use valid pin names
    for i, connection in enumerate(shdf_data.get("connections", [])):
        for j, endpoint in enumerate(connection):
            # Skip breadboard pins (they have a different format)
            if endpoint.startswith("breadboard."):
                continue

            # Extract component ID and pin name
            if "." in endpoint:
                comp_id, pin_name = endpoint.split(".", 1)

                # Skip unknown component IDs (already reported by validate_component_ids)
                if comp_id not in comp_types:
                    continue

                # Get component type and convert to lowercase for case-insensitive lookup
                comp_type = comp_types[comp_id].lower()

                # Get valid pin patterns for this component type
                patterns = pin_patterns.get(comp_type, default_pattern)

                # Check if pin name matches any valid pattern (case-insensitive)
                if not any(re.match(pattern, pin_name, re.IGNORECASE) for pattern in patterns):
                    errors.append(f"Connection {i} endpoint {j} uses invalid pin name: {pin_name} for component type: {comp_type}")

    return len(errors) == 0, errors

def validate_breadboard_positions(shdf_data):
    """
    Validate that breadboard positions follow the correct format.

    Args:
        shdf_data: The SHDF document as a dictionary

    Returns:
        A tuple (is_valid, errors) where:
        - is_valid is a boolean indicating whether the document is valid
        - errors is a list of validation error messages (empty if valid)
    """
    errors = []

    # Valid patterns for breadboard positions
    patterns = [
        r"^breadboard\.(\d+)([a-j])$",           # Format: breadboard.10a
        r"^breadboard\.pin(\d+)([tb])\.([a-j])$", # Format: breadboard.pin30t.c
        r"^breadboard\.bn\.(\d+)$"               # Format: breadboard.bn.18
    ]

    for i, connection in enumerate(shdf_data.get("connections", [])):
        for j, endpoint in enumerate(connection):
            if endpoint.startswith("breadboard."):
                # Check if the endpoint matches any valid pattern
                valid_format = False
                for pattern in patterns:
                    if re.match(pattern, endpoint):
                        valid_format = True

                        # For the first pattern, check column range
                        if pattern == patterns[0]:
                            match = re.match(pattern, endpoint)
                            column = int(match.group(1))

                            # Check column range (1-60)
                            if column < 1 or column > 60:
                                errors.append(f"Connection {i} endpoint {j} has invalid breadboard column: {column} (must be 1-60)")

                        # For the second pattern, check column range
                        elif pattern == patterns[1]:
                            match = re.match(pattern, endpoint)
                            column = int(match.group(1))

                            # Check column range (1-60)
                            if column < 1 or column > 60:
                                errors.append(f"Connection {i} endpoint {j} has invalid breadboard column: {column} (must be 1-60)")

                if not valid_format:
                    errors.append(f"Connection {i} endpoint {j} has invalid breadboard position format: {endpoint}")

    return len(errors) == 0, errors

def validate_shdf_document(shdf_data):
    """
    Perform comprehensive validation of an SHDF document.

    Args:
        shdf_data: The SHDF document as a dictionary

    Returns:
        A tuple (is_valid, errors) where:
        - is_valid is a boolean indicating whether the document is valid
        - errors is a list of validation error messages (empty if valid)
    """
    all_errors = []

    # Validate against JSON schema
    is_valid, errors = validate_shdf(shdf_data)
    all_errors.extend(errors)

    # Skip additional validation if schema validation failed
    if not is_valid:
        return False, all_errors

    # Validate component IDs
    is_valid, errors = validate_component_ids(shdf_data)
    all_errors.extend(errors)

    # Validate pin names
    is_valid, errors = validate_pin_names(shdf_data)
    all_errors.extend(errors)

    # Validate breadboard positions
    is_valid, errors = validate_breadboard_positions(shdf_data)
    all_errors.extend(errors)

    return len(all_errors) == 0, all_errors

if __name__ == "__main__":
    # Example usage
    import sys

    if len(sys.argv) < 2:
        print("Usage: python validator.py <shdf_file>")
        sys.exit(1)

    # Load SHDF file
    with open(sys.argv[1], "r") as f:
        shdf_data = json.load(f)

    # Validate
    is_valid, errors = validate_shdf_document(shdf_data)

    if is_valid:
        print("✅ SHDF document is valid")
    else:
        print("❌ SHDF document is invalid:")
        for error in errors:
            print(f"  - {error}")
