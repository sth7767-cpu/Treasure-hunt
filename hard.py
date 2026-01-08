# hard.py (복붙용 완성본)
# - 사이드바/화면 깜빡임 제거: 매 프레임 화면 전체 삭제(X) -> 커서만 HOME으로 이동해서 덮어쓰기
# - 커서 숨김/복구
# - 네모 SCORE 박스/결과 박스: 한글/전각 폭 고려(display_width/pad_to_width)
# - 기존 하드 로직(미사일/아이템/벽즉사/GOAL) 유지

import os
import sys
import time
import random
import shutil
import unicodedata
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


# -------------------------------
# 화면/ANSI
# -------------------------------
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
        # ENABLE_VIRTUAL_TERMINAL_PROCESSING
        if kernel32.SetConsoleMode(handle, mode.value | 0x0004) == 0:
            return False
        return True
    except Exception:
        return False


ANSI_OK = enable_ansi_on_windows()


def hide_cursor():
    if ANSI_OK:
        sys.stdout.write("\x1b[?25l")
        sys.stdout.flush()


def show_cursor():
    if ANSI_OK:
        sys.stdout.write("\x1b[?25h")
        sys.stdout.flush()


def move_cursor_home():
    # ✅ 깜빡임 제거 핵심: 전체 화면 지우지 말고 HOME으로만 이동해서 덮어쓰기
    if ANSI_OK:
        sys.stdout.write("\x1b[H")
        sys.stdout.flush()
    else:
        clear_screen()


