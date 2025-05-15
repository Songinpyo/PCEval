"""
Hardware evaluation metrics for Arduino-LLM project.

This module provides functions to evaluate hardware designs in SHDF format.
"""

def check_duplicate_connections(diagram):
    """
    Check for duplicate connections in a hardware diagram.
    
    Args:
        diagram (dict): Hardware diagram in SHDF format
        
    Returns:
        dict: Results containing duplicate connections information
    """
    results = {
        "duplicate_connections": 0,
        "duplicate_connection_list": []
    }
    
    # Create a set to track unique connections
    unique_connections = set()
    
    # Check each connection
    for i, connection in enumerate(diagram.get("connections", [])):
        # Ensure connection is a list with exactly 2 elements
        if not isinstance(connection, list):
            continue
            
        # Sort the endpoints to handle bidirectional connections
        # (A->B is the same as B->A in electrical connections)
        conn_pair = tuple(sorted(connection[:2]))
        
        # Check if this connection already exists
        if conn_pair in unique_connections:
            results["duplicate_connections"] += 1
            results["duplicate_connection_list"].append({
                "index": i,
                "connection": connection
            })
        else:
            unique_connections.add(conn_pair)
    
    return results


def check_endpoint_conflicts(diagram):
    """
    Check for endpoint conflicts (multiple connections to the same endpoint, 
    including breadboard holes and component pins).
    
    Args:
        diagram (dict): Hardware diagram in SHDF format
        
    Returns:
        dict: Results containing endpoint conflict information
    """
    results = {
        "endpoint_conflicts": 0,
        "conflict_endpoints": []
    }
    
    # Track endpoint usage
    endpoint_usage = {}
    
    # Process all connections
    for i, connection in enumerate(diagram.get("connections", [])):
        # Ensure connection is a list with exactly 2 elements
        if not isinstance(connection, list):
            continue
            
        # Check each endpoint
        for endpoint in connection[:2]:
            # 제거: if endpoint.startswith("breadboard"):
            # 모든 엔드포인트 처리
            if endpoint in endpoint_usage:
                endpoint_usage[endpoint].append(i)
            else:
                endpoint_usage[endpoint] = [i]
    
    # Find endpoints with multiple connections
    for endpoint, connection_indices in endpoint_usage.items():
        if len(connection_indices) > 1:
            results["endpoint_conflicts"] += 1
            results["conflict_endpoints"].append({
                "endpoint": endpoint,
                "connection_indices": connection_indices,
                "connection_count": len(connection_indices)
            })
    
    return results


def check_unused_components(diagram):
    """
    Check for components that are not used in any connection.
    
    Args:
        diagram (dict): Hardware diagram in SHDF format
        
    Returns:
        dict: Results containing unused components information
    """
    results = {
        "unused_components": 0,
        "unused_component_list": []
    }
    
    # Get all component IDs
    all_component_ids = {comp["id"] for comp in diagram.get("components", [])}
    
    # Track used components
    used_component_ids = set()
    
    # Process all connections
    for connection in diagram.get("connections", []):
        # Ensure connection is a list with exactly 2 elements
        if not isinstance(connection, list):
            continue
            
        # Check each endpoint
        for endpoint in connection[:2]:
            # Skip breadboard endpoints
            # if endpoint.startswith("breadboard"):
            #     continue
                
            # Extract component ID from endpoint (format: component.pin)
            if "." in endpoint:
                comp_id = endpoint.split(".", 1)[0]
                used_component_ids.add(comp_id)
    
    # Find unused components
    unused_ids = all_component_ids - used_component_ids
    results["unused_components"] = len(unused_ids)
    
    # Get full component details for unused components
    for comp in diagram.get("components", []):
        if comp["id"] in unused_ids:
            results["unused_component_list"].append(comp)
    
    return results


