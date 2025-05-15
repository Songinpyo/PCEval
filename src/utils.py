#!/usr/bin/env python3
# utils.py
# Common utilities for Arduino LLM testing modules

import os
import json
import yaml
import subprocess
import requests
import time

def load_project_files(project_path, file_types=None, diagram_mode="logical"):
    """
    Load necessary files from the project directory.

    Args:
        project_path: Path to the project directory
        file_types: List of file types to load (default: ["description", "code", "diagram", "scenario"])
        diagram_mode: Type of diagram to load ("logical" or "physical")

    Returns:
        Dictionary with loaded files
    """
    if file_types is None:
        file_types = ["description", "code", "diagram", "scenario"]

    result = {}

    # File paths
    description_path = os.path.join(project_path, "description.md")
    code_path = os.path.join(project_path, "src", "main.ino")

    # Select diagram path based on mode
    if diagram_mode == "logical":
        diagram_path = os.path.join(project_path, "diagram.json")
    else:  # physical
        diagram_path = os.path.join(project_path, "diagram_breadboard.json")
        # Fallback to logical diagram if physical doesn't exist
        if not os.path.exists(diagram_path):
            diagram_path = os.path.join(project_path, "diagram.json")
            print(f"Warning: Physical diagram not found at {diagram_path}, falling back to logical diagram")

    scenario_path = os.path.join(project_path, "scenario.yaml")

    # Load description.md if required
    if "description" in file_types:
        description = ""
        if os.path.exists(description_path):
            with open(description_path, "r") as f:
                description = f.read()
        else:
            print(f"Warning: description.md not found at {description_path}")
        result["description"] = description

    # Load main.ino if required
    if "code" in file_types:
        code = ""
        if os.path.exists(code_path):
            with open(code_path, "r") as f:
                code = f.read()
        else:
            print(f"Warning: main.ino not found at {code_path}")
        result["code"] = code

    # Load diagram.json if required
    if "diagram" in file_types:
        diagram = {}
        if os.path.exists(diagram_path):
            with open(diagram_path, "r") as f:
                diagram = json.load(f)
        else:
            print(f"Warning: diagram file not found at {diagram_path}")
        result["diagram"] = diagram
        # Also store which diagram mode was actually used
        result["diagram_mode"] = diagram_mode

    # Load scenario.yaml if required
    if "scenario" in file_types:
        scenario = {}
        if os.path.exists(scenario_path):
            with open(scenario_path, "r") as f:
                scenario = yaml.safe_load(f)
        else:
            print(f"Warning: scenario.yaml not found at {scenario_path}")
        result["scenario"] = scenario

    return result

def generate_with_openai(prompt, model=None):
    """
    Generate content using OpenAI API.

    Args:
        prompt: The prompt to send to the API
        model: The model to use (default: from environment variable)

    Returns:
        Generated content as string, or None if error
    """
    api_key = os.environ.get("OPENAI_API_KEY")
    model = model or os.environ.get("OPENAI_MODEL", "gpt-4o")

    if not api_key:
        print("Error: OpenAI API key not found in environment variables")
        return None

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    data = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
    }

    try:
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=data
        )
        response.raise_for_status()
        return response.json()['choices'][0]['message']['content']

    except Exception as e:
        print(f"Error with OpenAI API: {e}")
        if 'response' in locals() and hasattr(response, 'status_code') and response.status_code == 429:
            print("Rate limit exceeded. Waiting 60 seconds before retrying...")
            time.sleep(60)
            print("Retrying generation with OpenAI API...")
            return generate_with_openai(prompt, model)
        return None

