#!/usr/bin/env python3
# hardware_generation_test.py
# Tool for testing LLM's hardware design capability for Arduino projects

import os
import json
import argparse
import shutil
import re
from utils import (
    load_project_files,
    generate_with_llm,
    get_backup_filename,
    run_wokwi_tests,
    create_logger,
    compile_with_platformio,
    load_test_values,
    parse_description,
    generate_improvement_prompt
)
from converters.standard_to_wokwi import convert_standard_to_wokwi
from schema import validate_shdf_document
from evaluation.hardware_metrics import evaluate_hardware_design

def generate_prompt(project_description, sketch_code, mode="logical"):
    """
    Generate a prompt for the LLM to create a hardware diagram.

    Args:
        project_description: A description of the project
        sketch_code: The Arduino sketch code
        project_scenario: A scenario of the project
        mode: "logical" for abstract circuit connections or "physical" for breadboard layout

    Returns:
        A prompt string
    """
    # Create the logical prompt
    logical_prompt = f"""# Arduino Hardware Design Task

            ## Task
            Based on the Arduino code and project description, create a logical circuit diagram that will work correctly with this code.

            Focus on the direct connections between components at a conceptual level, NOT physical layout with breadboard positions.

            ## Output Format
            Provide your answer in JSON format with two main sections:
            1. "components": A list of all hardware components needed
            2. "connections": A list of all connections between components

            ### Components Format
            Each component should have:
            - "id": A unique, meaningful identifier with a number appended (e.g., "arduino1", "led2", "resistor1"), that is consistently used in the connections section
            - "type": Component type ("Arduino Uno", "LED", "Resistor", "Button", etc.)
            - "properties": Optional object with properties specific to the component type

            ### Connections Format
            Each connection is simply an array with exactly two elements, each being a connection point formatted as "componentId.pinName".
            For example: ["arduino1.pin13", "led2.anode"]

            ### Pin Naming Conventions
            - Arduino pins: "pin2", "pin13", "a0", "a1", "5v", "3.3v", "gnd1", "gnd2", "gnd3", etc.
            - LED pins: "anode", "cathode"
            - Resistor pins: "pin1", "pin2"
            - Button pins: "pin1.l", "pin1.r", "pin2.l", "pin2.r"

            ### Example
            ```json
            {{"components": [
                {{"id": "arduino1", "type": "Arduino Uno"}},
                {{"id": "ntc sensor1", "type": "NTC temperature sensor", "properties": {{"temperature": "24"}}}}
              ],
              "connections": [
                ["arduino1.pin13", "resistor2.pin1"],
                ["ntc sensor1.VCC", "arduino1.5v"],
                ["ntc sensor1.GND", "arduino1.gnd2"],
                ["ntc sensor1.OUT", "arduino1.A0"],
              ]
            }}
            ```

            Based on the code, provide a complete JSON with all components and direct logical connections to create a functional circuit.

            ## Project Description
            {project_description}

            ## Arduino Code
            ```cpp
            {sketch_code}
            ```
            """


    # Create the physical prompt
    physical_prompt = f"""# Arduino Hardware Design Task

            ## Task
            Based on the Arduino code and project description, create a physical breadboard layout that will work correctly with this code.

            Include a breadboard and show how components would be physically placed and connected on it.

            ## Output Format
            Provide your answer in JSON format with two main sections:
            1. "components": A list of all hardware components needed
            2. "connections": A list of all connections between components

            ### Components Format
            Each component should have:
            - "id": A unique, meaningful identifier with a number appended (e.g., "arduino1", "led2", "resistor1") that is consistently used in the connections section
            - "type": Component type ("Arduino Uno", "LED", "Resistor", "Button", "Breadboard", etc.)
            - "properties": Optional object with properties specific to the component type:

            ### Connections Format
            Each connection is simply an array with exactly two elements, which can be component pins or breadboard positions.
            For example: ["arduino1.pin13", "breadboard1.10a"]

            ### Pin Naming Conventions
            - Arduino pins: "pin2", "pin13", "a0", "a1", "5v", "3.3v", "gnd1", "gnd2", "gnd3", etc.
            - LED pins: "anode", "cathode"
            - Resistor pins: "pin1", "pin2"
            - Button pins: "pin1.l", "pin1.r", "pin2.l", "pin2.r"

            ### Pin and Position Naming Conventions
            - Component pins: "arduino1.pin13", "led1.anode", "resistor1.pin1", etc.
            - Breadboard positions (main area): "breadboard.COLUMN_ROW"
                - Column: A number from 1-60
                - Row: A letter from a-j
                - Rows a-e are on the top half, rows f-j are on the bottom half
                - Example: "breadboard.10a" refers to column 10, row a (top half)
            - Breadboard power rail positions: "breadboard.RAIL_TYPE.COLUMN_NUMBER"
                - RAIL_TYPE: tp (top positive), tn (top negative), bp (bottom positive), bn (bottom negative)
                - COLUMN_NUMBER: A number, typically referring to segments or positions along the rail (e.g., 1 up to 50)
                - Example: "breadboard.tp.1" refers to position 1 on the top positive (+) rail
                - Example: "breadboard.bn.12" refers to position 12 on the bottom negative (-) rail

            ### Breadboard Explanation
            A breadboard is divided into two halves separated by a central gap:
            - Top half: 5 rows of holes, commonly labeled a, b, c, d, e (from top to bottom for each column segment).
            - Bottom half: 5 rows of holes, commonly labeled f, g, h, i, j (from top to bottom for each column segment).
            - The columns are typically numbered 1-60 from left to right. So, for each column number, there's a set of 'a-e' holes and a set of 'f-j' holes.

            #### Electrical Connections:
            - **Terminal Strips (the main area with rows a-e and rows f-j):**
                - Within each half (top or bottom), and for each column number, **the 5 holes in that column segment are electrically connected vertically.**
                    - Example: `breadboard.1a`, `breadboard.1b`, `breadboard.1c`, `breadboard.1d`, and `breadboard.1e` are all connected.
                    - Example: `breadboard.1f`, `breadboard.1g`, `breadboard.1h`, `breadboard.1i`, and `breadboard.1j` are all connected.
                - **Holes in different columns are NOT connected.** (e.g., `breadboard.1a` is not connected to `breadboard.2a`)
                - **The top half (holes a-e) and the bottom half (holes f-j) are electrically separated by the central gap.** (e.g., `breadboard.1e` is not connected to `breadboard.1f`)
            - **Power Rails (tp, tn, bp, bn):**
                - **All holes in a single power rail (e.g., the 'tp' rail) are electrically connected horizontally along the length of that entire rail.**
                    - Example: All positions along "breadboard.tp" (e.g., `breadboard.tp.1`, `breadboard.tp.2`, ..., `breadboard.tp.50`) are connected.
                - Typically, the positive (+) and negative (-) rails are electrically separate from each other.
                - The top set of power rails (e.g., 'tp' and 'tn') are electrically separate from the bottom set of power rails (e.g., 'bp' and 'bn'), unless explicitly connected by external wires.

            ### Example
            ```json
            {{"components": [
                {{"id": "arduino1", "type": "Arduino Uno"}},
                {{"id": "breadboard1", "type": "Breadboard"}},
                {{"id": "ntc sensor1", "type": "NTC temperature sensor", "properties": {{"temperature": "24"}}}}
              ],
              "connections": [
                ["breadboard1.29g", "arduino1.gnd3" ],
                ["ntc sensor1.VCC", "breadboard1.28f"],
                ["ntc sensor1.GND", "breadboard1.29f"],
                ["ntc sensor1.OUT", "breadboard1.27f"],
                ["breadboard1.28g", "arduino.5V"],
                ["breadboard1.27g", "arduino.A0"]
              ]
            }}
            ```

            ### Important Constraints
            - Each Arduino pin can only have ONE connection assigned to it
            - Each breadboard hole can only have ONE connection assigned to it
            - Direct pin-to-pin connections without using a breadboard are not permitted.

            Pay attention to the internal connections of the breadboard.
            Based on the code, provide a complete JSON with all components and connections to create a functional physical circuit with breadboard layout.

            ## Project Description
            {project_description}

            ## Arduino Code
            ```cpp
            {sketch_code}
            ```
            """

    if mode == "logical":
        return logical_prompt
    else:
        return physical_prompt

