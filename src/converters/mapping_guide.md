# Mapping System Guide

This document explains how the mapping system works for converting between Wokwi and SHDF (Standardized Hardware Description Format) component types and pin names, as well as how the schema validation system works.

## Overview

The mapping system provides bidirectional conversion between Wokwi's hardware description format and the Standardized Hardware Description Format (SHDF). It handles two main types of conversions:

1. **Component Type Conversion**: Converting component types like "wokwi-arduino-uno" to "arduino uno" and vice versa
2. **Pin Name Conversion**: Converting pin names like "A" to "anode" for LEDs and vice versa

The system is designed to be:
- **Robust**: Handles variations in naming and case sensitivity
- **Extensible**: Easily add new components and pins
- **Maintainable**: Centralized mapping definitions

## File Structure

The system consists of several key files:

### Mapping Files
- `type_mappings.py`: Handles component type conversions
- `pin_mappings.py`: Handles pin name conversions

### Schema Validation Files
- `schema/shdf_schema.json`: JSON Schema definition for SHDF
- `schema/validator.py`: Functions for validating SHDF documents

### Data Files
- `converters/module_info.json`: Contains component information used to update mappings

The mapping files follow a similar structure with base mappings and additional features like aliases and automatic updates from `module_info.json`.

## How It Works

### 1. Base Mappings

Each file defines a base set of mappings for the most common components and pins:

```python
# Example from type_mappings.py
TYPE_MAPPINGS = {
    "wokwi-arduino-uno": "arduino uno",
    "wokwi-led": "led",
    # ... more mappings
}

# Example from pin_mappings.py
PIN_MAPPINGS = {
    "led": {
        "A": "anode",
        "C": "cathode",
    },
    # ... more component-specific pin mappings
}
```

### 2. Automatic Updates from module_info.json

Both files can automatically update their mappings using information from `src/converters/module_info.json`:

```python
def load_module_info():
    # Load the module_info.json file
    current_dir = Path(__file__).parent.parent.parent
    module_info_path = current_dir / "src" / "converters" / "module_info.json"

    with open(module_info_path, "r") as f:
        module_info = json.load(f)

    # Process the module info
    module_dict = {}
    for module in module_info:
        wokwi_type = module.get("wokwi_type", "")
        if wokwi_type:
            module_dict[wokwi_type] = module

    return module_dict

def update_mappings_from_module_info():
    module_info = load_module_info()

    # Update mappings with module info
    for wokwi_type, module in module_info.items():
        # Skip if we already have mappings for this component
        if wokwi_type in TYPE_MAPPINGS:
            continue

        # Add new mapping
        std_type = wokwi_type.replace("wokwi-", "").lower()
        TYPE_MAPPINGS[wokwi_type] = std_type
```

This allows the system to automatically support new components added to `module_info.json` without code changes.

### 3. Alias Support

The system supports aliases to handle different ways of expressing the same component or pin:

```python
# Component type aliases
SHDF_TYPE_ALIASES = {
    "7segment display": "7-segment display",
    "seven segment display": "7-segment display",
    "rgb-led": "rgb led",
    # ... more aliases
}

# Pin name aliases
PIN_NAME_ALIASES = {
    "ground": "gnd",
    "vcc": "5v",
    "positive": "anode",
    "negative": "cathode",
    # ... more aliases
}
```

When converting, the system checks if the input is an alias and converts it to the standard form:

```python
def shdf_to_wokwi_type(shdf_type):
    # Convert to lowercase for case-insensitive lookup
    shdf_type_lower = shdf_type.lower()

    # Check if this is an alias and convert to standard form
    if shdf_type_lower in SHDF_TYPE_ALIASES:
        shdf_type_lower = SHDF_TYPE_ALIASES[shdf_type_lower]

    # Continue with the conversion...
```

### 4. Case Insensitivity

The system handles case insensitivity by converting inputs to lowercase before lookup:

```python
# Convert to lowercase for case-insensitive lookup
pin_lower = pin.lower()

# Check if this is an alias and convert to standard form
if pin_lower in PIN_NAME_ALIASES:
    pin_lower = PIN_NAME_ALIASES[pin_lower]
```

This makes the system more robust against variations in case.

## Adding New Mappings

### Adding New Component Types

To add a new component type mapping:

1. **Option 1**: Add to the base mappings in `type_mappings.py`:
   ```python
   TYPE_MAPPINGS = {
       # Existing mappings...
       "wokwi-new-component": "new component",
   }
   ```

2. **Option 2**: Add to `module_info.json`:
   ```json
   {
     "wokwi_type": "wokwi-new-component",
     "pins": [
       {"pin_name": "VCC", "description": "Power supply"},
       {"pin_name": "GND", "description": "Ground"},
       {"pin_name": "OUT", "description": "Output"}
     ]
   }
   ```

### Adding New Pin Mappings

To add new pin mappings:

1. **Option 1**: Add to the base mappings in `pin_mappings.py`:
   ```python
   PIN_MAPPINGS = {
       # Existing mappings...
       "new-component": {
           "PIN1": "pin1",
           "PIN2": "pin2",
       },
   }
   ```

2. **Option 2**: Add pins to the component in `module_info.json`:
   ```json
   {
     "wokwi_type": "wokwi-new-component",
     "pins": [
       {"pin_name": "PIN1", "description": "First pin"},
       {"pin_name": "PIN2", "description": "Second pin"}
     ]
   }
   ```

