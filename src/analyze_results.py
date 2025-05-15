import os
import json
from pathlib import Path

# Constants
EXPERIMENTS_DIR = Path("experiments")
SUMMARY_DIR = EXPERIMENTS_DIR / "summary"
MODEL_PROJECT_SUMMARY_DIR = SUMMARY_DIR / "model_project"
ANALYSIS_OUTPUT_DIR = SUMMARY_DIR / "analysis"

# Projects
# L1 12
PROJECTS = [
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

# 프로젝트 이름에서 레벨 추출을 위한 매핑
PROJECT_TO_LEVEL = {}
for project in PROJECTS:
    parts = project.split('/')
    if len(parts) > 1:
        level, project_name = parts[0], parts[1]
        PROJECT_TO_LEVEL[project] = level
        PROJECT_TO_LEVEL[project_name] = level  # 레벨 없이 프로젝트 이름만 있는 경우도 처리

# 태스크 타입
CODE = "code"
HARDWARE = "hardware"
LOGICAL = "logical"
PHYSICAL = "physical"

# 평가 지표 상수
SCORE = "score"
SCORE_IF_NOT_ENDPOINT_CONFLICTS_DIRECT_CONNECTIONS_INCORRECT_ATTRS = "score_if_not_endpoint_conflicts_direct_connections_incorrect_attrs"

def load_json(file_path, default=None):
    """JSON 파일을 안전하게 불러옵니다."""
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading JSON from {file_path}: {e}")
        return default if default is not None else {}

def save_json(data, file_path, indent=4):
    """JSON 데이터를 파일에 저장합니다."""
    try:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=indent)
        print(f"Saved to {file_path}")
    except IOError as e:
        print(f"Error saving JSON to {file_path}: {e}")

def get_project_level(project_name):
    """프로젝트 이름에서 레벨 정보를 추출합니다."""
    # 전체 경로(level1/project_name)로 시도
    if project_name in PROJECT_TO_LEVEL:
        return PROJECT_TO_LEVEL[project_name]
    
    # 슬래시로 나눠진 형태로 시도
    parts = project_name.split('/')
    if len(parts) > 1 and parts[0].startswith('level'):
        return parts[0]
    
    # 프로젝트 이름만 있는 경우(project_name)
    for project in PROJECTS:
        if project.endswith('/' + project_name):
            return project.split('/')[0]
    
    # 레벨을 알 수 없는 경우
    print(f"알 수 없는 프로젝트 레벨: {project_name}, 'unknown'으로 처리합니다.")
    return "unknown"

