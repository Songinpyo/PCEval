import os
import json
import re

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

def count_parts_connections(json_file_path):
    """JSON 파일에서 부품 수와 연결 수를 계산"""
    try:
        with open(json_file_path, 'r') as file:
            data = json.load(file)
            parts_count = len(data.get('parts', []))
            connections_count = len(data.get('connections', []))
            return parts_count, connections_count
    except (FileNotFoundError, json.JSONDecodeError):
        return 0, 0

def calculate_cyclomatic_complexity(ino_file_path):
    """
    INO 파일의 사이클로매틱 복잡도 계산
    공식: M = E - N + 2P
    여기서,
    - E: 엣지(Edge) 수
    - N: 노드(Node) 수
    - P: 연결 컴포넌트(Connected Components) 수
    
    제어 흐름 그래프에서:
    - 노드: 코드 블록
    - 엣지: 코드 블록 간의 흐름
    - 연결 컴포넌트: 함수 수
    
    control flow graph를 구현하기 복잡하므로, 간단한 근사치 계산:
    - 노드 = 기본 블록 수 = 조건문 수 + 1
    - 엣지 = 노드 간 연결 = 조건문 수 * 2 (각 조건은 참과 거짓 2개의 경로 생성)
    - 연결 컴포넌트 = 함수 수(setup, loop, 사용자 정의 함수)
    
    따라서, M = (조건문 수 * 2) - (조건문 수 + 1) + 2 * 함수 수
    = 조건문 수 - 1 + 2 * 함수 수
    """
    try:
        with open(ino_file_path, 'r') as file:
            content = file.read()
            
            # 주석 제거
            content = re.sub(r'/\*[\s\S]*?\*/', '', content)  # 블록 주석 제거
            content = re.sub(r'//.*', '', content)  # 한 줄 주석 제거
            
            # 조건문 및 분기문 패턴
            branch_patterns = [
                r'\bif\s*\(', 
                r'\belse\s+if\s*\(', 
                r'\bfor\s*\(', 
                r'\bwhile\s*\(',
                r'\bswitch\s*\(',
                r'\bcase\s+.*:',
                r'\|\|',  # OR 연산자 (분기 생성)
                r'&&'     # AND 연산자 (분기 생성)
            ]
            
            # 함수 정의 패턴
            function_pattern = r'\b\w+\s+\w+\s*\([^)]*\)\s*{'
            
            # 각 패턴에 대해 매칭 개수 계산
            branch_count = 0
            for pattern in branch_patterns:
                branch_count += len(re.findall(pattern, content))
            
            # 함수 수 계산 - arduino에서는 최소 setup과 loop가 있음
            function_count = len(re.findall(function_pattern, content))
            if function_count < 2:  # 최소 setup과 loop 함수는 있어야 함
                function_count = 2
            
            # 사이클로매틱 복잡도 계산: M = E - N + 2P
            # E = branch_count * 2 (각 분기는 2개의 엣지 생성)
            # N = branch_count + 1 (분기 + 1개의 시작 노드)
            # P = function_count
            
            edges = branch_count * 2
            nodes = branch_count + 1
            components = function_count
            
            cc = edges - nodes + 2 * components
            return cc
    except FileNotFoundError:
        return 0

def count_code_lines(ino_file_path):
    """INO 파일에서 주석과 빈 줄을 제외한 코드 줄 수를 계산"""
    try:
        with open(ino_file_path, 'r') as file:
            lines = file.readlines()
            code_lines = 0
            in_comment_block = False
            
            for line in lines:
                # 공백 제거
                stripped_line = line.strip()
                
                # 빈 줄 무시
                if not stripped_line:
                    continue
                    
                # 블록 주석 처리
                if stripped_line.startswith('/*') or stripped_line.startswith('/**'):
                    in_comment_block = True
                    if '*/' in stripped_line:
                        in_comment_block = False
                    continue
                    
                if in_comment_block:
                    if '*/' in stripped_line:
                        in_comment_block = False
                    continue
                    
                # 한 줄 주석 처리
                if stripped_line.startswith('//'):
                    continue
                    
                # 중괄호만 있는 줄 무시
                if stripped_line in ['{', '}']:
                    continue
                    
                code_lines += 1
                
            return code_lines
    except FileNotFoundError:
        return 0

