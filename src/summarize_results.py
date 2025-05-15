import os
import json
import sys
from pathlib import Path

# --- Constants ---

EXPERIMENTS_DIR = Path("experiments")
SUMMARY_DIR_NAME = "summary"
MODEL_PROJECT_SUMMARY_SUBDIR = "model_project"

SUMMARY_DIR = EXPERIMENTS_DIR / SUMMARY_DIR_NAME
MODEL_PROJECT_SUMMARY_DIR = SUMMARY_DIR / MODEL_PROJECT_SUMMARY_SUBDIR
ALL_PROJECT_SUMMARY_FILE = SUMMARY_DIR / "all_project_summary.json"
ALL_MODEL_SUMMARY_FILE = SUMMARY_DIR / "all_model_summary.json"

# 자기 개선 관련 상수 추가
MAX_ITERATIONS = 5  # 최대 반복 횟수 기준값

LOGICAL = "logical"
PHYSICAL = "physical"
CODE = "code"
HARDWARE = "hardware"
CODEWARE = "codeware"

# Result Keys
RESULT = "result"
COMPILE_RESULT = "compile_result"
CONVERTING = "converting"
HW_EVAL_RESULT = "hardware_evaluation_result"
# 자기 개선 관련 키 추가
ITERATIONS = "iterations"
BEST_ITERATION = "best_iteration"
TOTAL_ITERATIONS = "total_iterations"
FINAL_SUCCESS = "final_success"
# 각 반복 횟수별 점수를 저장하기 위한 키 추가
ITERATION_SCORES = "iteration_scores"
ITERATION_DETAILS = "iteration_details"  # 모든 반복 결과의 상세 정보
# 조건부 성공 점수를 iteration별로 저장하기 위한 키 추가
ITERATION_SCORES_IF_NOT_ENDPOINT_CONFLICTS = "iteration_scores_if_not_endpoint_conflicts"
ITERATION_SCORES_IF_NOT_DIRECT_CONNECTIONS = "iteration_scores_if_not_direct_connections"
ITERATION_SCORES_IF_NOT_ENDPOINT_CONFLICTS_DIRECT_CONNECTIONS = "iteration_scores_if_not_endpoint_conflicts_direct_connections"
ITERATION_SCORES_IF_NOT_INCORRECT_ATTRS = "iteration_scores_if_not_incorrect_attrs"
ITERATION_SCORES_IF_NOT_ENDPOINT_CONFLICTS_INCORRECT_ATTRS = "iteration_scores_if_not_endpoint_conflicts_incorrect_attrs"
ITERATION_SCORES_IF_NOT_DIRECT_CONNECTIONS_INCORRECT_ATTRS = "iteration_scores_if_not_direct_connections_incorrect_attrs"
ITERATION_SCORES_IF_NOT_ENDPOINT_CONFLICTS_DIRECT_CONNECTIONS_INCORRECT_ATTRS = "iteration_scores_if_not_endpoint_conflicts_direct_connections_incorrect_attrs"

# Summary Keys
SUCCESS = "success"
TOTAL = "total"
SCORE = "score"
COMPILE_SUCCESS = "compile_success"
CONVERTING_SUCCESS = "converting_success"
HW_EVAL = "hardware_evaluation"
CODEBLEU_SCORE = "codebleu_score"
CODEBLEU_SCORE_SUM = "codebleu_score_sum"
CODEBLEU_SCORE_COUNT = "codebleu_score_count"
# 성공/실패 케이스 CodeBLEU 관련 키 추가
CODEBLEU_SCORE_SUCCESS = "codebleu_score_success"
CODEBLEU_SCORE_SUCCESS_SUM = "codebleu_score_success_sum"
CODEBLEU_SCORE_SUCCESS_COUNT = "codebleu_score_success_count"
CODEBLEU_SCORE_FAIL = "codebleu_score_fail"
CODEBLEU_SCORE_FAIL_SUM = "codebleu_score_fail_sum"
CODEBLEU_SCORE_FAIL_COUNT = "codebleu_score_fail_count"
# 자기 개선 관련 요약 키 추가
AVG_ITERATIONS_TO_SUCCESS = "avg_iterations_to_success"
ITERATIONS_TO_SUCCESS_SUM = "iterations_to_success_sum"
ITERATIONS_TO_SUCCESS_COUNT = "iterations_to_success_count"
SUCCESS_FIRST_ATTEMPT = "success_first_attempt"
SUCCESS_WITH_IMPROVEMENT = "success_with_improvement"

# Hardware Metric Keys (add others as needed)
DUPLICATE_CONNECTIONS = "duplicate_connections"
UNUSED_COMPONENTS = "unused_components"
UNNECESSARY_COMPONENTS = "unnecessary_components"
MISSING_COMPONENTS = "missing_components"
ENDPOINT_CONFLICTS = "endpoint_conflicts"
DIRECT_CONNECTIONS = "direct_connections"
BREADBOARD_CONNECTIONS = "breadboard_connections"
DIRECT_CONNECTION_PERCENTAGE = "direct_connection_percentage"
BREADBOARD_CONNECTION_PERCENTAGE = "breadboard_connection_percentage"
SUCCESS_IF_NOT_ENDPOINT_CONFLICTS = "success_if_not_endpoint_conflicts"
SCORE_IF_NOT_ENDPOINT_CONFLICTS = "score_if_not_endpoint_conflicts"
SUCCESS_IF_NOT_DIRECT_CONNECTIONS = "success_if_not_direct_connections"
SCORE_IF_NOT_DIRECT_CONNECTIONS = "score_if_not_direct_connections"
SUCCESS_IF_NOT_ENDPOINT_CONFLICTS_DIRECT_CONNECTIONS = "success_if_not_endpoint_conflicts_direct_connections"
SCORE_IF_NOT_ENDPOINT_CONFLICTS_DIRECT_CONNECTIONS = "score_if_not_endpoint_conflicts_direct_connections"
# 컴포넌트 속성 관련 상수 추가
INCORRECT_ATTRS = "incorrect_attrs"
INCORRECT_ATTRS_LIST = "incorrect_attrs_list"
# 컴포넌트 속성 관련 성공 조건 상수 추가
SUCCESS_IF_NOT_INCORRECT_ATTRS = "success_if_not_incorrect_attrs"
SCORE_IF_NOT_INCORRECT_ATTRS = "score_if_not_incorrect_attrs"
SUCCESS_IF_NOT_ENDPOINT_CONFLICTS_INCORRECT_ATTRS = "success_if_not_endpoint_conflicts_incorrect_attrs"
SCORE_IF_NOT_ENDPOINT_CONFLICTS_INCORRECT_ATTRS = "score_if_not_endpoint_conflicts_incorrect_attrs"
SUCCESS_IF_NOT_DIRECT_CONNECTIONS_INCORRECT_ATTRS = "success_if_not_direct_connections_incorrect_attrs"
SCORE_IF_NOT_DIRECT_CONNECTIONS_INCORRECT_ATTRS = "score_if_not_direct_connections_incorrect_attrs"
SUCCESS_IF_NOT_ENDPOINT_CONFLICTS_DIRECT_CONNECTIONS_INCORRECT_ATTRS = "success_if_not_endpoint_conflicts_direct_connections_incorrect_attrs"
SCORE_IF_NOT_ENDPOINT_CONFLICTS_DIRECT_CONNECTIONS_INCORRECT_ATTRS = "score_if_not_endpoint_conflicts_direct_connections_incorrect_attrs"

# Metrics to average (not recalculate percentage)
HW_COUNT_METRICS_TO_AVERAGE = [
    DUPLICATE_CONNECTIONS,
    UNUSED_COMPONENTS,
    ENDPOINT_CONFLICTS,
    UNNECESSARY_COMPONENTS,
    MISSING_COMPONENTS,
    INCORRECT_ATTRS,  # 평균을 계산할 메트릭에 추가
]


# --- Helper Functions ---

