import os
import time
import shutil
import game
import player
import item

# 키보드 모듈 체크
try:
    import keyboard
except ImportError:
    pass


# ==========================================
# 1. 화면 제어 및 유틸리티 함수
# ==========================================
def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')


def merge_car_on_track(track_slice, car_str, override_x=None, override_y=None):
    """ (보내주신 코드의 합성 로직 그대로 사용) """
    car_lines = car_str.split('\n')
    car_height = len(car_lines)
    car_width = len(car_lines[0]) if car_lines else 0
    track_height = len(track_slice)
    if track_height == 0: return track_slice

    if override_y is not None:
        start_y = int(override_y)
    else:
        start_y = track_height - car_height - 2

    if override_x is not None:
        start_x = int(override_x)
    else:
        reference_line = track_slice[0]
        for line in track_slice:
            if '════' in line or '====' in line:
                reference_line = line
                break
        left_wall = reference_line.find('│')
        if left_wall == -1: left_wall = reference_line.find('|')
        if left_wall == -1: left_wall = 0
        right_wall = reference_line.rfind('│')
        if right_wall == -1: right_wall = reference_line.rfind('|')
        if right_wall == -1: right_wall = len(reference_line)
        road_center = (left_wall + right_wall) // 2
        start_x = road_center - (car_width // 2)

    new_slice = []
    for i, line in enumerate(track_slice):
        if start_x >= 0 and start_y <= i < start_y + car_height:
            car_line_idx = i - start_y
            car_part = car_lines[car_line_idx]
            if start_x + len(car_part) <= len(line):
                prefix = line[:start_x]
                suffix = line[start_x + len(car_part):]
                new_slice.append(prefix + car_part + suffix)
            else:
                new_slice.append(line)
        else:
            new_slice.append(line)
    return new_slice


# ==========================================
# 2. Normal 모드 메인 로직 (보내주신 screen_two 이식)
# ==========================================
def screen_two():
    clear_screen()
    filename = "track.txt"
    if not os.path.exists(filename):
        print("오류: track.txt 파일이 없습니다.")
        time.sleep(2)
        return  # main.py로 복귀

    with open(filename, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # ✅ 아이템 및 장애물 배치
    lines, item_spots = item.add_items_to_track(lines, interval=8)
    lines, obstacle_spots = player.add_obstacles_to_track(lines, interval=5, chance=0.85)

    total_lines = len(lines)
    view_height = 20
    my_car = player.car_frame()
    gs = game.GameState()

    car_lines = my_car.split('\n')
    car_h = len(car_lines)
    car_w = len(car_lines[0]) if car_lines else 0

    # 도로 범위 계산용 변수
    last_min_x, last_max_x = 0, 0

    def get_road_bounds_from_view(view_slice, prefer_row):
        nonlocal last_min_x, last_max_x
        if not view_slice: return last_min_x, last_max_x

        rr = max(0, min(int(prefer_row), len(view_slice) - 1))
        raw = view_slice[rr]
        line = raw[:-1] if raw.endswith("\n") else raw

        left_wall = line.find('│')
        right_wall = line.rfind('│')
        if left_wall == -1 or right_wall == -1 or left_wall == right_wall:
            left_wall = line.find('|')
            right_wall = line.rfind('|')

        if left_wall == -1 or right_wall == -1 or left_wall == right_wall:
            return last_min_x, last_max_x

        min_x = left_wall + 1
        max_x = right_wall - car_w - 1
        if max_x < min_x: max_x = min_x

        last_min_x, last_max_x = min_x, max_x
        return min_x, max_x

    def bounce_x(current_x, dx, min_x, max_x):
        if current_x < min_x:
            current_x = min_x
        elif current_x > max_x:
            current_x = max_x
        if dx == 0: return current_x

        proposed = current_x + dx
        if proposed < min_x:
            proposed = min_x + (min_x - proposed)
        elif proposed > max_x:
            proposed = max_x - (proposed - max_x)

        if proposed < min_x:
            proposed = min_x
        elif proposed > max_x:
            proposed = max_x
        return int(proposed)

    # 초기 위치 설정
    current_car_y = 0
    initial_view_for_bounds = lines[0: view_height]
    car_ref_row0 = current_car_y + (car_h // 2)
    min_x0, max_x0 = get_road_bounds_from_view(initial_view_for_bounds, car_ref_row0)
    current_car_x = (min_x0 + max_x0) // 2

    # 카운트다운
    clear_screen()
    initial_view = lines[0: view_height]
    start_screen_view = merge_car_on_track(
        initial_view, my_car, override_x=current_car_x, override_y=current_car_y
    )
    for line in start_screen_view:
        print(line, end='')
    print("\n\n READY? 3초 후 출발합니다! (A/D: 이동)")
    time.sleep(3)

    start_time = time.time()

    # 아이템 및 장애물 처리 함수들 (내부 함수로 정의)
    def erase_item_from_lines(abs_line: int, x: int):
        if 0 <= abs_line < len(lines):
            raw = lines[abs_line]
            has_nl = raw.endswith("\n")
            line = raw[:-1] if has_nl else raw
            if 0 <= x < len(line):
                line_list = list(line)
                line_list[x] = ' '
                lines[abs_line] = "".join(line_list) + ("\n" if has_nl else "")

    def check_item_pickup(frame_top_i: int):
        nonlocal item_spots
        y1 = frame_top_i + current_car_y
        y2 = y1 + car_h - 1
        x1 = current_car_x
        x2 = current_car_x + car_w - 1

        for abs_line in list(item_spots.keys()):
            if y1 <= abs_line <= y2:
                ix = item_spots[abs_line]["x"]
                it = item_spots[abs_line]["item"]
                if x1 <= ix <= x2:
                    if it["effect"] == "double_score": gs.eat_item("double_score")
                    erase_item_from_lines(abs_line, ix)
                    del item_spots[abs_line]

    def check_track_obstacle_collision(frame_top_i: int):
        car_abs_y1 = frame_top_i + current_car_y
        car_abs_y2 = car_abs_y1 + car_h - 1
        car_x1 = current_car_x
        car_x2 = current_car_x + car_w - 1

        for ob in obstacle_spots:
            ob_y1, ob_y2 = ob["y"], ob["y"] + ob["h"] - 1
            ob_x1, ob_x2 = ob["x"], ob["x"] + ob["w"] - 1
            if (car_abs_y1 <= ob_y2 and car_abs_y2 >= ob_y1 and
                    car_x1 <= ob_x2 and car_x2 >= ob_x1):
                return True
        return False

    # 메인 게임 루프
    try:
        for i in range(total_lines - view_height):
            clear_screen()
            gs.update_score()

            current_view = lines[i: i + view_height]
            car_ref_row = current_car_y + (car_h // 2)
            min_x, max_x = get_road_bounds_from_view(current_view, car_ref_row)

            dx = 0
            if keyboard.is_pressed('a'): dx -= 2
            if keyboard.is_pressed('d'): dx += 2
            current_car_x = bounce_x(current_car_x, dx, min_x, max_x)

            elapsed_time = time.time() - start_time
            if elapsed_time < 15:
                delay = 0.1
            elif elapsed_time < 30:
                delay = 0.08
            else:
                delay = 0.05

            if check_track_obstacle_collision(i):
                gs.hit_obstacle()

            check_item_pickup(i)

            # 게임 오버 처리
            if gs.game_over:
                final_view = merge_car_on_track(current_view, my_car, override_x=current_car_x,
                                                override_y=current_car_y)
                for line in final_view: print(line, end='')
                print("\n" + gs.get_status_text())
                print("\nGAME OVER!")
                time.sleep(2)
                return gs.score  # 점수를 main.py로 전달

            # 화면 그리기
            final_view = merge_car_on_track(current_view, my_car, override_x=current_car_x, override_y=current_car_y)
            for line in final_view: print(line, end='')

            print("\n" + gs.get_status_text())
            print(f"[좌우 조작] X:{current_car_x} | 시간:{elapsed_time:.1f}초")
            time.sleep(delay)

        print("\n\n=== GOAL ===")
        time.sleep(3)
        return gs.score  # 완주 점수 전달

    except KeyboardInterrupt:
        print("\n게임 종료")
        return None