def run_hardware_test(project_path, mode, llm_provider, model_name, output_file=None, experiment_file=None, iterations=1, include_previous=False, save_intermediates=False):
    """Run hardware design test for a specific project and mode.

    Args:
        project_path: Path to the project directory
        mode: Mode of hardware generation ("logical" or "physical")
        llm_provider: LLM provider to use ("openai", "anthropic", or "custom")
        model_name: Name of the model to use
        output_file: Optional output file path for results
        experiment_file: Optional path to experiment results file
        iterations: Number of iterations for self-improvement
        include_previous: Whether to include previous results in improvement prompts
        save_intermediates: Whether to save intermediate diagram files
    """
    # Initialize logger
    log_message, logs = create_logger()

    log_message(f"Testing hardware design generation for project: {os.path.basename(project_path)}")
    
    if iterations > 1:
        log_message(f"Self-improvement enabled with {iterations} iterations")
        if include_previous:
            log_message("Including previous results in improvement prompts")
        if save_intermediates:
            log_message("Saving intermediate diagram files")

    # 공통 결과 저장 함수 정의
    def save_results_and_experiment(results):
        # Create results directory structure
        project_name = os.path.basename(project_path)
        model_dir = model_name.replace("-", "_") if model_name else llm_provider
        results_dir = os.path.join("results", model_dir, "diagram", mode)
        os.makedirs(results_dir, exist_ok=True)
        
        # Define output file path
        result_output_file = output_file
        if not result_output_file:
            result_output_file = os.path.join(results_dir, f"{project_name}_diagram_test.json")
        
        # Save results
        with open(result_output_file, "w") as f:
            json.dump(results, f, indent=2)
        log_message(f"\nEvaluation results saved to {result_output_file}")
        
        # Save experiment results if file path is provided
        if experiment_file:
            if os.path.exists(experiment_file):
                data = json.load(open(experiment_file))
            else:
                data = {
                    "level": project_path.split("/")[6] if len(project_path.split("/")) > 6 else "unknown"
                }
            
            # Get the best iteration if available, otherwise use the last one
            best_iter_index = results.get("best_iteration", -1)
            if best_iter_index >= 0 and best_iter_index < len(results.get("iterations", [])):
                best_iter = results["iterations"][best_iter_index]
            else:
                # Use the last iteration if no best or empty
                best_iter = results["iterations"][-1] if results.get("iterations") else {}
            
            # Create iterations data for experiment file
            iterations_data = []
            for iter_result in results.get("iterations", []):
                iter_hw_eval = None
                if iter_result.get("evaluation") and iter_result["evaluation"].get("metrics"):
                    metrics = iter_result["evaluation"]["metrics"]
                    iter_hw_eval = {
                        "duplicate_connections": metrics.get("duplicate_connections", {}).get("duplicate_connections", 0),
                        "unused_components": metrics.get("unused_components", {}).get("unused_components", 0),
                        "missing_components": metrics.get("missing_components", {}).get("missing_components", 0)
                    }
                    
                    if mode == "physical":
                        if "endpoint_conflicts" in metrics:
                            iter_hw_eval["endpoint_conflicts"] = metrics["endpoint_conflicts"].get("endpoint_conflicts", 0)
                        if "direct_connections" in metrics:
                            direct_conn = metrics["direct_connections"]
                            iter_hw_eval["direct_connections"] = direct_conn.get("direct_connections", 0)
                            iter_hw_eval["breadboard_connections"] = direct_conn.get("breadboard_connections", 0)
                    
                    if "unnecessary_components" in metrics:
                        iter_hw_eval["unnecessary_components"] = metrics["unnecessary_components"].get("unnecessary_components", 0)
                    
                    if "component_attrs" in metrics:
                        iter_hw_eval["incorrect_attrs"] = metrics["component_attrs"].get("incorrect_attrs", 0)
                
                iterations_data.append({
                    "iteration": iter_result.get("iteration", 0),
                    "success": int(iter_result.get("success", False)),
                    "converting": iter_result.get("converting", False),
                    "backup_file": iter_result.get("backup_file"),
                    "hardware_evaluation_result": iter_hw_eval
                })
            
            # Prepare hardware evaluation metrics for experiment section from best iteration
            hw_evaluation = None
            if best_iter.get("evaluation") and best_iter["evaluation"].get("metrics"):
                metrics = best_iter["evaluation"]["metrics"]
                hw_evaluation = {
                    "duplicate_connections": metrics.get("duplicate_connections", {}).get("duplicate_connections", 0),
                    "unused_components": metrics.get("unused_components", {}).get("unused_components", 0),
                    "missing_components": metrics.get("missing_components", {}).get("missing_components", 0)
                }
                
                if mode == "physical":
                    if "endpoint_conflicts" in metrics:
                        hw_evaluation["endpoint_conflicts"] = metrics["endpoint_conflicts"].get("endpoint_conflicts", 0)
                    if "direct_connections" in metrics:
                        direct_conn = metrics["direct_connections"]
                        hw_evaluation["direct_connections"] = direct_conn.get("direct_connections", 0)
                        hw_evaluation["breadboard_connections"] = direct_conn.get("breadboard_connections", 0)
                        hw_evaluation["direct_connection_percentage"] = direct_conn.get("direct_connection_percentage", 0)
                        hw_evaluation["breadboard_connection_percentage"] = direct_conn.get("breadboard_connection_percentage", 0)
                    
                    # Derived success metrics
                    for metric_name in [
                        "success_if_not_endpoint_conflicts",
                        "success_if_not_direct_connections",
                        "success_if_not_endpoint_conflicts_direct_connections"
                    ]:
                        if metric_name in metrics:
                            hw_evaluation[metric_name] = metrics[metric_name]
                
                if "unnecessary_components" in metrics:
                    hw_evaluation["unnecessary_components"] = metrics["unnecessary_components"].get("unnecessary_components", 0)
                
                # 컴포넌트 속성(attrs) 평가 결과 추가
                if "component_attrs" in metrics:
                    hw_evaluation["incorrect_attrs"] = metrics["component_attrs"].get("incorrect_attrs", 0)
                    # 잘못된 속성 세부 항목 추가 (선택 사항)
                    if metrics["component_attrs"].get("incorrect_attrs_list"):
                        hw_evaluation["incorrect_attrs_list"] = metrics["component_attrs"].get("incorrect_attrs_list", [])
                
                # 추가 조건부 성공 메트릭
                for metric_name in [
                    "success_if_not_incorrect_attrs",
                    "success_if_not_endpoint_conflicts_incorrect_attrs",
                    "success_if_not_direct_connections_incorrect_attrs",
                    "success_if_not_endpoint_conflicts_direct_connections_incorrect_attrs"
                ]:
                    if metric_name in metrics:
                        hw_evaluation[metric_name] = metrics[metric_name]
            
            data[f"{mode}_hardware"] = {
                "result": int(results.get("final_success", False)),
                "converting": best_iter.get("converting", False),
                "iterations": iterations_data,
                "best_iteration": results.get("best_iteration", -1),
                "total_iterations": results.get("total_iterations", 0),
                "hardware_evaluation_result": hw_evaluation,
                "wokwi_output": best_iter.get("wokwi_output"),
                "backup_file": best_iter.get("backup_file"),
                "error": best_iter.get("error")
            }
            
            with open(experiment_file, 'w') as f:
                json.dump(data, f, indent=4)
            
            log_message(f"Experiment results saved to {experiment_file}")
        
        return result_output_file

    # List to store all iteration results
    all_iterations = []
    
    # Variables to track current state
    initial_prompt = None
    diagram_file = os.path.join(project_path, "diagram.json")
    original_backup_file = f"{diagram_file}.original"
    original_diagram_backed_up = False
    final_success = False
    
    try:
        # Generate initial prompt
        log_message("Generating initial prompt...")
        try:
            project_data = load_project_files(project_path, ["description", "code", "scenario"])
            initial_prompt = generate_prompt(parse_description(project_data["description"], "hardware"), project_data["code"], mode)
        except Exception as e:
            log_message(f"Error generating initial prompt: {e}")
            error_message = f"Error generating initial prompt: {e}"
            
            # 실패 결과 저장
            results = {
                "project": os.path.basename(project_path),
                "mode": mode,
                "llm": llm_provider,
                "model": model_name,
                "prompt": None,
                "iterations": [],
                "final_success": False,
                "best_iteration": -1,
                "total_iterations": 0,
                "error": error_message,
                "log": logs
            }
            
            save_results_and_experiment(results)
            return results, None
            
        if not initial_prompt:
            log_message("Failed to generate initial prompt")
            error_message = "Failed to generate initial prompt"
            
            # 실패 결과 저장
            results = {
                "project": os.path.basename(project_path),
                "mode": mode,
                "llm": llm_provider,
                "model": model_name,
                "prompt": None,
                "iterations": [],
                "final_success": False,
                "best_iteration": -1,
                "total_iterations": 0,
                "error": error_message,
                "log": logs
            }
            
            save_results_and_experiment(results)
            return results, None
        
        # Backup original diagram if it exists and backup doesn't exist yet
        if os.path.exists(diagram_file) and not os.path.exists(original_backup_file):
            try:
                log_message("Backing up original diagram...")
                shutil.copy2(diagram_file, original_backup_file)
                original_diagram_backed_up = True
            except Exception as e:
                log_message(f"Error backing up original diagram: {e}")
        
        # Begin iterations
        current_prompt = initial_prompt
        previous_results = None
        previous_error = None
        
        for iteration in range(iterations):
            log_message(f"\n--- Starting Iteration {iteration+1}/{iterations} ---\n")
            
            # Variables to track this iteration's results
            generated_text = None
            generated_diagram = None
            wokwi_diagram = None
            test_result = False
            test_stdout = None
            test_stderr = None
            compile_result = False
            gen_backup_file = None
            evaluation_results = None
            error_message = None
            
            # Generate improvement prompt for iterations > 0
            if iteration > 0 and all_iterations:
                log_message(f"Generating improvement prompt for iteration {iteration+1}...")
                last_iteration = all_iterations[-1]
                current_prompt = generate_improvement_prompt(
                    original_prompt=initial_prompt,
                    iteration=iteration,
                    previous_generation=json.dumps(last_iteration["generated_diagram"], indent=2) if last_iteration.get("generated_diagram") else "Failed to generate valid diagram",
                    include_previous_results=include_previous,
                    previous_results=previous_results,
                    previous_error=previous_error
                )
            
            # Generate hardware design using LLM
            log_message(f"Generating {mode} hardware design using {llm_provider.upper()}...")
            try:
                generated_text = generate_with_llm(current_prompt, llm_provider)
            except Exception as e:
                log_message(f"Error during LLM generation: {e}")
                error_message = f"Error during LLM generation: {e}"
                generated_text = None
            
            if not generated_text:
                log_message(f"Failed to generate hardware design in iteration {iteration+1}")
                error_message = f"Failed to generate hardware design in iteration {iteration+1}"
                
                # Add failed iteration to results
                all_iterations.append({
                    "iteration": iteration,
                    "prompt": current_prompt,
                    "generated_text": generated_text,
                    "generated_diagram": None,
                    "success": False,
                    "compile_result": False,
                    "test_result": False,
                    "converting": False,
                    "error": error_message,
                    "wokwi_output": {"stdout": None, "stderr": None},
                    "backup_file": None,
                    "evaluation": None
                })
                
                # Continue to next iteration
                continue
            
            # Parse the generated diagram
            try:
                # Extract JSON from the response
                json_start = generated_text.find('{')
                json_end = generated_text.rfind('}')
                
                if json_start >= 0 and json_end >= 0:
                    json_text = generated_text[json_start:json_end+1]

                    # Remove comments from JSON before parsing
                    # Remove single-line comments (both // and # styles)
                    json_text = re.sub(r'\s*//.*$', '', json_text, flags=re.MULTILINE)
                    json_text = re.sub(r'\s*#.*$', '', json_text, flags=re.MULTILINE)

                    # Remove multi-line comments
                    json_text = re.sub(r'/\*.*?\*/', '', json_text, flags=re.DOTALL)

                    try:
                        generated_diagram = json.loads(json_text)
                        log_message("Successfully parsed generated diagram")
                    except json.JSONDecodeError as e:
                        log_message(f"Error parsing JSON after comment removal: {e}")
                        log_message(f"Processed JSON text: {json_text}")
                        error_message = f"Error parsing JSON: {e}"
                        generated_diagram = None
                else:
                    log_message("Could not find JSON in the generated text")
                    error_message = "Could not find JSON in the generated text"
                    generated_diagram = None
            except Exception as e:
                log_message(f"Error parsing generated diagram: {e}")
                error_message = f"Error parsing generated diagram: {e}"
                generated_diagram = None
            
            if not generated_diagram:
                # Add failed iteration to results
                all_iterations.append({
                    "iteration": iteration,
                    "prompt": current_prompt,
                    "generated_text": generated_text,
                    "generated_diagram": None,
                    "success": False,
                    "compile_result": False,
                    "test_result": False,
                    "converting": False,
                    "error": error_message,
                    "wokwi_output": {"stdout": None, "stderr": None},
                    "backup_file": None,
                    "evaluation": None
                })
                
                # Continue to next iteration
                continue
            
            # Validate the generated diagram against SHDF schema
            log_message("Validating generated diagram against SHDF schema...")
            try:
                is_valid, errors = validate_shdf_document(generated_diagram)
                if not is_valid:
                    log_message("Generated diagram is not valid SHDF:")
                    for error in errors:
                        log_message(f"  - {error}")
                    log_message("Continuing with conversion, but it might fail due to validation errors")
                else:
                    log_message("Generated diagram is valid SHDF")
            except Exception as e:
                log_message(f"Error during validation: {e}")
                error_message = f"Error during validation: {e}"
                # Continue despite validation error
            
            # Compile with PlatformIO
            log_message("Compiling with PlatformIO...")
            try:
                compile_result, compile_stdout, compile_stderr = compile_with_platformio(project_path)
                log_message(f"Compilation: {'Success' if compile_result else 'Failed'}")
                # 컴파일 실패 시 오류 메시지 추가
                if not compile_result:
                    log_message(f"Compilation stderr: {compile_stderr.strip()}")
                    error_message = (error_message + "; " if error_message else "") + f"Compilation failed: {compile_stderr.strip()}"
            except Exception as e:
                log_message(f"Error during compilation: {e}")
                error_message = (error_message + "; " if error_message else "") + f"Error during compilation: {e}"
                compile_result = False
                compile_stdout = None
                compile_stderr = None
            
            # Convert diagram to Wokwi format
            if generated_diagram:
                log_message("Converting diagram to Wokwi format...")
                try:
                    wokwi_diagram = convert_standard_to_wokwi(generated_diagram, mode=mode)
                    log_message("Conversion successful")
                except Exception as e:
                    log_message(f"Error during conversion: {e}")
                    error_message = (error_message + "; " if error_message else "") + f"Error during conversion: {e}"
                    wokwi_diagram = None
            
            # Include a test init value if it exists
            if wokwi_diagram:
                try:
                    wokwi_diagram = load_test_values(wokwi_diagram, project_path)
                except Exception as e:
                    log_message(f"Error loading test values: {e}")
                    error_message = (error_message + "; " if error_message else "") + f"Error loading test values: {e}"
            
            # Save generated diagram and run tests if conversion was successful
            if wokwi_diagram:
                try:
                    os.makedirs(os.path.dirname(diagram_file), exist_ok=True)
                    with open(diagram_file, "w") as f:
                        json.dump(wokwi_diagram, f, indent=2)
                    log_message(f"Generated diagram saved to {diagram_file}")
                    
                    # Save intermediate diagram files if requested
                    if save_intermediates:
                        try:
                            intermediate_backup = get_backup_filename(
                                diagram_file, 
                                f"{mode}_diagram_gen_iter{iteration}", 
                                model_name, 
                                llm_provider,
                                mode
                            )
                            shutil.copy2(diagram_file, intermediate_backup)
                            log_message(f"Saved intermediate diagram to {intermediate_backup}")
                            gen_backup_file = intermediate_backup
                        except Exception as e:
                            log_message(f"Error saving intermediate backup: {e}")
                    
                    # Run tests with wokwi-cli
                    log_message("Running tests with wokwi-cli...")
                    try:
                        test_result, test_stdout, test_stderr = run_wokwi_tests(project_path)
                        log_message(f"Testing: {'Success' if test_result else 'Failed'}")
                        # 테스트 실패 시 오류 메시지와 stderr 추가
                        if not test_result and test_stderr:
                            log_message(f"Testing stderr: {test_stderr.strip()}")
                            error_message = (error_message + "; " if error_message else "") + f"Testing failed: {test_stderr.strip()}"
                    except Exception as e:
                        log_message(f"Error during testing: {e}")
                        error_message = (error_message + "; " if error_message else "") + f"Error during testing: {e}"
                        test_result = False
                        test_stdout = None
                        test_stderr = None
                    
                    # Save regular backup if not saving intermediates
                    if not save_intermediates:
                        try:
                            gen_backup_file = get_backup_filename(diagram_file, f"{mode}_diagram_gen", model_name, llm_provider, mode)
                            shutil.copy2(diagram_file, gen_backup_file)
                            log_message(f"Saved generated diagram to {gen_backup_file}")
                        except Exception as e:
                            log_message(f"Error saving backup: {e}")
                            error_message = (error_message + "; " if error_message else "") + f"Error saving backup: {e}"
                except Exception as e:
                    log_message(f"Error saving diagram: {e}")
                    error_message = (error_message + "; " if error_message else "") + f"Error saving diagram: {e}"
                    test_result = False
            else:
                log_message("Warning: No valid diagram to save and test")
                error_message = error_message or "No valid diagram to save and test"
                test_result = False
            
            # Evaluate hardware design
            if generated_diagram:
                log_message("\nEvaluating hardware design metrics...")
                
                # Load reference diagram if it exists
                reference_diagram = None
                reference_file = os.path.join(project_path, "diagram.json.original")
                if os.path.exists(reference_file):
                    try:
                        with open(reference_file, "r") as f:
                            reference_wokwi = json.load(f)
                            # Convert Wokwi to SHDF if needed
                            from converters.wokwi_to_standard import convert_wokwi_to_standard
                            reference_diagram = convert_wokwi_to_standard(reference_wokwi, mode)
                            log_message("Loaded reference diagram for comparison")
                    except Exception as e:
                        log_message(f"Error loading reference diagram: {e}")
                        error_message = (error_message + "; " if error_message else "") + f"Error loading reference diagram: {e}"
                
                # Run evaluation
                try:
                    evaluation_results = evaluate_hardware_design(generated_diagram, reference_diagram, mode, project_path)
                    
                    # Log evaluation results
                    if "metrics" in evaluation_results:
                        metrics = evaluation_results["metrics"]
                        # Log various metrics (duplicate connections, unused components, etc.)
                        if "duplicate_connections" in metrics:
                            dup_conn = metrics["duplicate_connections"]
                            log_message(f"Duplicate Connections: {dup_conn.get('duplicate_connections', 0)}")
                        
                        if "unused_components" in metrics:
                            unused_comp = metrics["unused_components"]
                            log_message(f"Unused Components: {unused_comp.get('unused_components', 0)}")
                            if unused_comp.get('unused_components', 0) > 0 and unused_comp.get('unused_components_list'):
                                log_message("Unused component list:")
                                for comp in unused_comp.get('unused_components_list', []):
                                    log_message(f"  - {comp}")
                        
                        if "missing_components" in metrics:
                            missing_comp = metrics["missing_components"]
                            log_message(f"Missing Components: {missing_comp.get('missing_components', 0)}")
                            if missing_comp.get('missing_components', 0) > 0 and missing_comp.get('missing_components_list'):
                                log_message("Missing component list:")
                                for comp in missing_comp.get('missing_components_list', []):
                                    log_message(f"  - {comp}")
                        
                        if "unnecessary_components" in metrics:
                            unnecessary_comp = metrics["unnecessary_components"]
                            log_message(f"Unnecessary Components: {unnecessary_comp.get('unnecessary_components', 0)}")
                        
                        # 물리적 하드웨어 모드에 특화된 메트릭
                        if mode == "physical":
                            if "endpoint_conflicts" in metrics:
                                ep_conflicts = metrics["endpoint_conflicts"]
                                log_message(f"Endpoint Conflicts: {ep_conflicts.get('endpoint_conflicts', 0)}")
                                if ep_conflicts.get('endpoint_conflicts', 0) > 0 and ep_conflicts.get('conflicts_list'):
                                    log_message("Endpoint conflicts list:")
                                    for conflict in ep_conflicts.get('conflicts_list', []):
                                        log_message(f"  - {conflict}")
                            
                            if "direct_connections" in metrics:
                                direct_conn = metrics["direct_connections"]
                                log_message(f"Direct Connections: {direct_conn.get('direct_connections', 0)}")
                                log_message(f"Breadboard Connections: {direct_conn.get('breadboard_connections', 0)}")
                                if direct_conn.get('direct_connections', 0) > 0 and direct_conn.get('direct_connections_list'):
                                    log_message("Direct connections list:")
                                    for conn in direct_conn.get('direct_connections_list', []):
                                        log_message(f"  - {conn}")
                        
                        # 컴포넌트 속성 체크 결과 로깅
                        if "component_attrs" in metrics:
                            attrs_results = metrics["component_attrs"]
                            log_message(f"Incorrect Component Attributes: {attrs_results.get('incorrect_attrs', 0)}")
                            if attrs_results.get('incorrect_attrs', 0) > 0 and attrs_results.get('incorrect_attrs_list'):
                                log_message("Incorrect attribute details:")
                                for item in attrs_results.get('incorrect_attrs_list', []):
                                    log_message(f"  - {item['component_id']} ({item['component_type']}): {item['attribute']} = {item['generated_value']} (should be {item['reference_value']})")
                        
                        # Calculate derived success metrics
                        if mode == "physical" and "metrics" in evaluation_results:
                            metrics = evaluation_results["metrics"]
                            is_successful = compile_result and test_result
                            
                            # Calculate metric values (success_if_not_endpoint_conflicts, etc.)
                            # Get conflict counts (default to 1 if key missing to fail check)
                            endpoint_conflicts_count = metrics.get("endpoint_conflicts", {}).get("endpoint_conflicts", 1)
                            direct_connections_count = metrics.get("direct_connections", {}).get("direct_connections", 1)
                            
                            # Calculate derived metrics
                            success_if_ep_conflicts = 1 if is_successful and endpoint_conflicts_count == 0 else 0
                            success_if_direct_conn = 1 if is_successful and direct_connections_count == 0 else 0
                            success_if_both = 1 if is_successful and endpoint_conflicts_count == 0 and direct_connections_count == 0 else 0
                            
                            # Add them to the metrics dictionary
                            metrics["success_if_not_endpoint_conflicts"] = success_if_ep_conflicts
                            metrics["success_if_not_direct_connections"] = success_if_direct_conn
                            metrics["success_if_not_endpoint_conflicts_direct_connections"] = success_if_both
                            
                            log_message(f"Calculated derived success metrics:")
                            log_message(f"  - success_if_not_endpoint_conflicts: {success_if_ep_conflicts}")
                            log_message(f"  - success_if_not_direct_connections: {success_if_direct_conn}")
                            log_message(f"  - success_if_not_endpoint_conflicts_direct_connections: {success_if_both}")
                            
                            # Calculate success metrics with incorrect_attrs
                            if "component_attrs" in metrics:
                                incorrect_attrs_count = metrics["component_attrs"].get("incorrect_attrs", 1)  # Default to 1 to fail check if missing
                                
                                # Calculate success if no incorrect attributes
                                success_if_not_incorrect_attrs = 1 if is_successful and incorrect_attrs_count == 0 else 0
                                
                                # Calculate combined success metrics
                                success_if_ep_conflicts_incorrect_attrs = 1 if is_successful and endpoint_conflicts_count == 0 and incorrect_attrs_count == 0 else 0
                                success_if_direct_conn_incorrect_attrs = 1 if is_successful and direct_connections_count == 0 and incorrect_attrs_count == 0 else 0
                                success_if_all = 1 if is_successful and endpoint_conflicts_count == 0 and direct_connections_count == 0 and incorrect_attrs_count == 0 else 0
                                
                                # Add to metrics dictionary
                                metrics["success_if_not_incorrect_attrs"] = success_if_not_incorrect_attrs
                                metrics["success_if_not_endpoint_conflicts_incorrect_attrs"] = success_if_ep_conflicts_incorrect_attrs
                                metrics["success_if_not_direct_connections_incorrect_attrs"] = success_if_direct_conn_incorrect_attrs
                                metrics["success_if_not_endpoint_conflicts_direct_connections_incorrect_attrs"] = success_if_all
                                
                                log_message(f"Calculated additional derived success metrics with incorrect_attrs:")
                                log_message(f"  - success_if_not_incorrect_attrs: {success_if_not_incorrect_attrs}")
                                log_message(f"  - success_if_not_endpoint_conflicts_incorrect_attrs: {success_if_ep_conflicts_incorrect_attrs}")
                                log_message(f"  - success_if_not_direct_connections_incorrect_attrs: {success_if_direct_conn_incorrect_attrs}")
                                log_message(f"  - success_if_not_endpoint_conflicts_direct_connections_incorrect_attrs: {success_if_all}")
                except Exception as e:
                    log_message(f"Error during evaluation: {e}")
                    error_message = f"Error during evaluation: {e}"
                    evaluation_results = None
            
            # Always restore original diagram (for next iteration or at the end)
            if original_diagram_backed_up or os.path.exists(original_backup_file):
                try:
                    shutil.copy2(original_backup_file, diagram_file)
                    log_message("Restored original diagram for next iteration")
                except Exception as e:
                    log_message(f"Error restoring original diagram: {e}")
            
            # Store results for this iteration
            iteration_success = test_result
            all_iterations.append({
                "iteration": iteration,
                "prompt": current_prompt,
                "generated_text": generated_text,
                "generated_diagram": generated_diagram,
                "success": iteration_success,
                "compile_result": compile_result,
                "test_result": test_result,
                "converting": True if wokwi_diagram else False,
                "error": error_message,
                "wokwi_output": {
                    "stdout": test_stdout,
                    "stderr": test_stderr
                },
                "backup_file": gen_backup_file,
                "evaluation": evaluation_results
            })
            
            # Update previous results for next iteration
            previous_results = {
                "success": iteration_success,
                "compile_result": compile_result, 
                "test_result": test_result
            }
            previous_error = error_message
            
            # Update final success if any iteration succeeds
            if iteration_success:
                final_success = True
                log_message(f"\n✅ Iteration {iteration+1} successful!")
                # 성공 시 반복 중단
                log_message("Success achieved! Stopping iterations early.")
                break
            else:
                log_message(f"\n❌ Iteration {iteration+1} failed.")
            
            log_message(f"--- Completed Iteration {iteration+1}/{iterations} ---")
        
    except Exception as e:
        log_message(f"Unexpected error: {e}")
        error_message = f"Unexpected error: {e}"
    
    finally:
        # Always restore original diagram if backup exists at the end
        if original_diagram_backed_up or os.path.exists(original_backup_file):
            try:
                shutil.copy2(original_backup_file, diagram_file)
                log_message("Restored original diagram")
            except Exception as e:
                log_message(f"Error restoring original diagram: {e}")
    
    # Find the best iteration (first successful one, or last one if none succeeded)
    best_iteration = next((i for i, iter_result in enumerate(all_iterations) if iter_result["success"]), len(all_iterations) - 1 if all_iterations else -1)
    
    # Prepare results
    results = {
        "project": os.path.basename(project_path),
        "mode": mode,
        "llm": llm_provider,
        "model": model_name,
        "prompt": initial_prompt,
        "iterations": all_iterations,
        "final_success": final_success,
        "best_iteration": best_iteration,
        "total_iterations": len(all_iterations),
        "log": logs
    }
    
    # Save results
    result_file = save_results_and_experiment(results)
    
    if final_success:
        log_message(f"\n✅ Success! At least one iteration was successful.")
        successful_iterations = sum(1 for iter_result in all_iterations if iter_result["success"])
        log_message(f"Successful iterations: {successful_iterations}/{len(all_iterations)}")
    else:
        log_message(f"\n❌ Failed! All {len(all_iterations)} iterations failed.")
    
    return results, result_file

