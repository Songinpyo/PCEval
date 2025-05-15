#!/usr/bin/env python3
# code_generation_test.py
# Tool for testing LLM's code generation capability for Arduino projects

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
    compile_with_platformio,
    create_logger,
    parse_description,
    generate_improvement_prompt
)
from converters.wokwi_to_standard import convert_wokwi_to_standard
from schema import validate_shdf_document
from evaluation.code_metrics import calculate_codebleu

def generate_prompt(project_path, mode="logical", log_message=None):
    """
    Generate a prompt for the LLM to generate Arduino code.

    Args:
        project_path: Path to the project directory
        mode: "logical" for logical hardware or "physical" for physical hardware
        log_message: Optional logging function

    Returns:
        A prompt string
    """
    # Load project files with the appropriate diagram mode
    project_data = load_project_files(project_path, ["description", "diagram", "scenario"], mode)

    # Convert Wokwi diagram to standardized format
    standard_diagram = convert_wokwi_to_standard(project_data['diagram'], mode)

    # Validate the converted diagram against SHDF schema
    is_valid, errors = validate_shdf_document(standard_diagram)
    if log_message:
        if not is_valid:
            log_message("Warning: Converted diagram is not valid SHDF:")
            for error in errors:
                log_message(f"  - {error}")
            log_message("Continuing with generation, but results may be affected by invalid diagram format.")
        else:
            log_message("Converted diagram is valid SHDF.")
    else:
        if not is_valid:
            print("\nWarning: Converted diagram is not valid SHDF:")
            for error in errors:
                print(f"  - {error}")
            print("Continuing with generation, but results may be affected by invalid diagram format.\n")
        else:
            print("\nConverted diagram is valid SHDF.\n")

    logical_prompt = """# Arduino Code Generation Task (Logical Hardware)

    ## Task
    Please generate Arduino code (main.ino) that will work with this logical hardware configuration and produce the expected behavior.
    The code should fulfill all requirements and pass all test steps in the scenario.

    Note that this is a LOGICAL circuit diagram, meaning it shows the direct connections between components at a conceptual level,
    NOT physical layout with breadboard positions.

    ### Output Format
    Please provide only the code without explanations or markdown formatting.

    ## Project Description
    {0}

    ## Hardware Configuration (Logical Circuit)
    Below is the JSON diagram describing the logical hardware circuit:
    ```json
    {1}
    ```
    """.format(parse_description(project_data['description'], mode="code"), json.dumps(standard_diagram, indent=2))

    physical_prompt = """# Arduino Code Generation Task (Physical Hardware)

    ## Task
    Please generate Arduino code (main.ino) that will work with this physical hardware configuration and produce the expected behavior.
    The code should fulfill all requirements and pass all test steps in the scenario.

    Note that this is a PHYSICAL circuit diagram, meaning it shows the actual breadboard layout with specific component placements
    and wire connections using breadboard positions.

    ### Output Format
    Please provide only the code without explanations or markdown formatting.

    ## Project Description
    {0}

    ## Hardware Configuration (Physical Breadboard Layout)
    
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

    Below is the JSON diagram describing the physical hardware circuit with breadboard layout:
    ```json
    {1}
    ```
    """.format(parse_description(project_data['description'], mode="code"), json.dumps(standard_diagram, indent=2))

    if mode == "logical":
        return logical_prompt
    else:
        return physical_prompt

