import os
import sys
import time
import shutil
import random  # 랜덤 기능을 위해 추가
import player  # 플레이어 모양 가져오기

# 윈도우/리눅스 키보드 처리
try:
    import keyboard
    USE_KEYBOARD = True
except ImportError:
    import msvcrt
    USE_KEYBOARD = False

# -------------------------------
# 기본 유틸 (Hard Mode 전용)
# -------------------------------
def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")

def enable_ansi_on_windows():
    if os.name != "nt":
        return True
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        handle = kernel32.GetStdHandle(-11)
        mode = ctypes.c_uint32()
        if kernel32.GetConsoleMode(handle, ctypes.byref(mode)) == 0:
            return False
        if kernel32.SetConsoleMode(handle, mode.value | 0x0004) == 0:
            return False
        return True
    except Exception:
        return False

ANSI_OK = enable_ansi_on_windows()

def move_cursor_home():
    if ANSI_OK:
        sys.stdout.write("\x1b[H")
        sys.stdout.flush()
    else:
        clear_screen()

def to_grid(view_lines):
    stripped = [ln.rstrip("\n") for ln in view_lines]
    w = max((len(s) for s in stripped), default=0)
    return [list(s.ljust(w)) for s in stripped]

def draw_sprite_on_grid(grid, x, y, sprite_lines):
    for dy, line in enumerate(sprite_lines):
        gy = y + dy
        if 0 <= gy < len(grid):
            for dx, ch in enumerate(line):
                gx = x + dx
                if 0 <= gx < len(grid[gy]) and ch != " ":
                    grid[gy][gx] = ch

def rotate_sprite_180(sprite_str):
    lines = sprite_str.split("\n")
    lines = [ln[::-1] for ln in lines[::-1]]
    return "\n".join(lines)

def find_start_index(lines):
    for idx, line in enumerate(lines):
        if "START" in line:
            return idx
    return 0

def find_goal_abs_y(lines):
    for idx, line in enumerate(lines):
        if "GOAL" in line:
            return idx
    for idx in range(len(lines) - 1, -1, -1):
        if "════" in lines[idx] or "====" in lines[idx]:
            return idx
    return len(lines) - 1

def find_start_line_screen_y(view_lines):
    for y, ln in enumerate(view_lines):
        s = ln.rstrip("\n")
        if ("════" in s) or ("====" in s):
            return y
    return 3

def get_key_state():
    if USE_KEYBOARD:
        left = keyboard.is_pressed("a") or keyboard.is_pressed("left")
        right = keyboard.is_pressed("d") or keyboard.is_pressed("right")
        esc = keyboard.is_pressed("esc")
        return left, right, esc

    left = right = esc = False
    while msvcrt.kbhit():
        ch = msvcrt.getch()
        if ch == b"\x1b":
            esc = True
        elif ch in (b"\x00", b"\xe0"):
            ch2 = msvcrt.getch()
            if ch2 == b"K":
                left = True
            elif ch2 == b"M":
                right = True
    return left, right, esc

# -------------------------------
# 도로/벽 찾기 + 안전한 범위 계산
# -------------------------------
def _find_walls_in_row(row_chars):
    s = "".join(row_chars)
    left = s.find("│")
    if left == -1:
        left = s.find("|")
    right = s.rfind("│")
    if right == -1:
        right = s.rfind("|")
    if left != -1 and right != -1 and right > left:
        return left, right
    return None