def analyze_model_results():
    """모델별 프로젝트 결과를 분석하고 정리합니다."""
    # 출력 디렉토리 생성
    ANALYSIS_OUTPUT_DIR.mkdir(exist_ok=True, parents=True)
    
    # 모델 JSON 파일들 로드
    model_files = list(MODEL_PROJECT_SUMMARY_DIR.glob("*.json"))
    if not model_files:
        print(f"모델 프로젝트 요약 파일을 찾을 수 없습니다: {MODEL_PROJECT_SUMMARY_DIR}")
        return
    
    # 모델별 분석 결과 저장
    models_analysis = {}
    
    for model_file in model_files:
        model_name = model_file.stem
        print(f"분석 중: {model_name}")
        
        # 모델 데이터 로드
        model_data = load_json(model_file)
        
        # 모델 분석 결과 초기화
        model_analysis = {
            "model": model_name,
            "overall_score": 0,
            "tasks": {
                f"{LOGICAL}_{CODE}_score": 0,
                f"{PHYSICAL}_{CODE}_score": 0,
                f"{LOGICAL}_{HARDWARE}_score": 0,
                f"{PHYSICAL}_{HARDWARE}_score": 0
            },
            "projects_by_score": [],
            "level_scores": {
                "level1": 0,
                "level2": 0,
                "level3": 0,
                "level4": 0,
                "unknown": 0
            },
            "level_task_scores": {
                "level1": {
                    f"{LOGICAL}_{CODE}_score": 0,
                    f"{PHYSICAL}_{CODE}_score": 0,
                    f"{LOGICAL}_{HARDWARE}_score": 0,
                    f"{PHYSICAL}_{HARDWARE}_score": 0
                },
                "level2": {
                    f"{LOGICAL}_{CODE}_score": 0,
                    f"{PHYSICAL}_{CODE}_score": 0,
                    f"{LOGICAL}_{HARDWARE}_score": 0,
                    f"{PHYSICAL}_{HARDWARE}_score": 0
                },
                "level3": {
                    f"{LOGICAL}_{CODE}_score": 0,
                    f"{PHYSICAL}_{CODE}_score": 0,
                    f"{LOGICAL}_{HARDWARE}_score": 0,
                    f"{PHYSICAL}_{HARDWARE}_score": 0
                },
                "level4": {
                    f"{LOGICAL}_{CODE}_score": 0,
                    f"{PHYSICAL}_{CODE}_score": 0,
                    f"{LOGICAL}_{HARDWARE}_score": 0,
                    f"{PHYSICAL}_{HARDWARE}_score": 0
                },
                "unknown": {
                    f"{LOGICAL}_{CODE}_score": 0,
                    f"{PHYSICAL}_{CODE}_score": 0,
                    f"{LOGICAL}_{HARDWARE}_score": 0,
                    f"{PHYSICAL}_{HARDWARE}_score": 0
                }
            }
        }
        
        # 레벨별 태스크 카운터 초기화
        level_task_counters = {
            level: {
                f"{LOGICAL}_{CODE}_count": 0,
                f"{PHYSICAL}_{CODE}_count": 0,
                f"{LOGICAL}_{HARDWARE}_count": 0,
                f"{PHYSICAL}_{HARDWARE}_count": 0
            } for level in model_analysis["level_scores"].keys()
        }
        
        # 태스크별 카운터 초기화
        task_counters = {
            f"{LOGICAL}_{CODE}_count": 0,
            f"{PHYSICAL}_{CODE}_count": 0,
            f"{LOGICAL}_{HARDWARE}_count": 0,
            f"{PHYSICAL}_{HARDWARE}_count": 0
        }
        
        # 프로젝트 성적 분석
        project_scores = []
        
        for project_name, project_data in model_data.items():
            # 프로젝트 레벨 확인
            project_level = get_project_level(project_name)
            
            # 태스크 존재 여부 확인 (0점은 존재하는 것으로 간주)
            task_exists = {
                f"{LOGICAL}_{CODE}": False,
                f"{PHYSICAL}_{CODE}": False,
                f"{LOGICAL}_{HARDWARE}": False,
                f"{PHYSICAL}_{HARDWARE}": False
            }
            
            # 각 태스크 점수 추출
            logical_code_score = 0
            physical_code_score = 0
            logical_hardware_score = 0
            physical_hardware_score = 0
            
            # 코드 점수 추출
            if CODE in project_data:
                if LOGICAL in project_data[CODE]:
                    task_exists[f"{LOGICAL}_{CODE}"] = True
                    logical_code_score = project_data[CODE][LOGICAL].get(SCORE, 0)
                    model_analysis["tasks"][f"{LOGICAL}_{CODE}_score"] += logical_code_score
                    model_analysis["level_task_scores"][project_level][f"{LOGICAL}_{CODE}_score"] += logical_code_score
                    task_counters[f"{LOGICAL}_{CODE}_count"] += 1
                    level_task_counters[project_level][f"{LOGICAL}_{CODE}_count"] += 1
                
                if PHYSICAL in project_data[CODE]:
                    task_exists[f"{PHYSICAL}_{CODE}"] = True
                    physical_code_score = project_data[CODE][PHYSICAL].get(SCORE, 0)
                    model_analysis["tasks"][f"{PHYSICAL}_{CODE}_score"] += physical_code_score
                    model_analysis["level_task_scores"][project_level][f"{PHYSICAL}_{CODE}_score"] += physical_code_score
                    task_counters[f"{PHYSICAL}_{CODE}_count"] += 1
                    level_task_counters[project_level][f"{PHYSICAL}_{CODE}_count"] += 1
            
            # 하드웨어 점수 추출
            if HARDWARE in project_data:
                if LOGICAL in project_data[HARDWARE]:
                    task_exists[f"{LOGICAL}_{HARDWARE}"] = True
                    logical_hardware_score = project_data[HARDWARE][LOGICAL].get(SCORE, 0)
                    model_analysis["tasks"][f"{LOGICAL}_{HARDWARE}_score"] += logical_hardware_score
                    model_analysis["level_task_scores"][project_level][f"{LOGICAL}_{HARDWARE}_score"] += logical_hardware_score
                    task_counters[f"{LOGICAL}_{HARDWARE}_count"] += 1
                    level_task_counters[project_level][f"{LOGICAL}_{HARDWARE}_count"] += 1
                
                if PHYSICAL in project_data[HARDWARE]:
                    task_exists[f"{PHYSICAL}_{HARDWARE}"] = True
                    # 물리 하드웨어는 특수 점수 사용
                    hw_physical_data = project_data[HARDWARE][PHYSICAL]
                    if SCORE_IF_NOT_ENDPOINT_CONFLICTS_DIRECT_CONNECTIONS_INCORRECT_ATTRS in hw_physical_data:
                        physical_hardware_score = hw_physical_data[SCORE_IF_NOT_ENDPOINT_CONFLICTS_DIRECT_CONNECTIONS_INCORRECT_ATTRS]
                    else:
                        physical_hardware_score = hw_physical_data.get(SCORE, 0)
                    
                    model_analysis["tasks"][f"{PHYSICAL}_{HARDWARE}_score"] += physical_hardware_score
                    model_analysis["level_task_scores"][project_level][f"{PHYSICAL}_{HARDWARE}_score"] += physical_hardware_score
                    task_counters[f"{PHYSICAL}_{HARDWARE}_count"] += 1
                    level_task_counters[project_level][f"{PHYSICAL}_{HARDWARE}_count"] += 1
            
            # 프로젝트의 종합 점수 계산 (존재하는 태스크의 평균)
            existing_task_scores = []
            
            if task_exists[f"{LOGICAL}_{CODE}"]:
                existing_task_scores.append(logical_code_score)
            
            if task_exists[f"{PHYSICAL}_{CODE}"]:
                existing_task_scores.append(physical_code_score)
            
            if task_exists[f"{LOGICAL}_{HARDWARE}"]:
                existing_task_scores.append(logical_hardware_score)
            
            if task_exists[f"{PHYSICAL}_{HARDWARE}"]:
                existing_task_scores.append(physical_hardware_score)
            
            project_score = sum(existing_task_scores) / len(existing_task_scores) if existing_task_scores else 0
            
            # 프로젝트 점수 저장
            project_scores.append({
                "project": project_name,
                "score": project_score,
                "level": project_level,
                "tasks": {
                    f"{LOGICAL}_{CODE}_score": logical_code_score if task_exists[f"{LOGICAL}_{CODE}"] else None,
                    f"{PHYSICAL}_{CODE}_score": physical_code_score if task_exists[f"{PHYSICAL}_{CODE}"] else None,
                    f"{LOGICAL}_{HARDWARE}_score": logical_hardware_score if task_exists[f"{LOGICAL}_{HARDWARE}"] else None,
                    f"{PHYSICAL}_{HARDWARE}_score": physical_hardware_score if task_exists[f"{PHYSICAL}_{HARDWARE}"] else None
                },
                "task_exists": task_exists
            })
        
        # 프로젝트 점수 내림차순 정렬
        project_scores.sort(key=lambda x: x["score"], reverse=True)
        model_analysis["projects_by_score"] = project_scores
        
        # 태스크별 평균 점수 계산
        for task, score_sum in model_analysis["tasks"].items():
            count_key = f"{task[:-6]}_count"  # 'logical_code_score' -> 'logical_code_count'
            if task_counters[count_key] > 0:
                model_analysis["tasks"][task] = score_sum / task_counters[count_key]
        
        # 레벨별 태스크 평균 점수 계산
        for level in model_analysis["level_task_scores"].keys():
            for task, score_sum in model_analysis["level_task_scores"][level].items():
                count_key = f"{task[:-6]}_count"  # 'logical_code_score' -> 'logical_code_count'
                if level_task_counters[level][count_key] > 0:
                    model_analysis["level_task_scores"][level][task] = score_sum / level_task_counters[level][count_key]
        
        # 레벨별 종합 점수 계산 (존재하는 태스크의 평균, 0점도 포함)
        for level in model_analysis["level_scores"].keys():
            level_task_scores = []
            for task, score in model_analysis["level_task_scores"][level].items():
                count_key = f"{task[:-6]}_count"  # 'logical_code_score' -> 'logical_code_count'
                # 태스크가 존재하는 경우(count > 0)에만 점수 포함
                if level_task_counters[level][count_key] > 0:
                    level_task_scores.append(score)
            
            if level_task_scores:
                model_analysis["level_scores"][level] = sum(level_task_scores) / len(level_task_scores)
        
        # 전체 평균 점수 계산 (태스크 평균)
        task_scores = []
        for task, score in model_analysis["tasks"].items():
            count_key = f"{task[:-6]}_count"  # 'logical_code_score' -> 'logical_code_count'
            # 태스크가 존재하는 경우에만 포함 (전체 모델에서 한 번이라도 평가된 태스크)
            if task_counters[count_key] > 0:
                task_scores.append(score)
        
        if task_scores:
            model_analysis["overall_score"] = sum(task_scores) / len(task_scores)
        
        # 모델 분석 결과 저장
        models_analysis[model_name] = model_analysis
    
    # 모델별 분석 결과를 내림차순 정렬 (overall_score 기준)
    sorted_models = sorted(models_analysis.items(), key=lambda x: x[1]["overall_score"], reverse=True)
    sorted_models_analysis = {model: data for model, data in sorted_models}
    
    # 모델별 분석 결과 저장 (단일 JSON 파일)
    save_json(sorted_models_analysis, ANALYSIS_OUTPUT_DIR / "models_analysis.json")
    print(f"모델별 분석 결과 저장 완료: {ANALYSIS_OUTPUT_DIR / 'models_analysis.json'}")

def main():
    """메인 함수"""
    print("모델별 프로젝트 결과 분석 시작...")
    analyze_model_results()
    print("분석 완료!")

if __name__ == "__main__":
    main()