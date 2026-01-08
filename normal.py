import os
import sys
import time
import random
import shutil
import player

# -------------------------------
# 키보드 처리
# -------------------------------
try:
    import keyboard
    USE_KEYBOARD = True
except ImportError:
    import msvcrt
    USE_KEYBOARD = False


# =========================
# 0) 기본 유틸
# =========================
def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")


def enable_ansi_on_windows():
    if os.name != "nt":
        return True
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        handle = kernel32.GetStdHandle(-11)  # STD_OUTPUT_HANDLE
        mode = ctypes.c_uint32()
        if kernel32.GetConsoleMode(handle, ctypes.byref(mode)) == 0:
            return False
        if kernel32.SetConsoleMode(handle, mode.value | 0x0004) == 0:  # ENABLE_VIRTUAL_TERMINAL_PROCESSING
            return False
        return True
    except Exception:
        return False


ANSI_OK = enable_ansi_on_windows()


def move_cursor_home():
    # ✅ 잔상 제거 + 덮어쓰기 안정화
    if ANSI_OK:
        sys.stdout.write("\x1b[H\x1b[J")  # home + clear-to-end
        sys.stdout.flush()
    else:
        clear_screen()


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


def wait_result_choice():
    """
    결과 화면에서:
    - R: 다시하기
    - ESC: 메뉴로
    """
    while True:
        if USE_KEYBOARD:
            if keyboard.is_pressed("r"):
                time.sleep(0.2)
                return "restart"
            if keyboard.is_pressed("esc"):
                time.sleep(0.2)
                return "menu"
            time.sleep(0.03)
        else:
            if msvcrt.kbhit():
                ch = msvcrt.getch()
                if ch in (b"r", b"R"):
                    return "restart"
                if ch == b"\x1b":
                    return "menu"
            time.sleep(0.03)