def create_metrics_structure():
    """Creates the base nested dictionary structure for storing metrics."""
    metrics = {
        SCORE: 0,
        TOTAL: 0,
        SUCCESS: 0,
        CODE: {
            SCORE: 0,
            TOTAL: 0,
            SUCCESS: 0,
            COMPILE_SUCCESS: 0,
            # 자기 개선 관련 통계 필드 추가
            AVG_ITERATIONS_TO_SUCCESS: 0.0,
            ITERATIONS_TO_SUCCESS_SUM: 0,
            ITERATIONS_TO_SUCCESS_COUNT: 0,
            SUCCESS_FIRST_ATTEMPT: 0,
            SUCCESS_WITH_IMPROVEMENT: 0,
            # 각 반복 횟수별 점수 및 상세 정보 저장
            ITERATION_SCORES: {str(i): 0 for i in range(1, MAX_ITERATIONS+1)},
            ITERATION_DETAILS: {},
            LOGICAL: {
                SCORE: 0,
                TOTAL: 0,
                SUCCESS: 0,
                COMPILE_SUCCESS: 0,
                CODEBLEU_SCORE: 0.0,
                CODEBLEU_SCORE_SUM: 0.0,
                CODEBLEU_SCORE_COUNT: 0,
                # 성공/실패 케이스 CodeBLEU 추가
                CODEBLEU_SCORE_SUCCESS: 0.0,
                CODEBLEU_SCORE_SUCCESS_SUM: 0.0,
                CODEBLEU_SCORE_SUCCESS_COUNT: 0,
                CODEBLEU_SCORE_FAIL: 0.0,
                CODEBLEU_SCORE_FAIL_SUM: 0.0,
                CODEBLEU_SCORE_FAIL_COUNT: 0,
                # 자기 개선 관련 통계 필드 추가
                AVG_ITERATIONS_TO_SUCCESS: 0.0,
                ITERATIONS_TO_SUCCESS_SUM: 0,
                ITERATIONS_TO_SUCCESS_COUNT: 0,
                SUCCESS_FIRST_ATTEMPT: 0,
                SUCCESS_WITH_IMPROVEMENT: 0,
                # 각 반복 횟수별 점수 및 상세 정보 저장
                ITERATION_SCORES: {str(i): 0 for i in range(1, MAX_ITERATIONS+1)},
                ITERATION_DETAILS: {}
            },
            PHYSICAL: {
                SCORE: 0,
                TOTAL: 0,
                SUCCESS: 0,
                COMPILE_SUCCESS: 0,
                CODEBLEU_SCORE: 0.0,
                CODEBLEU_SCORE_SUM: 0.0,
                CODEBLEU_SCORE_COUNT: 0,
                # 성공/실패 케이스 CodeBLEU 추가
                CODEBLEU_SCORE_SUCCESS: 0.0,
                CODEBLEU_SCORE_SUCCESS_SUM: 0.0,
                CODEBLEU_SCORE_SUCCESS_COUNT: 0,
                CODEBLEU_SCORE_FAIL: 0.0,
                CODEBLEU_SCORE_FAIL_SUM: 0.0,
                CODEBLEU_SCORE_FAIL_COUNT: 0,
                # 자기 개선 관련 통계 필드 추가
                AVG_ITERATIONS_TO_SUCCESS: 0.0,
                ITERATIONS_TO_SUCCESS_SUM: 0,
                ITERATIONS_TO_SUCCESS_COUNT: 0,
                SUCCESS_FIRST_ATTEMPT: 0,
                SUCCESS_WITH_IMPROVEMENT: 0,
                # 각 반복 횟수별 점수 및 상세 정보 저장
                ITERATION_SCORES: {str(i): 0 for i in range(1, MAX_ITERATIONS+1)},
                ITERATION_DETAILS: {},
                # 조건부 성공 관련 필드
                SUCCESS_IF_NOT_ENDPOINT_CONFLICTS: 0,
                SUCCESS_IF_NOT_DIRECT_CONNECTIONS: 0,
                SUCCESS_IF_NOT_ENDPOINT_CONFLICTS_DIRECT_CONNECTIONS: 0,
                # 조건부 성공에 대한 반복별 점수
                ITERATION_SCORES_IF_NOT_ENDPOINT_CONFLICTS: {str(i): 0 for i in range(1, MAX_ITERATIONS+1)},
                ITERATION_SCORES_IF_NOT_DIRECT_CONNECTIONS: {str(i): 0 for i in range(1, MAX_ITERATIONS+1)},
                ITERATION_SCORES_IF_NOT_ENDPOINT_CONFLICTS_DIRECT_CONNECTIONS: {str(i): 0 for i in range(1, MAX_ITERATIONS+1)},
                ITERATION_SCORES_IF_NOT_INCORRECT_ATTRS: {str(i): 0 for i in range(1, MAX_ITERATIONS+1)},
                ITERATION_SCORES_IF_NOT_ENDPOINT_CONFLICTS_INCORRECT_ATTRS: {str(i): 0 for i in range(1, MAX_ITERATIONS+1)},
                ITERATION_SCORES_IF_NOT_DIRECT_CONNECTIONS_INCORRECT_ATTRS: {str(i): 0 for i in range(1, MAX_ITERATIONS+1)},
                ITERATION_SCORES_IF_NOT_ENDPOINT_CONFLICTS_DIRECT_CONNECTIONS_INCORRECT_ATTRS: {str(i): 0 for i in range(1, MAX_ITERATIONS+1)},
                HW_EVAL: {
                    DUPLICATE_CONNECTIONS: 0,
                    UNUSED_COMPONENTS: 0,
                    UNNECESSARY_COMPONENTS: 0,
                    MISSING_COMPONENTS: 0
                }
            }
        },
        HARDWARE: {
            SCORE: 0,
            TOTAL: 0,
            SUCCESS: 0,
            CONVERTING_SUCCESS: 0,
            # 자기 개선 관련 통계 필드 추가
            AVG_ITERATIONS_TO_SUCCESS: 0.0,
            ITERATIONS_TO_SUCCESS_SUM: 0,
            ITERATIONS_TO_SUCCESS_COUNT: 0,
            SUCCESS_FIRST_ATTEMPT: 0,
            SUCCESS_WITH_IMPROVEMENT: 0,
            # 각 반복 횟수별 점수 및 상세 정보 저장
            ITERATION_SCORES: {str(i): 0 for i in range(1, MAX_ITERATIONS+1)},
            ITERATION_DETAILS: {},
            LOGICAL: {
                SCORE: 0,
                TOTAL: 0,
                SUCCESS: 0,
                CONVERTING_SUCCESS: 0,
                # 자기 개선 관련 통계 필드 추가
                AVG_ITERATIONS_TO_SUCCESS: 0.0,
                ITERATIONS_TO_SUCCESS_SUM: 0,
                ITERATIONS_TO_SUCCESS_COUNT: 0,
                SUCCESS_FIRST_ATTEMPT: 0,
                SUCCESS_WITH_IMPROVEMENT: 0,
                # 각 반복 횟수별 점수 및 상세 정보 저장
                ITERATION_SCORES: {str(i): 0 for i in range(1, MAX_ITERATIONS+1)},
                ITERATION_DETAILS: {},
                HW_EVAL: {
                    DUPLICATE_CONNECTIONS: 0,
                    UNUSED_COMPONENTS: 0,
                    UNNECESSARY_COMPONENTS: 0,
                    MISSING_COMPONENTS: 0,
                    INCORRECT_ATTRS: 0
                }
            },
            PHYSICAL: {
                SCORE: 0,
                TOTAL: 0,
                SUCCESS: 0,
                CONVERTING_SUCCESS: 0,
                # 자기 개선 관련 통계 필드 추가
                AVG_ITERATIONS_TO_SUCCESS: 0.0,
                ITERATIONS_TO_SUCCESS_SUM: 0,
                ITERATIONS_TO_SUCCESS_COUNT: 0,
                SUCCESS_FIRST_ATTEMPT: 0,
                SUCCESS_WITH_IMPROVEMENT: 0,
                # 각 반복 횟수별 점수 및 상세 정보 저장
                ITERATION_SCORES: {str(i): 0 for i in range(1, MAX_ITERATIONS+1)},
                ITERATION_DETAILS: {},
                # 조건부 성공 관련 필드
                SUCCESS_IF_NOT_ENDPOINT_CONFLICTS: 0,
                SUCCESS_IF_NOT_DIRECT_CONNECTIONS: 0,
                SUCCESS_IF_NOT_ENDPOINT_CONFLICTS_DIRECT_CONNECTIONS: 0,
                # 컴포넌트 속성 관련 성공 조건 추가
                SUCCESS_IF_NOT_INCORRECT_ATTRS: 0,
                SUCCESS_IF_NOT_ENDPOINT_CONFLICTS_INCORRECT_ATTRS: 0,
                SUCCESS_IF_NOT_DIRECT_CONNECTIONS_INCORRECT_ATTRS: 0,
                SUCCESS_IF_NOT_ENDPOINT_CONFLICTS_DIRECT_CONNECTIONS_INCORRECT_ATTRS: 0,
                # 조건부 성공에 대한 반복별 점수
                ITERATION_SCORES_IF_NOT_ENDPOINT_CONFLICTS: {str(i): 0 for i in range(1, MAX_ITERATIONS+1)},
                ITERATION_SCORES_IF_NOT_DIRECT_CONNECTIONS: {str(i): 0 for i in range(1, MAX_ITERATIONS+1)},
                ITERATION_SCORES_IF_NOT_ENDPOINT_CONFLICTS_DIRECT_CONNECTIONS: {str(i): 0 for i in range(1, MAX_ITERATIONS+1)},
                ITERATION_SCORES_IF_NOT_INCORRECT_ATTRS: {str(i): 0 for i in range(1, MAX_ITERATIONS+1)},
                ITERATION_SCORES_IF_NOT_ENDPOINT_CONFLICTS_INCORRECT_ATTRS: {str(i): 0 for i in range(1, MAX_ITERATIONS+1)},
                ITERATION_SCORES_IF_NOT_DIRECT_CONNECTIONS_INCORRECT_ATTRS: {str(i): 0 for i in range(1, MAX_ITERATIONS+1)},
                ITERATION_SCORES_IF_NOT_ENDPOINT_CONFLICTS_DIRECT_CONNECTIONS_INCORRECT_ATTRS: {str(i): 0 for i in range(1, MAX_ITERATIONS+1)},
                HW_EVAL: {
                    DUPLICATE_CONNECTIONS: 0,
                    UNUSED_COMPONENTS: 0,
                    ENDPOINT_CONFLICTS: 0,
                    UNNECESSARY_COMPONENTS: 0,
                    MISSING_COMPONENTS: 0,
                    DIRECT_CONNECTIONS: 0,
                    BREADBOARD_CONNECTIONS: 0,
                    DIRECT_CONNECTION_PERCENTAGE: 0,
                    BREADBOARD_CONNECTION_PERCENTAGE: 0,
                    INCORRECT_ATTRS: 0
                }
            }
        },
        CODEWARE: {
            SCORE: 0,
            TOTAL: 0,
            SUCCESS: 0,
            # 자기 개선 관련 통계 필드 추가
            AVG_ITERATIONS_TO_SUCCESS: 0.0,
            ITERATIONS_TO_SUCCESS_SUM: 0,
            ITERATIONS_TO_SUCCESS_COUNT: 0,
            SUCCESS_FIRST_ATTEMPT: 0,
            SUCCESS_WITH_IMPROVEMENT: 0,
            # 각 반복 횟수별 점수 및 상세 정보 저장
            ITERATION_SCORES: {str(i): 0 for i in range(1, MAX_ITERATIONS+1)},
            ITERATION_DETAILS: {},
            LOGICAL: {
                SCORE: 0,
                TOTAL: 0,
                SUCCESS: 0,
                COMPILE_SUCCESS: 0,
                CODEBLEU_SCORE: 0.0,
                CODEBLEU_SCORE_SUM: 0.0,
                CODEBLEU_SCORE_COUNT: 0,
                # 성공/실패 케이스 CodeBLEU 추가
                CODEBLEU_SCORE_SUCCESS: 0.0,
                CODEBLEU_SCORE_SUCCESS_SUM: 0.0,
                CODEBLEU_SCORE_SUCCESS_COUNT: 0,
                CODEBLEU_SCORE_FAIL: 0.0,
                CODEBLEU_SCORE_FAIL_SUM: 0.0,
                CODEBLEU_SCORE_FAIL_COUNT: 0,
                # 각 반복 횟수별 점수 및 상세 정보 저장
                ITERATION_SCORES: {str(i): 0 for i in range(1, MAX_ITERATIONS+1)},
                ITERATION_DETAILS: {},
                HW_EVAL: {
                    DUPLICATE_CONNECTIONS: 0,
                    UNUSED_COMPONENTS: 0,
                    UNNECESSARY_COMPONENTS: 0,
                    MISSING_COMPONENTS: 0,
                    INCORRECT_ATTRS: 0
                }
            },
            PHYSICAL: {
                SCORE: 0,
                TOTAL: 0,
                SUCCESS: 0,
                COMPILE_SUCCESS: 0,
                CODEBLEU_SCORE: 0.0,
                CODEBLEU_SCORE_SUM: 0.0,
                CODEBLEU_SCORE_COUNT: 0,
                # 성공/실패 케이스 CodeBLEU 추가
                CODEBLEU_SCORE_SUCCESS: 0.0,
                CODEBLEU_SCORE_SUCCESS_SUM: 0.0,
                CODEBLEU_SCORE_SUCCESS_COUNT: 0,
                CODEBLEU_SCORE_FAIL: 0.0,
                CODEBLEU_SCORE_FAIL_SUM: 0.0,
                CODEBLEU_SCORE_FAIL_COUNT: 0,
                # 각 반복 횟수별 점수 및 상세 정보 저장
                ITERATION_SCORES: {str(i): 0 for i in range(1, MAX_ITERATIONS+1)},
                ITERATION_DETAILS: {},
                # 조건부 성공 관련 필드
                SUCCESS_IF_NOT_ENDPOINT_CONFLICTS: 0,
                SUCCESS_IF_NOT_DIRECT_CONNECTIONS: 0,
                SUCCESS_IF_NOT_ENDPOINT_CONFLICTS_DIRECT_CONNECTIONS: 0,
                # 컴포넌트 속성 관련 성공 조건 추가
                SUCCESS_IF_NOT_INCORRECT_ATTRS: 0,
                SUCCESS_IF_NOT_ENDPOINT_CONFLICTS_INCORRECT_ATTRS: 0,
                SUCCESS_IF_NOT_DIRECT_CONNECTIONS_INCORRECT_ATTRS: 0,
                SUCCESS_IF_NOT_ENDPOINT_CONFLICTS_DIRECT_CONNECTIONS_INCORRECT_ATTRS: 0,
                # 조건부 성공에 대한 반복별 점수
                ITERATION_SCORES_IF_NOT_ENDPOINT_CONFLICTS: {str(i): 0 for i in range(1, MAX_ITERATIONS+1)},
                ITERATION_SCORES_IF_NOT_DIRECT_CONNECTIONS: {str(i): 0 for i in range(1, MAX_ITERATIONS+1)},
                ITERATION_SCORES_IF_NOT_ENDPOINT_CONFLICTS_DIRECT_CONNECTIONS: {str(i): 0 for i in range(1, MAX_ITERATIONS+1)},
                ITERATION_SCORES_IF_NOT_INCORRECT_ATTRS: {str(i): 0 for i in range(1, MAX_ITERATIONS+1)},
                ITERATION_SCORES_IF_NOT_ENDPOINT_CONFLICTS_INCORRECT_ATTRS: {str(i): 0 for i in range(1, MAX_ITERATIONS+1)},
                ITERATION_SCORES_IF_NOT_DIRECT_CONNECTIONS_INCORRECT_ATTRS: {str(i): 0 for i in range(1, MAX_ITERATIONS+1)},
                ITERATION_SCORES_IF_NOT_ENDPOINT_CONFLICTS_DIRECT_CONNECTIONS_INCORRECT_ATTRS: {str(i): 0 for i in range(1, MAX_ITERATIONS+1)},
                HW_EVAL: {
                    DUPLICATE_CONNECTIONS: 0,
                    UNUSED_COMPONENTS: 0,
                    ENDPOINT_CONFLICTS: 0,
                    UNNECESSARY_COMPONENTS: 0,
                    MISSING_COMPONENTS: 0,
                    DIRECT_CONNECTIONS: 0,
                    BREADBOARD_CONNECTIONS: 0,
                    DIRECT_CONNECTION_PERCENTAGE: 0,
                    BREADBOARD_CONNECTION_PERCENTAGE: 0,
                    INCORRECT_ATTRS: 0
                }
            }
        }
    }
    return metrics