def main():
    parser = argparse.ArgumentParser(description="Test LLM code generation for Arduino projects")
    parser.add_argument("project_path", help="Path to the Arduino project")
    parser.add_argument("--mode", choices=["logical", "physical"], default="logical",
                       help="Mode of hardware input: logical circuit or physical breadboard layout")
    parser.add_argument("--llm", choices=["openai", "anthropic", "gemini", "ollama", "custom"],
                        default="openai", help="LLM provider to use")
    parser.add_argument("--output", help="Output JSON file for results")
    parser.add_argument("--experiment", help="Output JSON file for experiments", default=None)
    # Add self-improvement related parameters
    parser.add_argument("--iterations", type=int, default=1,
                       help="Number of iterations for self-improvement (default: 1)")
    parser.add_argument("--include-previous", action="store_true",
                       help="Include previous results in improvement prompts")
    parser.add_argument("--save-intermediates", action="store_true",
                       help="Save intermediate code files")
    args = parser.parse_args()

    # Get model name from environment variable
    model_name = None
    if args.llm == "openai":
        model_name = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
    elif args.llm == "anthropic":
        model_name = os.environ.get("ANTHROPIC_MODEL", "claude-3-haiku-20240307")
    elif args.llm == "gemini":
        model_name = os.environ.get("GEMINI_MODEL", "gemini-2.0-flash-lite")
    elif args.llm == "ollama":
        model_name = os.environ.get("OLLAMA_MODEL", "llama3")

    # Initialize logger
    log_message, logs = create_logger()

    log_message(f"Testing code generation for project: {os.path.basename(args.project_path)}")
    
    if args.iterations > 1:
        log_message(f"Self-improvement enabled with {args.iterations} iterations")
        if args.include_previous:
            log_message("Including previous results in improvement prompts")
        if args.save_intermediates:
            log_message("Saving intermediate code files")

    # 공통 결과 저장 함수 정의
    def save_results_and_experiment(results):
        # Create results directory structure and save results
        project_name = os.path.basename(args.project_path)
        # Use model name instead of LLM provider for results directory
        model_dir = model_name.replace("-", "_") if model_name else args.llm
        results_dir = os.path.join("results", model_dir, "code", args.mode)
        os.makedirs(results_dir, exist_ok=True)

        # Define output file path
        output_file = args.output
        if not output_file:
            output_file = os.path.join(results_dir, f"{project_name}_code_test.json")

        # Save results
        with open(output_file, "w") as f:
            json.dump(results, f, indent=2)
        log_message(f"\nEvaluation results saved to {output_file}")
        
        # Save experiment results if file path is provided
        if args.experiment:
            if os.path.exists(args.experiment):
                data = json.load(open(args.experiment))
            else:
                data = {
                    "level": args.project_path.split("/")[6] if len(args.project_path.split("/")) > 6 else "unknown"
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
                iterations_data.append({
                    "iteration": iter_result.get("iteration", 0),
                    "success": int(iter_result.get("success", False)),
                    "compile_result": int(iter_result.get("compile_result", False)),
                    "backup_file": iter_result.get("backup_file"),
                    "codebleu_score": iter_result.get("codebleu_score")
                })

            data[f"{args.mode}_code"] = {
                "result": int(results.get("final_success", False)),
                "compile_result": int(any(iter_result.get("compile_result", False) for iter_result in results.get("iterations", []))),
                "iterations": iterations_data,
                "best_iteration": results.get("best_iteration", -1),
                "total_iterations": results.get("total_iterations", 0),
                "wokwi_output": best_iter.get("wokwi_output", {"stdout": None, "stderr": None}),
                "backup_file": best_iter.get("backup_file"),
                "codebleu_score": best_iter.get("codebleu_score"),
                "error": best_iter.get("error")
            }
            
            with open(args.experiment, 'w') as f:
                json.dump(data, f, indent=2)
                
            log_message(f"Experiment results saved to {args.experiment}")

    # List to store all iteration results
    all_iterations = []
    
    # Variables to track current state
    initial_prompt = None
    original_backup_file = None
    reference_code = None
    final_success = False
    
    try:
        # Generate initial prompt
        log_message("Generating initial prompt...")
        try:
            initial_prompt = generate_prompt(args.project_path, args.mode, log_message)
        except Exception as e:
            log_message(f"Error generating initial prompt: {e}")
            error_message = f"Error generating initial prompt: {e}"
            
            # 실패 결과 저장
            results = {
                "project": os.path.basename(args.project_path),
                "mode": args.mode,
                "llm": args.llm,
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
            return
            
        # Define code file path for use throughout the process
        code_file = os.path.join(args.project_path, "src", "main.ino")
        original_backup_file = f"{code_file}.original"
        
        # Backup original code if it exists and load reference code
        if os.path.exists(code_file):
            if not os.path.exists(original_backup_file):
                log_message("Backing up original code...")
                shutil.copy2(code_file, original_backup_file)
            # Load reference code from original file for CodeBLEU
            try:
                with open(code_file, 'r') as f_ref:
                    reference_code = f_ref.read()
            except Exception as e:
                log_message(f"Warning: Could not read reference code for CodeBLEU from {code_file}: {e}")
        else:
             log_message(f"Warning: No original code file found at {code_file} to use as reference for CodeBLEU.")
        
        # Begin iterations
        current_prompt = initial_prompt
        previous_results = None
        previous_error = None
        
        for iteration in range(args.iterations):
            log_message(f"\n--- Starting Iteration {iteration+1}/{args.iterations} ---\n")
            
            # Variables to track this iteration's results
            generated_response = None
            generated_code = None
            compile_result = False
            test_result = False
            test_stdout = None
            test_stderr = None
            gen_backup_file = None
            error_message = None
            codebleu_score = None
            
            # Generate improvement prompt for iterations > 0
            if iteration > 0 and all_iterations:
                log_message(f"Generating improvement prompt for iteration {iteration+1}...")
                last_iteration = all_iterations[-1]
                current_prompt = generate_improvement_prompt(
                    original_prompt=initial_prompt,
                    iteration=iteration,
                    previous_generation=last_iteration["generated_code"],
                    include_previous_results=args.include_previous,
                    previous_results=previous_results,
                    previous_error=previous_error
                )
            
            # Generate code using LLM
            log_message(f"Generating Arduino code using {args.llm.upper()}...")
            try:
                generated_response = generate_with_llm(current_prompt, args.llm)
            except Exception as e:
                log_message(f"Error during LLM generation: {e}")
                error_message = (error_message + "; " if error_message else "") + f"Error during LLM generation: {e}"
                generated_response = None
            
            if not generated_response:
                log_message(f"Failed to generate code in iteration {iteration+1}")
                error_message = (error_message + "; " if error_message else "") + f"Failed to generate code in iteration {iteration+1}"
                
                # Add failed iteration to results
                all_iterations.append({
                    "iteration": iteration,
                    "prompt": current_prompt,
                    "generated_response": None,
                    "generated_code": None,
                    "success": False,
                    "compile_result": False,
                    "test_result": False,
                    "error": error_message,
                    "wokwi_output": {"stdout": None, "stderr": None},
                    "backup_file": None,
                    "codebleu_score": None
                })
                
                # Continue to next iteration
                continue
            
            # Extract code from response
            try:
                generated_code = extract_code_from_response(generated_response)
                log_message("Code extracted from LLM response")
            except Exception as e:
                log_message(f"Error extracting code: {e}")
                error_message = (error_message + "; " if error_message else "") + f"Error extracting code: {e}"
                generated_code = None
            
            if not generated_code:
                log_message(f"Failed to extract valid code from response in iteration {iteration+1}")
                error_message = (error_message + "; " if error_message else "") + f"Failed to extract valid code from response in iteration {iteration+1}"
                
                # Add failed iteration to results
                all_iterations.append({
                    "iteration": iteration,
                    "prompt": current_prompt,
                    "generated_response": generated_response,
                    "generated_code": None,
                    "success": False,
                    "compile_result": False,
                    "test_result": False,
                    "error": error_message,
                    "wokwi_output": {"stdout": None, "stderr": None},
                    "backup_file": None,
                    "codebleu_score": None
                })
                
                # Continue to next iteration
                continue
            
            # Save generated code
            os.makedirs(os.path.dirname(code_file), exist_ok=True)
            with open(code_file, "w") as f:
                f.write(generated_code)
            
            log_message(f"Generated code saved to {code_file}")
            
            # Save intermediate code files if requested
            if args.save_intermediates:
                try:
                    intermediate_backup = get_backup_filename(
                        code_file, 
                        f"{args.mode}_main_gen_iter{iteration}", 
                        model_name, 
                        args.llm,
                        args.mode
                    )
                    shutil.copy2(code_file, intermediate_backup)
                    log_message(f"Saved intermediate code to {intermediate_backup}")
                    gen_backup_file = intermediate_backup
                except Exception as e:
                    log_message(f"Error saving intermediate backup: {e}")
            
            # Compile with PlatformIO
            log_message("Compiling with PlatformIO...")
            try:
                compile_result, compile_stdout, compile_stderr = compile_with_platformio(args.project_path)
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
            
            if compile_result:
                # Run tests with wokwi-cli
                log_message("Running tests with wokwi-cli...")
                try:
                    test_result, test_stdout, test_stderr = run_wokwi_tests(args.project_path)
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
            else:
                test_result = False
                test_stdout = None
                test_stderr = None
            
            # Calculate CodeBLEU score if possible
            if generated_code and reference_code:
                log_message("Calculating CodeBLEU score...")
                try:
                    codebleu_score = calculate_codebleu(generated_code, reference_code)
                    if codebleu_score is not None:
                        log_message(f"CodeBLEU score: {codebleu_score:.4f}")
                    else:
                        log_message("CodeBLEU score calculation skipped or failed.")
                except Exception as e:
                    log_message(f"Error during CodeBLEU calculation: {e}")
                    error_message = error_message + f"; Error during CodeBLEU calculation: {e}" if error_message else f"Error during CodeBLEU calculation: {e}"
            else:
                log_message("Skipping CodeBLEU calculation because generated or reference code is missing.")
            
            # Save regular backup if not saving intermediates
            if not args.save_intermediates:
                try:
                    gen_backup_file = get_backup_filename(code_file, f"{args.mode}_main_gen", model_name, args.llm, args.mode)
                    shutil.copy2(code_file, gen_backup_file)
                    log_message(f"Saved generated code to {gen_backup_file}")
                except Exception as e:
                    log_message(f"Error saving backup: {e}")
                    error_message = (error_message + "; " if error_message else "") + f"Error saving backup: {e}"
            
            # Store results for this iteration
            iteration_success = compile_result and test_result
            all_iterations.append({
                "iteration": iteration,
                "prompt": current_prompt,
                "generated_response": generated_response,
                "generated_code": generated_code,
                "success": iteration_success,
                "compile_result": compile_result,
                "test_result": test_result,
                "error": error_message,
                "wokwi_output": {
                    "stdout": test_stdout,
                    "stderr": test_stderr
                },
                "backup_file": gen_backup_file,
                "codebleu_score": codebleu_score
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
            
            log_message(f"--- Completed Iteration {iteration+1}/{args.iterations} ---")
            
    except Exception as e:
        log_message(f"Unexpected error: {e}")
        error_message = (error_message + "; " if error_message else "") + f"Unexpected error: {e}"
        
    finally:
        # Always restore original code if backup exists
        if original_backup_file and os.path.exists(original_backup_file):
            try:
                shutil.copy2(original_backup_file, code_file)
                log_message("Restored original code")
            except Exception as e:
                log_message(f"Error restoring original code: {e}")
        else:
            log_message("Warning: No original code backup found to restore")
    
    # Find the best iteration (first successful one, or last one if none succeeded)
    best_iteration = next((i for i, iter_result in enumerate(all_iterations) if iter_result["success"]), len(all_iterations) - 1 if all_iterations else -1)
    
    # Prepare results
    results = {
        "project": os.path.basename(args.project_path),
        "mode": args.mode,
        "llm": args.llm,
        "model": model_name,
        "prompt": initial_prompt,
        "iterations": all_iterations,
        "final_success": final_success,
        "best_iteration": best_iteration,
        "total_iterations": len(all_iterations),
        "log": logs
    }
    
    # Save the results
    save_results_and_experiment(results)
    
    if final_success:
        log_message(f"\n✅ Success! At least one iteration was successful.")
        successful_iterations = sum(1 for iter_result in all_iterations if iter_result["success"])
        log_message(f"Successful iterations: {successful_iterations}/{len(all_iterations)}")
    else:
        log_message(f"\n❌ Failed! All {len(all_iterations)} iterations failed.")

def extract_code_from_response(response):
    """
    Extract code from LLM response, removing markdown formatting if present.

    Args:
        response: The LLM response text

    Returns:
        Extracted code without markdown formatting
    """
    # Check for code blocks with ```
    code_block_pattern = r"```(?:arduino|c\+\+|cpp|ino)?\s*([\s\S]*?)```"
    code_blocks = re.findall(code_block_pattern, response)

    if code_blocks:
        # Return the first code block found
        return code_blocks[0].strip()

    # If no code blocks found, return the original response
    return response

if __name__ == "__main__":
    main()