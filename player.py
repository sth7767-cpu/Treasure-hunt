# player.py
import random


# =========================
# CAR
# =========================
def car_frame():
    exhaust = "^"
    car = [
        ".-.",                 # Y=0
        "|_|",                 # Y=1
        "[_]",                 # Y=2
        "   " + exhaust + " "  # Y=3
    ]
    return "\n".join(car)


# =========================
# OBSTACLE SHAPES
# =========================
def get_rock():
    rock = [
        "  .-.  ",
        " (   ) ",
        "  `-'  "
    ]
    return "\n".join(rock)


def get_cone():
    cone = [
        "  ^  ",
        " / \\ ",
        "/___\\"
    ]
    return "\n".join(cone)


# =========================
# TRACK UTIL
# =========================
def _find_road_bounds(line: str):
    """도로 좌/우 벽 위치 찾기(│ 우선, 없으면 |)"""
    left = line.find('│')
    right = line.rfind('│')
    if left == -1 or right == -1 or left == right:
        left = line.find('|')
        right = line.rfind('|')
    return left, right


def _parse_lines(ascii_art: str):
    lines = ascii_art.split("\n")
    h = len(lines)
    w = max((len(x) for x in lines), default=0)
    lines = [ln.ljust(w) for ln in lines]  # 폭 맞추기
    return lines, w, h


def _stamp(lines, abs_y, x, art_lines):
    """트랙(lines)에 ASCII 아트를 '박아넣기'"""
    h = len(art_lines)
    for dy in range(h):
        yy = abs_y + dy
        if not (0 <= yy < len(lines)):
            continue

        raw = lines[yy]
        has_nl = raw.endswith("\n")
        base = raw[:-1] if has_nl else raw

        base_list = list(base)
        art = art_lines[dy]

        # 범위 보호
        if x < 0 or x + len(art) > len(base_list):
            continue

        for dx, ch in enumerate(art):
            if ch == " ":
                continue
            # 벽 위에는 덮어쓰지 않기
            if base_list[x + dx] in ("│", "|"):
                continue
            base_list[x + dx] = ch

        lines[yy] = "".join(base_list) + ("\n" if has_nl else "")


# =========================
# ✅ NEW: 트랙에 랜덤 장애물 심기
# =========================
def add_obstacles_to_track(lines, interval=12, chance=0.7, safe_start=10):
    """
    safe_start: 트랙 시작에서 최소 몇 줄은 절대 장애물 안 나오게 (0-index 기준)
               예) safe_start=6 -> abs_y 0~5 구간엔 장애물 없음
    """
    obstacle_spots = []

    obstacle_arts = [get_rock(), get_cone()]

    # ✅ 초반 안전구간 보장
    start = max(int(safe_start), 0)
    end = max(start, len(lines) - 10)

    for abs_y in range(start, end, interval):
        if random.random() > chance:
            continue

        art = random.choice(obstacle_arts)
        art_lines, w, h = _parse_lines(art)

        raw = lines[abs_y]
        base = raw[:-1] if raw.endswith("\n") else raw

        left, right = _find_road_bounds(base)
        if left == -1 or right == -1 or left >= right:
            continue

        min_x = left + 1
        max_x = right - 1 - w
        if min_x > max_x:
            continue

        x = random.randint(min_x, max_x)

        _stamp(lines, abs_y, x, art_lines)
        obstacle_spots.append({"y": abs_y, "x": x, "w": w, "h": h})

    return lines, obstacle_spots

