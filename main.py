import keyboard
import os
import time
import shutil  # 터미널 크기를 구하기 위해 추가
import sys
import player



def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')


def get_big_start_text():
    return r"""
███████╗████████╗ █████╗ ██████╗ ████████╗
██╔════╝╚══██╔══╝██╔══██╗██╔══██╗╚══██╔══╝
███████╗   ██║   ███████║██████╔╝   ██║   
╚════██║   ██║   ██╔══██║██╔══██╗   ██║   
███████║   ██║   ██║  ██║██║  ██║   ██║   
╚══════╝   ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝   ╚═╝   
    """

def get_big_end_text():
    return r"""
 ██████╗  █████╗ ███╗   ███╗███████╗    ██████╗ ██╗   ██╗███████╗██████╗ 
██╔════╝ ██╔══██╗████╗ ████║██╔════╝    ██╔═══██╗██║   ██║██╔════╝██╔══██╗
██║  ███╗███████║██╔████╔██║█████╗      ██║   ██║██║   ██║█████╗  ██████╔╝
██║   ██║██╔══██║██║╚██╔╝██║██╔══╝      ██║   ██║╚██╗ ██╔╝██╔══╝  ██╔══██╗
╚██████╔╝██║  ██║██║ ╚═╝ ██║███████╗    ╚██████╔╝ ╚████╔╝ ███████╗██║  ██║
 ╚═════╝ ╚═╝  ╚═╝╚═╝     ╚═╝╚══════╝     ╚═════╝   ╚═══╝  ╚══════╝╚═╝  ╚═╝
    """


def get_big_text(step):
    """ 3, 2, 1, GO 글자 그림을 반환하는 함수 """
    if step == 3:
        return [
            "  #######  ",
            "       #   ",
            "   #####   ",
            "       #   ",
            "  #######  "
        ]
    elif step == 2:
        return [
            "  #######  ",
            "        #  ",
            "  #######  ",
            "  #        ",
            "  #######  "
        ]
    elif step == 1:
        return [
            "     #     ",
            "    ##     ",
            "     #     ",
            "     #     ",
            "   #####   "
        ]
    elif step == "GO":
        return [
            "  #####   #######  ",
            " #     #  #     #  ",
            " #        #     #  ",
            " #  ####  #     #  ",
            " #     #  #     #  ",
            "  #####   #######  "
        ]
    return []


def overlay_text_on_screen(background_lines, text_art):
    """ 배경 화면(리스트) 위에 글자 그림(리스트)을 중앙에 덮어씌우는 함수 """
    # 배경 복사 (원본 훼손 방지)
    canvas = background_lines[:]

    bg_h = len(canvas)
    bg_w = len(canvas[0]) if bg_h > 0 else 0
    text_h = len(text_art)
    text_w = len(text_art[0]) if text_h > 0 else 0

    # 화면 중앙 좌표 계산
    start_y = (bg_h - text_h) // 2
    start_x = (bg_w - text_w) // 2

    # 합성 시작
    for i in range(text_h):
        y = start_y + i
        if 0 <= y < bg_h:
            # 파이썬 문자열은 수정 불가하므로 잘라서 붙이기
            line = canvas[y].rstrip()  # 오른쪽 공백 제거
            # 배경이 짧으면 공백으로 채움
            if len(line) < start_x:
                line += " " * (start_x - len(line))

            # [배경앞부분] + [글자] + [배경뒷부분]
            prefix = line[:start_x]
            # 글자가 배경보다 길어질 수 있으니 처리
            suffix_start = start_x + text_w
            suffix = line[suffix_start:] if len(line) > suffix_start else ""

            canvas[y] = prefix + text_art[i] + suffix

    return canvas



def print_centered(text):
    # 터미널 크기 구하기
    columns, lines = shutil.get_terminal_size()

    # 텍스트를 줄 단위로 분리
    text_lines = text.strip().split('\n')
    text_height = len(text_lines)

    # 수직(세로) 중앙 정렬을 위한 빈 줄 계산
    vertical_padding = (lines - text_height) // 2

    # 위쪽 빈 줄 출력
    print('\n' * vertical_padding)

    # 텍스트 수평(가로) 중앙 정렬 후 출력
    for line in text_lines:
        print(line.center(columns))


def screen_one():
    clear_screen()

    # 큰 글씨 가져오기
    big_text = get_big_start_text()

    # 가운데 정렬해서 출력
    print_centered(big_text)

    # 안내 문구도 가운데 정렬
    columns, _ = shutil.get_terminal_size()
    print("\n" + "잠시 후 게임이 시작됩니다...".center(columns))

    time.sleep(2)
    screen_two()

