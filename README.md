# PCEval: A Benchmark for Evaluating Physical Computing Capabilities of Large Language Models

## Overview
We introduce PCEVAL, a new benchmark to evaluate LLMs' capabilities in physical computing, assessing both logical and physical circuit generation alongside code generation. Our findings reveal LLMs excel at code/logical design but struggle significantly with physical breadboard layouts, highlighting challenges in reasoning about hardware constraints.

## Dataset

The Arduino projects used for evaluation are organized into different levels of complexity. These projects include descriptions, and for some, reference code or diagrams.

**Important:** The `projects/` directory, containing the dataset, is provided via a private Kaggle link for NeurIPS review purposes due to its size and proprietary nature. Reviewers will have access to this link.

The dataset is structured as follows (within the `projects/` directory, once downloaded):
```
projects/
├── level1/
│   ├── project_name_1/
│   │   ├── description.md
│   │   ├── diagram.json (optional initial diagram)
│   │   └── src/
│   │       └── main.ino (optional initial code)
│   └── ...
├── level2/
│   └── ...
├── level3/
│   └── ...
└── level4/
    └── ...
```
Each project typically contains a `description.md` file outlining the task. Some may include initial `diagram.json` (for hardware) or `main.ino` (for code) files.

## Environment Setup

### 1. Prerequisites