def aggregate_metrics(source_dict, target_dict):
    """Recursively aggregates numerical values from source_dict into target_dict."""
    for key, value in source_dict.items():
        if key in target_dict:
            if isinstance(value, (int, float)):
                target_dict[key] += value
            elif isinstance(value, dict):
                aggregate_metrics(value, target_dict[key])
            # Ignore non-numeric types like 'project' or 'model' name


def calculate_scores(metrics_dict):
    """Recursively calculates the 'score' (success / total) in a metrics dictionary."""
    for key, value in metrics_dict.items():
        if key == SCORE and metrics_dict.get(TOTAL, 0) != 0:
            metrics_dict[SCORE] = metrics_dict.get(SUCCESS, 0) / metrics_dict[TOTAL]
        elif key == AVG_ITERATIONS_TO_SUCCESS and metrics_dict.get(ITERATIONS_TO_SUCCESS_COUNT, 0) != 0:
            # 성공까지 걸린 평균 반복 횟수 계산
            metrics_dict[AVG_ITERATIONS_TO_SUCCESS] = metrics_dict[ITERATIONS_TO_SUCCESS_SUM] / metrics_dict[ITERATIONS_TO_SUCCESS_COUNT]
        elif isinstance(value, dict):
            calculate_scores(value)


def calculate_average_hardware_metrics(hw_eval_dict, success_count):
    """Calculates averages for count-based hardware metrics."""
    if success_count > 0:
        for key in HW_COUNT_METRICS_TO_AVERAGE:
            if key in hw_eval_dict:
                hw_eval_dict[key] /= success_count


def recalculate_physical_hw_percentages(physical_hw_eval):
    """Recalculates direct/breadboard connection percentages based on summed counts."""
    direct_connections_sum = physical_hw_eval.get(DIRECT_CONNECTIONS, 0)
    breadboard_connections_sum = physical_hw_eval.get(BREADBOARD_CONNECTIONS, 0)
    total_connections_sum = direct_connections_sum + breadboard_connections_sum

    if total_connections_sum > 0:
        physical_hw_eval[DIRECT_CONNECTION_PERCENTAGE] = (direct_connections_sum / total_connections_sum) * 100
        physical_hw_eval[BREADBOARD_CONNECTION_PERCENTAGE] = (breadboard_connections_sum / total_connections_sum) * 100
    else:
        physical_hw_eval[DIRECT_CONNECTION_PERCENTAGE] = 0
        physical_hw_eval[BREADBOARD_CONNECTION_PERCENTAGE] = 0


