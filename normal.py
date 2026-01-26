import os
import sys
import time
import random
import shutil
import unicodedata
import player


# 키보드 처리
try:
    import keyboard
    USE_KEYBOARD = True
except ImportError:
    import msvcrt
    USE_KEYBOARD = False



# 1. 화면/ANSI/유틸
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
    except:
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
    if ANSI_OK:
        sys.stdout.write("\x1b[H")
        sys.stdout.flush()
    else:
        clear_screen()


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


# 2. 입력 및 렌더링
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
    while True:
        if USE_KEYBOARD:
            if keyboard.is_pressed("r"):
                time.sleep(0.2)
                return "restart"
            elif keyboard.is_pressed("esc"):
                time.sleep(0.2)
                return "exit"
            time.sleep(0.03)
        else:
            if msvcrt.kbhit():
                ch = msvcrt.getch()
                if ch in (b"r", b"R"):
                    return "restart"
                if ch == b"\x1b":
                    return "exit"
            time.sleep(0.03)


TRACK_WIDTH = None
SIDEBAR_WIDTH = 35


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
        out.append(row + "  " + pad_to_width(side, SIDEBAR_WIDTH))
    return "\n".join(out) + "\n"


def rotate_sprite_180(sprite_str):
    lines = sprite_str.split("\n")
    lines = [ln[::-1] for ln in lines[::-1]]
    return "\n".join(lines)


def find_goal_abs_y(lines):
    for idx, line in enumerate(lines):
        if "GOAL" in line:
            return idx
    for idx in range(len(lines) - 1, -1, -1):
        if "════" in lines[idx] or "====" in lines[idx]:
            return idx
    return len(lines) - 1


WALL_SET = set(["│", "|", "╱", "╲", "/", "\\", "║", "¦"])


def _find_walls_in_row(row_chars):
    """한 줄(row)에서 좌/우 벽(대각선 포함)의 바깥 경계를 찾는다."""
    s = "".join(row_chars)

    idxs = []
    for ch in WALL_SET:
        i = s.find(ch)
        if i != -1:
            idxs.append(i)
        j = s.rfind(ch)
        if j != -1:
            idxs.append(j)

    if not idxs:
        return None

    left = min(idxs)
    right = max(idxs)
    if right > left:
        return left, right
    return None


def make_car_cells(car_sprite_lines, car_x, car_y):
    cells = set()
    for dy, line in enumerate(car_sprite_lines):
        for dx, ch in enumerate(line):
            if ch != " ":
                cells.add((car_x + dx, car_y + dy))
    return cells



# SCORE 박스
SCORE_BOX_INNER = 24


def build_score_box(points, best, sec, speed_status):
    top = "┌" + ("─" * SCORE_BOX_INNER) + "┐"
    l1 = "│" + pad_to_width(f" Points : {points}", SCORE_BOX_INNER) + "│"
    l2 = "│" + pad_to_width(f" Best   : {best}", SCORE_BOX_INNER) + "│"
    l3 = "│" + pad_to_width(f" Time   : {sec}", SCORE_BOX_INNER) + "│"
    l4 = "│" + pad_to_width(f" Speed  : {speed_status}", SCORE_BOX_INNER) + "│"
    bot = "└" + ("─" * SCORE_BOX_INNER) + "┘"
    return [top, l1, l2, l3, l4, bot]



