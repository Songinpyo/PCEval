#!/bin/bash

# 실험 반복 횟수
TEST_ITERATIONS=5
GPU_ID=0

# 테스트할 모델 목록 (형식: "provider/model_name")
models=(
    "openai/gpt-4o-mini"
    # "openai/gpt-4o"
    # "openai/o3-mini"
    # "openai/gpt-4.1"
    # "anthropic/claude-3-opus-20240229"
    # "anthropic/claude-3-7-sonnet-20250219"
    "anthropic/claude-3-5-haiku-20241022"
    # "gemini/gemini-2.5-flash-preview-04-17"
    # "gemini/gemini-2.5-pro-preview-03-25"
    "gemini/gemini-2.0-flash-lite"
    # "gemini/gemini-2.0-flash"
    # "gemini/gemini-1.5-flash"
    # "ollama/gemma3:1b"
    # "ollama/gemma3:4b"
    # "ollama/gemma3:12b"
    # "ollama/gemma3:27b"
    # "ollama/gemma2:2b"
    # "ollama/gemma2:9b"
    # "ollama/gemma:2b"
    # "ollama/gemma:7b"
    # "ollama/mistral" # 7b
    # "ollama/mistral-small:24b"
    # "ollama/phi4" # 14b
    # "ollama/phi3:14b" # 14b
    # "ollama/llama3.2:1b"
    # "ollama/llama3.2"
    # "ollama/llama3.1:8b"
    # "ollama/llama3:8b"
    # "ollama/llama2:7b"
    # "ollama/qwen3:30b"
    # "ollama/qwen3"
    # "ollama/qwen2.5:14b"
    # "ollama/qwen2.5:7b"
    # "ollama/qwen2.5:3b"
    # "ollama/qwen2.5:1.5b"
    # "ollama/qwen2.5:0.5b"
    # "ollama/qwen:0.5b"
    # "ollama/qwen:1.8b"
    # "ollama/qwen:4b"
    # "ollama/qwen:7b"
    # "ollama/deepseek-coder-v2:16b"
    # "ollama/deepseek-v2:16b"
    # "ollama/deepseek-r1:14b"
)

# 테스트할 프로젝트 목록
projects=(
    level1/7_segment_display_basic
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

# 자기 개선 매개변수 문자열 생성
SELF_IMPROVE_ARGS=""
if $USE_SELF_IMPROVEMENT; then
    SELF_IMPROVE_ARGS="--iterations $ITERATIONS"
    if $INCLUDE_PREVIOUS; then
        SELF_IMPROVE_ARGS="$SELF_IMPROVE_ARGS --include-previous"
    fi
    if $SAVE_INTERMEDIATES; then
        SELF_IMPROVE_ARGS="$SELF_IMPROVE_ARGS --save-intermediates"
    fi
fi

echo "Starting serial experiments..."

# 모든 프로젝트에 대해 반복
for project in "${projects[@]}"
do
    # 모든 모델에 대해 반복
    for model_entry in "${models[@]}"
    do
        # 모델 정보 파싱 (provider/model_name)
        provider=$(echo "$model_entry" | cut -d'/' -f1)
        model_name=$(echo "$model_entry" | cut -d'/' -f2)

        # 로그 파일명/디렉토리명으로 사용하기 위해 모델 이름의 ':'를 '_'로 변경
        log_model_name=$(echo "$model_name" | tr ':' '_')
        exp_model_name=$(echo "$model_name" | tr '-' '_')

        project_name=$(echo "$project" | cut -d'/' -f2)

        # 실험 디렉토리 삭제 (experiments/{model}/{project})
        exp_dir="experiments/${exp_model_name}/${project_name}"
        if [ -d "$exp_dir" ]; then
            echo "Deleting experiment directory: $exp_dir"
            rm -rf "$exp_dir"
        fi

        # 지정된 횟수만큼 반복
        for i in $(seq 1 $TEST_ITERATIONS)
        do
            # 로그 디렉토리 경로 설정 및 생성
            # log/${log_model_name}/${project} 디렉토리를 만들고, 그 안에 ${i}.log 파일을 생성합니다.
            log_dir="log/${log_model_name}/${project}"
            mkdir -p "$log_dir"
            log_file="${log_dir}/run_${i}.log"

            echo "Running Project: $project | Model: $model_name | Iteration: $i"

            # arduino_llm_test.py 실행 (백그라운드 + 직렬 실행을 위한 wait)
            CUDA_VISIBLE_DEVICES=$GPU_ID nohup python src/arduino_llm_test.py \
                --test_type both \
                --project_path "projects/$project" \
                --llm "$provider" \
                --mode both \
                --model "$model_name" \
                --experiment \
                $SELF_IMPROVE_ARGS \
                > "$log_file" 2>&1 &

            # 현재 실행된 백그라운드 프로세스가 끝날 때까지 기다림
            wait
            sleep 3
            echo "Finished Project: $project | Model: $model_name | Iteration: $i"
            echo "--------------------------------------------------"

        done # Iteration loop end
    done # Model loop end
done # Project loop end

echo 'All serial experiments finished!'