def process_code_result(data, mode, project_summary):
    """Processes code results (logical/physical) from experiment data."""
    result_key = f"{mode}_{CODE}"
    if result_key in data:
        code_data = data[result_key]
        project_summary[TOTAL] += 1
        project_summary[CODE][TOTAL] += 1
        project_summary[CODE][mode][TOTAL] += 1
        
        # 자기 개선 처리를 위한 변수
        final_success = code_data.get(FINAL_SUCCESS, code_data.get(RESULT, False))
        best_iteration = code_data.get(BEST_ITERATION, -1)
        has_iterations = ITERATIONS in code_data and code_data[ITERATIONS]
        iterations_data = code_data.get(ITERATIONS, [])
        
        # 프로젝트명과 모델명 추출 (상세 정보에 포함)
        project_name = data.get('project', 'UnknownProject')
        model_name = data.get('model', 'UnknownModel')
        
        if final_success:
            project_summary[SUCCESS] += 1  # 상위 레벨 SUCCESS 업데이트
            project_summary[CODE][SUCCESS] += 1
            project_summary[CODE][mode][SUCCESS] += 1
            
            # 자기 개선 관련 통계 업데이트
            if has_iterations:
                # 성공한 베스트 반복 횟수 (0-기반 인덱스이므로 +1)
                if best_iteration >= 0:
                    iterations_to_success = best_iteration + 1
                    
                    project_summary[CODE][ITERATIONS_TO_SUCCESS_SUM] += iterations_to_success
                    project_summary[CODE][ITERATIONS_TO_SUCCESS_COUNT] += 1
                    project_summary[CODE][mode][ITERATIONS_TO_SUCCESS_SUM] += iterations_to_success
                    project_summary[CODE][mode][ITERATIONS_TO_SUCCESS_COUNT] += 1
                    
                    # 첫 시도 성공 vs 개선 후 성공 분류
                    if iterations_to_success == 1:
                        project_summary[CODE][SUCCESS_FIRST_ATTEMPT] += 1
                        project_summary[CODE][mode][SUCCESS_FIRST_ATTEMPT] += 1
                    else:
                        project_summary[CODE][SUCCESS_WITH_IMPROVEMENT] += 1
                        project_summary[CODE][mode][SUCCESS_WITH_IMPROVEMENT] += 1
                
                # 각 반복 횟수별 점수 업데이트
                for iter_data in iterations_data:
                    iter_num = iter_data.get("iteration", 0) + 1  # 0-기반 인덱스를 1-기반으로 변환
                    iter_success = iter_data.get("success", False)
                    
                    # 성공한 iteration 및 그 이전 iteration만 점수 업데이트
                    if str(iter_num) in project_summary[CODE][ITERATION_SCORES] and (iter_success or iter_num <= iterations_to_success):
                        # iteration이 성공했으면 1점, 아니면 0점
                        if iter_success:
                            project_summary[CODE][ITERATION_SCORES][str(iter_num)] += 1
                            project_summary[CODE][mode][ITERATION_SCORES][str(iter_num)] += 1
                
                # 상세 정보 저장
                project_key = f"{model_name}_{project_name}"
                if project_key not in project_summary[CODE][ITERATION_DETAILS]:
                    project_summary[CODE][ITERATION_DETAILS][project_key] = {}
                if project_key not in project_summary[CODE][mode][ITERATION_DETAILS]:
                    project_summary[CODE][mode][ITERATION_DETAILS][project_key] = {}
                
                # 상세 정보에 각 iteration 결과 저장
                project_summary[CODE][ITERATION_DETAILS][project_key] = {
                    "project": project_name,
                    "model": model_name,
                    "mode": mode,
                    "final_success": final_success,
                    "best_iteration": best_iteration,
                    "iterations": [
                        {
                            "iteration": i.get("iteration", -1) + 1,  # 1-기반 인덱스로 변환
                            "success": i.get("success", False),
                            "compile_result": i.get("compile_result", False),
                            "test_result": i.get("test_result", False),
                            "codebleu_score": i.get("codebleu_score", None),
                            "error": i.get("error", None)
                        } for i in iterations_data
                    ]
                }
                
                # 모드별 상세 정보도 동일하게 저장
                project_summary[CODE][mode][ITERATION_DETAILS][project_key] = project_summary[CODE][ITERATION_DETAILS][project_key]
        
        if code_data.get(COMPILE_RESULT):
            project_summary[CODE][COMPILE_SUCCESS] += 1
            project_summary[CODE][mode][COMPILE_SUCCESS] += 1
            
        codebleu_score = code_data.get(CODEBLEU_SCORE)
        if codebleu_score is not None and isinstance(codebleu_score, (int, float)):
            project_summary[CODE][mode][CODEBLEU_SCORE_SUM] += codebleu_score
            project_summary[CODE][mode][CODEBLEU_SCORE_COUNT] += 1
            
            # 성공/실패 케이스 CodeBLEU 처리 추가
            is_success = code_data.get(RESULT, False)
            if is_success:
                project_summary[CODE][mode][CODEBLEU_SCORE_SUCCESS_SUM] += codebleu_score
                project_summary[CODE][mode][CODEBLEU_SCORE_SUCCESS_COUNT] += 1
            else:
                project_summary[CODE][mode][CODEBLEU_SCORE_FAIL_SUM] += codebleu_score
                project_summary[CODE][mode][CODEBLEU_SCORE_FAIL_COUNT] += 1
        
        return True # Indicate result was processed
    else:
        print(f"Warning: No {result_key} result found in {data.get('model', 'UnknownModel')}/{data.get('project', 'UnknownProject')}", file=sys.stderr)
        return False # Indicate result was missing


def process_hardware_result(data, mode, project_summary):
    """Processes hardware results (logical/physical) from experiment data."""
    result_key = f"{mode}_{HARDWARE}"
    if result_key in data:
        hw_data = data[result_key]
        project_summary[TOTAL] += 1
        project_summary[HARDWARE][TOTAL] += 1
        project_summary[HARDWARE][mode][TOTAL] += 1

        # 자기 개선 처리를 위한 변수
        final_success = hw_data.get(FINAL_SUCCESS, hw_data.get(RESULT, False))
        best_iteration = hw_data.get(BEST_ITERATION, -1)
        has_iterations = ITERATIONS in hw_data and hw_data[ITERATIONS]
        iterations_data = hw_data.get(ITERATIONS, [])
        
        # 프로젝트명과 모델명 추출 (상세 정보에 포함)
        project_name = data.get('project', 'UnknownProject')
        model_name = data.get('model', 'UnknownModel')

        if final_success:
            project_summary[SUCCESS] += 1  # 상위 레벨 SUCCESS 업데이트
            project_summary[HARDWARE][SUCCESS] += 1
            project_summary[HARDWARE][mode][SUCCESS] += 1
            
            # 자기 개선 관련 통계 업데이트
            if has_iterations:
                # 성공한 베스트 반복 횟수 (0-기반 인덱스이므로 +1)
                if best_iteration >= 0:
                    iterations_to_success = best_iteration + 1
                    
                    project_summary[HARDWARE][ITERATIONS_TO_SUCCESS_SUM] += iterations_to_success
                    project_summary[HARDWARE][ITERATIONS_TO_SUCCESS_COUNT] += 1
                    project_summary[HARDWARE][mode][ITERATIONS_TO_SUCCESS_SUM] += iterations_to_success
                    project_summary[HARDWARE][mode][ITERATIONS_TO_SUCCESS_COUNT] += 1
                    
                    # 첫 시도 성공 vs 개선 후 성공 분류
                    if iterations_to_success == 1:
                        project_summary[HARDWARE][SUCCESS_FIRST_ATTEMPT] += 1
                        project_summary[HARDWARE][mode][SUCCESS_FIRST_ATTEMPT] += 1
                    else:
                        project_summary[HARDWARE][SUCCESS_WITH_IMPROVEMENT] += 1
                        project_summary[HARDWARE][mode][SUCCESS_WITH_IMPROVEMENT] += 1
                
                # 각 반복 횟수별 점수 업데이트
                for iter_data in iterations_data:
                    iter_num = iter_data.get("iteration", 0) + 1  # 0-기반 인덱스를 1-기반으로 변환
                    iter_success = iter_data.get("success", False)
                    
                    # 성공한 iteration 및 그 이전 iteration만 점수 업데이트
                    if str(iter_num) in project_summary[HARDWARE][ITERATION_SCORES] and (iter_success or iter_num <= iterations_to_success):
                        # iteration이 성공했으면 1점, 아니면 0점
                        if iter_success:
                            project_summary[HARDWARE][ITERATION_SCORES][str(iter_num)] += 1
                            project_summary[HARDWARE][mode][ITERATION_SCORES][str(iter_num)] += 1
                    
                    # physical 모드에서 조건부 성공 점수 업데이트
                    if mode == PHYSICAL and iter_data.get("evaluation_results_hw") and iter_data["evaluation_results_hw"].get("metrics"):
                        metrics = iter_data["evaluation_results_hw"]["metrics"]
                        
                        # 조건부 성공 여부 계산
                        # endpoint_conflicts와 direct_connections의 조건부 성공 업데이트
                        endpoint_conflicts_count = metrics.get("endpoint_conflicts", {}).get("endpoint_conflicts", 1)
                        direct_connections_count = metrics.get("direct_connections", {}).get("direct_connections", 1)
                        is_successful = iter_success
                        
                        # 조건부 성공 점수 업데이트
                        if str(iter_num) in project_summary[HARDWARE][mode][ITERATION_SCORES_IF_NOT_ENDPOINT_CONFLICTS]:
                            if is_successful and endpoint_conflicts_count == 0:
                                project_summary[HARDWARE][mode][ITERATION_SCORES_IF_NOT_ENDPOINT_CONFLICTS][str(iter_num)] += 1
                                
                        if str(iter_num) in project_summary[HARDWARE][mode][ITERATION_SCORES_IF_NOT_DIRECT_CONNECTIONS]:
                            if is_successful and direct_connections_count == 0:
                                project_summary[HARDWARE][mode][ITERATION_SCORES_IF_NOT_DIRECT_CONNECTIONS][str(iter_num)] += 1
                                
                        if str(iter_num) in project_summary[HARDWARE][mode][ITERATION_SCORES_IF_NOT_ENDPOINT_CONFLICTS_DIRECT_CONNECTIONS]:
                            if is_successful and endpoint_conflicts_count == 0 and direct_connections_count == 0:
                                project_summary[HARDWARE][mode][ITERATION_SCORES_IF_NOT_ENDPOINT_CONFLICTS_DIRECT_CONNECTIONS][str(iter_num)] += 1
                                
                        # 컴포넌트 속성 관련 조건부 성공 점수 업데이트
                        if "component_attrs" in metrics:
                            incorrect_attrs_count = metrics["component_attrs"].get("incorrect_attrs", 1)
                            
                            if str(iter_num) in project_summary[HARDWARE][mode][ITERATION_SCORES_IF_NOT_INCORRECT_ATTRS]:
                                if is_successful and incorrect_attrs_count == 0:
                                    project_summary[HARDWARE][mode][ITERATION_SCORES_IF_NOT_INCORRECT_ATTRS][str(iter_num)] += 1
                                    
                            if str(iter_num) in project_summary[HARDWARE][mode][ITERATION_SCORES_IF_NOT_ENDPOINT_CONFLICTS_INCORRECT_ATTRS]:
                                if is_successful and endpoint_conflicts_count == 0 and incorrect_attrs_count == 0:
                                    project_summary[HARDWARE][mode][ITERATION_SCORES_IF_NOT_ENDPOINT_CONFLICTS_INCORRECT_ATTRS][str(iter_num)] += 1
                                    
                            if str(iter_num) in project_summary[HARDWARE][mode][ITERATION_SCORES_IF_NOT_DIRECT_CONNECTIONS_INCORRECT_ATTRS]:
                                if is_successful and direct_connections_count == 0 and incorrect_attrs_count == 0:
                                    project_summary[HARDWARE][mode][ITERATION_SCORES_IF_NOT_DIRECT_CONNECTIONS_INCORRECT_ATTRS][str(iter_num)] += 1
                                    
                            if str(iter_num) in project_summary[HARDWARE][mode][ITERATION_SCORES_IF_NOT_ENDPOINT_CONFLICTS_DIRECT_CONNECTIONS_INCORRECT_ATTRS]:
                                if is_successful and endpoint_conflicts_count == 0 and direct_connections_count == 0 and incorrect_attrs_count == 0:
                                    project_summary[HARDWARE][mode][ITERATION_SCORES_IF_NOT_ENDPOINT_CONFLICTS_DIRECT_CONNECTIONS_INCORRECT_ATTRS][str(iter_num)] += 1
                
                # 상세 정보 저장
                project_key = f"{model_name}_{project_name}"
                if project_key not in project_summary[HARDWARE][ITERATION_DETAILS]:
                    project_summary[HARDWARE][ITERATION_DETAILS][project_key] = {}
                if project_key not in project_summary[HARDWARE][mode][ITERATION_DETAILS]:
                    project_summary[HARDWARE][mode][ITERATION_DETAILS][project_key] = {}
                
                # 상세 정보에 각 iteration 결과 저장
                hw_eval_data = {}
                for iter_data in iterations_data:
                    if "evaluation" in iter_data and iter_data["evaluation"] and "metrics" in iter_data["evaluation"]:
                        hw_eval_data = iter_data["evaluation"]["metrics"]
                        break
                
                project_summary[HARDWARE][ITERATION_DETAILS][project_key] = {
                    "project": project_name,
                    "model": model_name,
                    "mode": mode,
                    "final_success": final_success,
                    "best_iteration": best_iteration,
                    "iterations": [
                        {
                            "iteration": i.get("iteration", -1) + 1,  # 1-기반 인덱스로 변환
                            "success": i.get("success", False),
                            "converting": i.get("converting", False),
                            "error": i.get("error", None),
                            "hardware_evaluation": i.get("evaluation", {}).get("metrics", {}) if i.get("evaluation") else {}
                        } for i in iterations_data
                    ],
                    "hardware_evaluation": hw_eval_data
                }
                
                # 모드별 상세 정보도 동일하게 저장
                project_summary[HARDWARE][mode][ITERATION_DETAILS][project_key] = project_summary[HARDWARE][ITERATION_DETAILS][project_key]

        if hw_data.get(CONVERTING):
            project_summary[HARDWARE][CONVERTING_SUCCESS] += 1
            project_summary[HARDWARE][mode][CONVERTING_SUCCESS] += 1

        # Aggregate hardware evaluation metrics
        if HW_EVAL_RESULT in hw_data and hw_data[HW_EVAL_RESULT]:
            eval_results = hw_data[HW_EVAL_RESULT]
            target_eval_dict = project_summary[HARDWARE][mode][HW_EVAL]
            for key, value in eval_results.items():
                if key in target_eval_dict:
                    target_eval_dict[key] += value
                # 컴포넌트 속성 리스트는 별도 처리 (옵션)
                elif key == INCORRECT_ATTRS_LIST and INCORRECT_ATTRS in target_eval_dict and value:
                    # 리스트는 복사하지 않고 카운터만 사용하므로 여기서는 아무것도 하지 않음
                    pass

            # Update special physical success metrics
            if mode == PHYSICAL:
                phys_summary = project_summary[HARDWARE][PHYSICAL]
                success_ep = eval_results.get(SUCCESS_IF_NOT_ENDPOINT_CONFLICTS, 0)
                success_dc = eval_results.get(SUCCESS_IF_NOT_DIRECT_CONNECTIONS, 0)
                success_both = eval_results.get(SUCCESS_IF_NOT_ENDPOINT_CONFLICTS_DIRECT_CONNECTIONS, 0)
                
                # 기본 성공 메트릭 업데이트
                phys_summary[SUCCESS_IF_NOT_ENDPOINT_CONFLICTS] += success_ep
                phys_summary[SUCCESS_IF_NOT_DIRECT_CONNECTIONS] += success_dc
                phys_summary[SUCCESS_IF_NOT_ENDPOINT_CONFLICTS_DIRECT_CONNECTIONS] += success_both
                
                # 컴포넌트 속성 관련 성공 메트릭 업데이트
                phys_summary[SUCCESS_IF_NOT_INCORRECT_ATTRS] += eval_results.get(SUCCESS_IF_NOT_INCORRECT_ATTRS, 0)
                phys_summary[SUCCESS_IF_NOT_ENDPOINT_CONFLICTS_INCORRECT_ATTRS] += eval_results.get(SUCCESS_IF_NOT_ENDPOINT_CONFLICTS_INCORRECT_ATTRS, 0)
                phys_summary[SUCCESS_IF_NOT_DIRECT_CONNECTIONS_INCORRECT_ATTRS] += eval_results.get(SUCCESS_IF_NOT_DIRECT_CONNECTIONS_INCORRECT_ATTRS, 0)
                phys_summary[SUCCESS_IF_NOT_ENDPOINT_CONFLICTS_DIRECT_CONNECTIONS_INCORRECT_ATTRS] += eval_results.get(SUCCESS_IF_NOT_ENDPOINT_CONFLICTS_DIRECT_CONNECTIONS_INCORRECT_ATTRS, 0)
                
        return True # Indicate result was processed
    else:
        print(f"Warning: No {result_key} result found in {data.get('model', 'UnknownModel')}/{data.get('project', 'UnknownProject')}", file=sys.stderr)
        return False # Indicate result was missing