def print_centered_block(text: str):
    cols, rows = shutil.get_terminal_size((80, 24))
    lines = [ln.rstrip("\n") for ln in text.split("\n")]
    top_pad = max(0, (rows - len(lines)) // 2)
    sys.stdout.write("\n" * top_pad)
    for ln in lines:
        sys.stdout.write(ln.center(cols) + "\n")
    sys.stdout.flush()


# =========================
# 1) 렌더링(고정폭) 유틸
# =========================
TRACK_WIDTH = None
SIDEBAR_WIDTH = 32


def to_grid(view_lines):
    global TRACK_WIDTH
    stripped = [ln.rstrip("\n") for ln in view_lines]
    w = max((len(s) for s in stripped), default=0)

    if TRACK_WIDTH is None:
        TRACK_WIDTH = w
    else:
        if w > TRACK_WIDTH:
            TRACK_WIDTH = w
        w = TRACK_WIDTH

    return [list(s.ljust(w)) for s in stripped]


def draw_sprite_on_grid(grid, x, y, sprite_lines):
    for dy, line in enumerate(sprite_lines):
        gy = y + dy
        if 0 <= gy < len(grid):
            for dx, ch in enumerate(line):
                gx = x + dx
                if 0 <= gx < len(grid[gy]) and ch != " ":
                    grid[gy][gx] = ch


def render_with_sidebar(grid, sidebar_lines):
    H = len(grid)
    out = []
    for i in range(H):
        row = "".join(grid[i])
        side = sidebar_lines[i] if i < len(sidebar_lines) else ""
        out.append(row + "  " + side.ljust(SIDEBAR_WIDTH))
    return "\n".join(out) + "\n"


# =========================
# 2) 카운트다운 3,2,1,START
# =========================
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

        sidebar = [
            "┌──────── SCORE ────────┐",
            "│ Points : 0         │",
            "│ Best   : 0         │",
            "│ Time   : 0         │",
            "│ Speed  : READY     │",
            "└───────────────────────┘",
            "",
            "Items:",
            "  ★ = +5",
            "  ● = +3",
            "  ▲ = -2",
            "",
            "Controls:",
            "  A/D 또는 ←/→",
            "  ESC 종료",
        ]

        move_cursor_home()
        sys.stdout.write(render_with_sidebar(grid, sidebar))
        sys.stdout.flush()
        time.sleep(sec)


# =========================
# 3) 하이스코어 저장
# =========================
HIGHSCORE_FILE = "highscore_normal.txt"


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


# =========================
# 4) GOAL 위치 찾기(중요)
# =========================
def find_goal_abs_y(lines):
    for idx, line in enumerate(lines):
        if "GOAL" in line:
            return idx
    for idx in range(len(lines) - 1, -1, -1):
        if "════" in lines[idx] or "====" in lines[idx]:
            return idx
    return len(lines) - 1


# =========================
# 5) 아이템
# =========================
ITEMS = [
    {"name": "STAR", "ch": "★", "score": 5},
    {"name": "CIRCLE", "ch": "●", "score": 3},
    {"name": "TRI", "ch": "▲", "score": -2},
]


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
        if road_right - road_left >= 2:
            candidates.append((y, road_left, road_right))

    if not candidates:
        return None

    for _ in range(30):
        y, road_left, road_right = random.choice(candidates)
        x = random.randint(road_left, road_right)
        if 0 <= y < H and 0 <= x < W and grid[y][x] == " ":
            return y, x
    return None


def make_car_cells(car_sprite_lines, car_x, car_y):
    cells = set()
    for dy, line in enumerate(car_sprite_lines):
        for dx, ch in enumerate(line):
            if ch != " ":
                cells.add((car_x + dx, car_y + dy))
    return cells


# =========================
# 6) 장애물 충돌 체크
# =========================
def car_hits_obstacle(obstacle_spots, scroll_i, car_x, car_y, car_w, car_h, view_height):
    car_abs_y1 = scroll_i + car_y
    car_abs_y2 = car_abs_y1 + car_h - 1
    car_x1 = car_x
    car_x2 = car_x + car_w - 1

    view_abs_y1 = scroll_i
    view_abs_y2 = scroll_i + view_height - 1

    for ob in obstacle_spots:
        oy1 = ob["y"]
        oy2 = ob["y"] + ob["h"] - 1
        if oy2 < view_abs_y1 or oy1 > view_abs_y2:
            continue

        ox1 = ob["x"]
        ox2 = ob["x"] + ob["w"] - 1

        if (car_abs_y1 <= oy2 and car_abs_y2 >= oy1 and
                car_x1 <= ox2 and car_x2 >= ox1):
            return True
    return False


# =========================
# 7) 가운데 결과 화면(죽었을 때와 동일 스타일)
# =========================
def show_result_centered(kind: str, final_score: int, best_score: int, sec: int, speed_status: str, reason: str = ""):
    arts = {
        "GAME OVER": r"""
 ██████╗  █████╗ ███╗   ███╗███████╗
██╔════╝ ██╔══██╗████╗ ████║██╔════╝
██║  ███╗███████║██╔████╔██║█████╗  
██║   ██║██╔══██║██║╚██╔╝██║██╔══╝  
╚██████╔╝██║  ██║██║ ╚═╝ ██║███████╗
 ╚═════╝ ╚═╝  ╚═╝╚═╝     ╚═╝╚══════╝
""".strip("\n"),

        "GOAL": r"""
 ██████╗  █████╗  █████╗ ██╗     
██╔════╝ ██╔══██╗██╔══██╗██║     
██║  ███╗██║  ██║███████║██║     
██║   ██║██║  ██║██╔══██║██║     
╚██████╔╝╚█████╔╝██║  ██║███████╗
 ╚═════╝  ╚════╝ ╚═╝  ╚═╝╚══════╝
""".strip("\n"),
    }

    title_art = arts.get(kind, kind)
    reason_line = f"REASON : {reason}" if reason else ""

    box = f"""
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃              {kind:^10}              ┃
┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫
┃   SCORE : {final_score:<26}┃
┃   BEST  : {best_score:<26}┃
┃   TIME  : {sec:<26}┃
┃   SPEED : {speed_status:<26}┃
┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫
┃   {reason_line:<34}┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
""".strip("\n")

    hint = "R = 다시하기   |   ESC = 메뉴로"
    clear_screen()
    print_centered_block(title_art + "\n\n" + box + "\n\n" + hint)


# =========================
# 8) Normal 실행
# =========================
def screen_two_normal():
    global TRACK_WIDTH

    while True:  # ✅ R로 재시작
        TRACK_WIDTH = None
        clear_screen()

        filename = "track.txt"
        if not os.path.exists(filename):
            print("오류: track.txt 파일이 없습니다.")
            time.sleep(1.2)
            return None

        with open(filename, "r", encoding="utf-8") as f:
            lines = f.readlines()

        # ✅ GOAL 위치(절대 라인)
        goal_abs_y = find_goal_abs_y(lines)

        # ✅ 장애물 배치
        try:
            lines, obstacle_spots = player.add_obstacles_to_track(lines, interval=8, chance=0.85, safe_start=6)
        except TypeError:
            lines, obstacle_spots = player.add_obstacles_to_track(lines, interval=8, chance=0.85)

        total_lines = len(lines)
        view_height = 20

        # 차
        car_str = player.car_frame()
        car_sprite_lines = car_str.split("\n")
        car_h = len(car_sprite_lines)
        car_w = max((len(l) for l in car_sprite_lines), default=0)

        scroll_i = 0
        car_y = 0  # normal: 위 고정

        # 도로 경계
        last_min_x, last_max_x = 0, 0

        def get_road_bounds_from_view(view_lines, prefer_row):
            nonlocal last_min_x, last_max_x
            grid = to_grid(view_lines)
            H = len(grid)
            if H == 0:
                return last_min_x, last_max_x

            rr = max(0, min(int(prefer_row), H - 1))
            walls = _find_walls_in_row(grid[rr])
            if not walls:
                return last_min_x, last_max_x

            l, r = walls
            min_x = l + 1
            max_x = (r - 1) - car_w + 1
            if max_x < min_x:
                max_x = min_x

            last_min_x, last_max_x = min_x, max_x
            return min_x, max_x

        def bounce_x(current_x, dx, min_x, max_x):
            if current_x < min_x:
                current_x = min_x
            elif current_x > max_x:
                current_x = max_x

            if dx == 0:
                return current_x

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

        # 점수/시간
        points = 0
        start_time = time.time()
        last_sec = 0
        highscore = load_highscore()

        # 아이템
        items = []
        item_interval = 0.9
        last_item_spawn = time.time() - 999

        # 초기 X 중앙
        init_view = lines[scroll_i: scroll_i + view_height]
        mn0, mx0 = get_road_bounds_from_view(init_view, car_y + (car_h // 2))
        car_x = (mn0 + mx0) // 2

        # 카운트다운
        countdown_on_map(lines, view_height, scroll_i, car_sprite_lines, car_x, car_y)
        clear_screen()

        ended_kind = None
        ended_reason = ""
        speed_status = "보통"
        sec = 0

        while scroll_i < total_lines:
            now = time.time()
            current_view = lines[scroll_i: scroll_i + view_height]
            if not current_view:
                break

            grid = to_grid(current_view)
            H = len(grid)
            W = len(grid[0]) if H > 0 else 0

            # 점수(초당 1점)
            elapsed = now - start_time
            sec = int(elapsed)
            if sec > last_sec:
                points += (sec - last_sec)
                last_sec = sec

            if points > highscore:
                highscore = points
                save_highscore(highscore)

            # 속도
            if elapsed < 15:
                delay = 0.1
                speed_status = "보통"
            elif elapsed < 30:
                delay = 0.08
                speed_status = "빠름"
            else:
                delay = 0.05
                speed_status = "매우 빠름"

            # 입력
            left, right, esc = get_key_state()
            if esc:
                return points

            mn, mx = get_road_bounds_from_view(current_view, car_y + (car_h // 2))

            dx = 0
            if left and not right:
                dx = -2
            elif right and not left:
                dx = 2

            car_x = bounce_x(car_x, dx, mn, mx)

            # ✅ 장애물 충돌
            if car_hits_obstacle(obstacle_spots, scroll_i, car_x, car_y, car_w, car_h, view_height):
                ended_kind = "GAME OVER"
                ended_reason = "OBSTACLE"
                break

            # ✅ GOAL 진입(차 바닥 절대 Y가 GOAL 라인에 닿으면 즉시 종료)
            car_abs_bottom = scroll_i + car_y + car_h - 1
            if car_abs_bottom >= goal_abs_y:
                ended_kind = "GAME OVER"  # <- "죽었을 때처럼" 동일한 결과 흐름
                ended_reason = "GOAL"
                break

            # 아이템 스폰
            if now - last_item_spawn >= item_interval and W > 0 and H > 0:
                sp = choose_item_spawn(current_view, view_height)
                if sp:
                    screen_y, x = sp
                    abs_y = scroll_i + screen_y
                    it = random.choice(ITEMS)
                    items.append({"x": x, "abs_y": abs_y, "ch": it["ch"], "score": it["score"]})
                    last_item_spawn = now

            # 아이템 판정
            car_cells = make_car_cells(car_sprite_lines, car_x, car_y)
            alive_items = []
            for it in items:
                screen_y = it["abs_y"] - scroll_i
                if 0 <= screen_y < H:
                    if 0 <= it["x"] < W and grid[screen_y][it["x"]] == " ":
                        grid[screen_y][it["x"]] = it["ch"]
                    if (it["x"], screen_y) in car_cells:
                        points += it["score"]
                        if points < 0:
                            points = 0
                        continue
                    alive_items.append(it)
                else:
                    alive_items.append(it)
            items = alive_items

            if points > highscore:
                highscore = points
                save_highscore(highscore)

            # 차 그리기
            draw_sprite_on_grid(grid, car_x, car_y, car_sprite_lines)

            # 사이드바
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
                "Controls:",
                "  A/D 또는 ←/→",
                "  ESC 종료",
            ]

            move_cursor_home()
            sys.stdout.write(render_with_sidebar(grid, sidebar))
            sys.stdout.flush()

            time.sleep(delay)
            scroll_i += 1

        # ✅ 결과 처리
        if points > highscore:
            highscore = points
            save_highscore(highscore)

        # GOAL로 끝났으면 GOAL 아트 보여주기(죽었을 때처럼 같은 흐름이지만, 아트는 GOAL 사용)
        if ended_kind == "GAME OVER" and ended_reason == "GOAL":
            show_result_centered("GOAL", points, highscore, sec, "FINISH", reason="")
        else:
            show_result_centered("GAME OVER", points, highscore, sec, speed_status, reason=ended_reason)

        choice = wait_result_choice()
        if choice == "restart":
            continue
        return points


# ✅ main.py가 normal.screen_two()를 호출해도 동작하도록 별칭 제공
def screen_two():
    return screen_two_normal()