def generate_with_anthropic(prompt, model=None):
    """
    Generate content using Anthropic API.

    Args:
        prompt: The prompt to send to the API
        model: The model to use (default: from environment variable)

    Returns:
        Generated content as string, or None if error
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    model = model or os.environ.get("ANTHROPIC_MODEL", "claude-3-opus-20240229")

    if not api_key:
        print("Error: Anthropic API key not found in environment variables")
        return None

    headers = {
        "Content-Type": "application/json",
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01"
    }

    data = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 4000
    }

    try:
        response = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers=headers,
            json=data
        )
        response.raise_for_status()
        return response.json()['content'][0]['text']

    except Exception as e:
        print(f"Error with Anthropic API: {e}")
        if 'response' in locals() and hasattr(response, 'status_code') and response.status_code == 429:
            print("Rate limit exceeded. Waiting 60 seconds before retrying...")
            time.sleep(60)
            print("Retrying generation with Anthropic API...")
            return generate_with_anthropic(prompt, model)
        return None

def generate_with_gemini(prompt, model=None):
    """
    Generate content using Gemini API.

    Args:
        prompt: The prompt to send to the API
        model: The model to use (default: from environment variable)

    Returns:
        Generated content as string, or None if error
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    model = model or os.environ.get("GEMINI_MODEL", "gemini-2.0-flash-lite")

    if not api_key:
        print("Error: Gemini API key not found in environment variables")
        return None

    headers = {
        "Content-Type": "application/json"
    }

    data = {
        "contents": [
            {
                "role": "user",
                "parts": [{"text": prompt}]
            }
        ],
        "generationConfig": {
            "maxOutputTokens": 4000,
        }
    }

    try:
        response = requests.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}",
            headers=headers,
            json=data
        )
        response.raise_for_status()
        return response.json()['candidates'][0]['content']['parts'][0]['text']

    except Exception as e:
        print(f"Error with Gemini API: {e}")
        if 'response' in locals() and hasattr(response, 'status_code') and response.status_code == 429:
            print("Rate limit exceeded. Waiting 60 seconds before retrying...")
            time.sleep(60)
            print("Retrying generation with Gemini API...")
            return generate_with_gemini(prompt, model)
        return None

def generate_with_ollama(prompt, model=None, system_message=None):
    """
    Generate content using Ollama API via the official Python library.

    Args:
        prompt: The prompt to send to the API
        model: The model to use (default: from environment variable)

    Returns:
        Generated content as string, or None if error
    """
    try:
        # Import the ollama library
        import ollama
    except ImportError:
        print("Error: Ollama Python library not found. Please install it with 'pip install ollama'")
        return None

    model = model or os.environ.get("OLLAMA_MODEL", "llama3")
    
    try:
        # If system message is provided, use chat API with messages format
        if system_message:
            response = ollama.chat(
                model=model,
                messages=[
                    {'role': 'system', 'content': system_message},
                    {'role': 'user', 'content': prompt}
                ],
                options={
                    'temperature': 0.2,
                    'num_predict': 4000
                }
            )
            return response['message']['content']
        # Otherwise use the simpler generate API
        else:
            response = ollama.generate(
                model=model,
                prompt=prompt,
                options={
                    'temperature': 0.2,
                    'num_predict': 4000
                }
            )
            return response['response']

    except Exception as e:
        print(f"Error with Ollama API: {e}")
        if 'model not found' in str(e).lower():
            print(f"Model '{model}' not found. Try running 'ollama pull {model}' to download it.")
        elif 'connection refused' in str(e).lower():
            print("Could not connect to Ollama. Make sure Ollama is installed and running.")
            print("Visit https://ollama.ai/ for installation instructions.")
        return None

def get_available_ollama_models():
    """
    Get a list of available Ollama models using the official Python library.

    Returns:
        List of model names, or empty list if error
    """
    try:
        # Import the ollama library
        import ollama
    except ImportError:
        print("Error: Ollama Python library not found. Please install it with 'pip install ollama'")
        return []

    try:
        # Get list of models
        models = ollama.list()
        return [model['name'] for model in models['models']]
    except Exception as e:
        print(f"Error getting Ollama models: {e}")
        if 'connection refused' in str(e).lower():
            print("Could not connect to Ollama. Make sure Ollama is installed and running.")
            print("Visit https://ollama.ai/ for installation instructions.")
        return []

