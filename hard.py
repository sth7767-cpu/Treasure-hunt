import os
import sys
import time
import shutil
import random
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


# =================================================
# 1. 화면/ANSI/유틸
# =================================================
def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")


def enable_ansi_on_windows():
    if os.name != "nt": return True
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        handle = kernel32.GetStdHandle(-11)
        mode = ctypes.c_uint32()
        if kernel32.GetConsoleMode(handle, ctypes.byref(mode)) == 0: return False
        if kernel32.SetConsoleMode(handle, mode.value | 0x0004) == 0: return False
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
    # 화면을 지우지 않고 커서만 홈으로 이동 (깜빡임 방지)
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
    if cur >= width: return s
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


# =================================================
# 2. 입력 및 렌더링
# =================================================
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
            if keyboard.is_pressed("esc"):
                time.sleep(0.2)
                return "menu"
            time.sleep(0.03)
        else:
            if msvcrt.kbhit():
                ch = msvcrt.getch()
                if ch in (b"r", b"R"): return "restart"
                if ch == b"\x1b": return "menu"
            time.sleep(0.03)


# -------------------------------
# 그리드/렌더
# -------------------------------
TRACK_WIDTH = None
SIDEBAR_WIDTH = 70  # ✅ TrackMap 및 정보를 위해 넓힘


def to_grid(view_lines):
    global TRACK_WIDTH
    stripped = [ln.rstrip("\n") for ln in view_lines]
    w = max((len(s) for s in stripped), default=0)

    if TRACK_WIDTH is None:
        TRACK_WIDTH = w
    else:
        if w > TRACK_WIDTH: TRACK_WIDTH = w
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
        if "START" in line: return idx
    return 0


def find_goal_abs_y(lines):
    for idx, line in enumerate(lines):
        if "GOAL" in line: return idx
    for idx in range(len(lines) - 1, -1, -1):
        if "════" in lines[idx] or "====" in lines[idx]: return idx
    return len(lines) - 1


def find_start_line_screen_y(view_lines):
    for y, ln in enumerate(view_lines):
        s = ln.rstrip("\n")
        if ("════" in s) or ("====" in s): return y
    return 3


WALL_SET = set(["│", "|", "╱", "╲", "/", "\\", "║", "¦"])


def _find_walls_in_row(row_chars):
    s = "".join(row_chars)
    idxs = []
    for ch in WALL_SET:
        i = s.find(ch)
        if i != -1: idxs.append(i)
        j = s.rfind(ch)
        if j != -1: idxs.append(j)
    if not idxs: return None
    return min(idxs), max(idxs)