def get_road_bounds_safe(view_lines, car_y, car_w, car_h, last_bounds=None):
    grid = to_grid(view_lines)
    H = len(grid)
    W = len(grid[0]) if H > 0 else 0

    lefts = []
    rights = []
    for yy in range(car_y, car_y + car_h):
        if 0 <= yy < H:
            walls = _find_walls_in_row(grid[yy])
            if walls:
                l, r = walls
                lefts.append(l)
                rights.append(r)

    if lefts and rights:
        safe_left = max(lefts) + 1
        safe_right = min(rights) - 1

        min_x = safe_left
        max_x = safe_right - car_w + 1
        if max_x < min_x:
            mid = W // 2
            min_x = max(0, mid - car_w // 2)
            max_x = min_x
        return (min_x, max_x)

    if last_bounds is not None:
        return last_bounds

    return (0, max(0, W - car_w))

# -------------------------------
# 큰 카운트다운 (3,2,1,START)
# -------------------------------
def countdown_on_map(lines, view_height, scroll_i, car_sprite_lines, car_x, car_y):
    BIG = {
        "3": [
            " ██████╗ ",
            " ╚════██╗",
            "  █████╔╝",
            "  ╚═══██╗",
            " ██████╔╝",
            " ╚═════╝ ",
        ],
        "2": [
            " ██████╗ ",
            " ╚════██╗",
            "  █████╔╝",
            " ██╔═══╝ ",
            " ███████╗",
            " ╚══════╝",
        ],
        "1": [
            "  ██╗",
            " ███║",
            " ╚██║",
            "  ██║",
            "  ██║",
            "  ╚═╝",
        ],
        "START": [
            "███████╗████████╗ █████╗ ██████╗ ████████╗",
            "██╔════╝╚══██╔══╝██╔══██╗██╔══██╗╚══██╔══╝",
            "███████╗   ██║   ███████║██████╔╝   ██║   ",
            "╚════██║   ██║   ██╔══██║██╔══██╗   ██║   ",
            "███████║   ██║   ██║  ██║██║  ██║   ██║   ",
            "╚══════╝   ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝   ╚═╝   ",
        ],
    }

    steps = [("3", 0.7), ("2", 0.7), ("1", 0.7), ("START", 0.9)]

    for key, sec in steps:
        clear_screen()
        view = lines[scroll_i: scroll_i + view_height]
        grid = to_grid(view)

        draw_sprite_on_grid(grid, car_x, car_y, car_sprite_lines)

        H = len(grid)
        W = len(grid[0]) if H > 0 else 0

        art = BIG[key]
        art_h = len(art)
        art_w = max(len(s) for s in art)

        ty = max(0, (H // 2) - (art_h // 2))
        tx = max(0, (W // 2) - (art_w // 2))

        for dy, line in enumerate(art):
            gy = ty + dy
            if 0 <= gy < H:
                for dx, ch in enumerate(line):
                    gx = tx + dx
                    if 0 <= gx < W and ch != " ":
                        grid[gy][gx] = ch

        frame = "".join("".join(row) + "\n" for row in grid)
        frame += "\nA/D 또는 ←/→ 이동 준비… (카운트다운 끝나면 출발)\n"
        sys.stdout.write(frame)
        sys.stdout.flush()
        time.sleep(sec)

# -------------------------------
# 점수/최고점수 저장 (점수제 버전)
# -------------------------------
HIGHSCORE_FILE = "highscore_points.txt"

def load_highscore():
    try:
        if os.path.exists(HIGHSCORE_FILE):
            with open(HIGHSCORE_FILE, "r", encoding="utf-8") as f:
                v = f.read().strip()
                return int(v) if v else 0
    except Exception:
        pass
    return 0

def save_highscore(score):
    try:
        with open(HIGHSCORE_FILE, "w", encoding="utf-8") as f:
            f.write(str(int(score)))
    except Exception:
        pass

# -------------------------------
# 아이템 (별/동그라미/세모)
# -------------------------------
ITEMS = [
    {"name": "STAR", "ch": "★", "score": 5},
    {"name": "CIRCLE", "ch": "●", "score": 3},
    {"name": "TRI", "ch": "▲", "score": -2},
]

def choose_item_spawn(current_view, view_height):
    grid = to_grid(current_view)
    H = len(grid)
    W = len(grid[0]) if H > 0 else 0
    if H == 0 or W == 0:
        return None

    candidates = []
    y_start = 2
    y_end = max(2, min(view_height - 3, H - 2))

    for y in range(y_start, y_end + 1):
        walls = _find_walls_in_row(grid[y])
        if not walls:
            continue
        l, r = walls
        road_left = l + 1
        road_right = r - 1
        if road_right - road_left >= 4:
            candidates.append((y, road_left, road_right))

    if not candidates:
        return None

    y, road_left, road_right = random.choice(candidates)
    x = random.randint(road_left, road_right)
    return y, x

def make_car_cells(car_sprite_lines, car_x, car_y):
    cells = set()
    for dy, line in enumerate(car_sprite_lines):
        for dx, ch in enumerate(line):
            if ch != " ":
                cells.add((car_x + dx, car_y + dy))
    return cells

# -------------------------------
# 오른쪽 점수판(사이드바) 렌더
# -------------------------------
def render_with_sidebar(grid, sidebar_lines):
    H = len(grid)
    out = []
    for i in range(H):
        row = "".join(grid[i])
        side = sidebar_lines[i] if i < len(sidebar_lines) else ""
        out.append(row + "  " + side)
    return "\n".join(out) + "\n"

# -------------------------------
# 메인 게임 (하드모드 실행 함수)
# -------------------------------
def screen_two_hard():
    clear_screen()
    filename = "track_hard.txt"
    if not os.path.exists(filename):
        print("오류: track.txt 파일이 없습니다.")
        time.sleep(1.2)
        return

    with open(filename, "r", encoding="utf-8") as f:
        lines = f.readlines()

    total_lines = len(lines)
    view_height = 28

    start_index = find_start_index(lines)
    goal_abs_y = find_goal_abs_y(lines)

    base_car = player.car_frame()
    car_str = rotate_sprite_180(base_car)
    car_sprite_lines = car_str.split("\n")
    car_h = len(car_sprite_lines)
    car_w = max((len(l) for l in car_sprite_lines), default=0)

    # 미사일
    MISSILE_SHAPE = "=====>"
    missile_len = len(MISSILE_SHAPE)
    missiles = []
    missile_interval = 1.2
    missile_speed = 2
    last_missile_spawn = time.time() - 999

    # 아이템
    items = []
    item_interval = 0.9
    last_item_spawn = time.time() - 999

    # 하이스코어
    highscore = load_highscore()

    def init_start_state():
        scroll_i = max(0, start_index - 5)
        v = lines[scroll_i: scroll_i + view_height]
        sy = find_start_line_screen_y(v)
        car_y = max(0, sy - car_h)

        last_bounds = get_road_bounds_safe(v, car_y, car_w, car_h, last_bounds=None)
        car_x = (last_bounds[0] + last_bounds[1]) // 2
        return scroll_i, car_x, car_y, last_bounds

    def hard_reset(reason, score_now):
        """
        벽/충돌 실패 시 즉시 초기화 + 문구 출력 + 카운트다운
        """
        nonlocal scroll_i, car_x, car_y, last_bounds
        nonlocal missiles, items
        nonlocal start_time, points, last_sec
        nonlocal last_missile_spawn, last_item_spawn, last_move_time

        move_cursor_home()
        msg = f"\n💥 {reason}!  (이번 점수: {score_now}) | 최고기록: {highscore}\n"
        msg += "=> START로 즉시 초기화합니다!!!\n"
        sys.stdout.write(msg)
        sys.stdout.flush()
        time.sleep(20)

        # 초기화
        missiles.clear()
        items.clear()
        scroll_i, car_x, car_y, last_bounds = init_start_state()
        last_missile_spawn = time.time() - 999
        last_item_spawn = time.time() - 999
        last_move_time = time.time()

        start_time = time.time()
        points = 0
        last_sec = 0

        countdown_on_map(lines, view_height, scroll_i, car_sprite_lines, car_x, car_y)
        clear_screen()

    # -------- 게임 시작 로직 --------
    scroll_i, car_x, car_y, last_bounds = init_start_state()
    start_time = time.time()
    points = 0
    last_sec = 0
    last_move_time = time.time()

    countdown_on_map(lines, view_height, scroll_i, car_sprite_lines, car_x, car_y)
    clear_screen()

    while True:
        try:
            while scroll_i < total_lines:
                now = time.time()
                current_view = lines[scroll_i: scroll_i + view_height]
                if not current_view:
                    break

                grid = to_grid(current_view)
                H = len(grid)
                W = len(grid[0]) if H > 0 else 0

                # 1) 점수 누적
                elapsed = now - start_time
                sec = int(elapsed)
                if sec > last_sec:
                    points += (sec - last_sec)
                    last_sec = sec

                if points > highscore:
                    highscore = points
                    save_highscore(highscore)

                # 2) 속도 설정
                if elapsed < 15:
                    delay = 0.09
                    speed_status = "보통"
                elif elapsed < 30:
                    delay = 0.07
                    speed_status = "빠름"
                else:
                    delay = 0.055
                    speed_status = "매우 빠름"

                MOVE_COOLDOWN = delay

                # 3) 입력 처리
                left, right, esc = get_key_state()
                if esc:
                    raise KeyboardInterrupt

                last_bounds = get_road_bounds_safe(current_view, car_y, car_w, car_h, last_bounds=last_bounds)
                mn, mx = last_bounds

                attempted_left = False
                attempted_right = False

                if now - last_move_time >= MOVE_COOLDOWN:
                    if left and not right:
                        attempted_left = True
                        car_x -= 1
                        last_move_time = now
                    elif right and not left:
                        attempted_right = True
                        car_x += 1
                        last_move_time = now

                # ✅ 하드모드 벽 충돌 체크
                if attempted_left and car_x < mn:
                    hard_reset("벽에 부딪혔습니다", points)
                    continue
                if attempted_right and car_x > mx:
                    hard_reset("벽에 부딪혔습니다", points)
                    continue

                if car_x < mn: car_x = mn
                elif car_x > mx: car_x = mx

                # 4) 미사일 생성
                if now - last_missile_spawn >= missile_interval and W > 0 and H > 0:
                    pick = None
                    candidates = []
                    y_start = 2
                    y_end = max(2, min(view_height - 3, H - 2))
                    for y in range(y_start, y_end + 1):
                        walls = _find_walls_in_row(grid[y])
                        if not walls: continue
                        l, r = walls
                        road_left, road_right = l + 1, r - 1
                        if road_right - road_left + 1 >= missile_len + 1:
                            spawn_x = max(road_left, road_right - missile_len)
                            candidates.append((y, spawn_x))
                    if candidates: pick = random.choice(candidates)

                    if pick:
                        screen_y, spawn_x = pick
                        abs_y = scroll_i + screen_y
                        missiles.append({"x": spawn_x, "abs_y": abs_y})
                        last_missile_spawn = now

                # 5) 아이템 생성
                if now - last_item_spawn >= item_interval and W > 0 and H > 0:
                    sp = choose_item_spawn(current_view, view_height)
                    if sp:
                        screen_y, x = sp
                        abs_y = scroll_i + screen_y
                        item = random.choice(ITEMS)
                        items.append({"x": x, "abs_y": abs_y, "ch": item["ch"], "score": item["score"]})
                        last_item_spawn = now

                # 6) 좌표 및 판정
                car_cells = make_car_cells(car_sprite_lines, car_x, car_y)

                # 아이템 판정
                alive_items = []
                for it in items:
                    screen_y = it["abs_y"] - scroll_i
                    if 0 <= screen_y < H:
                        if 0 <= it["x"] < W: grid[screen_y][it["x"]] = it["ch"]
                        if (it["x"], screen_y) in car_cells:
                            points += it["score"]
                            if points < 0: points = 0
                            continue
                        else:
                            alive_items.append(it)
                    else:
                        alive_items.append(it)
                items = alive_items

                if points > highscore:
                    highscore = points
                    save_highscore(highscore)

                # 미사일 판정
                alive_missiles = []
                hit_by_missile = False
                for m in missiles:
                    m["x"] -= missile_speed
                    screen_y = m["abs_y"] - scroll_i
                    if 0 <= screen_y < H:
                        x0 = m["x"]
                        missile_cells = set()
                        for k, ch in enumerate(MISSILE_SHAPE):
                            xx = x0 + k
                            if 0 <= xx < W and ch != " ": missile_cells.add((xx, screen_y))
                        if car_cells & missile_cells: hit_by_missile = True
                        for k, ch in enumerate(MISSILE_SHAPE):
                            xx = x0 + k
                            if 0 <= xx < W: grid[screen_y][xx] = ch
                    if m["x"] > -missile_len: alive_missiles.append(m)
                missiles = alive_missiles

                if hit_by_missile:
                    hard_reset("미사일에 맞았습니다", points)
                    continue

                # 그리기 및 골 판정
                draw_sprite_on_grid(grid, car_x, car_y, car_sprite_lines)

                car_abs_bottom = scroll_i + car_y + car_h - 1
                if car_abs_bottom >= goal_abs_y:
                    move_cursor_home()
                    sidebar = [
                        "┌──────── SCORE ────────┐",
                        f"│ Points : {points:<10}│",
                        f"│ Best   : {highscore:<10}│",
                        f"│ Time   : {sec:<10}│",
                        f"│ Speed  : {speed_status:<10}│",
                        "└───────────────────────┘",
                        "",
                        "=== GOAL 통과! ===",
                    ]
                    frame = render_with_sidebar(grid, sidebar)
                    frame += f"\n\n=== GOAL 선을 통과했습니다! ===\n이번 점수: {points} | 최고기록: {highscore}\n"
                    sys.stdout.write(frame)
                    sys.stdout.flush()
                    time.sleep(1.6)
                    return  # 메인으로 복귀

                # 출력
                sidebar = [
                    "┌──────── SCORE ────────┐",
                    f"│ Points : {points:<10}│",
                    f"│ Best   : {highscore:<10}│",
                    f"│ Time   : {sec:<10}│",
                    f"│ Speed  : {speed_status:<10}│",
                    "└───────────────────────┘",
                    "",
                    "Items:",
                    "  ★ = +5",
                    "  ● = +3",
                    "  ▲ = -2",
                    "",
                    "Hard Mode:",
                    "  벽 닿으면 즉시 초기화!",
                    "",
                    "Controls:",
                    "  A/D 또는 ←/→",
                    "  ESC 종료",
                ]
                move_cursor_home()
                frame = render_with_sidebar(grid, sidebar)
                sys.stdout.write(frame)
                sys.stdout.flush()

                time.sleep(delay)
                scroll_i += 1

            clear_screen()
            print("\n\n=== GOAL ===")
            time.sleep(1.0)
            return

        except KeyboardInterrupt:
            clear_screen()
            print("게임을 종료합니다.")
            time.sleep(0.8)
            return  # 메인 메뉴로 복귀 (종료 X)