#!/usr/bin/env python3
"""
Test script for hardware evaluation metrics.
"""

import os
import json
import argparse
from hardware_metrics import (
    check_duplicate_connections,
    check_breadboard_hole_conflicts,
    check_unused_components,
    check_direct_connections,
    compare_with_reference,
    evaluate_hardware_design
)

def main():
    parser = argparse.ArgumentParser(description="Test hardware evaluation metrics")
    parser.add_argument("diagram_file", help="Path to the SHDF diagram file")
    parser.add_argument("--reference", help="Path to the reference diagram file")
    parser.add_argument("--mode", choices=["logical", "physical"], default="logical",
                       help="Mode of hardware design (logical or physical)")
    parser.add_argument("--output", help="Output JSON file for results")
    args = parser.parse_args()
    
    # Load diagram file
    with open(args.diagram_file, "r") as f:
        diagram = json.load(f)
    
    # Load reference file if provided
    reference_diagram = None
    if args.reference:
        with open(args.reference, "r") as f:
            reference_diagram = json.load(f)
    
    # Run evaluation
    results = evaluate_hardware_design(diagram, reference_diagram, args.mode)
    
    # Print results
    print("\n=== Hardware Evaluation Results ===\n")
    print(f"Mode: {args.mode.upper()}")
    
    # Print duplicate connections
    dup_conn = results["metrics"]["duplicate_connections"]
    print(f"\nDuplicate Connections: {dup_conn['duplicate_connections']}")
    if dup_conn["duplicate_connections"] > 0:
        print("Duplicate connection details:")
        for dup in dup_conn["duplicate_connection_list"]:
            print(f"  - Connection {dup['index']}: {dup['connection']}")
    
    # Print unused components
    unused = results["metrics"]["unused_components"]
    print(f"\nUnused Components: {unused['unused_components']}")
    if unused["unused_components"] > 0:
        print("Unused component details:")
        for comp in unused["unused_component_list"]:
            print(f"  - {comp['id']} (Type: {comp['type']})")
    
    # Print breadboard conflicts for physical mode
    if args.mode == "physical":
        conflicts = results["metrics"]["breadboard_conflicts"]
        print(f"\nBreadboard Hole Conflicts: {conflicts['hole_conflicts']}")
        if conflicts["hole_conflicts"] > 0:
            print("Conflict details:")
            for conflict in conflicts["conflict_holes"]:
                print(f"  - Hole {conflict['hole']} has {conflict['connection_count']} connections")
                
        # Print direct connections metrics for physical mode
        if "direct_connections" in results["metrics"]:
            direct_conn = results["metrics"]["direct_connections"]
            print(f"\nDirect Connections: {direct_conn['direct_connections']} ({direct_conn.get('direct_connection_percentage', 0):.1f}%)")
            print(f"Breadboard Connections: {direct_conn['breadboard_connections']} ({direct_conn.get('breadboard_connection_percentage', 0):.1f}%)")
            if direct_conn['direct_connections'] > 0:
                print("Direct connection details:")
                for conn in direct_conn.get('direct_connection_list', [])[:5]:  # Show only first 5 to avoid too much output
                    print(f"  - Connection {conn['index']}: {conn['connection']}")
                if len(direct_conn.get('direct_connection_list', [])) > 5:
                    print(f"  ... and {len(direct_conn.get('direct_connection_list', [])) - 5} more")
    
    # Print comparison with reference if provided
    if reference_diagram:
        unnecessary = results["metrics"]["unnecessary_components"]
        print(f"\nUnnecessary Components: {unnecessary['unnecessary_components']}")
        if unnecessary['unnecessary_components'] > 0:
            print("Unnecessary component details:")
            for comp in unnecessary["unnecessary_component_list"]:
                print(f"  - {comp['type']}: {comp['extra_count']} extra " +
                      f"(Generated: {comp['generated_count']}, Reference: {comp['reference_count']})")
    
    # Save results if output file is specified
    if args.output:
        os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
        with open(args.output, "w") as f:
            json.dump(results, f, indent=2)
        print(f"\nResults saved to {args.output}")

if __name__ == "__main__":
    main()