def process_codeware_result(data, mode, project_summary):
    """Processes combined code+hardware (codeware) results."""
    result_key = f"{mode}_{CODEWARE}"
    if result_key in data:
        codeware_data = data[result_key]
        project_summary[TOTAL] += 1
        project_summary[CODEWARE][TOTAL] += 1
        project_summary[CODEWARE][mode][TOTAL] += 1

        # 자기 개선 처리를 위한 변수
        final_success = codeware_data.get(FINAL_SUCCESS, codeware_data.get(RESULT, False))
        best_iteration = codeware_data.get(BEST_ITERATION, -1)
        has_iterations = ITERATIONS in codeware_data and codeware_data[ITERATIONS]
        iterations_data = codeware_data.get(ITERATIONS, [])
        
        # 프로젝트명과 모델명 추출 (상세 정보에 포함)
        project_name = data.get('project', 'UnknownProject')
        model_name = data.get('model', 'UnknownModel')

        if final_success:
            project_summary[SUCCESS] += 1
            project_summary[CODEWARE][SUCCESS] += 1
            project_summary[CODEWARE][mode][SUCCESS] += 1
            
            # 자기 개선 관련 통계 업데이트
            if has_iterations:
                # 성공한 베스트 반복 횟수 (0-기반 인덱스이므로 +1)
                if best_iteration >= 0:
                    iterations_to_success = best_iteration + 1
                    
                    project_summary[CODEWARE][ITERATIONS_TO_SUCCESS_SUM] += iterations_to_success
                    project_summary[CODEWARE][ITERATIONS_TO_SUCCESS_COUNT] += 1
                    project_summary[CODEWARE][mode][ITERATIONS_TO_SUCCESS_SUM] += iterations_to_success
                    project_summary[CODEWARE][mode][ITERATIONS_TO_SUCCESS_COUNT] += 1
                    
                    # 첫 시도 성공 vs 개선 후 성공 분류
                    if iterations_to_success == 1:
                        project_summary[CODEWARE][SUCCESS_FIRST_ATTEMPT] += 1
                        project_summary[CODEWARE][mode][SUCCESS_FIRST_ATTEMPT] += 1
                    else:
                        project_summary[CODEWARE][SUCCESS_WITH_IMPROVEMENT] += 1
                        project_summary[CODEWARE][mode][SUCCESS_WITH_IMPROVEMENT] += 1
                
                # 각 반복 횟수별 점수 업데이트
                for iter_data in iterations_data:
                    iter_num = iter_data.get("iteration", 0) + 1  # 0-기반 인덱스를 1-기반으로 변환
                    iter_success = iter_data.get("success", False)
                    
                    # 성공한 iteration 및 그 이전 iteration만 점수 업데이트
                    if str(iter_num) in project_summary[CODEWARE][ITERATION_SCORES] and (iter_success or iter_num <= iterations_to_success):
                        # iteration이 성공했으면 1점, 아니면 0점
                        if iter_success:
                            project_summary[CODEWARE][ITERATION_SCORES][str(iter_num)] += 1
                            project_summary[CODEWARE][mode][ITERATION_SCORES][str(iter_num)] += 1
                    
                    # physical 모드에서 조건부 성공 점수 업데이트
                    if mode == PHYSICAL and iter_data.get("hardware_evaluation") and isinstance(iter_data["hardware_evaluation"], dict):
                        metrics = iter_data["hardware_evaluation"]
                        
                        # 조건부 성공 여부 계산
                        # endpoint_conflicts와 direct_connections의 조건부 성공 업데이트
                        endpoint_conflicts_count = metrics.get("endpoint_conflicts", {}).get("endpoint_conflicts", 1) if isinstance(metrics.get("endpoint_conflicts"), dict) else metrics.get("endpoint_conflicts", 1)
                        direct_connections_count = metrics.get("direct_connections", {}).get("direct_connections", 1) if isinstance(metrics.get("direct_connections"), dict) else metrics.get("direct_connections", 1)
                        is_successful = iter_success
                        
                        # 조건부 성공 점수 업데이트
                        if str(iter_num) in project_summary[CODEWARE][mode][ITERATION_SCORES_IF_NOT_ENDPOINT_CONFLICTS]:
                            if is_successful and endpoint_conflicts_count == 0:
                                project_summary[CODEWARE][mode][ITERATION_SCORES_IF_NOT_ENDPOINT_CONFLICTS][str(iter_num)] += 1
                                
                        if str(iter_num) in project_summary[CODEWARE][mode][ITERATION_SCORES_IF_NOT_DIRECT_CONNECTIONS]:
                            if is_successful and direct_connections_count == 0:
                                project_summary[CODEWARE][mode][ITERATION_SCORES_IF_NOT_DIRECT_CONNECTIONS][str(iter_num)] += 1
                                
                        if str(iter_num) in project_summary[CODEWARE][mode][ITERATION_SCORES_IF_NOT_ENDPOINT_CONFLICTS_DIRECT_CONNECTIONS]:
                            if is_successful and endpoint_conflicts_count == 0 and direct_connections_count == 0:
                                project_summary[CODEWARE][mode][ITERATION_SCORES_IF_NOT_ENDPOINT_CONFLICTS_DIRECT_CONNECTIONS][str(iter_num)] += 1
                                
                        # 컴포넌트 속성 관련 조건부 성공 점수 업데이트
                        if "component_attrs" in metrics:
                            incorrect_attrs_count = metrics["component_attrs"].get("incorrect_attrs", 1) if isinstance(metrics["component_attrs"], dict) else metrics.get("incorrect_attrs", 1)
                            
                            if str(iter_num) in project_summary[CODEWARE][mode][ITERATION_SCORES_IF_NOT_INCORRECT_ATTRS]:
                                if is_successful and incorrect_attrs_count == 0:
                                    project_summary[CODEWARE][mode][ITERATION_SCORES_IF_NOT_INCORRECT_ATTRS][str(iter_num)] += 1
                                    
                            if str(iter_num) in project_summary[CODEWARE][mode][ITERATION_SCORES_IF_NOT_ENDPOINT_CONFLICTS_INCORRECT_ATTRS]:
                                if is_successful and endpoint_conflicts_count == 0 and incorrect_attrs_count == 0:
                                    project_summary[CODEWARE][mode][ITERATION_SCORES_IF_NOT_ENDPOINT_CONFLICTS_INCORRECT_ATTRS][str(iter_num)] += 1
                                    
                            if str(iter_num) in project_summary[CODEWARE][mode][ITERATION_SCORES_IF_NOT_DIRECT_CONNECTIONS_INCORRECT_ATTRS]:
                                if is_successful and direct_connections_count == 0 and incorrect_attrs_count == 0:
                                    project_summary[CODEWARE][mode][ITERATION_SCORES_IF_NOT_DIRECT_CONNECTIONS_INCORRECT_ATTRS][str(iter_num)] += 1
                                    
                            if str(iter_num) in project_summary[CODEWARE][mode][ITERATION_SCORES_IF_NOT_ENDPOINT_CONFLICTS_DIRECT_CONNECTIONS_INCORRECT_ATTRS]:
                                if is_successful and endpoint_conflicts_count == 0 and direct_connections_count == 0 and incorrect_attrs_count == 0:
                                    project_summary[CODEWARE][mode][ITERATION_SCORES_IF_NOT_ENDPOINT_CONFLICTS_DIRECT_CONNECTIONS_INCORRECT_ATTRS][str(iter_num)] += 1
                
                # 상세 정보 저장
                project_key = f"{model_name}_{project_name}"
                if project_key not in project_summary[CODEWARE][ITERATION_DETAILS]:
                    project_summary[CODEWARE][ITERATION_DETAILS][project_key] = {}
                if project_key not in project_summary[CODEWARE][mode][ITERATION_DETAILS]:
                    project_summary[CODEWARE][mode][ITERATION_DETAILS][project_key] = {}
                
                # 상세 정보에 각 iteration 결과 저장
                project_summary[CODEWARE][ITERATION_DETAILS][project_key] = {
                    "project": project_name,
                    "model": model_name,
                    "mode": mode,
                    "final_success": final_success,
                    "best_iteration": best_iteration,
                    "iterations": [
                        {
                            "iteration": i.get("iteration", -1) + 1,  # 1-기반 인덱스로 변환
                            "success": i.get("success", False),
                            "compile_result": i.get("compile_result", False),
                            "test_result": i.get("test_result", False),
                            "hardware_success": i.get("hardware_success", False),
                            "codebleu_score": i.get("codebleu_score", None),
                            "error": i.get("error", None),
                            "hardware_evaluation": i.get("hardware_evaluation", {})
                        } for i in iterations_data
                    ]
                }
                
                # 모드별 상세 정보도 동일하게 저장
                project_summary[CODEWARE][mode][ITERATION_DETAILS][project_key] = project_summary[CODEWARE][ITERATION_DETAILS][project_key]

        if codeware_data.get(COMPILE_RESULT):
            project_summary[CODEWARE][mode][COMPILE_SUCCESS] += 1

        codebleu_score = codeware_data.get(CODEBLEU_SCORE)
        if codebleu_score is not None and isinstance(codebleu_score, (int, float)):
            project_summary[CODEWARE][mode][CODEBLEU_SCORE_SUM] += codebleu_score
            project_summary[CODEWARE][mode][CODEBLEU_SCORE_COUNT] += 1
            
            # 성공/실패 케이스 CodeBLEU 처리 추가
            is_success = codeware_data.get(RESULT, False)
            if is_success:
                project_summary[CODEWARE][mode][CODEBLEU_SCORE_SUCCESS_SUM] += codebleu_score
                project_summary[CODEWARE][mode][CODEBLEU_SCORE_SUCCESS_COUNT] += 1
            else:
                project_summary[CODEWARE][mode][CODEBLEU_SCORE_FAIL_SUM] += codebleu_score
                project_summary[CODEWARE][mode][CODEBLEU_SCORE_FAIL_COUNT] += 1

        hw_eval_data = codeware_data.get(HW_EVAL_RESULT)
        if hw_eval_data:
            target_eval_dict = project_summary[CODEWARE][mode][HW_EVAL]
            for key, value in hw_eval_data.items():
                if key in target_eval_dict:
                    if isinstance(value, (int, float)):
                        target_eval_dict[key] += value
                # 컴포넌트 속성 리스트는 별도 처리 (옵션)
                elif key == INCORRECT_ATTRS_LIST and INCORRECT_ATTRS in target_eval_dict and value:
                    # 리스트는 복사하지 않고 카운터만 사용하므로 여기서는 아무것도 하지 않음
                    pass

            # Update special physical success metrics
            if mode == PHYSICAL:
                phys_summary = project_summary[CODEWARE][PHYSICAL]
                
                # 기본 성공 메트릭 업데이트
                success_ep = hw_eval_data.get(SUCCESS_IF_NOT_ENDPOINT_CONFLICTS, 0)
                success_dc = hw_eval_data.get(SUCCESS_IF_NOT_DIRECT_CONNECTIONS, 0)
                success_both = hw_eval_data.get(SUCCESS_IF_NOT_ENDPOINT_CONFLICTS_DIRECT_CONNECTIONS, 0)
                phys_summary[SUCCESS_IF_NOT_ENDPOINT_CONFLICTS] += success_ep
                phys_summary[SUCCESS_IF_NOT_DIRECT_CONNECTIONS] += success_dc
                phys_summary[SUCCESS_IF_NOT_ENDPOINT_CONFLICTS_DIRECT_CONNECTIONS] += success_both
                
                # 컴포넌트 속성 관련 성공 메트릭 업데이트
                phys_summary[SUCCESS_IF_NOT_INCORRECT_ATTRS] += hw_eval_data.get(SUCCESS_IF_NOT_INCORRECT_ATTRS, 0)
                phys_summary[SUCCESS_IF_NOT_ENDPOINT_CONFLICTS_INCORRECT_ATTRS] += hw_eval_data.get(SUCCESS_IF_NOT_ENDPOINT_CONFLICTS_INCORRECT_ATTRS, 0)
                phys_summary[SUCCESS_IF_NOT_DIRECT_CONNECTIONS_INCORRECT_ATTRS] += hw_eval_data.get(SUCCESS_IF_NOT_DIRECT_CONNECTIONS_INCORRECT_ATTRS, 0)
                phys_summary[SUCCESS_IF_NOT_ENDPOINT_CONFLICTS_DIRECT_CONNECTIONS_INCORRECT_ATTRS] += hw_eval_data.get(SUCCESS_IF_NOT_ENDPOINT_CONFLICTS_DIRECT_CONNECTIONS_INCORRECT_ATTRS, 0)

        return True
    else:
        return False


