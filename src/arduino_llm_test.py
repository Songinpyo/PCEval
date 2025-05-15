#!/usr/bin/env python3
# arduino_llm_test.py
# Main tool for testing LLM capabilities for Arduino projects

import os
import sys
import argparse
import subprocess
import configparser
import requests
import time

# Default configuration file path
CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "arduino_llm_config.ini")

def setup_config_if_needed(config_file=CONFIG_FILE):
    """Create a configuration file with API keys if it doesn't exist."""
    if os.path.exists(config_file):
        return

    print(f"Configuration file not found at {config_file}")
    print("Let's set up your LLM API credentials.")

    config = configparser.ConfigParser()

    # OpenAI section
    config['openai'] = {}
    openai_key = input("Enter your OpenAI API key (press Enter to skip): ").strip()
    if openai_key:
        config['openai']['api_key'] = openai_key
        config['openai']['model'] = input("Enter OpenAI model name [default: gpt-4o-mini]: ").strip() or "gpt-4o-mini"

    # Anthropic section
    config['anthropic'] = {}
    anthropic_key = input("Enter your Anthropic API key (press Enter to skip): ").strip()
    if anthropic_key:
        config['anthropic']['api_key'] = anthropic_key
        config['anthropic']['model'] = input("Enter Anthropic model name [default: claude-3-haiku-20240307]: ").strip() or "claude-3-haiku-20240307"

    config['gemini'] = {}
    gemini_key = input("Enter your Gemini API key (press Enter to skip): ").strip()
    if gemini_key:
        config['gemini']['api_key'] = gemini_key
        config['gemini']['model'] = input("Enter Gemini model name [default: gemini-2.0-flash-lite]: ").strip() or "gemini-2.0-flash-lite"

    config['ollama'] = {}
    ollama_url = input("Enter your Ollama API URL [default: http://localhost:11434]: ").strip() or "http://localhost:11434"
    config['ollama']['api_url'] = ollama_url
    config['ollama']['model'] = input("Enter Ollama model name [default: llama3]: ").strip() or "llama3"

    # Write configuration to file
    os.makedirs(os.path.dirname(os.path.abspath(config_file)), exist_ok=True)
    with open(config_file, 'w') as f:
        config.write(f)

    print(f"Configuration saved to {config_file}")

    # Set file permissions to be readable only by the user
    os.chmod(config_file, 0o600)

def load_config(config_file=CONFIG_FILE):
    """Load LLM configuration from file."""
    if not os.path.exists(config_file):
        setup_config_if_needed(config_file)

    config = configparser.ConfigParser()
    config.read(config_file)
    return config

def print_available_models(llm_provider):
    """Print available models for the specified LLM provider."""
    print(f"\nAvailable models for {llm_provider}:")

    if llm_provider == "openai":
        models = [
            "gpt-4.1-nano-2025-04-14",
            "gpt-4.1-mini-2025-04-14",
            "o4-mini-2025-04-16",
            "o3-mini-2025-01-31",
            "o1-mini-2024-09-12"
            "gpt-4o-mini",
            "gpt-4o"
        ]
    elif llm_provider == "anthropic":
        models = [
            "claude-3-7-sonnet-20250219",
            "claude-3-5-haiku-20241022",
        ]
    elif llm_provider == "gemini":
        models = [
            "gemini-2.5-flash-preview-04-17",
            "gemini-2.5-pro-preview-03-25", # 비싸요
            "gemini-2.0-flash-lite",
            "gemini-2.0-flash",
            "gemini-1.5-flash"
        ]
    elif llm_provider == "ollama":
        # Try to get available models from Ollama API
        try:
            # Import the ollama library
            import ollama
            # Get list of models
            models_data = ollama.list()
            models = [model['name'] for model in models_data['models']]
            if not models:
                raise Exception("No models found")
        except ImportError:
            print("Error: Ollama Python library not found. Please install it with 'pip install ollama'")
            models = []
        except Exception as e:
            print(f"Could not connect to Ollama API: {e}")
            models = [
                "gemma3:1b",
                "gemma3:4b",
                "gemma2:2b",
                "gemma2:9b",
                "gemma:2b",
                "gemma:7b",
                "mistral", # 7b
                "llama3.2:1b",
                "llama3.2", # 3b
                "llama3.1:8b",
                "llama3:8b",
                "llama2:7b",
                "qwen3", # 8b
                "qwen2.5:7b",
                "qwen2.5:3b",
                "qwen2.5:1.5b",
                "qwen2.5:0.5b",
                "qwen:0.5b",
                "qwen:1.8b",
                "qwen:4b",
                "qwen:7b"
            ]
            print("Showing common models. To use Ollama, make sure it's installed and running.")
            print("Visit https://ollama.ai/ for installation instructions.")
    else:
        models = []

    for model in models:
        print(f"  - {model}")