def compare_with_reference(generated_diagram, reference_diagram):
    """
    Compare generated diagram with reference diagram to find unnecessary and missing components.
    
    Args:
        generated_diagram (dict): Generated hardware diagram in SHDF format
        reference_diagram (dict): Reference hardware diagram in SHDF format
        
    Returns:
        dict: Results containing comparison information (unnecessary and missing components)
    """
    results = {
        "unnecessary_components": 0,
        "unnecessary_component_list": [],
        "missing_components": 0,
        "missing_component_list": []
    }
    
    # Get component types and counts from reference diagram
    reference_components = {}
    for comp in reference_diagram.get("components", []):
        comp_type = comp.get("type", "").lower()
        if comp_type in reference_components:
            reference_components[comp_type] += 1
        else:
            reference_components[comp_type] = 1
    
    # Count component types in generated diagram
    generated_components = {}
    for comp in generated_diagram.get("components", []):
        comp_type = comp.get("type", "").lower()
        if comp_type in generated_components:
            generated_components[comp_type] += 1
        else:
            generated_components[comp_type] = 1
    
    # Find unnecessary components (more in generated than reference)
    for comp_type, count in generated_components.items():
        ref_count = reference_components.get(comp_type, 0)
        if count > ref_count:
            extra_count = count - ref_count
            results["unnecessary_components"] += extra_count
            results["unnecessary_component_list"].append({
                "type": comp_type,
                "extra_count": extra_count,
                "generated_count": count,
                "reference_count": ref_count
            })
    
    # Find missing components (more in reference than generated)
    for comp_type, ref_count in reference_components.items():
        gen_count = generated_components.get(comp_type, 0)
        if ref_count > gen_count:
            missing_count = ref_count - gen_count
            results["missing_components"] += missing_count
            results["missing_component_list"].append({
                "type": comp_type,
                "missing_count": missing_count,
                "generated_count": gen_count,
                "reference_count": ref_count
            })
    
    return results


def check_direct_connections(diagram):
    """
    Check for direct component-to-component connections without using breadboard in a physical layout.
    In a proper physical layout, components should be connected via breadboard, not directly to each other.
    
    Args:
        diagram (dict): Hardware diagram in SHDF format
        
    Returns:
        dict: Results containing direct connection information
    """
    results = {
        "direct_connections": 0,
        "breadboard_connections": 0,
        "direct_connection_list": []
    }
    
    # Process all connections
    for i, connection in enumerate(diagram.get("connections", [])):
        # Ensure connection is a list with exactly 2 elements
        if not isinstance(connection, list):
            continue
        
        # Check if at least one endpoint is a breadboard
        has_breadboard = any(endpoint.startswith("breadboard") for endpoint in connection[:2])
        
        if has_breadboard:
            results["breadboard_connections"] += 1
        else:
            results["direct_connections"] += 1
            results["direct_connection_list"].append({
                "index": i,
                "connection": connection
            })
    
    # Calculate percentage
    total_connections = len(diagram.get("connections", []))
    if total_connections > 0:
        results["direct_connection_percentage"] = (results["direct_connections"] / total_connections) * 100
        results["breadboard_connection_percentage"] = (results["breadboard_connections"] / total_connections) * 100
    else:
        results["direct_connection_percentage"] = 0
        results["breadboard_connection_percentage"] = 0
    
    return results


