#!/bin/bash

# 실험 반복 횟수
TEST_ITERATIONS=5
GPU_ID=0

# 이 목록은 순차적으로 처리
models=(
    "openai/gpt-4o-mini"
    # "openai/gpt-4o"
    # "openai/gpt-4.1"
    # "openai/o3-mini"
    # "anthropic/claude-3-opus-20240229"
    # "anthropic/claude-3-7-sonnet-20250219"
    "anthropic/claude-3-5-haiku-20241022"
    # "anthropic/claude-3-haiku-20240307"
    # "gemini/gemini-2.5-flash-preview-04-17"
    # "gemini/gemini-2.5-pro-preview-03-25"
    "gemini/gemini-2.0-flash-lite"
    # "gemini/gemini-2.0-flash"
    # "gemini/gemini-1.5-pro"
    # "gemini/gemini-1.5-flash"
    # "ollama/gemma3:1b"
    # "ollama/gemma3:4b"
    # "ollama/gemma2:2b"
    # "ollama/gemma2:9b"
    # "ollama/gemma:2b"
    # "ollama/gemma:7b"
    # "ollama/mistral"
    # "ollama/llama3.2:1b"
    # "ollama/llama3.2"
    # "ollama/llama3.1:8b"
    # "ollama/llama3:8b"
    # "ollama/llama2:7b"
    # "ollama/qwen2.5:7b"
    # "ollama/qwen2.5:3b"
    # "ollama/qwen2.5:1.5b"
    # "ollama/qwen2.5:0.5b"
    # "ollama/qwen:0.5b"
    # "ollama/qwen:1.8b"
    # "ollama/qwen:4b"
    # "ollama/qwen:7b"
)

# 각 모델 내에서 이 목록은 병렬로 처리
projects=(
    # level1/7_segment_display_basic
    level1/bar_led_basic
    level1/buzzer_basic
    level1/distance_sensor_basic
    level1/humidity_sensor_basic
    level1/LCD_display_basic
    level1/led_blink_basic
    level1/led_RGB_basic
    level1/photoresistor_basic
    level1/RTC_module_basic
    level1/servo_motor_basic
    level1/temperature_sensor_basic
    level2/7_segment_display_counter
    level2/accelerometer
    level2/button_duration
    level2/button_pulldown
    level2/button_pullup
    level2/distance_sensor
    level2/gyroscope
    level2/humidity_sensor
    level2/serial_bar_led
    level2/serial_LCD_display
    level2/serial_monitor
    level2/serial_RGB_led
    level2/temperature_sensor
    level3/4_digit_7_segment_display
    level3/7_segment_display_serial
    level3/button_buzzer
    level3/button_LCD_display
    level3/button_led
    level3/button_RGB_led
    level3/button_RTC_timezone
    level3/button_servo_motor
    level3/dht22_LCD_display
    level3/multiplexer_photoresistor
    level3/multiplexer_potentiometer
    level3/photoresistor_bar_led
    level3/potentiometer_bar_led
    level3/potentiometer_servo_motor
    level4/alarm
    level4/binary_led
    level4/calendar_display
    level4/clock
    level4/dday_counter
    level4/exercise_counter
    level4/multiple_timezone
    level4/parking_spot_monitor
    level4/piano_keyboard
    level4/smart_led_system
    level4/traffic_light
)

# 자기 개선 옵션 설정
ITERATIONS=1
INCLUDE_PREVIOUS=true # 지난 결과 포함 여부
SAVE_INTERMEDIATES=true # 중간 결과 저장 여부

USE_SELF_IMPROVEMENT=false # 이 값을 true로 설정하면 자기 개선 기능 활성화

local_improve_args=""
if $USE_SELF_IMPROVEMENT; then
    local_improve_args="--iterations $ITERATIONS"
    if $INCLUDE_PREVIOUS; then
        local_improve_args="$local_improve_args --include-previous"
    fi
    if $SAVE_INTERMEDIATES; then
        local_improve_args="$local_improve_args --save-intermediates"
    fi
fi

echo "Starting model-serial, iteration-serial, project-parallel experiments..."

# 모델 루프 (순차적)
for model_entry in "${models[@]}"
do
    provider=$(echo "$model_entry" | cut -d'/' -f1)
    model_name=$(echo "$model_entry" | cut -d'/' -f2)
    log_model_name=$(echo "$model_name" | tr ':' '_') # 로그 파일 경로용 이름

    echo "Processing Model: $model_name"

    # 반복 루프 (순차적)
    for i in $(seq 1 $TEST_ITERATIONS)
    do
        echo "  Starting Iteration: $i for Model: $model_name"

        # 프로젝트 루프 (병렬 실행 시작)
        for project in "${projects[@]}"
        do
            # 로그 디렉토리 경로 설정 및 생성
            log_dir="log/${log_model_name}/${project}" # codeware
            mkdir -p "$log_dir"
            log_file="${log_dir}/run_${i}.log" # 로그 파일 이름에 반복 횟수 포함

            echo "    Starting Project: $project for Iteration: $i, Model: $model_name"

            # arduino_llm_test.py 실행 (백그라운드로)
            CUDA_VISIBLE_DEVICES=$GPU_ID nohup python src/arduino_llm_test.py \
                --test_type both \
                --project_path "projects/$project" \
                --llm "$provider" \
                --mode both \
                --model "$model_name" \
                --experiment \
                $local_improve_args \
                > "$log_file" 2>&1 &

        done # Project loop end

        # 현재 모델과 현재 반복에 대해 시작된 모든 프로젝트 프로세스가 끝날 때까지 기다림
        echo "    Waiting for all projects in Iteration $i of model '$model_name' to finish..."
        wait
        sleep 10
        echo "  Finished Iteration: $i for Model: $model_name"
        echo "  -------------------------------------"

    done # Iteration loop end

    echo "Finished all iterations for Model: $model_name"
    echo "--------------------------------------------------"

done # Model loop end

echo 'All experiments finished!'