def generate_with_llm(prompt, llm_provider):
    """
    Generate content using the specified LLM provider.

    Args:
        prompt: The prompt to send to the API
        llm_provider: The LLM provider to use ("openai", "anthropic", "gemini", "ollama", or "custom")
        system_message: Optional system message to set context

    Returns:
        Generated content as string, or None if error
    """
    if llm_provider == "openai":
        return generate_with_openai(prompt)
    elif llm_provider == "anthropic":
        return generate_with_anthropic(prompt)
    elif llm_provider == "gemini":
        return generate_with_gemini(prompt)
    elif llm_provider == "ollama":
        return generate_with_ollama(prompt)

def parse_description(description, mode="both"):
    result = []
    
    if mode == "code":
        selected_sections = ["Project Description", "Circuit Description", "Expected Behavior", "Success Criteria", "Notes for Implementation"]
    elif mode == "hardware":
        selected_sections = ["Project Description", "Circuit Description", "Success Criteria", "Notes for Implementation", "Attributes"]
    else:
        selected_sections = ["Project Description", "Circuit Description", "Expected Behavior", "Success Criteria", "Notes for Implementation", "Attributes"]
    
    selected = False
    lines = description.splitlines()
    
    for line in lines:
        if line.startswith("# "):
            result.append(line)
            continue
        
        if line.startswith("## "):
            heading = line[3:].strip()
            if heading in selected_sections:
                selected = True
            else:
                selected = False
                
        if selected:
            result.append(line)
    
    return "\n".join(result).strip()

def get_manual_input(prompt, end_marker="END"):
    """
    Get manual input from the user.

    Args:
        prompt: The prompt to display to the user
        end_marker: The marker that indicates the end of input

    Returns:
        User input as string
    """
    print("\n" + "="*80)
    print("PROMPT FOR LLM:")
    print("="*80)
    print(prompt)
    print("="*80 + "\n")

    print(f"Please submit this prompt to the LLM and paste the generated output below.")
    print(f"When finished, enter '{end_marker}' on a new line:\n")

    lines = []
    while True:
        line = input()
        if line.strip() == end_marker:
            break
        lines.append(line)

    return "\n".join(lines)

def get_backup_filename(base_path, prefix, model_name=None, llm_provider=None, mode=None):
    """
    Generate a backup filename with timestamp and model name, stored in a backup folder.

    Args:
        base_path: Path to the original file
        prefix: Prefix for the backup file
        model_name: Optional name of the LLM model used
        llm_provider: Optional LLM provider (openai, anthropic, custom)
        mode: Optional mode (logical, physical)

    Returns:
        Path to the backup file
    """
    timestamp = time.strftime("%Y%m%d_%H%M%S")

    # Extract project directory correctly
    # For diagram.json, the project dir is the parent directory
    # For src/main.ino, the project dir is the grandparent directory
    if os.path.basename(os.path.dirname(base_path)) == "src":
        project_dir = os.path.dirname(os.path.dirname(base_path))
    else:
        project_dir = os.path.dirname(base_path)

    base_name = os.path.basename(base_path)
    _, ext = os.path.splitext(base_name)

    # Create backup directory structure
    backup_dir = os.path.join(project_dir, "backup")
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)

    # Create model directory (use model name if available, otherwise use LLM provider)
    model_dir = model_name.replace("-", "_") if model_name else llm_provider
    if model_dir:
        backup_dir = os.path.join(backup_dir, model_dir)
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)

    # Determine subdirectory based on prefix
    if "code" in prefix or "main" in prefix:
        subdir = "code"
    elif "diagram" in prefix:
        subdir = "diagram"
    else:
        subdir = "other"

    subdir_path = os.path.join(backup_dir, subdir)
    if not os.path.exists(subdir_path):
        os.makedirs(subdir_path)

    # Add mode directory if provided
    if mode:
        mode_path = os.path.join(subdir_path, mode)
        if not os.path.exists(mode_path):
            os.makedirs(mode_path)
        subdir_path = mode_path

    # Add model name to filename if provided
    if model_name:
        model_suffix = f"_{model_name.replace('-', '_')}"
    else:
        model_suffix = ""

    return os.path.join(subdir_path, f"{prefix}{model_suffix}{ext}.{timestamp}.bak")