def check_component_attrs(generated_diagram, reference_diagram, project_path=None):
    """
    Check for component attributes (attrs) matching between generated and reference diagrams.
    Currently checks for resistor 'value' and LED 'color' (LED only for traffic_light project).
    
    Args:
        generated_diagram (dict): Generated hardware diagram in SHDF format
        reference_diagram (dict): Reference hardware diagram in SHDF format
        project_path (str, optional): Path to the project for project-specific checks
        
    Returns:
        dict: Results containing component attribute comparison information
    """
    results = {
        "incorrect_attrs": 0,
        "incorrect_attrs_list": []
    }
    
    # Check if we should do LED color check (only for traffic_light project)
    check_led_color = False
    if project_path and "traffic_light" in project_path:
        check_led_color = True
    
    # Get reference components with their attrs
    reference_components = {}
    for comp in reference_diagram.get("components", []):
        comp_id = comp.get("id", "")
        comp_type = comp.get("type", "").lower()
        
        # Get properties or attrs based on what's available
        attrs = comp.get("attrs", comp.get("properties", {}))
        
        # For resistors, check value
        if "resistor" in comp_type and "value" in attrs:
            reference_components[comp_id] = {
                "type": "resistor",
                "value": attrs["value"]
            }
        
        # For LEDs in traffic_light project, check color
        elif check_led_color and "led" in comp_type and "color" in attrs:
            reference_components[comp_id] = {
                "type": "led",
                "color": attrs["color"]
            }
    
    # Check each generated component against reference
    for comp in generated_diagram.get("components", []):
        comp_id = comp.get("id", "")
        comp_type = comp.get("type", "").lower()
        
        # Get properties or attrs based on what's available
        attrs = comp.get("attrs", comp.get("properties", {}))
        
        # For resistors, check value
        if "resistor" in comp_type and comp_id in reference_components and reference_components[comp_id]["type"] == "resistor":
            ref_value = reference_components[comp_id]["value"]
            gen_value = attrs.get("value", "")
            
            # Normalize values for comparison (remove "ohm", "Ω", etc.)
            ref_value_norm = str(ref_value).lower().replace("ohm", "").replace("ω", "").replace("Ω", "").strip()
            gen_value_norm = str(gen_value).lower().replace("ohm", "").replace("ω", "").replace("Ω", "").strip()
            
            if gen_value_norm != ref_value_norm:
                results["incorrect_attrs"] += 1
                results["incorrect_attrs_list"].append({
                    "component_id": comp_id,
                    "component_type": "resistor",
                    "attribute": "value",
                    "generated_value": gen_value,
                    "reference_value": ref_value
                })
        
        # For LEDs in traffic_light project, check color
        elif check_led_color and "led" in comp_type and comp_id in reference_components and reference_components[comp_id]["type"] == "led":
            ref_color = reference_components[comp_id]["color"]
            gen_color = attrs.get("color", "")
            
            # Normalize color for comparison
            ref_color_norm = str(ref_color).lower().strip()
            gen_color_norm = str(gen_color).lower().strip()
            
            if gen_color_norm != ref_color_norm:
                results["incorrect_attrs"] += 1
                results["incorrect_attrs_list"].append({
                    "component_id": comp_id,
                    "component_type": "led",
                    "attribute": "color",
                    "generated_value": gen_color,
                    "reference_value": ref_color
                })
    
    return results


def evaluate_hardware_design(diagram, reference_diagram=None, mode="logical", project_path=None):
    """
    Comprehensive evaluation of a hardware design.
    
    Args:
        diagram (dict): Hardware diagram in SHDF format
        reference_diagram (dict, optional): Reference diagram for comparison
        mode (str): "logical" or "physical"
        project_path (str, optional): Path to the project for project-specific checks
        
    Returns:
        dict: Comprehensive evaluation results
    """
    results = {
        "mode": mode,
        "metrics": {}
    }
    
    # Check for duplicate connections
    results["metrics"]["duplicate_connections"] = check_duplicate_connections(diagram)
    
    # Check for unused components
    results["metrics"]["unused_components"] = check_unused_components(diagram)
    
    # For physical mode only
    if mode == "physical":
        # 이름 및 키 변경: Check endpoint conflicts (includes breadboard holes and component pins)
        results["metrics"]["endpoint_conflicts"] = check_endpoint_conflicts(diagram) 
        
        # Check direct connections
        results["metrics"]["direct_connections"] = check_direct_connections(diagram)
    
    # If reference diagram is provided, compare with it
    if reference_diagram:
        unnecessary_and_missing = compare_with_reference(diagram, reference_diagram)
        results["metrics"]["unnecessary_components"] = unnecessary_and_missing
        results["metrics"]["missing_components"] = unnecessary_and_missing
        # Check component attributes (resistor value, LED color for traffic_light)
        results["metrics"]["component_attrs"] = check_component_attrs(diagram, reference_diagram, project_path)
    
    return results


if __name__ == "__main__":
    # Example usage
    import json
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python hardware_metrics.py <shdf_file> [reference_file] [mode] [project_path]")
        sys.exit(1)
    
    # Load SHDF file
    with open(sys.argv[1], "r") as f:
        diagram = json.load(f)
    
    # Load reference file if provided
    reference_diagram = None
    if len(sys.argv) > 2:
        with open(sys.argv[2], "r") as f:
            reference_diagram = json.load(f)
    
    # Get mode
    mode = "logical"
    if len(sys.argv) > 3:
        mode = sys.argv[3]
    
    # Get project path if provided
    project_path = None
    if len(sys.argv) > 4:
        project_path = sys.argv[4]
    
    # Evaluate
    results = evaluate_hardware_design(diagram, reference_diagram, mode, project_path)
    print(json.dumps(results, indent=2))