def print_centered_block(text: str):
    cols, rows = shutil.get_terminal_size((80, 24))
    lines = [ln.rstrip("\n") for ln in text.split("\n")]

    top_pad = max(0, (rows - len(lines)) // 2)
    sys.stdout.write("\n" * top_pad)

    for ln in lines:
        w = display_width(ln)
        if w >= cols:
            sys.stdout.write(ln + "\n")
            continue
        left_pad = (cols - w) // 2
        sys.stdout.write((" " * left_pad) + ln + "\n")

    sys.stdout.flush()


# -------------------------------
# 표시 폭(한글/전각=2칸) 기반 패딩 유틸
# -------------------------------
def display_width(s: str) -> int:
    w = 0
    for ch in s:
        if unicodedata.east_asian_width(ch) in ("F", "W"):
            w += 2
        else:
            w += 1
    return w


def pad_to_width(s: str, width: int) -> str:
    cur = display_width(s)
    if cur >= width:
        return s
    return s + (" " * (width - cur))


# -------------------------------
# 입력
# -------------------------------
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


# -------------------------------
# 그리드/렌더 (트랙 폭 고정 + 사이드바 폭 고정)
# -------------------------------
TRACK_WIDTH = None
SIDEBAR_WIDTH = 36

def to_grid(view_lines):
    global TRACK_WIDTH
    stripped = [ln.rstrip("\n") for ln in view_lines]
    w = max((len(s) for s in stripped), default=0)

    # 첫 프레임 폭 기준 고정(흔들림 방지)
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
        out.append(row + "  " + pad_to_width(side, SIDEBAR_WIDTH))
    return "\n".join(out) + "\n"


# -------------------------------
# 스프라이트/도우미
# -------------------------------
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
# 카운트다운
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

        sidebar = []
        sidebar += build_score_box(0, 0, 0, "READY")
        sidebar += [
            "",
            "Items:",
            "  ★ = +5",
            "  ● = +3",
            "  ▲ = -2",
            "",
            "Hard Mode:",
            "  벽/미사일=즉시 종료",
            "",
            "Controls:",
            "  A/D 또는 ←/→",
            "  ESC 종료",
        ]

        move_cursor_home()
        sys.stdout.write(render_with_sidebar(grid, sidebar))
        sys.stdout.flush()
        time.sleep(sec)


# -------------------------------
# 하이스코어 저장
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
# 아이템
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


# -------------------------------
# SCORE 박스(완전 네모)
# -------------------------------
SCORE_BOX_INNER = 24

def build_score_box(points, best, sec, speed_status):
    top = "┌" + ("─" * SCORE_BOX_INNER) + "┐"
    l1 = "│" + pad_to_width(f" Points : {points}", SCORE_BOX_INNER) + "│"
    l2 = "│" + pad_to_width(f" Best   : {best}", SCORE_BOX_INNER) + "│"
    l3 = "│" + pad_to_width(f" Time   : {sec}", SCORE_BOX_INNER) + "│"
    l4 = "│" + pad_to_width(f" Speed  : {speed_status}", SCORE_BOX_INNER) + "│"
    bot = "└" + ("─" * SCORE_BOX_INNER) + "┘"
    return [top, l1, l2, l3, l4, bot]


# -------------------------------
# 결과 화면(가운데) - 완전 네모
# -------------------------------
def show_hard_result(kind, points, highscore, sec, speed_status, reason=""):
    if points > highscore:
        highscore = points
        save_highscore(highscore)

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
    title = arts.get(kind, kind)

    inner = 34

    def row(content: str) -> str:
        return "┃" + pad_to_width(content, inner) + "┃"

    top = "┏" + ("━" * inner) + "┓"
    mid = "┣" + ("━" * inner) + "┫"
    bot = "┗" + ("━" * inner) + "┛"

    reason_line = f"REASON : {reason}" if reason else ""
    header = f"{kind:^10}".center(inner)

    box_lines = [
        top,
        row(header),
        mid,
        row(f"   SCORE : {points}"),
        row(f"   BEST  : {highscore}"),
        row(f"   TIME  : {sec}"),
        row(f"   SPEED : {speed_status}"),
        mid,
        row(f"   {reason_line}"),
        bot,
    ]
    box = "\n".join(box_lines)

    hint = "R = 다시하기   |   ESC = 메뉴로"
    clear_screen()
    print_centered_block(title + "\n\n" + box + "\n\n" + hint)
    return highscore


# -------------------------------
# 하드모드 실행
# -------------------------------
def screen_two_hard():
    global TRACK_WIDTH
    hide_cursor()

    filename = "track_hard.txt"
    if not os.path.exists(filename):
        show_cursor()
        clear_screen()
        print("오류: track_hard.txt 파일이 없습니다.")
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
    missile_interval = 1.2
    missile_speed = 2

    # 아이템
    item_interval = 0.9

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

    try:
        while True:  # R 다시하기 루프
            TRACK_WIDTH = None

            missiles = []
            items = []
            last_missile_spawn = time.time() - 999
            last_item_spawn = time.time() - 999
            last_move_time = time.time()

            scroll_i, car_x, car_y, last_bounds = init_start_state()

            start_time = time.time()
            points = 0
            last_sec = 0
            speed_status = "보통"

            countdown_on_map(lines, view_height, scroll_i, car_sprite_lines, car_x, car_y)
            clear_screen()

            ended_kind = None
            ended_reason = ""

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
                    delay = 0.09
                    speed_status = "보통"
                elif elapsed < 30:
                    delay = 0.07
                    speed_status = "빠름"
                else:
                    delay = 0.055
                    speed_status = "매우 빠름"

                MOVE_COOLDOWN = delay

                # 입력
                left, right, esc = get_key_state()
                if esc:
                    show_cursor()
                    return

                last_bounds = get_road_bounds_safe(current_view, car_y, car_w, car_h, last_bounds=last_bounds)
                mn, mx = last_bounds

                attempted_left = attempted_right = False

                if now - last_move_time >= MOVE_COOLDOWN:
                    if left and not right:
                        attempted_left = True
                        car_x -= 1
                        last_move_time = now
                    elif right and not left:
                        attempted_right = True
                        car_x += 1
                        last_move_time = now

                # 벽 충돌 즉시 GAME OVER
                if attempted_left and car_x < mn:
                    ended_kind, ended_reason = "GAME OVER", "WALL"
                    break
                if attempted_right and car_x > mx:
                    ended_kind, ended_reason = "GAME OVER", "WALL"
                    break

                if car_x < mn:
                    car_x = mn
                elif car_x > mx:
                    car_x = mx

                # 미사일 생성
                if now - last_missile_spawn >= missile_interval and W > 0 and H > 0:
                    candidates = []
                    y_start = 2
                    y_end = max(2, min(view_height - 3, H - 2))
                    for y in range(y_start, y_end + 1):
                        walls = _find_walls_in_row(grid[y])
                        if not walls:
                            continue
                        l, r = walls
                        road_left, road_right = l + 1, r - 1
                        if road_right - road_left + 1 >= missile_len + 1:
                            spawn_x = max(road_left, road_right - missile_len)
                            candidates.append((y, spawn_x))

                    if candidates:
                        screen_y, spawn_x = random.choice(candidates)
                        abs_y = scroll_i + screen_y
                        missiles.append({"x": spawn_x, "abs_y": abs_y})
                        last_missile_spawn = now

                # 아이템 생성
                if now - last_item_spawn >= item_interval and W > 0 and H > 0:
                    sp = choose_item_spawn(current_view, view_height)
                    if sp:
                        screen_y, x = sp
                        abs_y = scroll_i + screen_y
                        it = random.choice(ITEMS)
                        items.append({"x": x, "abs_y": abs_y, "ch": it["ch"], "score": it["score"]})
                        last_item_spawn = now

                car_cells = make_car_cells(car_sprite_lines, car_x, car_y)

                # 아이템 판정
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
                            if 0 <= xx < W and ch != " ":
                                missile_cells.add((xx, screen_y))
                        if car_cells & missile_cells:
                            hit_by_missile = True
                        for k, ch in enumerate(MISSILE_SHAPE):
                            xx = x0 + k
                            if 0 <= xx < W:
                                grid[screen_y][xx] = ch
                    if m["x"] > -missile_len:
                        alive_missiles.append(m)
                missiles = alive_missiles

                if hit_by_missile:
                    ended_kind, ended_reason = "GAME OVER", "MISSILE"
                    break

                # 렌더: 차
                draw_sprite_on_grid(grid, car_x, car_y, car_sprite_lines)

                # GOAL 판정
                car_abs_bottom = scroll_i + car_y + car_h - 1
                if car_abs_bottom >= goal_abs_y:
                    ended_kind, ended_reason = "GOAL", ""
                    break

                # 사이드바
                sidebar = []
                sidebar += build_score_box(points, highscore, sec, speed_status)
                sidebar += [
                    "",
                    "Items:",
                    "  ★ = +5",
                    "  ● = +3",
                    "  ▲ = -2",
                    "",
                    "Hard Mode:",
                    "  벽/미사일=즉시 종료",
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

            # 결과 처리
            elapsed = time.time() - start_time
            sec = int(elapsed)
            if ended_kind is None:
                ended_kind, ended_reason = "GAME OVER", "END"

            final_speed = "FINISH" if ended_kind == "GOAL" else speed_status

            show_cursor()
            highscore = show_hard_result(ended_kind, points, highscore, sec, final_speed, reason=ended_reason)
            hide_cursor()

            choice = wait_result_choice()
            if choice == "restart":
                continue
            show_cursor()
            return

    finally:
        # 어떤 예외든 커서 복구
        show_cursor()


# main.py에서 호출용 별칭이 필요하면:
def screen_two():
    return screen_two_hard()