def run_wokwi_tests(project_path):
    """
    Run tests using wokwi-cli via npm start, passing the project path as an argument.

    Args:
        project_path: Path to the project directory containing diagram.json and scenario.yaml

    Returns:
        Tuple of (success, stdout, stderr)
    """
    # Determine absolute path for the project
    abs_project_path = os.path.abspath(project_path)

    workspace_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    wokwi_dir = os.path.join(workspace_root, "wokwi-cli") # User specified base_dir/wokwi-cli

    try:
        # Check if project path and wokwi directory exist
        if not os.path.isdir(abs_project_path):
            raise NotADirectoryError(f"Project directory not found at {abs_project_path}")
        if not os.path.isdir(wokwi_dir):
            raise NotADirectoryError(f"Wokwi directory not found at {wokwi_dir}")

        # Determine timeout
        long_projects = {
            "button_duration": 10000,
            "serial_monitor": 10000,
            "temperature_sensor": 15000,
            "servo_motor_basic": 10000,
            "distance_sensor": 15000,
            "multiple_timezone": 12000,
            "humidity_sensor": 10000,
            "serial_LCD_display": 8000,
            "button_LCD_display": 8000,
            "dht22_LCD_display": 12000,
            "binary_led": 7000,
            "calendar_display": 10000
        }
        timeout_ms = 5000 # Default timeout
        for long_project, duration in long_projects.items():
            # Check if the project name (last part of the path) matches
            if long_project == os.path.basename(abs_project_path):
                timeout_ms = duration
                break

        # Construct the command: npm start -- --diagram-file diagram.json --scenario scenario.yaml <abs_project_path> --timeout <timeout>
        command = [
            "npm", "start", "--",
            "--diagram-file", "diagram.json",
            "--scenario", "scenario.yaml",
            abs_project_path,
            "--timeout", str(timeout_ms)
        ]

        # Run wokwi-cli test using 'npm start --' from the wokwi_dir
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            cwd=wokwi_dir # Execute from the wokwi-cli directory
        )

        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        print(f"Error during testing: {e}")
        # Ensure stderr reflects the exception if subprocess didn't run
        stderr_output = ""
        if 'result' in locals() and hasattr(result, 'stderr'):
            stderr_output = result.stderr
        return False, "", f"{str(e)}\n{stderr_output}".strip()

def load_test_values(wokwi_diagram, project_path):
    with open(os.path.join(project_path, "scenario.yaml")) as f:
        scenario = yaml.safe_load(f)
    
    if "test-values" in scenario:
        print("Loading test values from scenario file...")
        for test_value in scenario["test-values"]:
            for part in wokwi_diagram["parts"]:
                if "part-type" in test_value:
                    if part["type"] == test_value["part-type"]:
                        part["attrs"][test_value["attr-name"]] = test_value["value"]
                elif "part-id" in test_value:
                    if part["id"] == test_value["part-id"]:
                        part["attrs"][test_value["attr-name"]] = test_value["value"]
        
    return wokwi_diagram

def compile_with_platformio(project_path):
    """
    Compile the Arduino code using PlatformIO.

    Args:
        project_path: Path to the project directory

    Returns:
        Tuple of (success, stdout, stderr)
    """
    try:
        # Check if platformio.ini exists
        pio_ini = os.path.join(project_path, "platformio.ini")
        if not os.path.exists(pio_ini):
            raise FileNotFoundError(f"platformio.ini not found at {pio_ini}")

        # Run PlatformIO build
        result = subprocess.run(
            ["pio", "run", "-d", project_path],
            capture_output=True,
            text=True
        )

        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        print(f"Error during compilation: {e}")
        return False, "", str(e)