def main():
    parser = argparse.ArgumentParser(description="Test LLM hardware design generation for Arduino projects")
    parser.add_argument("project_path", help="Path to the Arduino project")
    parser.add_argument("--mode", choices=["logical", "physical", "both"], default="physical",
                       help="Mode of hardware generation: logical circuit, physical breadboard layout, or both")
    parser.add_argument("--llm", choices=["openai", "anthropic", "gemini", "ollama", "custom"],
                        default="openai", help="LLM provider to use")
    parser.add_argument("--model", help="Specific model to use (overrides environment variable)")
    parser.add_argument("--output", help="Output JSON file for results")
    parser.add_argument("--experiment", help="Output JSON file for experiments", default=None)
    # Add self-improvement related parameters
    parser.add_argument("--iterations", type=int, default=1,
                       help="Number of iterations for self-improvement (default: 1)")
    parser.add_argument("--include-previous", action="store_true",
                       help="Include previous results in improvement prompts")
    parser.add_argument("--save-intermediates", action="store_true",
                       help="Save intermediate diagram files")
    args = parser.parse_args()

    # Get model name from command line or environment variable
    model_name = None
    if args.model:
        model_name = args.model
    elif args.llm == "openai":
        model_name = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
    elif args.llm == "anthropic":
        model_name = os.environ.get("ANTHROPIC_MODEL", "claude-3-haiku-20240307")
    elif args.llm == "gemini":
        model_name = os.environ.get("GEMINI_MODEL", "gemini-2.0-flash-lite")
    elif args.llm == "ollama":
        model_name = os.environ.get("OLLAMA_MODEL", "llama3")

    # Print model being used
    if model_name:
        print(f"Using {args.llm.capitalize()} model: {model_name}")

    # If mode is 'both', run tests for both logical and physical modes
    if args.mode == "both":
        print("\n=== Running Hardware Design Test for {} ===\n".format(os.path.basename(args.project_path)))

        # Run logical mode first
        print("Mode: LOGICAL")
        logical_results = run_hardware_test(
            args.project_path, 
            "logical", 
            args.llm, 
            model_name, 
            args.output, 
            args.experiment,
            args.iterations,
            args.include_previous,
            args.save_intermediates
        )

        # Then run physical mode
        print("\n=== Running Hardware Design Test for {} ===\n".format(os.path.basename(args.project_path)))
        print("Mode: PHYSICAL")
        physical_results = run_hardware_test(
            args.project_path, 
            "physical", 
            args.llm, 
            model_name, 
            args.output, 
            args.experiment,
            args.iterations,
            args.include_previous,
            args.save_intermediates
        )

        if args.experiment:
            if os.path.exists(args.experiment):
                data = json.load(open(args.experiment))
            else:
                data = {
                    "level": args.project_path.split("/")[6]
                }
            
            # Access the results dictionary from the tuple using index [0]
            data["logical_hardware"] = {
                "result": int(logical_results[0].get("success", 0)), # Use index [0] and .get() for safety
                "converting": logical_results[0].get("converting", False), # Use index [0] and .get()
                "hardware_evaluation_result": None, # Initialize as None
                "wokwi_output": logical_results[0].get("wokwi_output"), # Use index [0] and .get()
                "backup_file": logical_results[0].get("backup_file") # Use index [0] and .get()
            }

            # Safely access nested evaluation results for logical hardware
            logical_evaluation = logical_results[0].get("evaluation")
            if logical_evaluation and logical_evaluation.get("metrics"):
                logical_metrics = logical_evaluation["metrics"]
                data["logical_hardware"]["hardware_evaluation_result"] = {
                    "duplicate_connections": logical_metrics.get("duplicate_connections", {}).get("duplicate_connections", 0),
                    "unused_components": logical_metrics.get("unused_components", {}).get("unused_components", 0),
                    "unnecessary_components": logical_metrics.get("unnecessary_components", {}).get("unnecessary_components", 0),
                    "missing_components": logical_metrics.get("missing_components", {}).get("missing_components", 0)
                }

            # Access the results dictionary from the tuple using index [0]
            data["physical_hardware"] = {
                "result": int(physical_results[0].get("success", 0)), # Use index [0] and .get()
                "converting": physical_results[0].get("converting", False), # Use index [0] and .get()
                "hardware_evaluation_result": None, # Initialize as None
                "wokwi_output": physical_results[0].get("wokwi_output"), # Use index [0] and .get()
                "backup_file": physical_results[0].get("backup_file") # Use index [0] and .get()
            }

            # Safely access nested evaluation results for physical hardware
            physical_evaluation = physical_results[0].get("evaluation")
            if physical_evaluation and physical_evaluation.get("metrics"):
                physical_metrics = physical_evaluation["metrics"]
                physical_hw_eval_result = {
                    "duplicate_connections": physical_metrics.get("duplicate_connections", {}).get("duplicate_connections", 0),
                    "unused_components": physical_metrics.get("unused_components", {}).get("unused_components", 0),
                    "endpoint_conflicts": physical_metrics.get("endpoint_conflicts", {}).get("endpoint_conflicts", 0),
                    "unnecessary_components": physical_metrics.get("unnecessary_components", {}).get("unnecessary_components", 0),
                    "missing_components": physical_metrics.get("missing_components", {}).get("missing_components", 0)
                }
                
                # Safely access direct connection metrics
                direct_conn_metrics = physical_metrics.get("direct_connections", {})
                physical_hw_eval_result.update({
                    "direct_connections": direct_conn_metrics.get("direct_connections", 0),
                    "breadboard_connections": direct_conn_metrics.get("breadboard_connections", 0),
                    "direct_connection_percentage": direct_conn_metrics.get("direct_connection_percentage", 0),
                    "breadboard_connection_percentage": direct_conn_metrics.get("breadboard_connection_percentage", 0),
                })

                # Calculate derived success metrics based on evaluation results
                is_successful = physical_results[0].get("success", False)
                duplicate_connections_count = physical_metrics.get("duplicate_connections", {}).get("duplicate_connections", 1) # Default to 1 to fail check if missing
                direct_connections_count = direct_conn_metrics.get("direct_connections", 1) # Default to 1 to fail check if missing
                endpoint_conflicts_count = physical_metrics.get("endpoint_conflicts", {}).get("endpoint_conflicts", 1) # Default to 1

                physical_hw_eval_result.update({
                    "success_if_not_endpoint_conflicts": 1 if is_successful and endpoint_conflicts_count == 0 else 0,
                    "success_if_not_direct_connections": 1 if is_successful and direct_connections_count == 0 else 0,
                    "success_if_not_endpoint_conflicts_direct_connections": 1 if is_successful and endpoint_conflicts_count == 0 and direct_connections_count == 0 else 0
                })
                
                # 컴포넌트 속성 관련 조건부 성공 메트릭 추가
                if "component_attrs" in physical_metrics:
                    incorrect_attrs_count = physical_metrics["component_attrs"].get("incorrect_attrs", 1) # Default to 1 to fail check if missing
                    physical_hw_eval_result.update({
                        "success_if_not_incorrect_attrs": 1 if is_successful and incorrect_attrs_count == 0 else 0,
                        "success_if_not_endpoint_conflicts_incorrect_attrs": 1 if is_successful and endpoint_conflicts_count == 0 and incorrect_attrs_count == 0 else 0,
                        "success_if_not_direct_connections_incorrect_attrs": 1 if is_successful and direct_connections_count == 0 and incorrect_attrs_count == 0 else 0,
                        "success_if_not_endpoint_conflicts_direct_connections_incorrect_attrs": 1 if is_successful and endpoint_conflicts_count == 0 and direct_connections_count == 0 and incorrect_attrs_count == 0 else 0
                    })

                data["physical_hardware"]["hardware_evaluation_result"] = physical_hw_eval_result
        
            with open(args.experiment, 'w') as f:
                json.dump(data, f, indent=4)
                
            print("Experiment results saved to", args.experiment)
            
        return 

    # For single mode, print header and run the test
    print("\n=== Running Hardware Design Test for {} ===\n".format(os.path.basename(args.project_path)))
    print(f"Mode: {args.mode.upper()}")
    results = run_hardware_test(
        args.project_path, 
        args.mode, 
        args.llm, 
        model_name, 
        args.output, 
        args.experiment,
        args.iterations,
        args.include_previous,
        args.save_intermediates
    )


if __name__ == "__main__":
    main()