# 카운트다운(맵 위)
def countdown_on_map(lines, view_height, scroll_i, car_sprite_lines, car_x, car_y):
    BIG = {
        "3": [" ██████╗ ", " ╚════██╗", "  █████╔╝", "  ╚═══██╗", " ██████╔╝", " ╚═════╝ "],
        "2": [" ██████╗ ", " ╚════██╗", "  █████╔╝", " ██╔═══╝ ", " ███████╗", " ╚══════╝"],
        "1": ["  ██╗", " ███║", " ╚██║", "  ██║", "  ██║", "  ╚═╝"],
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
    sidebar = build_score_box(0, 0, 0, "READY") + ["", "Normal Mode:", "Controls:", "  A/D 또는 ←/→", "  ESC 종료"]

    for key, sec in steps:
        clear_screen()
        view = lines[scroll_i: scroll_i + view_height]
        grid = to_grid(view)
        draw_sprite_on_grid(grid, car_x, car_y, car_sprite_lines)

        H, W = len(grid), len(grid[0]) if grid else 0
        art = BIG[key]
        ty = max(0, (H // 2) - (len(art) // 2))
        tx = max(0, (W // 2) - (max(len(s) for s in art) // 2))

        for dy, line in enumerate(art):
            gy = ty + dy
            if 0 <= gy < H:
                for dx, ch in enumerate(line):
                    gx = tx + dx
                    if 0 <= gx < W and ch != " ":
                        grid[gy][gx] = ch

        move_cursor_home()
        sys.stdout.write(render_with_sidebar(grid, sidebar))
        sys.stdout.flush()
        time.sleep(sec)



# 하이스코어
HIGHSCORE_FILE = "highscore.txt"


def load_highscore():
    try:
        if os.path.exists(HIGHSCORE_FILE):
            with open(HIGHSCORE_FILE, "r", encoding="utf-8") as f:
                return int(f.read().strip() or 0)
    except:
        pass
    return 0


def save_highscore(score):
    try:
        with open(HIGHSCORE_FILE, "w", encoding="utf-8") as f:
            f.write(str(int(score)))
    except:
        pass


# 아이템
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
        if road_right - road_left >= 2:
            candidates.append((y, road_left, road_right))

    if not candidates:
        return None

    for _ in range(30):
        y, road_left, road_right = random.choice(candidates)
        x = random.randint(road_left, road_right)
        if 0 <= y < H:
            return y, x

    return None


# 장애물 (노말용)
OBSTACLE_CH = "X"

def build_obstacles(lines, start_index, goal_abs_y):
    obstacles = []
    # 간단히 길 중간중간 X 생성(원래 로직 유지)
    y0 = max(0, start_index + 10)
    y1 = min(len(lines) - 1, goal_abs_y - 10)
    if y1 <= y0:
        return obstacles

    for _ in range(80):
        y = random.randint(y0, y1)
        obstacles.append({"abs_y": y, "x": random.randint(5, 60)})
    return obstacles


def car_hits_obstacle(obstacle_spots, scroll_i, car_x, car_y, car_w, car_h, view_height):
    car_abs_y_top = scroll_i + car_y
    car_abs_y_bottom = car_abs_y_top + car_h - 1

    for ob in obstacle_spots:
        ay = ob["abs_y"]
        if ay < car_abs_y_top or ay > car_abs_y_bottom:
            continue
        sy = ay - scroll_i
        ox = ob["x"]
        if (car_x <= ox <= car_x + car_w - 1) and (car_y <= sy <= car_y + car_h - 1):
            return True
    return False


# 결과 화면
def show_normal_result(kind, points, highscore, sec, speed_status, reason=""):
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
    hint = "R = 다시하기 | ESC = 종료"

    clear_screen()
    print_centered_block(title + "\n\n" + box + "\n\n" + hint)
    return highscore


# 메인 게임 (Normal Mode)
def screen_two_normal():
    global TRACK_WIDTH
    hide_cursor()

    filename = "track.txt"
    if not os.path.exists(filename):
        show_cursor()
        clear_screen()
        print("오류: track.txt 파일이 없습니다.")
        time.sleep(1.2)
        return

    with open(filename, "r", encoding="utf-8") as f:
        lines = f.readlines()

    goal_abs_y = find_goal_abs_y(lines)

    car_str = rotate_sprite_180(player.car_frame())
    car_sprite_lines = car_str.split("\n")
    car_h = len(car_sprite_lines)
    car_w = max((len(l) for l in car_sprite_lines), default=0)

    view_height = 28

    # 장애물
    obstacle_spots = build_obstacles(lines, 0, goal_abs_y)

    while True:
        TRACK_WIDTH = None
        clear_screen()

        scroll_i = 0
        car_y = 0
        last_bounds = None 

        points = 0
        # start_time 초기화 제거 (아래에서 카운트다운 후 설정)
        last_sec = 0
        highscore = load_highscore()

        items = []
        item_interval = 0.9
        last_item_spawn = time.time() - 999

        # 초기 X 중앙
        init_view = lines[scroll_i: scroll_i + view_height]
        grid0 = to_grid(init_view)
        rr = min(max(0, car_y + (car_h // 2)), len(grid0) - 1) if grid0 else 0
        walls0 = _find_walls_in_row(grid0[rr]) if grid0 else None
        if walls0:
            mn0 = walls0[0] + 1
            mx0 = (walls0[1] - 1) - car_w + 1
            if mx0 < mn0:
                mx0 = mn0
        else:
            mn0 = 0
            mx0 = max(0, (len(grid0[0]) if grid0 else 0) - car_w)

        last_bounds = (mn0, mx0)
        car_x = (mn0 + mx0) // 2

        countdown_on_map(lines, view_height, scroll_i, car_sprite_lines, car_x, car_y)
        clear_screen()

        #  카운트다운 끝난 직후 시간 초기화 (점수 0부터 시작)
        start_time = time.time()

        ended_kind = None
        ended_reason = ""
        speed_status = "보통"
        sec = 0

        try:
            while scroll_i < len(lines):
                now = time.time()
                current_view = lines[scroll_i: scroll_i + view_height]
                if not current_view:
                    break

                grid = to_grid(current_view)
                H = len(grid)
                W = len(grid[0]) if H > 0 else 0

                elapsed = now - start_time
                sec = int(elapsed)
                if sec > last_sec:
                    points += (sec - last_sec)
                    last_sec = sec

                if points > highscore:
                    highscore = points
                    save_highscore(highscore)

                if elapsed < 15:
                    delay = 0.10
                    speed_status = "보통"
                elif elapsed < 30:
                    delay = 0.08
                    speed_status = "빠름"
                else:
                    delay = 0.05
                    speed_status = "매우 빠름"

                left, right, esc = get_key_state()
                if esc:
                    show_cursor()
                    return points

                # 도로 경계: 대각선 벽 포함 + 차 높이만큼 안전 경계 + last_bounds 
                lefts, rights = [], []
                for yy in range(car_y, car_y + car_h):
                    if 0 <= yy < H:
                        wlr = _find_walls_in_row(grid[yy])
                        if wlr:
                            l, r = wlr
                            lefts.append(l)
                            rights.append(r)

                if lefts and rights:
                    safe_left = max(lefts) + 1
                    safe_right = min(rights) - 1
                    mn = safe_left
                    mx = safe_right - car_w + 1
                    if mx < mn:
                        mx = mn
                    last_bounds = (mn, mx)
                else:
                    if last_bounds is not None:
                        mn, mx = last_bounds
                    else:
                        mn = 0
                        mx = max(0, W - car_w)

                dx = 0
                if left and not right:
                    dx = -2
                elif right and not left:
                    dx = 2

                car_x += dx
                if car_x < mn:
                    car_x = mn
                elif car_x > mx:
                    car_x = mx

                # 장애물 충돌 -> GAME OVER
                if car_hits_obstacle(obstacle_spots, scroll_i, car_x, car_y, car_w, car_h, view_height):
                    ended_kind = "GAME OVER"
                    ended_reason = "OBSTACLE"
                    break

                # GOAL
                car_abs_bottom = scroll_i + car_y + car_h - 1
                if car_abs_bottom >= goal_abs_y:
                    ended_kind = "GOAL"
                    ended_reason = ""
                    break

                # 아이템 생성
                if now - last_item_spawn >= item_interval and W > 0 and H > 0:
                    sp = choose_item_spawn(current_view, view_height)
                    if sp:
                        screen_y, x = sp
                        abs_y = scroll_i + screen_y
                        it = random.choice(ITEMS)
                        items.append({"x": x, "abs_y": abs_y, "ch": it["ch"], "score": it["score"]})
                        last_item_spawn = now

                # 아이템 그리기 + 먹기
                car_cells = make_car_cells(car_sprite_lines, car_x, car_y)
                alive_items = []
                for it in items:
                    sy = it["abs_y"] - scroll_i
                    if 0 <= sy < H:
                        if 0 <= it["x"] < W:
                            grid[sy][it["x"]] = it["ch"]
                        if (it["x"], sy) in car_cells:
                            points = max(0, points + it["score"])
                            continue
                    alive_items.append(it)
                items = alive_items

                # 장애물 그리기
                for ob in obstacle_spots:
                    sy = ob["abs_y"] - scroll_i
                    if 0 <= sy < H and 0 <= ob["x"] < W:
                        grid[sy][ob["x"]] = OBSTACLE_CH

                # 차 그리기
                draw_sprite_on_grid(grid, car_x, car_y, car_sprite_lines)

                # 사이드바
                sidebar = build_score_box(points, highscore, sec, speed_status)
                sidebar += [
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

            # 결과 처리
            if ended_kind is None:
                ended_kind, ended_reason = "GAME OVER", "END"

            show_cursor()
            highscore = show_normal_result(ended_kind, points, highscore, sec, speed_status, reason=ended_reason)
            hide_cursor()

            choice = wait_result_choice()
            if choice == "restart":
                hide_cursor()
                continue
            elif choice == "exit":
                return points

        except KeyboardInterrupt:
            show_cursor()
            return points

    show_cursor()


def screen_two():
    return screen_two_normal()