### Adding Aliases

To add new aliases for component types or pin names:

1. For component types, add to `SHDF_TYPE_ALIASES` in `type_mappings.py`:
   ```python
   SHDF_TYPE_ALIASES = {
       # Existing aliases...
       "new-component-alias": "new component",
   }
   ```

2. For pin names, add to `PIN_NAME_ALIASES` in `pin_mappings.py`:
   ```python
   PIN_NAME_ALIASES = {
       # Existing aliases...
       "pin1_alias": "pin1",
   }
   ```

## Best Practices

1. **Prioritize Base Mappings**: Put the most common and critical mappings in the base mappings for better control and code review.

2. **Use module_info.json for Extensions**: Use `module_info.json` for adding support for new or less common components.

3. **Add Aliases for Common Variations**: When you encounter different ways to express the same component or pin, add aliases to make the system more robust.

4. **Maintain Consistency**: Try to follow consistent naming patterns for SHDF types and pin names:
   - Component types: lowercase with spaces (e.g., "arduino uno", "rgb led")
   - Pin names: lowercase with underscores for multi-word names (e.g., "segment_a", "decimal_point")

5. **Test New Mappings**: After adding new mappings, test them with real projects to ensure they work correctly.

## Schema Validation System

The schema validation system ensures that hardware descriptions conform to the SHDF standard. It consists of two main files:

- `src/schema/shdf_schema.json`: The JSON Schema definition for SHDF
- `src/schema/validator.py`: Functions for validating SHDF documents

### How Schema Validation Works

1. **JSON Schema Validation**: The system first validates the document against the JSON Schema defined in `shdf_schema.json`.

2. **Component Type Validation**: It checks that component types are valid according to the enum list in the schema.

3. **Pin Name Validation**: It validates that pin names follow the conventions for each component type using regex patterns.

4. **Breadboard Position Validation**: For physical layouts, it validates that breadboard positions follow the correct format.

### Updating the Schema

When adding new component types or pin names, you need to update the schema validation system:

1. **Adding New Component Types**:
   - Add the new component type to the `enum` list in `shdf_schema.json`:
   ```json
   "enum": [
     "arduino uno",
     "led",
     "new component",  // Add your new component here
     // ... other components
   ]
   ```

2. **Adding New Pin Patterns**:
   - Add regex patterns for the new component's pins in `validator.py`:
   ```python
   pin_patterns = {
       # Existing patterns...
       "new component": [
           r"^pin1$",
           r"^pin2$",
           # ... more pin patterns
       ],
   }
   ```

### Best Practices for Schema Management

1. **Keep Schema and Mappings in Sync**: When adding new components or pins to the mapping system, also update the schema validation system.

2. **Use Consistent Naming**: Follow the same naming conventions in both the mapping system and the schema.

3. **Test Validation**: After updating the schema, test it with sample SHDF documents to ensure validation works correctly.

4. **Document Schema Changes**: When making significant changes to the schema, document them in comments or in this guide.

5. **Consider Backward Compatibility**: When updating the schema, consider whether the changes might break existing SHDF documents.

## Testing System

The project includes two main test files that serve different purposes:

### 1. `src/test_converters.py`

**Purpose**: Tests the bidirectional conversion between Wokwi format and SHDF format.

**Key Functions**:
- Tests Wokwi → SHDF conversion
- Tests SHDF → Wokwi conversion
- Tests pin name mapping functions
- Verifies that bidirectional conversion preserves information

**When to Use**:
- When you've modified the conversion logic
- When you've added new pin mappings
- When you've added support for new component types
- To verify that converted diagrams maintain all necessary information

### 2. `src/test_validator.py`

**Purpose**: Tests the SHDF schema validation system.

**Key Functions**:
- Tests that valid SHDF documents pass validation
- Tests that invalid SHDF documents fail validation with appropriate error messages
- Checks consistency between mapping files and schema
- Tests validation with real project files

**When to Use**:
- When you've modified the schema
- When you've added new component types or pin patterns to the validator
- To verify that the schema correctly enforces SHDF standards
- To check if mapping files and schema are in sync

### Differences and Relationship

- **Different Focus**: `test_converters.py` focuses on format conversion, while `test_validator.py` focuses on schema validation.
- **Complementary Roles**: Both tests are important - conversion ensures data integrity between formats, while validation ensures adherence to the SHDF standard.
- **Usage in Workflow**: Typically, you would run `test_converters.py` after modifying conversion logic, and `test_validator.py` after modifying the schema or adding new component types.

## Troubleshooting

If you encounter issues with the mapping or validation systems:

1. **Check Case Sensitivity**: Ensure the case of your component types and pin names matches the expected format.

2. **Check for Missing Mappings**: If a component or pin is not being converted correctly, check if it's defined in the mappings.

3. **Check Schema Validation**: If validation fails, check the error messages to identify which part of the schema is not being satisfied.

4. **Add Aliases**: If you find a common variation that's not being handled, add an alias for it.

5. **Update module_info.json**: For new components, make sure they're properly defined in `module_info.json`.

6. **Update Schema**: If validation fails for valid components or pins, update the schema to include them.

7. **Debug Conversion Functions**: Use print statements in the conversion functions to see how inputs are being processed.

8. **Run Both Tests**: When making significant changes, run both `test_converters.py` and `test_validator.py` to ensure both conversion and validation work correctly.
