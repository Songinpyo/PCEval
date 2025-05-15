#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json

# PROVIDED PROJECTS LIST 
PROJECTS_WITH_LEVEL = [
    "level1/7_segment_display_basic",
    "level1/bar_led_basic",
    "level1/buzzer_basic",
    "level1/distance_sensor_basic",
    "level1/humidity_sensor_basic",
    "level1/LCD_display_basic",
    "level1/led_blink_basic",
    "level1/led_RGB_basic",
    "level1/photoresistor_basic",
    "level1/RTC_module_basic",
    "level1/servo_motor_basic",
    "level1/temperature_sensor_basic",
    "level2/7_segment_display_counter",
    "level2/accelerometer",
    "level2/button_duration",
    "level2/button_pulldown",
    "level2/button_pullup",
    "level2/distance_sensor",
    "level2/gyroscope",
    "level2/humidity_sensor",
    "level2/serial_bar_led",
    "level2/serial_LCD_display",
    "level2/serial_monitor",
    "level2/serial_RGB_led",
    "level2/temperature_sensor",
    "level3/4_digit_7_segment_display",
    "level3/7_segment_display_serial",
    "level3/button_buzzer",
    "level3/button_LCD_display",
    "level3/button_led",
    "level3/button_RGB_led",
    "level3/button_RTC_timezone",
    "level3/button_servo_motor",
    "level3/dht22_LCD_display",
    "level3/multiplexer_photoresistor",
    "level3/multiplexer_potentiometer",
    "level3/photoresistor_bar_led",
    "level3/potentiometer_bar_led",
    "level3/potentiometer_servo_motor",
    "level4/alarm",
    "level4/binary_led",
    "level4/calendar_display",
    "level4/clock",
    "level4/dday_counter",
    "level4/exercise_counter",
    "level4/multiple_timezone",
    "level4/parking_spot_monitor",
    "level4/piano_keyboard",
    "level4/smart_led_system",
    "level4/traffic_light",
]

EXPERIMENTS_BASE_DIR = "experiments"
EXPECTED_FILES_PER_PROJECT = 5 
# Directories to ignore within EXPERIMENTS_BASE_DIR when looking for model directories
IGNORE_DIRS = ["summary", "plots"] 

def get_clean_project_names(projects_with_level_list):
    """Extracts project names by stripping the 'levelX/' prefix."""
    cleaned_names = []
    for project_path in projects_with_level_list:
        if '/' in project_path:
            cleaned_names.append(project_path.split('/', 1)[1])
        else:
            # In case a project name doesn't have the level prefix for some reason
            cleaned_names.append(project_path)
            print(f"Warning: Project '{project_path}' does not seem to have a level prefix.")
    return cleaned_names