def load_json(file_path, default=None):
    """Safely loads JSON data from a file."""
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading JSON from {file_path}: {e}", file=sys.stderr)
        return default


def save_json(data, file_path):
    """Saves data to a JSON file with indentation."""
    try:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=4)
    except IOError as e:
        print(f"Error saving JSON to {file_path}: {e}", file=sys.stderr)


def main():
    """Main function to summarize experiment results."""
    # Create summary directories if they don't exist
    SUMMARY_DIR.mkdir(exist_ok=True)
    MODEL_PROJECT_SUMMARY_DIR.mkdir(exist_ok=True)

    all_models_summary = {}
    all_projects_summary = {}
    # 모델별 프로젝트 결과를 저장할 딕셔너리 추가
    model_projects_summary = {}

    # Iterate through models
    models = [d for d in EXPERIMENTS_DIR.iterdir() if d.is_dir() and d.name != SUMMARY_DIR_NAME]
    for model_dir in models:
        model_name = model_dir.name
        model_summary = create_metrics_structure()
        model_summary['model'] = model_name # Add model name for context
        # 모델별 프로젝트 요약을 저장할 딕셔너리 초기화
        model_projects_summary[model_name] = {}

        print(f"Processing model: {model_name}...")

        # Iterate through projects for the current model
        projects = [d for d in model_dir.iterdir() if d.is_dir()]
        for project_dir in projects:
            project_name = project_dir.name
            project_summary = create_metrics_structure()
            project_summary['project'] = project_name
            project_summary['model'] = model_name # Keep model info for individual file

            # Iterate through result files for the current project
            result_files = list(project_dir.glob("*.json"))
            if not result_files:
                print(f"  No result files found for project: {project_name}")
                continue

            for result_file in result_files:
                data = load_json(result_file, default={})
                if not data: # Skip if file couldn't be loaded
                    continue

                # Inject identifiers for better error messages
                data['model'] = model_name
                data['project'] = project_name

                # Process results for each type if present
                process_code_result(data, LOGICAL, project_summary)
                process_code_result(data, PHYSICAL, project_summary)
                process_hardware_result(data, LOGICAL, project_summary)
                process_hardware_result(data, PHYSICAL, project_summary)
                process_codeware_result(data, LOGICAL, project_summary)
                process_codeware_result(data, PHYSICAL, project_summary)

            if project_summary[TOTAL] == 0: # Check if any results were processed
                 print(f"  No valid results processed for project: {project_name}. Skipping summary aggregation.")
                 continue # Skip aggregation if no results were processed

            # Aggregate project results into model summary
            aggregate_metrics(project_summary, model_summary)

            # Aggregate project results into the overall project summary
            if project_name in all_projects_summary:
                aggregate_metrics(project_summary, all_projects_summary[project_name])
            else:
                # Create a copy and remove model name for the general project summary
                all_projects_summary[project_name] = project_summary.copy()
                del all_projects_summary[project_name]['model']

            # Aggregate sum/count for CodeBLEU manually (after general aggregation)
            if project_name in all_projects_summary: # Check necessary for the first time
                for mode in [LOGICAL, PHYSICAL]:
                    # 기존 CodeBLEU 합계 및 카운트 업데이트
                    sum_key_code = CODEBLEU_SCORE_SUM
                    count_key_code = CODEBLEU_SCORE_COUNT
                    if sum_key_code in project_summary[CODE][mode]:
                       all_projects_summary[project_name][CODE][mode][sum_key_code] += project_summary[CODE][mode][sum_key_code]
                       all_projects_summary[project_name][CODE][mode][count_key_code] += project_summary[CODE][mode][count_key_code]
                    
                    # 성공/실패 CodeBLEU 합계 및 카운트 업데이트
                    success_sum_key = CODEBLEU_SCORE_SUCCESS_SUM
                    success_count_key = CODEBLEU_SCORE_SUCCESS_COUNT
                    fail_sum_key = CODEBLEU_SCORE_FAIL_SUM
                    fail_count_key = CODEBLEU_SCORE_FAIL_COUNT
                    
                    if success_sum_key in project_summary[CODE][mode]:
                        all_projects_summary[project_name][CODE][mode][success_sum_key] += project_summary[CODE][mode][success_sum_key]
                        all_projects_summary[project_name][CODE][mode][success_count_key] += project_summary[CODE][mode][success_count_key]
                    
                    if fail_sum_key in project_summary[CODE][mode]:
                        all_projects_summary[project_name][CODE][mode][fail_sum_key] += project_summary[CODE][mode][fail_sum_key]
                        all_projects_summary[project_name][CODE][mode][fail_count_key] += project_summary[CODE][mode][fail_count_key]
                    
                    # Codeware 관련 CodeBLEU 업데이트
                    sum_key_codeware = CODEBLEU_SCORE_SUM
                    count_key_codeware = CODEBLEU_SCORE_COUNT
                    if sum_key_codeware in project_summary[CODEWARE][mode]:
                       all_projects_summary[project_name][CODEWARE][mode][sum_key_codeware] += project_summary[CODEWARE][mode][sum_key_codeware]
                       all_projects_summary[project_name][CODEWARE][mode][count_key_codeware] += project_summary[CODEWARE][mode][count_key_codeware]
                    
                    # Codeware 성공/실패 CodeBLEU 합계 및 카운트 업데이트
                    if success_sum_key in project_summary[CODEWARE][mode]:
                        all_projects_summary[project_name][CODEWARE][mode][success_sum_key] += project_summary[CODEWARE][mode][success_sum_key]
                        all_projects_summary[project_name][CODEWARE][mode][success_count_key] += project_summary[CODEWARE][mode][success_count_key]
                    
                    if fail_sum_key in project_summary[CODEWARE][mode]:
                        all_projects_summary[project_name][CODEWARE][mode][fail_sum_key] += project_summary[CODEWARE][mode][fail_sum_key]
                        all_projects_summary[project_name][CODEWARE][mode][fail_count_key] += project_summary[CODEWARE][mode][fail_count_key]
            else: # First time adding this project, sums/counts are already in the copy
                 pass

            # Aggregate Hardware metrics manually for Codeware section
            if project_name in all_projects_summary:
                 for mode in [LOGICAL, PHYSICAL]:
                     if HW_EVAL in project_summary[CODEWARE][mode]:
                         source_hw_eval = project_summary[CODEWARE][mode][HW_EVAL]
                         target_hw_eval = all_projects_summary[project_name][CODEWARE][mode][HW_EVAL]
                         for key, value in source_hw_eval.items():
                              if key in target_hw_eval and isinstance(value, (int, float)):
                                  target_hw_eval[key] += value
                     # Aggregate derived success metrics (outside HW_EVAL)
                     if mode == PHYSICAL:
                         source_phys_summary = project_summary[CODEWARE][PHYSICAL]
                         target_phys_summary = all_projects_summary[project_name][CODEWARE][PHYSICAL]
                         for key in [SUCCESS_IF_NOT_ENDPOINT_CONFLICTS, SUCCESS_IF_NOT_DIRECT_CONNECTIONS, SUCCESS_IF_NOT_ENDPOINT_CONFLICTS_DIRECT_CONNECTIONS]:
                             if key in source_phys_summary:
                                 target_phys_summary[key] += source_phys_summary[key]

            # Calculate scores for the individual project summary (including CodeBLEU average)
            calculate_scores(project_summary) # Calculates general score
            for mode in [LOGICAL, PHYSICAL]: # Calculate CodeBLEU average
                count_code = project_summary[CODE][mode][CODEBLEU_SCORE_COUNT]
                if count_code > 0:
                    project_summary[CODE][mode][CODEBLEU_SCORE] = project_summary[CODE][mode][CODEBLEU_SCORE_SUM] / count_code
                
                # 성공/실패 케이스 CodeBLEU 평균 계산 추가
                success_count = project_summary[CODE][mode][CODEBLEU_SCORE_SUCCESS_COUNT]
                if success_count > 0:
                    project_summary[CODE][mode][CODEBLEU_SCORE_SUCCESS] = project_summary[CODE][mode][CODEBLEU_SCORE_SUCCESS_SUM] / success_count
                    
                fail_count = project_summary[CODE][mode][CODEBLEU_SCORE_FAIL_COUNT]
                if fail_count > 0:
                    project_summary[CODE][mode][CODEBLEU_SCORE_FAIL] = project_summary[CODE][mode][CODEBLEU_SCORE_FAIL_SUM] / fail_count

            # Calculate average HW metrics for Codeware section in individual project summary
            for mode in [LOGICAL, PHYSICAL]:
                 codeware_total_count = project_summary[CODEWARE][mode][TOTAL]
                 if codeware_total_count > 0 and HW_EVAL in project_summary[CODEWARE][mode]:
                      calculate_average_hardware_metrics(project_summary[CODEWARE][mode][HW_EVAL], codeware_total_count)
                      if mode == PHYSICAL:
                           recalculate_physical_hw_percentages(project_summary[CODEWARE][mode][HW_EVAL])

            # Calculate derived HW success scores for individual project summary
            phys_hw_summary = project_summary[HARDWARE][PHYSICAL]
            total_hw_phys = phys_hw_summary[TOTAL]
            if total_hw_phys > 0:
                phys_hw_summary[SCORE_IF_NOT_ENDPOINT_CONFLICTS] = phys_hw_summary[SUCCESS_IF_NOT_ENDPOINT_CONFLICTS] / total_hw_phys
                phys_hw_summary[SCORE_IF_NOT_DIRECT_CONNECTIONS] = phys_hw_summary[SUCCESS_IF_NOT_DIRECT_CONNECTIONS] / total_hw_phys
                phys_hw_summary[SCORE_IF_NOT_ENDPOINT_CONFLICTS_DIRECT_CONNECTIONS] = phys_hw_summary[SUCCESS_IF_NOT_ENDPOINT_CONFLICTS_DIRECT_CONNECTIONS] / total_hw_phys
                # 컴포넌트 속성 관련 성공 비율 계산
                phys_hw_summary[SCORE_IF_NOT_INCORRECT_ATTRS] = phys_hw_summary[SUCCESS_IF_NOT_INCORRECT_ATTRS] / total_hw_phys
                phys_hw_summary[SCORE_IF_NOT_ENDPOINT_CONFLICTS_INCORRECT_ATTRS] = phys_hw_summary[SUCCESS_IF_NOT_ENDPOINT_CONFLICTS_INCORRECT_ATTRS] / total_hw_phys
                phys_hw_summary[SCORE_IF_NOT_DIRECT_CONNECTIONS_INCORRECT_ATTRS] = phys_hw_summary[SUCCESS_IF_NOT_DIRECT_CONNECTIONS_INCORRECT_ATTRS] / total_hw_phys
                phys_hw_summary[SCORE_IF_NOT_ENDPOINT_CONFLICTS_DIRECT_CONNECTIONS_INCORRECT_ATTRS] = phys_hw_summary[SUCCESS_IF_NOT_ENDPOINT_CONFLICTS_DIRECT_CONNECTIONS_INCORRECT_ATTRS] / total_hw_phys
                
            phys_cw_summary = project_summary[CODEWARE][PHYSICAL]
            total_cw_phys = phys_cw_summary[TOTAL]
            if total_cw_phys > 0:
                phys_cw_summary[SCORE_IF_NOT_ENDPOINT_CONFLICTS] = phys_cw_summary[SUCCESS_IF_NOT_ENDPOINT_CONFLICTS] / total_cw_phys
                phys_cw_summary[SCORE_IF_NOT_DIRECT_CONNECTIONS] = phys_cw_summary[SUCCESS_IF_NOT_DIRECT_CONNECTIONS] / total_cw_phys
                phys_cw_summary[SCORE_IF_NOT_ENDPOINT_CONFLICTS_DIRECT_CONNECTIONS] = phys_cw_summary[SUCCESS_IF_NOT_ENDPOINT_CONFLICTS_DIRECT_CONNECTIONS] / total_cw_phys
                # 컴포넌트 속성 관련 성공 비율 계산
                phys_cw_summary[SCORE_IF_NOT_INCORRECT_ATTRS] = phys_cw_summary[SUCCESS_IF_NOT_INCORRECT_ATTRS] / total_cw_phys
                phys_cw_summary[SCORE_IF_NOT_ENDPOINT_CONFLICTS_INCORRECT_ATTRS] = phys_cw_summary[SUCCESS_IF_NOT_ENDPOINT_CONFLICTS_INCORRECT_ATTRS] / total_cw_phys
                phys_cw_summary[SCORE_IF_NOT_DIRECT_CONNECTIONS_INCORRECT_ATTRS] = phys_cw_summary[SUCCESS_IF_NOT_DIRECT_CONNECTIONS_INCORRECT_ATTRS] / total_cw_phys
                phys_cw_summary[SCORE_IF_NOT_ENDPOINT_CONFLICTS_DIRECT_CONNECTIONS_INCORRECT_ATTRS] = phys_cw_summary[SUCCESS_IF_NOT_ENDPOINT_CONFLICTS_DIRECT_CONNECTIONS_INCORRECT_ATTRS] / total_cw_phys

            # 각 프로젝트 결과를 모델별 딕셔너리에 추가
            model_projects_summary[model_name][project_name] = project_summary

        # Calculate scores for the model summary
        calculate_scores(model_summary)
        # Calculate CodeBLEU average for the model summary
        for mode in [LOGICAL, PHYSICAL]:
            count_code = model_summary[CODE][mode][CODEBLEU_SCORE_COUNT]
            if count_code > 0:
                 model_summary[CODE][mode][CODEBLEU_SCORE] = model_summary[CODE][mode][CODEBLEU_SCORE_SUM] / count_code
            
            # 성공/실패 케이스 CodeBLEU 평균 계산 추가
            success_count_code = model_summary[CODE][mode][CODEBLEU_SCORE_SUCCESS_COUNT]
            if success_count_code > 0:
                 model_summary[CODE][mode][CODEBLEU_SCORE_SUCCESS] = model_summary[CODE][mode][CODEBLEU_SCORE_SUCCESS_SUM] / success_count_code
            
            fail_count_code = model_summary[CODE][mode][CODEBLEU_SCORE_FAIL_COUNT]
            if fail_count_code > 0:
                 model_summary[CODE][mode][CODEBLEU_SCORE_FAIL] = model_summary[CODE][mode][CODEBLEU_SCORE_FAIL_SUM] / fail_count_code

            count_codeware = model_summary[CODEWARE][mode][CODEBLEU_SCORE_COUNT]
            if count_codeware > 0:
                 model_summary[CODEWARE][mode][CODEBLEU_SCORE] = model_summary[CODEWARE][mode][CODEBLEU_SCORE_SUM] / count_codeware
            
            # 성공/실패 케이스 CodeBLEU 평균 계산 추가
            success_count_codeware = model_summary[CODEWARE][mode][CODEBLEU_SCORE_SUCCESS_COUNT]
            if success_count_codeware > 0:
                 model_summary[CODEWARE][mode][CODEBLEU_SCORE_SUCCESS] = model_summary[CODEWARE][mode][CODEBLEU_SCORE_SUCCESS_SUM] / success_count_codeware
            
            fail_count_codeware = model_summary[CODEWARE][mode][CODEBLEU_SCORE_FAIL_COUNT]
            if fail_count_codeware > 0:
                 model_summary[CODEWARE][mode][CODEBLEU_SCORE_FAIL] = model_summary[CODEWARE][mode][CODEBLEU_SCORE_FAIL_SUM] / fail_count_codeware

        # Calculate average hardware metrics for the model summary
        if model_summary[HARDWARE][LOGICAL][CONVERTING_SUCCESS] > 0:
             calculate_average_hardware_metrics(
                 model_summary[HARDWARE][LOGICAL][HW_EVAL],
                 model_summary[HARDWARE][LOGICAL][CONVERTING_SUCCESS]
            )
        if model_summary[HARDWARE][PHYSICAL][CONVERTING_SUCCESS] > 0:
            calculate_average_hardware_metrics(
                model_summary[HARDWARE][PHYSICAL][HW_EVAL],
                model_summary[HARDWARE][PHYSICAL][CONVERTING_SUCCESS]
            )
            recalculate_physical_hw_percentages(model_summary[HARDWARE][PHYSICAL][HW_EVAL])

        # Codeware section HW metrics average
        for mode in [LOGICAL, PHYSICAL]:
            codeware_total_count = model_summary[CODEWARE][mode][TOTAL]
            if codeware_total_count > 0 and HW_EVAL in model_summary[CODEWARE][mode]:
                calculate_average_hardware_metrics(model_summary[CODEWARE][mode][HW_EVAL], codeware_total_count)
                if mode == PHYSICAL:
                    recalculate_physical_hw_percentages(model_summary[CODEWARE][mode][HW_EVAL])

        # Store model summary (remove model name as it's the key)
        del model_summary['model']
        all_models_summary[model_name] = model_summary

        # 모델별 프로젝트 요약 파일 저장 (모델별 하나의、파일로)
        model_summary_file = MODEL_PROJECT_SUMMARY_DIR / f"{model_name}.json"
        save_json(model_projects_summary[model_name], model_summary_file)

    # --- Final Calculations and Saving ---

    # Calculate scores for the overall project summary
    calculate_scores(all_projects_summary) # Operates recursively
    # Calculate CodeBLEU average for the overall project summary
    for project_data in all_projects_summary.values():
        for mode in [LOGICAL, PHYSICAL]:
            if CODE in project_data and mode in project_data[CODE]:
                count = project_data[CODE][mode].get(CODEBLEU_SCORE_COUNT, 0)
                if count > 0:
                    project_data[CODE][mode][CODEBLEU_SCORE] = project_data[CODE][mode].get(CODEBLEU_SCORE_SUM, 0.0) / count
            
                # 성공/실패 케이스 CodeBLEU 평균 계산 추가
                success_count = project_data[CODE][mode].get(CODEBLEU_SCORE_SUCCESS_COUNT, 0)
                if success_count > 0:
                    project_data[CODE][mode][CODEBLEU_SCORE_SUCCESS] = project_data[CODE][mode].get(CODEBLEU_SCORE_SUCCESS_SUM, 0.0) / success_count
                    
                fail_count = project_data[CODE][mode].get(CODEBLEU_SCORE_FAIL_COUNT, 0)
                if fail_count > 0:
                    project_data[CODE][mode][CODEBLEU_SCORE_FAIL] = project_data[CODE][mode].get(CODEBLEU_SCORE_FAIL_SUM, 0.0) / fail_count

            if CODEWARE in project_data and mode in project_data[CODEWARE]:
                count = project_data[CODEWARE][mode].get(CODEBLEU_SCORE_COUNT, 0)
                if count > 0:
                    project_data[CODEWARE][mode][CODEBLEU_SCORE] = project_data[CODEWARE][mode].get(CODEBLEU_SCORE_SUM, 0.0) / count
                
                # 성공/실패 케이스 CodeBLEU 평균 계산 추가
                success_count = project_data[CODEWARE][mode].get(CODEBLEU_SCORE_SUCCESS_COUNT, 0)
                if success_count > 0:
                    project_data[CODEWARE][mode][CODEBLEU_SCORE_SUCCESS] = project_data[CODEWARE][mode].get(CODEBLEU_SCORE_SUCCESS_SUM, 0.0) / success_count
                    
                fail_count = project_data[CODEWARE][mode].get(CODEBLEU_SCORE_FAIL_COUNT, 0)
                if fail_count > 0:
                    project_data[CODEWARE][mode][CODEBLEU_SCORE_FAIL] = project_data[CODEWARE][mode].get(CODEBLEU_SCORE_FAIL_SUM, 0.0) / fail_count

    # Recalculate physical hardware percentages for the overall project summary
    for project_data in all_projects_summary.values():
        if HARDWARE in project_data and PHYSICAL in project_data[HARDWARE]:
             physical_hw_eval_sum = project_data[HARDWARE][PHYSICAL].get(HW_EVAL)
             if physical_hw_eval_sum:
                 recalculate_physical_hw_percentages(physical_hw_eval_sum)
        if CODEWARE in project_data and PHYSICAL in project_data[CODEWARE]:
             physical_hw_eval_sum_cw = project_data[CODEWARE][PHYSICAL].get(HW_EVAL)
             if physical_hw_eval_sum_cw:
                 recalculate_physical_hw_percentages(physical_hw_eval_sum_cw)


    # Save final summary files
    save_json(all_projects_summary, ALL_PROJECT_SUMMARY_FILE)
    save_json(all_models_summary, ALL_MODEL_SUMMARY_FILE)

    print("Summary generation complete.")
    print(f"Overall project summary saved to: {ALL_PROJECT_SUMMARY_FILE}")
    print(f"Overall model summary saved to: {ALL_MODEL_SUMMARY_FILE}")
    print(f"Model-project summaries saved in: {MODEL_PROJECT_SUMMARY_DIR}")

if __name__ == "__main__":
    main()