*   **Python:** Version 3.x (e.g., 3.8+ recommended)
*   **PlatformIO:** For compiling and uploading Arduino code. Follow the installation instructions at [https://platformio.org/install](https://platformio.org/install).
    *   Ensure PlatformIO Core is installed and accessible from your terminal.
    *   Activate PlatformIO's Python environment if necessary: `source ~/.platformio/penv/bin/activate` (path may vary).
*   **Wokwi-CLI:** For simulating Arduino projects.
    *   Installation: `curl -L https://wokwi.com/ci/install.sh | sh`
    *   You might need to add it to your PATH: `export PATH="$HOME/.local/bin:$PATH"`
    *   A Wokwi CLI token might be required for certain operations. Set it as an environment variable: `export WOKWI_CLI_TOKEN="YOUR_TOKEN_HERE"` (Refer to Wokwi-CLI documentation for obtaining a token if needed).
*   **Build Essentials (for CodeBLEU):** `sudo apt update && sudo apt install build-essential` (or equivalent for your OS).

### 2. Python Libraries

Install the required Python libraries using the `requirements.txt` file:
```bash
pip install -r requirements.txt
```
The key libraries include: `pyyaml`, `tqdm`, `jsonschema`, `requests`, `tree-sitter-cpp`, `codebleu`.
For LLM API access, you might also need:
```bash
pip install openai anthropic ollama google-generativeai
```

### 3. API Configuration (for LLM-based tests)

To use LLMs like OpenAI or Anthropic for automated testing, you need to configure your API keys.
Run the following command and follow the prompts:
```bash
python src/arduino_llm_test.py --setup-config
```
This will create a configuration file (default: `~/.arduino_llm_config.ini` or `src/arduino_llm_config.ini` if the former is not writable). You can specify a custom config location:
```bash
python src/arduino_llm_test.py --setup-config --config my_config.ini
```
The config file structure is:
```ini
[openai]
api_key = your_openai_api_key
model = gpt-4o

[anthropic]
api_key = your_anthropic_api_key
model = claude-3-opus-20240229

[google]
api_key = your_google_api_key
model = gemini-1.5-pro-latest
```
You can view available models for a provider:
```bash
python src/arduino_llm_test.py --llm openai --show-models
```

## How to Run Experiments

**Note:** Before running experiments, ensure the `projects/` dataset directory is downloaded from the private Kaggle link and placed in the root of this repository.

### 1. Main Test Script (`src/arduino_llm_test.py`)

This is the core script for testing an LLM on a specific project.
**Usage:**
```bash
python src/arduino_llm_test.py {code|hardware|both} PATH_TO_PROJECT [--llm {openai,anthropic,google,custom}] [--model MODEL_NAME] [--output-dir OUTPUT_DIR] [--config CONFIG_FILE] [--experiment] [--iterations N] [--save-intermediates]
```
**Arguments:**
*   `{code|hardware|both}`: Specify the test type.
    *   `code`: Test code generation.
    *   `hardware`: Test hardware (diagram) generation.
    *   `both`: Test both code and hardware generation.
*   `PATH_TO_PROJECT`: Relative path to the project folder (e.g., `projects/level1/led_blink_basic`).
*   `--llm`: Specify the LLM provider (`openai`, `anthropic`, `google`, `custom` for manual input).
*   `--model`: Specify the model name (e.g., `gpt-4o-mini`, `claude-3-haiku-20240307`).
*   `--output-dir`: Directory to save results (default: `experiments/{model_name_safe}/{project_name_safe}/`).
*   `--config`: Path to a custom API configuration file.
*   `--experiment`: Flag to save detailed experimental results.
*   `--iterations N`: Number of self-improvement iterations (default: 1).
*   `--save-intermediates`: Save results from each self-improvement iteration.

**Examples:**
```bash
# Test code generation for blink_led project using OpenAI's default model
python src/arduino_llm_test.py code projects/level1/led_blink_basic --llm openai --experiment

# Test hardware generation for blink_led using Anthropic's specific model, with 3 iterations
python src/arduino_llm_test.py hardware projects/level1/led_blink_basic --llm anthropic --model claude-3-sonnet-20240229 --iterations 3 --save-intermediates --experiment

# Test both code and hardware using Google Gemini, saving to a custom directory
python src/arduino_llm_test.py both projects/level2/distance_sensor --llm google --model gemini-1.5-flash --output-dir my_custom_results --experiment
```

### 2. Batch Execution Scripts

These shell scripts automate running tests across multiple projects and models. They utilize `src/arduino_llm_test.py`.

*   **`src/run_experiments.sh`:**
    *   Purpose: Runs experiments sequentially for a predefined list of models and projects.
    *   Configuration: Modify `TEST_ITERATIONS`, `models`, and `projects` arrays within the script.
    *   Execution: `bash src/run_experiments.sh`
    *   Logs are saved to `log/{model_name_safe}/{project_path}/run_{iteration}.log`.
    *   Experiment results are saved in the `experiments/` directory.

*   **`src/run_experiments_parallel.sh`:**
    *   Purpose: Runs experiments in parallel for projects within each model, speeding up the process. Models are processed sequentially.
    *   Configuration: Similar to `run_experiments.sh`.
    *   Execution: `bash src/run_experiments_parallel.sh`
    *   Logging and result saving are similar to `run_experiments.sh`.

### 3. Individual Test Tools (Advanced)

The main test script (`arduino_llm_test.py`) calls these underlying scripts. They can also be run individually for more granular testing:

*   `src/code_generation_test.py PATH_TO_PROJECT [...]`: Tests LLM's ability to generate Arduino code.
*   `src/hardware_generation_test.py PATH_TO_PROJECT [...]`: Tests LLM's ability to generate hardware diagrams.

Refer to `src/README.md` for more details on these individual scripts.

## Analyzing Results

After running experiments, use the following scripts to process and analyze the generated data (typically JSON files in the `experiments/` directory).

*   **`src/summarize_results.py`:**
    *   Purpose: Aggregates raw results from individual experiment runs into summary files.
    *   Execution: `python src/summarize_results.py`
    *   Output:
        *   `experiments/summary/model_project/{model_name}.json`: Per-model summary across all its projects.
        *   `experiments/summary/all_project_summary.json`: Summary aggregated by project across all models.
        *   `experiments/summary/all_model_summary.json`: Overall summary aggregated by model.
        *   These summaries include metrics like success rates, compile rates, CodeBLEU scores, hardware evaluation details, and self-improvement statistics.

*   **`src/analyze_results.py`:**
    *   Purpose: Performs a higher-level analysis on the summarized data from `summarize_results.py`.
    *   Execution: `python src/analyze_results.py`
    *   Output: `experiments/summary/analysis/` directory will contain JSON files with aggregated scores (overall, per-task, per-level) for each model.

*   **`src/verify_results.py`:**
    *   Purpose: Verifies that the expected number of result files have been generated for each model and project after running experiments.
    *   Execution: `python src/verify_results.py`
    *   Output: Prints a report to the console indicating any missing or surplus result files.

## File Structure

```
.
├── README.md                   # This file
├── requirements.txt            # Python dependencies
├── .gitignore
├── projects/                   # (To be downloaded from private Kaggle link) Contains Arduino project definitions
├── src/                        # Source code for test framework and analysis
│   ├── arduino_llm_test.py     # Main test script
│   ├── code_generation_test.py # Core logic for code generation tests
│   ├── hardware_generation_test.py # Core logic for hardware generation tests
│   ├── run_experiments.sh      # Script for sequential batch experiments
│   ├── run_experiments_parallel.sh # Script for parallelized batch experiments
│   ├── summarize_results.py    # Script to aggregate raw experiment results
│   ├── analyze_results.py      # Script for higher-level analysis of summarized results
│   ├── verify_results.py       # Script to check completeness of experiment output files
│   ├── utils.py                # Utility functions
│   ├── arduino_llm_config.ini  # Default location for API configuration
│   ├── converters/             # Modules for converting between formats (e.g., Fritzing to JSON)
│   ├── evaluation/             # Modules for evaluating code and hardware
│   ├── schema/                 # JSON schemas for validation
│   └── README.md               # Detailed README for the src/ directory tools
├── experiments/                # Default directory for storing experiment results
│   ├── {model_name}/           # Results for a specific model
│   │   ├── {project_name}/     # Results for a specific project
│   │   │   └── results_*.json  # Raw JSON output from tests
│   └── summary/                # Aggregated and analyzed results
│       ├── model_project/
│       ├── analysis/
│       └── plots/
└── log/                        # Default directory for storing execution logs from batch scripts
    └── {model_name}/
        └── {project_path}/
            └── run_*.log
```