def get_road_bounds_safe(view_lines, car_y, car_w, car_h, last_bounds=None):
    grid = to_grid(view_lines)
    H = len(grid)
    W = len(grid[0]) if H > 0 else 0
    lefts, rights = [], []

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
        min_x, max_x = safe_left, safe_right - car_w + 1
        if max_x < min_x:
            mid = W // 2
            min_x = max(0, mid - car_w // 2)
            max_x = min_x
        return (min_x, max_x)

    if last_bounds: return last_bounds
    return (0, max(0, W - car_w))


def make_car_cells(car_sprite_lines, car_x, car_y):
    cells = set()
    for dy, line in enumerate(car_sprite_lines):
        for dx, ch in enumerate(line):
            if ch != " ":
                cells.add((car_x + dx, car_y + dy))
    return cells


# ✅ [핵심] 실제 충돌 판정 함수 (좌표 겹침 확인)
def car_hits_wall(grid, car_x, car_y, car_sprite_lines):
    H = len(grid)
    W = len(grid[0]) if H > 0 else 0

    for dy, line in enumerate(car_sprite_lines):
        gy = car_y + dy
        if not (0 <= gy < H): continue
        for dx, ch in enumerate(line):
            if ch == " ": continue  # 차의 빈 공간은 충돌 안 함
            gx = car_x + dx
            if not (0 <= gx < W): continue

            # 벽 문자와 겹치면 충돌!
            if grid[gy][gx] in WALL_SET: return True

    return False


# =================================================
# 4. UI 및 데이터
# =================================================
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
# ✅ TrackMap(원본 잘라서 + 조금 축소) + 아이템 표시 + 가변 높이
# -------------------------------
MINI_INNER_W = 50   # ✅ 넓힘
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

    # 차는 최우선(덮어쓰기)
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


# -------------------------------
# 결과 화면
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

    box_lines = [top, row(header), mid, row(f"   SCORE : {points}"), row(f"   BEST  : {highscore}"),
                 row(f"   TIME  : {sec}"), row(f"   SPEED : {speed_status}"), mid, row(f"   {reason_line}"), bot]
    box = "\n".join(box_lines)
    hint = "R = 다시하기   |   ESC = 메뉴로"

    clear_screen()
    print_centered_block(title + "\n\n" + box + "\n\n" + hint)
    return highscore


def countdown_on_map(lines, view_height, scroll_i, car_sprite_lines, car_x, car_y):
    BIG = {
        "3": [" ██████╗ ", " ╚════██╗", "  █████╔╝", "  ╚═══██╗", " ██████╔╝", " ╚═════╝ "],
        "2": [" ██████╗ ", " ╚════██╗", "  █████╔╝", " ██╔═══╝ ", " ███████╗", " ╚══════╝"],
        "1": ["  ██╗", " ███║", " ╚██║", "  ██║", "  ██║", "  ╚═╝"],
        "START": ["███████╗████████╗ █████╗ ██████╗ ████████╗", "██╔════╝╚══██╔══╝██╔══██╗██╔══██╗╚══██╔══╝",
                  "███████╗   ██║   ███████║██████╔╝   ██║   ", "╚════██║   ██║   ██╔══██║██╔══██╗   ██║   ",
                  "███████║   ██║   ██║  ██║██║  ██║   ██║   ", "╚══════╝   ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝   ╚═╝   "],
    }
    steps = [("3", 0.7), ("2", 0.7), ("1", 0.7), ("START", 0.9)]
    sidebar = build_score_box(0, 0, 0, "READY")
    sidebar += ["", "Hard Mode:", "  [!] 미사일", "      닿으면 즉사", "", "Controls:", "  A/D, ESC"]

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
                    if 0 <= gx < W and ch != " ": grid[gy][gx] = ch

        move_cursor_home()
        sys.stdout.write(render_with_sidebar(grid, sidebar))
        sys.stdout.flush()
        time.sleep(sec)


# =================================================
# 하이스코어
# =================================================
HIGHSCORE_FILE = "highscore_points.txt"


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
    H, W = len(grid), len(grid[0]) if grid else 0
    if H == 0: return None
    candidates = []
    y_start, y_end = 2, max(2, min(view_height - 3, H - 2))
    for y in range(y_start, y_end + 1):
        walls = _find_walls_in_row(grid[y])
        if not walls: continue
        l, r = walls
        if (r - 1) - (l + 1) >= 4:
            candidates.append((y, l + 1, r - 1))

    if not candidates: return None
    y, l, r = random.choice(candidates)
    return y, random.randint(l, r)


def make_car_cells(car_sprite_lines, car_x, car_y):
    cells = set()
    for dy, line in enumerate(car_sprite_lines):
        for dx, ch in enumerate(line):
            if ch != " ": cells.add((car_x + dx, car_y + dy))
    return cells


# =================================================
# 6. 메인 게임 (Hard Mode)
# =================================================
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

    start_index = find_start_index(lines)
    goal_abs_y = find_goal_abs_y(lines)

    base_car = player.car_frame()
    car_str = rotate_sprite_180(base_car)
    car_sprite_lines = car_str.split("\n")
    car_h = len(car_sprite_lines)
    car_w = max((len(l) for l in car_sprite_lines), default=0)

    view_height = 28

    # 미사일 모양 및 설정
    MISSILE_SHAPE = "<===="
    missile_len = len(MISSILE_SHAPE)

    highscore = load_highscore()

    def init_start_state():
        scroll_i = max(0, start_index - 5)
        v = lines[scroll_i: scroll_i + view_height]
        sy = find_start_line_screen_y(v)
        car_y = max(0, sy - car_h)
        last_bounds = get_road_bounds_safe(v, car_y, car_w, car_h)
        car_x = (last_bounds[0] + last_bounds[1]) // 2
        return scroll_i, car_x, car_y, last_bounds

    while True:  # R 다시하기 루프
        TRACK_WIDTH = None
        missiles = []
        items = []
        last_ms_spawn = last_it_spawn = time.time() - 999
        last_mv_time = time.time()

        scroll_i, car_x, car_y, last_bounds = init_start_state()
        start_time = time.time()
        points = 0
        last_sec = 0
        speed_status = "보통"

        countdown_on_map(lines, view_height, scroll_i, car_sprite_lines, car_x, car_y)
        clear_screen()

        ended_kind = None
        ended_reason = ""

        try:
            while scroll_i < len(lines):
                now = time.time()
                current_view = lines[scroll_i: scroll_i + view_height]
                if not current_view: break

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
                    delay, speed_status = 0.09, "보통"
                elif elapsed < 30:
                    delay, speed_status = 0.07, "빠름"
                else:
                    delay, speed_status = 0.055, "매우 빠름"

                left, right, esc = get_key_state()
                if esc:
                    show_cursor()
                    return

                # 좌표 이동 처리 (먼저 이동시키고 검증)
                mn, mx = get_road_bounds_safe(current_view, car_y, car_w, car_h, last_bounds)
                last_bounds = (mn, mx)

                proposed_x = car_x
                moved = False
                if now - last_mv_time >= delay:
                    if left and not right:
                        proposed_x -= 1
                        moved = True
                        last_mv_time = now
                    elif right and not left:
                        proposed_x += 1
                        moved = True
                        last_mv_time = now

                # 안전 장치
                if proposed_x < mn: proposed_x = mn
                if proposed_x > mx: proposed_x = mx

                # [수정] 벽 충돌 시 즉시 게임 오버 처리
                if moved and proposed_x != car_x:
                    if car_hits_wall(grid, proposed_x, car_y, car_sprite_lines):
                        ended_kind = "GAME OVER"
                        ended_reason = "벽에 충돌"
                        break

                elif car_hits_wall(grid, car_x, car_y, car_sprite_lines):
                    ended_kind = "GAME OVER"
                    ended_reason = "벽에 충돌"
                    break

                car_x = proposed_x

                # 미사일 생성
                if now - last_ms_spawn >= 1.2 and W > 0 and H > 0:
                    cands = []
                    for y in range(2, max(2, min(view_height - 3, H - 2))):
                        wals = _find_walls_in_row(grid[y])
                        if wals:
                            l, r = wals
                            rl, rr = l + 1, r - 1
                            if rr - rl + 1 >= missile_len + 1:
                                cands.append((y, max(rl, rr - missile_len)))
                    if cands:
                        sy, sx = random.choice(cands)
                        missiles.append({"x": float(sx), "abs_y": scroll_i + sy})
                        last_ms_spawn = now

                # 아이템 생성
                if now - last_it_spawn >= 0.9 and W > 0 and H > 0:
                    sp = choose_item_spawn(current_view, view_height)
                    if sp:
                        sy, sx = sp
                        it = random.choice(ITEMS)
                        items.append({"x": sx, "abs_y": scroll_i + sy, "ch": it["ch"], "score": it["score"]})
                        last_it_spawn = now

                car_cells = make_car_cells(car_sprite_lines, car_x, car_y)

                # 아이템 처리
                alive_items = []
                for it in items:
                    sy = it["abs_y"] - scroll_i
                    if 0 <= sy < H:
                        if 0 <= it["x"] < W: grid[sy][it["x"]] = it["ch"]
                        if (it["x"], sy) in car_cells:
                            points = max(0, points + it["score"])
                            continue
                    alive_items.append(it)
                items = alive_items

                # 미사일 처리
                alive_missiles = []
                hit_missile = False
                for m in missiles:
                    m["x"] -= 2.0
                    sy = int(m["abs_y"] - scroll_i)
                    if 0 <= sy < H:
                        mx_int = int(m["x"])
                        m_cells = set()
                        for k, ch in enumerate(MISSILE_SHAPE):
                            xx = mx_int + k
                            if 0 <= xx < W and ch != " ": m_cells.add((xx, sy))

                        if car_cells & m_cells: hit_missile = True

                        for k, ch in enumerate(MISSILE_SHAPE):
                            xx = mx_int + k
                            if 0 <= xx < W: grid[sy][xx] = ch

                    if m["x"] > -missile_len: alive_missiles.append(m)
                missiles = alive_missiles

                # [수정] 미사일 충돌 시 즉시 게임 오버
                if hit_missile:
                    ended_kind = "GAME OVER"
                    ended_reason = "미사일 피격"
                    break

                draw_sprite_on_grid(grid, car_x, car_y, car_sprite_lines)

                # GOAL
                if scroll_i + car_y + car_h - 1 >= goal_abs_y:
                    ended_kind, ended_reason = "GOAL", ""
                    break

                # ✅ [NEW] 미니맵 안 잘리게 mini_view_h 자동 계산 및 정보 표시
                info_lines = [
                    "",
                    "Items:",
                    "  ★ = +5",
                    "  ● = +3",
                    "  ▲ = -2",
                    "",
                    "Hard Mode:",
                    "  [!] 미사일=즉시 종료",
                    "",
                    "Controls:",
                    "  A/D 또는 ←/→",
                    "  ESC 종료",
                ]
                base_sidebar = build_score_box(points, highscore, sec, speed_status) + [""]

                # minimap(타이틀/테두리/바닥/progress) = +4줄 여유 필요
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

            # 결과 처리
            if ended_kind is None: ended_kind, ended_reason = "GAME OVER", "END"
            final_speed = "FINISH" if ended_kind == "GOAL" else speed_status

            show_cursor()
            highscore = show_hard_result(ended_kind, points, highscore, sec, final_speed, reason=ended_reason)
            hide_cursor()

            choice = wait_result_choice()
            if choice == "restart": continue
            show_cursor()
            return

        except KeyboardInterrupt:
            show_cursor()
            return

    # 안전하게 커서 복구
    show_cursor()


# main.py 호환용
def screen_two():
    return screen_two_hard()