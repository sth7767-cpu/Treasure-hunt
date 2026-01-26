import os
import sys
import time
import random
import shutil
import unicodedata
import player

# 키보드 처리 (key)
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
    if ANSI_OK:
        sys.stdout.write("\x1b[H")
        sys.stdout.flush()
    else:
        clear_screen()


# 표시 폭(한글/전각=2칸)
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


# 스프라이트 180도 회전

def rotate_sprite_180(sprite: str) -> str:
    lines = sprite.split("\n")
    if lines and lines[-1] == "":
        lines.pop()

    if not lines:
        return sprite

    w = max(len(line) for line in lines)
    padded = [line.ljust(w) for line in lines]

    rotated = []
    for line in reversed(padded):
        rotated.append(line[::-1])

    return "\n".join(rotated)

# 입력
def get_key_state():
    if USE_KEYBOARD:
        # A/D 키와 화살표 키 모두 인식하도록 수정
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
            elif keyboard.is_pressed("m"):
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


# 그리드/렌더
TRACK_WIDTH = None
SIDEBAR_WIDTH = 70


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



# 트랙/도로
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
    # 차의 높이만큼 모든 행을 검사하여 가장 좁은 폭을 찾음
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

        # 도로 폭이 차보다 좁은 경우 예외 처리
        if max_x < min_x:
            mid = W // 2
            min_x = max(0, mid - car_w // 2)
            max_x = min_x
        return (min_x, max_x)

    # 벽을 못 찾은 경우 이전 값을 쓰거나 전체 폭 사용
    if last_bounds is not None:
        return last_bounds

    return (0, max(0, W - car_w))


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


# 카운트다운
def countdown_on_map(lines, view_height, scroll_i, car_sprite_lines, car_x, car_y):
    steps = [("3", 0.7), ("2", 0.7), ("1", 0.7), ("START", 0.9)]
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

    sidebar = build_score_box(0, 0, 0, "READY")
    sidebar += [
        "",
        "Items:",
        "  ★ = +5",
        "  ● = +3",
        "  ▲ = -2",
        "",
        "Normal Mode:",
        "  벽은 즉사X",
        "  장애물=즉시 종료",
        "",
        "Controls:",
        "  A/D 또는 ←/→",
        "  ESC 종료",
    ]

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

        move_cursor_home()
        sys.stdout.write(render_with_sidebar(grid, sidebar))
        sys.stdout.flush()
        time.sleep(sec)



# 하이스코어
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
        if 0 <= y < H and 0 <= x < W and grid[y][x] == " ":
            return y, x
    return None


# 장애물 충돌
def car_hits_obstacle(obstacle_spots, scroll_i, car_x, car_y, car_w, car_h, view_height):
    if not obstacle_spots:
        return False

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



# TrackMap
MINI_INNER_W = 40
MINI_X_SHRINK = 2
MINI_Y_SHRINK = 2

_MINI_IMPORTANT = set("│|╲╱═─━┌┐└┘┏┓┗┛┠┨┣┫╔╗╚╝╠╣╦╩╬")
_MINI_SPACEY = set([" ", "\t", "\r", "\n"])


def _mini_pick_char(block_chars):
    for ch in block_chars:
        if ch in _MINI_IMPORTANT:
            return ch
    for ch in block_chars:
        if ch not in _MINI_SPACEY:
            return ch
    return " "


def _compress_segment(seg: str, out_w: int, shrink: int) -> str:
    if shrink <= 1:
        return seg[:out_w].ljust(out_w)

    need_src = out_w * shrink
    seg = seg[:need_src].ljust(need_src)

    out = []
    for i in range(out_w):
        block = seg[i * shrink:(i + 1) * shrink]
        out.append(_mini_pick_char(block))
    return "".join(out)


def build_track_ascii_minimap(track_lines, start_index, goal_abs_y,
                              scroll_i, car_y, car_h, car_x,
                              mini_view_h: int,
                              items=None):
    if items is None:
        items = []

    H = len(track_lines)
    if H <= 0:
        return ["TrackMap: (empty)"]

    car_abs_y = max(0, min(H - 1, scroll_i + car_y + (car_h // 2)))

    s = max(0, min(H - 1, start_index))
    g = max(0, min(H - 1, goal_abs_y))
    y0, y1 = (s, g) if s <= g else (g, s)

    src_span = mini_view_h * max(1, MINI_Y_SHRINK)
    up = src_span // 3
    top = max(y0, car_abs_y - up)
    bot = min(y1, top + src_span - 1)
    top = max(y0, bot - (src_span - 1))

    need_src_w = MINI_INNER_W * max(1, MINI_X_SHRINK)

    cur_line = track_lines[car_abs_y].rstrip("\n")
    line_len = len(cur_line)
    if line_len <= 0:
        clip_start = 0
    else:
        clip_start = car_x - (need_src_w // 2)
        clip_start = max(0, min(clip_start, max(0, line_len - need_src_w)))

    out = []
    out.append("TrackMap:")
    out.append("┌" + ("─" * MINI_INNER_W) + "┐")

    ys = []
    yy = top
    for _ in range(mini_view_h):
        yy = min(bot, yy)
        ys.append(yy)

        ln = track_lines[yy].rstrip("\n")
        raw_seg = ln[clip_start: clip_start + need_src_w].ljust(need_src_w)
        seg = _compress_segment(raw_seg, MINI_INNER_W, MINI_X_SHRINK)
        out.append("│" + seg + "│")

        yy += max(1, MINI_Y_SHRINK)

    out.append("└" + ("─" * MINI_INNER_W) + "┘")

    def overlay(row_i, mx, ch):
        line_idx = 2 + row_i
        line = out[line_idx]
        content = list(line[1:-1])
        if 0 <= mx < MINI_INNER_W:
            content[mx] = ch
            out[line_idx] = "│" + "".join(content) + "│"

    # 아이템 먼저 표시
    if ys:
        for it in items:
            ay = it.get("abs_y")
            ax = it.get("x")
            ch = it.get("ch")
            if ay is None or ax is None or not ch:
                continue
            if ay < top or ay > bot:
                continue
            row_i = min(range(len(ys)), key=lambda i: abs(ys[i] - ay))
            mx = (ax - clip_start) // max(1, MINI_X_SHRINK)
            if 0 <= mx < MINI_INNER_W:
                overlay(row_i, mx, ch)

    if ys:
        best_i = min(range(len(ys)), key=lambda i: abs(ys[i] - car_abs_y))
    else:
        best_i = 0
    mx_car = (car_x - clip_start) // max(1, MINI_X_SHRINK)
    mx_car = max(0, min(MINI_INNER_W - 1, mx_car))
    overlay(best_i, mx_car, "▶")

    denom = max(1, abs(g - s))
    prog = (car_abs_y - s) / denom if s <= g else (s - car_abs_y) / denom
    prog = max(0.0, min(1.0, prog))
    out.append(f"Progress: {int(prog * 100)}%")

    return out


# 결과 화면
def show_result_centered(kind: str, score: int, best: int, sec: int, speed_status: str, reason: str = ""):
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
        row(f"   SCORE : {score}"),
        row(f"   BEST  : {best}"),
        row(f"   TIME  : {sec}"),
        row(f"   SPEED : {speed_status}"),
        mid,
        row(f"   {reason_line}"),
        bot,
    ]
    box = "\n".join(box_lines)

    hint = "R = 다시하기 | M = 메뉴 | ESC = 종료"
    clear_screen()
    print_centered_block(title_art + "\n\n" + box + "\n\n" + hint)


# NORMAL 실행
def screen_two_normal():
    global TRACK_WIDTH
    hide_cursor()

    filename = "track.txt"
    if not os.path.exists(filename):
        show_cursor()
        clear_screen()
        print("오류: track.txt 파일이 없습니다.")
        time.sleep(1.2)
        return None

    with open(filename, "r", encoding="utf-8") as f:
        base_lines = f.readlines()

    start_index = find_start_index(base_lines)
    goal_abs_y = find_goal_abs_y(base_lines)

    obstacle_spots = []
    lines = base_lines
    try:
        try:
            lines, obstacle_spots = player.add_obstacles_to_track(lines, interval=8, chance=0.85, safe_start=6)
        except TypeError:
            lines, obstacle_spots = player.add_obstacles_to_track(lines, interval=8, chance=0.85)
    except AttributeError:
        obstacle_spots = []
        lines = base_lines

    total_lines = len(lines)
    view_height = 28

    car_str = rotate_sprite_180(player.car_frame())
    car_sprite_lines = car_str.split("\n")
    car_h = len(car_sprite_lines)
    car_w = max((len(l) for l in car_sprite_lines), default=0)

    while True:
        TRACK_WIDTH = None
        clear_screen()

        scroll_i = 0
        car_y = 0

        points = 0
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

        car_x = (mn0 + mx0) // 2
        last_bounds = None

        countdown_on_map(lines, view_height, scroll_i, car_sprite_lines, car_x, car_y)
        clear_screen()

        start_time = time.time()

        ended_kind = None
        ended_reason = ""
        speed_status = "보통"
        sec = 0

        try:
            while scroll_i < total_lines:
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

                #  hard.py의 도로 경계 계산 적용
                mn, mx = get_road_bounds_safe(current_view, car_y, car_w, car_h, last_bounds)
                last_bounds = (mn, mx)

                dx = 0
                if left and not right:
                    dx = -2
                elif right and not left:
                    dx = 2

                # 제안된 이동 위치 계산 및 범위 제한
                proposed_x = car_x + dx
                if proposed_x < mn:
                    proposed_x = mn
                elif proposed_x > mx:
                    proposed_x = mx

                car_x = proposed_x

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

                # 아이템 판정/렌더
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

                draw_sprite_on_grid(grid, car_x, car_y, car_sprite_lines)

                info_lines = [
                    "",
                    "Items:",
                    "  ★ = +5",
                    "  ● = +3",
                    "  ▲ = -2",
                    "",
                    "Normal Mode:",
                    "  벽은 즉사X",
                    "  장애물=즉시 종료",
                    "",
                    "Controls:",
                    "  A/D 또는 ←/→",
                    "  ESC 종료",
                ]
                base_sidebar = build_score_box(points, highscore, sec, speed_status) + [""]

                fixed = len(base_sidebar) + 4 + len(info_lines)
                mini_view_h = max(3, H - fixed)

                minimap = build_track_ascii_minimap(
                    lines, start_index, goal_abs_y,
                    scroll_i, car_y, car_h, car_x,
                    mini_view_h=mini_view_h,
                    items=items
                )

                sidebar = []
                sidebar += base_sidebar
                sidebar += minimap
                sidebar += info_lines

                move_cursor_home()
                sys.stdout.write(render_with_sidebar(grid, sidebar))
                sys.stdout.flush()

                time.sleep(delay)
                scroll_i += 1

        except KeyboardInterrupt:
            show_cursor()
            return

        if points > highscore:
            highscore = points
            save_highscore(highscore)

        show_cursor()
        if ended_kind is None:
            ended_kind = "GAME OVER"
            ended_reason = "END"

        final_speed = "FINISH" if ended_kind == "GOAL" else speed_status
        show_result_centered("GOAL" if ended_kind == "GOAL" else "GAME OVER",
                             points, highscore, sec, final_speed,
                             reason=ended_reason)

        choice = wait_result_choice()
        if choice == "restart":
            hide_cursor()
            continue
        elif choice == "menu":
            return points
        elif choice == "exit":
            sys.exit(0)  # 프로그램 종료


def screen_two():
    return screen_two_normal()
