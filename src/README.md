# Arduino-LLM Test Tools

This directory contains tools for testing LLM capabilities in generating Arduino code and hardware designs.

## Requirements

Before using these tools, make sure you have the following dependencies installed:

```bash
pip install pyyaml requests
```

You also need to have [PlatformIO](https://platformio.org/) and [wokwi-cli](https://github.com/wokwi/wokwi-cli) installed and configured.

## API Configuration

The tools can use OpenAI or Anthropic APIs for automated testing. To set up your API keys:

```bash
python arduino_llm_test.py --setup-config
```

This will create a configuration file at `~/.arduino_llm_config.ini` with your API keys and model preferences. You can also specify a custom config location:

```bash
python arduino_llm_test.py --setup-config --config my_config.ini
```

The config file will have this structure:
```ini
[openai]
api_key = your_openai_api_key
model = gpt-4o

[anthropic]
api_key = your_anthropic_api_key
model = claude-3-opus-20240229
```

## Model Selection

You can view available models for a specific provider:

```bash
python arduino_llm_test.py --llm openai --show-models
python arduino_llm_test.py --llm anthropic --show-models
```

To specify a model at runtime (overriding the default in the config file):

```bash
python arduino_llm_test.py code ../projects/level1/blink_led --llm openai --model gpt-4o
python arduino_llm_test.py code ../projects/level1/blink_led --llm anthropic --model claude-3-sonnet-20240229
```

## Main Test Script

The simplest way to run tests is using the main script:

```bash
python arduino_llm_test.py {code|hardware|both} PATH_TO_PROJECT [--llm {openai,anthropic,custom}] [--model MODEL_NAME] [--output-dir OUTPUT_DIR] [--config CONFIG_FILE]
```

Examples:
```bash
# Test code generation only using OpenAI
python arduino_llm_test.py code ../projects/level1/blink_led --llm openai

# Test hardware design only using Anthropic with a specific model
python arduino_llm_test.py hardware ../projects/level1/blink_led --llm anthropic --model claude-3-haiku-20240307

# Test both capabilities with custom output directory and config file
python arduino_llm_test.py both ../projects/level1/blink_led --output-dir my_results --config my_config.ini

# Use manual input (no API keys required)
python arduino_llm_test.py both ../projects/level1/blink_led --llm custom
```

## Individual Test Tools

You can also run the individual test scripts directly:

### 1. Code Generation Test (`code_generation_test.py`)

This tool tests an LLM's ability to generate Arduino code from project descriptions, hardware diagrams, and expected behaviors.

#### Usage:

```bash
python code_generation_test.py PATH_TO_PROJECT [--llm {openai,anthropic,custom}] [--output RESULTS_FILE]
```

Example:
```bash
python code_generation_test.py ../projects/level1/blink_led --output results/blink_led_code_test.json
```

This will:
1. Generate a prompt with the project description, hardware diagram, and expected behavior
2. Submit the prompt to the specified LLM or prompt you to input manually if using "custom"
3. Save the generated code to the project's src/main.ino file (backing up the original)
4. Compile and test the code with PlatformIO and wokwi-cli
5. Report success or failure and save results if specified

### 2. Hardware Design Test (`hardware_generation_test.py`)

This tool tests an LLM's ability to generate hardware diagrams from project descriptions, code, and expected behaviors.

#### Usage:

```bash
python hardware_generation_test.py PATH_TO_PROJECT [--llm {openai,anthropic,custom}] [--output RESULTS_FILE]
```

Example:
```bash
python hardware_generation_test.py ../projects/level1/blink_led --output results/blink_led_hardware_test.json
```

This will:
1. Generate a prompt with the project description, Arduino code, and expected behavior
2. Submit the prompt to the specified LLM or prompt you to input manually if using "custom"
3. Save the generated diagram to the project's diagram.json file (backing up the original)
4. Compile and test the setup with PlatformIO and wokwi-cli
5. Report success or failure and save results if specified

## Understanding Test Results

Both tools will:
- Print "✅ Success!" if the generated code/hardware passes all tests
- Print "❌ Failed!" with error details if something doesn't work
- Save detailed output including prompts, generated content, and test results to the output file if specified

## Example Workflow

1. Choose a project to test
2. Set up your API configuration (or use the "custom" option for manual input)
3. Run the test script with the appropriate type (code, hardware, or both)
4. If using the "custom" option, submit the generated prompt to your chosen LLM and paste the response back
5. Review the test results and examine any failures
6. Compare results across different LLMs or project complexity levels

## Adding New Projects

To test with additional projects:
1. Ensure the project follows the structure in `projects/`
2. Run the same test commands with the new project path 