def screen_two():
    clear_screen()
    filename = "track.txt"
    if not os.path.exists(filename): return

    with open(filename, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    total_lines = len(lines)
    view_height = 20
    my_car = player.car_frame()

    # --- [위치 고정 설정] ---

    # 1. Y좌표: 무조건 0 (화면 최상단 가장자리 고정)
    current_car_y = 0

    # 2. X좌표: 초기 위치 (중간쯤)
    # track.txt의 도로 위치에 맞춰서 숫자를 조절하세요 (예: 25)
    current_car_x = 25

    # ==========================================
    # [변경된 부분] 1. 출발 전 정지 화면 보여주기
    # ==========================================
    clear_screen()

    # 트랙의 맨 처음 부분 가져오기
    initial_view = lines[0: view_height]

    # 자동차 합성 (현재 위치에)
    start_screen_view = merge_car_on_track(
        initial_view,
        my_car,
        override_x=current_car_x,
        override_y=current_car_y
    )

    # 화면 출력
    for line in start_screen_view:
        print(line, end='')

    print("\n\n READY? 3초 후 출발합니다! (A/D: 이동)")

    # 트랙과 자동차가 보이는 상태로 3초 대기
    time.sleep(3)

    # ==========================================
    # 2. 레이싱 시작 (시간 측정 시작)
    # ==========================================
    start_time = time.time()  # 대기가 끝난 후부터 시간을 재야 함

    try:
        for i in range(total_lines - view_height):
            clear_screen()

            # --- [키보드 입력] ---
            if keyboard.is_pressed('a'):
                current_car_x -= 2
            if keyboard.is_pressed('d'):
                current_car_x += 2

            # --- [화면 밖 이탈 방지] ---
            current_car_x = max(0, current_car_x)

            # --- [속도 계산] ---
            elapsed_time = time.time() - start_time
            if elapsed_time < 15:
                delay = 0.1
            elif elapsed_time < 30:
                delay = 0.08
            else:
                delay = 0.05

            # --- [화면 그리기] ---
            current_view = lines[i: i + view_height]

            final_view = merge_car_on_track(
                current_view,
                my_car,
                override_x=current_car_x,
                override_y=current_car_y
            )

            for line in final_view:
                print(line, end='')

            print(f"\n[좌우 조작] X:{current_car_x} | 시간:{elapsed_time:.1f}초")
            time.sleep(delay)

        print("\n\n=== GOAL ===")
        time.sleep(3)
        screen_three()

    except KeyboardInterrupt:
        print("\n게임 종료")


    # 게임이 끝나면 화면 3으로 이동
    screen_three()




def merge_car_on_track(track_slice, car_str, override_x=None, override_y=None):
    """
    override_x: 자동차 가로 위치 (없으면 자동 중앙)
    override_y: 자동차 세로 위치 (없으면 바닥)
    """
    car_lines = car_str.split('\n')
    car_height = len(car_lines)
    car_width = len(car_lines[0]) if car_lines else 0
    track_height = len(track_slice)
    if track_height == 0: return track_slice

    # 1. 세로 위치 결정
    if override_y is not None:
        start_y = int(override_y)
    else:
        start_y = track_height - car_height - 2

    # 2. 가로 위치 결정
    if override_x is not None:
        # [수동 모드] 사용자가 키보드로 움직인 위치 사용
        start_x = int(override_x)
    else:
        # [자동 모드] START 박스나 도로 중앙 찾기 (초기 위치 잡기용)
        # (기존 로직과 동일하게 중앙을 찾습니다)
        reference_line = track_slice[0]
        for line in track_slice:
            if '════' in line or '====' in line:
                reference_line = line
                break

        # 도로 중앙 계산
        left_wall = reference_line.find('│')
        if left_wall == -1: left_wall = reference_line.find('|')
        if left_wall == -1: left_wall = 0

        right_wall = reference_line.rfind('│')
        if right_wall == -1: right_wall = reference_line.rfind('|')
        if right_wall == -1: right_wall = len(reference_line)

        road_center = (left_wall + right_wall) // 2
        start_x = road_center - (car_width // 2)

    # 3. 합성 (그리기)
    new_slice = []
    for i, line in enumerate(track_slice):
        if start_x >= 0 and start_y <= i < start_y + car_height:
            car_line_idx = i - start_y
            car_part = car_lines[car_line_idx]

            # 화면 밖으로 나가지 않게 안전장치
            if start_x + len(car_part) <= len(line):
                prefix = line[:start_x]
                suffix = line[start_x + len(car_part):]
                new_line = prefix + car_part + suffix
                new_slice.append(new_line)
            else:
                new_slice.append(line)
        else:
            new_slice.append(line)

    return new_slice



def screen_three():
    clear_screen()

    # 1. 큰 글씨(GAME OVER) 출력
    big_text = get_big_end_text()
    print_centered(big_text)

    # 2. 계속하기 질문 가운데 정렬 출력
    columns, _ = shutil.get_terminal_size()
    question = "게임을 계속하시겠습니까? (Y/N)"
    print("\n" + question.center(columns))
    print()  # 줄바꿈

    # 3. Y/N 입력 받기 (반복문으로 올바른 키 입력 유도)
    while True:
        # 입력 프롬프트도 약간 들여쓰기 하거나 그냥 두어도 됩니다.
        choice = input("선택 > ".center(columns // 2)).strip().upper()

        if choice == 'Y':
            print()
            print("게임을 다시 시작합니다!".center(columns))
            time.sleep(1)  # 잠시 대기 후 전환
            screen_two()  # 화면 2로 이동 (재시작)
            return  # 현재 함수 종료

        elif choice == 'N':
            print()
            print("게임을 종료합니다. 이용해 주셔서 감사합니다.".center(columns))
            sys.exit()  # 프로그램 완전 종료

        else:
            print("잘못된 입력입니다. Y 또는 N을 입력해주세요.".center(columns))



if __name__ == "__main__":
    screen_one()