def main():
    parser = argparse.ArgumentParser(description="Test LLM capabilities for Arduino projects")
    parser.add_argument("--test_type", choices=["code", "hardware", "both", "codeware", "triple"],
                        help="Type of test to run (code, hardware, codeware, both(code+hw), or triple(code+hw+codeware))")
    parser.add_argument("--mode", choices=["logical", "physical", "both"], default="physical", help="Mode for hardware representation (logical, physical, or both)")
    parser.add_argument("--project_path", help="Path to the Arduino project")
    parser.add_argument("--llm", choices=["openai", "anthropic", "gemini", "ollama", "custom"],
                        default="openai", help="LLM provider to use")
    parser.add_argument("--model", help="Specific model to use (if not provided, uses config default)")
    parser.add_argument("--output-dir", default="results",
                        help="Directory to save the evaluation results")
    parser.add_argument("--config", default=CONFIG_FILE,
                        help="Path to configuration file with API keys")
    parser.add_argument("--setup-config", action="store_true",
                        help="Set up configuration file with API keys")
    parser.add_argument("--show-models", action="store_true",
                        help="Show available models for the selected LLM provider and exit")
    parser.add_argument("--experiment", action="store_true",
                        help="Save to the experiment folder")
    # Add self-improvement related parameters
    parser.add_argument("--iterations", type=int, default=1,
                        help="Number of iterations for self-improvement (default: 1)")
    parser.add_argument("--include-previous", action="store_true",
                        help="Include previous results in improvement prompts")
    parser.add_argument("--save-intermediates", action="store_true",
                        help="Save intermediate code/diagram files")

    args = parser.parse_args()

    # Set up configuration if requested
    if args.setup_config:
        setup_config_if_needed(args.config)
        print("Configuration complete. Exiting.")
        sys.exit(0)

    # Show available models if requested
    if args.show_models:
        print_available_models(args.llm)
        sys.exit(0)

    # Load configuration
    config = load_config(args.config)

    # Validate project path
    project_path = os.path.abspath(args.project_path)
    if not os.path.exists(project_path):
        print(f"Project path does not exist: {project_path}")
        sys.exit(1)

    project_name = os.path.basename(project_path)

    # Create output directory if it doesn't exist
    if args.output_dir:
        os.makedirs(args.output_dir, exist_ok=True)

    current_dir = os.path.dirname(os.path.abspath(__file__))

    # Pass config information to the scripts
    env = os.environ.copy()
    if args.llm != "custom":
        if args.llm == "openai" and 'openai' in config and 'api_key' in config['openai']:
            env["OPENAI_API_KEY"] = config['openai']['api_key']
            model = args.model or config['openai'].get('model', 'gpt-4o')
            env["OPENAI_MODEL"] = model
            print(f"Using OpenAI model: {model}")
        elif args.llm == "anthropic" and 'anthropic' in config and 'api_key' in config['anthropic']:
            env["ANTHROPIC_API_KEY"] = config['anthropic']['api_key']
            model = args.model or config['anthropic'].get('model', 'claude-3-opus-20240229')
            env["ANTHROPIC_MODEL"] = model
            print(f"Using Anthropic model: {model}")
        elif args.llm == "gemini" and 'gemini' in config and 'api_key' in config['gemini']:
            env["GEMINI_API_KEY"] = config['gemini']['api_key']
            model = args.model or config['gemini'].get('model', 'gemini-2.0-flash-lite')
            env["GEMINI_MODEL"] = model
            print(f"Using Gemini model: {model}")
        elif args.llm == "ollama" and 'ollama' in config:
            env["OLLAMA_API_URL"] = config['ollama'].get('api_url', 'http://localhost:11434')
            model = args.model or config['ollama'].get('model', 'llama3')
            env["OLLAMA_MODEL"] = model
            print(f"Using Ollama model: {model}")

    model_dir_for_exp = model.replace("-", "_") if model else args.llm # Use resolved model name

    if args.experiment:
        experiment_base_dir = os.path.join("experiments", model_dir_for_exp, project_name)
        os.makedirs(experiment_base_dir, exist_ok=True)
        experiment_id = 1
        while True:
            experiment_file_path = os.path.join(experiment_base_dir, f"results_{experiment_id}.json")
            if os.path.exists(experiment_file_path):
                experiment_id += 1
            else:
                break
    else:
        experiment_id = 0 # experiment_id는 사용되지 않지만 초기화
        experiment_file_path = None # 경로도 None으로 초기화
    
    # Define a function to run code generation test
    def run_code_test(mode, experiment_file_path):
        print(f"\n=== Running Code Generation Test for {project_name} ===\n")
        print(f"Mode: {mode.upper()} hardware input")

        cmd = [
            sys.executable,
            os.path.join(current_dir, "code_generation_test.py"),
            project_path,
            "--llm", args.llm,
            "--mode", mode
        ]
        
        # Add self-improvement parameters if specified
        if args.iterations > 1:
            cmd.extend(["--iterations", str(args.iterations)])
        if args.include_previous:
            cmd.append("--include-previous")
        if args.save_intermediates:
            cmd.append("--save-intermediates")
        
        # 수정: experiment_file_path 사용
        if args.experiment and experiment_file_path:
            cmd.append("--experiment")
            cmd.append(experiment_file_path)

        subprocess.run(cmd, env=env)

    # Run code generation test if requested (only if not triple)
    if args.test_type in ["code", "both"]:
        if args.mode == "both":
            run_code_test("logical", experiment_file_path)
            run_code_test("physical", experiment_file_path)
        else:
            run_code_test(args.mode, experiment_file_path)

    # Define a function to run hardware design test
    def run_hardware_test(mode, experiment_file_path):
        print(f"\n=== Running Hardware Design Test for {project_name} ===\n")
        print(f"Mode: {mode.upper()}")

        cmd = [
            sys.executable,
            os.path.join(current_dir, "hardware_generation_test.py"),
            project_path,
            "--llm", args.llm,
            "--mode", mode
        ]
        
        # Add self-improvement parameters if specified
        if args.iterations > 1:
            cmd.extend(["--iterations", str(args.iterations)])
        if args.include_previous:
            cmd.append("--include-previous")
        if args.save_intermediates:
            cmd.append("--save-intermediates")
        
        # 수정: experiment_file_path 사용
        if args.experiment and experiment_file_path:
            cmd.append("--experiment")
            cmd.append(experiment_file_path)

        subprocess.run(cmd, env=env)

    # Run hardware design test if requested (only if not triple)
    if args.test_type in ["hardware", "both"]:
        # 수정: "both" 일 때는 hardware 만 실행 (code는 위에서 이미 실행됨), triple 아닐 때만
        if args.mode == "both": 
             run_hardware_test("logical", experiment_file_path)
             run_hardware_test("physical", experiment_file_path)
        else:
             run_hardware_test(args.mode, experiment_file_path)

    # Define a function to run codeware generation test
    def run_codeware_test(mode, experiment_file_path):
        print(f"\n=== Running Codeware Generation Test for {project_name} ===\n")
        print(f"Mode: {mode.upper()}")

        cmd = [
            sys.executable,
            os.path.join(current_dir, "codeware_generation_test.py"),
            project_path,
            "--llm", args.llm,
            "--mode", mode
        ]
        
        # Add self-improvement parameters if specified
        if args.iterations > 1:
            cmd.extend(["--iterations", str(args.iterations)])
        if args.include_previous:
            cmd.append("--include-previous")
        if args.save_intermediates:
            cmd.append("--save-intermediates")
        
        # 수정: experiment_file_path 사용 (codeware 분기 제거)
        if args.experiment and experiment_file_path:
            cmd.append("--experiment")
            cmd.append(experiment_file_path)

        subprocess.run(cmd, env=env)

    # Run codeware generation test if requested (only if not triple)
    if args.test_type == "codeware":
        if args.mode == "both":
            run_codeware_test("logical", experiment_file_path)
            run_codeware_test("physical", experiment_file_path)
        else:
            run_codeware_test(args.mode, experiment_file_path)

    # Run all three tests if type is triple
    if args.test_type == "triple":
        print(f"\n=== Running TRIPLE Test (Code, Hardware, Codeware) for {project_name} ===\n")
        if args.mode == "both":
            print("--- Running LOGICAL mode tests ---")
            run_code_test("logical", experiment_file_path)
            run_hardware_test("logical", experiment_file_path)
            run_codeware_test("logical", experiment_file_path)
            print("\n--- Running PHYSICAL mode tests ---")
            run_code_test("physical", experiment_file_path)
            run_hardware_test("physical", experiment_file_path)
            run_codeware_test("physical", experiment_file_path)
        else: # Single mode (logical or physical)
            run_code_test(args.mode, experiment_file_path)
            run_hardware_test(args.mode, experiment_file_path)
            run_codeware_test(args.mode, experiment_file_path)

    # Get model name from environment variable
    model_name = None
    if args.llm == "openai":
        model_name = os.environ.get("OPENAI_MODEL", "gpt-4o")
    elif args.llm == "anthropic":
        model_name = os.environ.get("ANTHROPIC_MODEL", "claude-3.5-haiku")
    elif args.llm == "gemini":
        model_name = os.environ.get("GEMINI_MODEL", "gemini-2.0-flash-lite")
    elif args.llm == "ollama":
        model_name = os.environ.get("OLLAMA_MODEL", "llama3")

    # Use model name for results directory if available
    model_dir = model_name.replace("-", "_") if model_name else args.llm

    print("\n=== Testing Complete ===")
    print(f"Results saved to results/{model_dir_for_exp}/")
    if args.experiment:
        print(f"Experiment data saved to {experiment_file_path}")

if __name__ == "__main__":
    main()