def verify_experiment_results():
    """
    Verifies that each model has the expected number of result files for all projects.
    Outputs details for models that do not meet the expectation.
    """
    project_names = get_clean_project_names(PROJECTS_WITH_LEVEL)
    if not project_names:
        print("오류: 프로젝트 이름을 추출할 수 없습니다. PROJECTS_WITH_LEVEL 리스트를 확인하세요.")
        return

    num_total_projects = len(project_names)
    expected_total_files_per_model = num_total_projects * EXPECTED_FILES_PER_PROJECT

    print(f"총 프로젝트 수: {num_total_projects}")
    print(f"프로젝트당 예상 result 파일 수: {EXPECTED_FILES_PER_PROJECT}")
    print(f"모델당 총 예상 result 파일 수: {expected_total_files_per_model}\n")

    if not os.path.isdir(EXPERIMENTS_BASE_DIR):
        print(f"오류: '{EXPERIMENTS_BASE_DIR}' 디렉토리를 찾을 수 없습니다. 스크립트 위치를 확인하세요.")
        return

    model_dirs = [d for d in os.listdir(EXPERIMENTS_BASE_DIR) 
                  if os.path.isdir(os.path.join(EXPERIMENTS_BASE_DIR, d)) and d not in IGNORE_DIRS]

    if not model_dirs:
        print(f"오류: '{EXPERIMENTS_BASE_DIR}' 디렉토리 내에서 모델 디렉토리를 찾을 수 없습니다.")
        return

    all_models_ok = True
    for model_name in sorted(model_dirs):
        print(f"모델 검증 중: {model_name}")
        current_model_total_files = 0
        projects_with_missing_files = {} # {project_name: actual_file_count}

        for project_name in project_names:
            project_file_count = 0
            project_path = os.path.join(EXPERIMENTS_BASE_DIR, model_name, project_name)

            if not os.path.isdir(project_path):
                print(f"  알림: 모델 '{model_name}'에 대한 프로젝트 디렉토리 '{project_name}' 없음.")
                projects_with_missing_files[project_name] = 0 # Mark as 0 files if dir missing
                continue # Skip to next project if project directory doesn't exist

            # 디렉토리 내의 모든 result_*.json 파일 수를 직접 카운트
            try:
                actual_files_in_project = [
                    f for f in os.listdir(project_path)
                    if f.startswith("results_") and f.endswith(".json") and \
                       os.path.isfile(os.path.join(project_path, f))
                ]
                project_file_count = len(actual_files_in_project)
            except OSError as e:
                print(f"  [오류] 프로젝트 디렉토리 '{project_path}' 접근 중 오류 발생: {e}")
                projects_with_missing_files[project_name] = -1 # Indicate error
                continue
            
            current_model_total_files += project_file_count
            if project_file_count != EXPECTED_FILES_PER_PROJECT:
                projects_with_missing_files[project_name] = project_file_count
        
        print(f"  모델 '{model_name}'의 총 result 파일 수: {current_model_total_files}/{expected_total_files_per_model}")

        # 프로젝트별 파일 수에 문제가 있는지 먼저 확인
        if projects_with_missing_files: 
            all_models_ok = False
            # 총 파일 수도 다른지, 아니면 총 파일 수는 맞는데 내부적으로 틀린지 구분
            if current_model_total_files != expected_total_files_per_model:
                diff_files = expected_total_files_per_model - current_model_total_files
                status_msg = f"{abs(diff_files)}개 {'누락' if diff_files > 0 else '초과'}"
                print(f"  [경고] 모델 '{model_name}'의 총 result 파일 수가 예상과 다릅니다. ({status_msg})")
            else:
                # 이 경우는 총 파일 수는 맞지만 (예: A=4, B=6 -> 총합 10), 개별 프로젝트 파일 수가 문제인 경우.
                print(f"  [경고] 모델 '{model_name}'의 총 result 파일 수는 정상이지만, 일부 프로젝트의 파일 수가 올바르지 않습니다.")
            
            print(f"    프로젝트별 파일 수 상세:")
            for proj, count in sorted(projects_with_missing_files.items()):
                 # projects_with_missing_files에는 이미 count != EXPECTED_FILES_PER_PROJECT 인 것들만 들어있음.
                 print(f"      - 프로젝트 '{proj}': {count}/{EXPECTED_FILES_PER_PROJECT} 개의 파일 존재")
        
        # projects_with_missing_files가 비어있을 때 (모든 프로젝트가 5개 파일 가짐)
        # 이 경우, current_model_total_files는 expected_total_files_per_model와 같아야 정상
        elif current_model_total_files != expected_total_files_per_model:
            # 이 경우는 거의 발생하지 않아야 하지만, 방어적으로 로깅
            all_models_ok = False
            diff_files = expected_total_files_per_model - current_model_total_files
            status_msg = f"{abs(diff_files)}개 {'누락' if diff_files > 0 else '초과'}"
            print(f"  [오류] 모델 '{model_name}': 모든 프로젝트가 각 {EXPECTED_FILES_PER_PROJECT}개의 파일을 가진 것으로 보이나, 총 파일 수가 예상과 다릅니다 ({status_msg}). 내부 로직 확인 필요.")
        
        # projects_with_missing_files도 비어있고, 총 파일 수도 맞는 완벽한 경우
        else:
            print(f"  [성공] 모델 '{model_name}'은(는) 모든 예상 result 파일을 가지고 있으며, 각 프로젝트별 파일 수도 정확합니다.")
        
        print("-" * 30)

    if all_models_ok:
        print("\n모든 검증된 모델이 예상된 수의 result 파일을 가지고 있습니다.")
    else:
        print("\n일부 모델에서 누락된 result 파일이 발견되었습니다. 위 로그를 확인하세요.")

if __name__ == "__main__":
    verify_experiment_results() 