def create_logger(logs=None):
    """
    Create a logger function that both prints and records log messages.

    Args:
        logs: Optional list to store log messages

    Returns:
        Logger function
    """
    if logs is None:
        logs = []

    def log_message(message):
        print(message)
        logs.append(message)

    return log_message, logs

def generate_improvement_prompt(original_prompt, iteration, previous_generation, include_previous_results=False, previous_results=None, previous_error=None):
    """
    Generate a prompt for improving previous generation based on results.
    
    Args:
        original_prompt: Original prompt used for first generation
        iteration: Current iteration number
        previous_generation: Previous generated content (code or hardware)
        include_previous_results: Whether to include previous results details
        previous_results: Previous simulation/evaluation results
        previous_error: Previous error message
        
    Returns:
        An improvement prompt string
    """
    
    # 기본 개선 프롬프트 (previous_results를 포함하지 않는 경우)
    improvement_template = """
# Arduino {type} Self-Improvement Task (Iteration {iteration})

## Original Task
{original_prompt}

## Your Previous {type}
{previous_generation}

## Self-Improvement Instructions
Please analyze your previous {type} for potential issues and create an improved version. 
Focus on making it work correctly with the hardware specification and fulfill all requirements in the task.

Ensure your improved {type} follows all formatting requirements from the original prompt.
{output_format_reminder}
"""

    # previous_results를 포함하는 개선 프롬프트
    improvement_template_with_results = """
# Arduino {type} Self-Improvement Task (Iteration {iteration})

## Original Task
{original_prompt}

## Your Previous {type}
{previous_generation}

## Previous Results
- Compilation: {compile_result}
- Testing: {test_result}
{error_details}

## Self-Improvement Instructions
Please analyze your previous {type} and the test results, then create an improved version.
Focus on fixing the issues mentioned in the test results and error messages.
Make sure your {type} works correctly with the hardware specification and fulfills all requirements.

Ensure your improved {type} follows all formatting requirements from the original prompt.
{output_format_reminder}
"""

    type_name = "Code" if "Code Generation" in original_prompt else "Hardware Design"
    
    # 출력 형식 요구사항 추출 (원본 프롬프트에서 형식 요구사항 부분 보존)
    output_format_reminder = ""
    try:
        if "## Output Format" in original_prompt:
            output_format_section = original_prompt.split("## Output Format")[1].split("##")[0]
            output_format_reminder = f"\n## Output Format Reminder\n{output_format_section.strip()}"
        elif "### Output Format" in original_prompt:
            output_format_section = original_prompt.split("### Output Format")[1].split("##")[0]
            output_format_reminder = f"\n### Output Format Reminder\n{output_format_section.strip()}"
        else:
            output_format_reminder = "\nPlease follow the output format specified in the original prompt."
    except Exception:
        output_format_reminder = "\nPlease follow the output format specified in the original prompt."
    
    if include_previous_results and previous_results:
        error_details = f"\n### Error Details\n{previous_error}" if previous_error else ""
        compile_status = "Success" if previous_results.get("compile_result", False) else "Failed"
        test_status = "Success" if previous_results.get("test_result", False) else "Failed"
        
        return improvement_template_with_results.format(
            type=type_name,
            iteration=iteration,
            original_prompt=original_prompt,
            previous_generation=previous_generation,
            compile_result=compile_status,
            test_result=test_status,
            error_details=error_details,
            output_format_reminder=output_format_reminder
        )
    else:
        return improvement_template.format(
            type=type_name,
            iteration=iteration,
            original_prompt=original_prompt,
            previous_generation=previous_generation,
            output_format_reminder=output_format_reminder
        )