def analyze_projects():
    """모든 프로젝트를 분석하고 통계를 계산"""
    project_stats = {}
    level_stats = {"level1": {}, "level2": {}, "level3": {}, "level4": {}}
    total_stats = {
        "projects_count": 0,
        "diagram_parts_avg": 0,
        "diagram_connections_avg": 0,
        "breadboard_parts_avg": 0,
        "breadboard_connections_avg": 0,
        "code_lines_avg": 0,
        "cyclomatic_complexity_avg": 0,
        "total_diagram_parts": 0,
        "total_diagram_connections": 0,
        "total_breadboard_parts": 0,
        "total_breadboard_connections": 0,
        "total_code_lines": 0,
        "total_cyclomatic_complexity": 0
    }
    
    # 레벨별 초기화
    for level in level_stats:
        level_stats[level] = {
            "projects_count": 0,
            "diagram_parts_avg": 0,
            "diagram_connections_avg": 0,
            "breadboard_parts_avg": 0,
            "breadboard_connections_avg": 0,
            "code_lines_avg": 0,
            "cyclomatic_complexity_avg": 0,
            "total_diagram_parts": 0,
            "total_diagram_connections": 0,
            "total_breadboard_parts": 0,
            "total_breadboard_connections": 0,
            "total_code_lines": 0,
            "total_cyclomatic_complexity": 0
        }
    
    # 각 프로젝트 분석
    for project_path in PROJECTS:
        level = project_path.split('/')[0]
        project_name = project_path.split('/')[1]
        base_path = os.path.join("projects", project_path)
        
        # 파일 경로
        diagram_path = os.path.join(base_path, "diagram.json")
        breadboard_path = os.path.join(base_path, "diagram_breadboard.json")
        ino_path = os.path.join(base_path, "src", "main.ino")
        
        # 각 파일 분석
        diagram_parts, diagram_connections = count_parts_connections(diagram_path)
        breadboard_parts, breadboard_connections = count_parts_connections(breadboard_path)
        code_lines = count_code_lines(ino_path)
        cyclomatic_complexity = calculate_cyclomatic_complexity(ino_path)
        
        # 프로젝트 통계 저장
        project_stats[project_path] = {
            "diagram_parts": diagram_parts,
            "diagram_connections": diagram_connections,
            "breadboard_parts": breadboard_parts,
            "breadboard_connections": breadboard_connections,
            "code_lines": code_lines,
            "cyclomatic_complexity": cyclomatic_complexity
        }
        
        # 레벨별 통계 누적
        level_stats[level]["projects_count"] += 1
        level_stats[level]["total_diagram_parts"] += diagram_parts
        level_stats[level]["total_diagram_connections"] += diagram_connections
        level_stats[level]["total_breadboard_parts"] += breadboard_parts
        level_stats[level]["total_breadboard_connections"] += breadboard_connections
        level_stats[level]["total_code_lines"] += code_lines
        level_stats[level]["total_cyclomatic_complexity"] += cyclomatic_complexity
        
        # 전체 통계 누적
        total_stats["projects_count"] += 1
        total_stats["total_diagram_parts"] += diagram_parts
        total_stats["total_diagram_connections"] += diagram_connections
        total_stats["total_breadboard_parts"] += breadboard_parts
        total_stats["total_breadboard_connections"] += breadboard_connections
        total_stats["total_code_lines"] += code_lines
        total_stats["total_cyclomatic_complexity"] += cyclomatic_complexity
    
    # 레벨별 평균 계산
    for level, stats in level_stats.items():
        if stats["projects_count"] > 0:
            stats["diagram_parts_avg"] = stats["total_diagram_parts"] / stats["projects_count"]
            stats["diagram_connections_avg"] = stats["total_diagram_connections"] / stats["projects_count"]
            stats["breadboard_parts_avg"] = stats["total_breadboard_parts"] / stats["projects_count"]
            stats["breadboard_connections_avg"] = stats["total_breadboard_connections"] / stats["projects_count"]
            stats["code_lines_avg"] = stats["total_code_lines"] / stats["projects_count"]
            stats["cyclomatic_complexity_avg"] = stats["total_cyclomatic_complexity"] / stats["projects_count"]
    
    # 전체 평균 계산
    if total_stats["projects_count"] > 0:
        total_stats["diagram_parts_avg"] = total_stats["total_diagram_parts"] / total_stats["projects_count"]
        total_stats["diagram_connections_avg"] = total_stats["total_diagram_connections"] / total_stats["projects_count"]
        total_stats["breadboard_parts_avg"] = total_stats["total_breadboard_parts"] / total_stats["projects_count"]
        total_stats["breadboard_connections_avg"] = total_stats["total_breadboard_connections"] / total_stats["projects_count"]
        total_stats["code_lines_avg"] = total_stats["total_code_lines"] / total_stats["projects_count"]
        total_stats["cyclomatic_complexity_avg"] = total_stats["total_cyclomatic_complexity"] / total_stats["projects_count"]
    
    # 결과 JSON 생성
    result = {
        "total_stats": total_stats,
        "level_stats": level_stats,
        "project_stats": project_stats
    }
    
    # JSON 저장
    with open('arduino_project_stats.json', 'w') as f:
        json.dump(result, f, indent=4)
    
    print("분석 완료. 결과가 arduino_project_stats.json 파일에 저장되었습니다.")

if __name__ == "__main__":
    analyze_projects()