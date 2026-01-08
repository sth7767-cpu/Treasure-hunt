import random
from typing import Dict, List, Tuple, Optional

# 아이템 풀 (원하면 추가/수정)
ITEM_POOL = [
    {"name": "무적", "effect": "invincible", "symbol": "★"},
    {"name": "2점", "effect": "double_score", "symbol": "◆"},

]

# 트랙 벽(경계)로 취급할 문자들
WALL_CHARS = set(["│", "┃", "|", "╲", "╱", "\\", "/"])


def _find_track_bounds(line: str) -> Optional[Tuple[int, int]]:
    """한 줄에서 트랙의 왼쪽/오른쪽 경계(벽) 위치를 찾음"""
    left = -1
    right = -1

    for i, ch in enumerate(line):
        if ch in WALL_CHARS:
            left = i
            break

    for i in range(len(line) - 1, -1, -1):
        if line[i] in WALL_CHARS:
            right = i
            break

    if left == -1 or right == -1 or right <= left:
        return None
    return left, right


def _place_symbol_in_road(line: str, left: int, right: int, symbol: str) -> Tuple[str, int]:
    """
    도로(left~right) 내부 중앙에 symbol을 '한 글자 치환'으로 배치.
    중앙이 공백이 아니면 중앙 근처의 공백을 찾아서 배치.
    반환: (수정된 line, 실제로 찍힌 x좌표)
    """
    line_list = list(line)
    center = (left + right) // 2

    # 도로 내부 범위
    road_l = left + 1
    road_r = right - 1
    if road_l > road_r:
        return line, -1

    # 1) 중앙이 공백이면 바로 찍기
    if 0 <= center < len(line_list) and line_list[center] == " ":
        line_list[center] = symbol
        return "".join(line_list), center

    # 2) 중앙 근처로 공백 탐색 (좌우로 퍼지며 찾기)
    for d in range(1, max(center - road_l, road_r - center) + 1):
        lx = center - d
        rx = center + d
        if road_l <= lx <= road_r and line_list[lx] == " ":
            line_list[lx] = symbol
            return "".join(line_list), lx
        if road_l <= rx <= road_r and line_list[rx] == " ":
            line_list[rx] = symbol
            return "".join(line_list), rx

    # 3) 공백이 하나도 없으면 그냥 배치 포기
    return line, -1


def add_items_to_track(
    lines: List[str],
    interval: int = 8,
    block_if_contains: str = "═",
    rng_seed: Optional[int] = None
) -> Tuple[List[str], Dict[int, dict]]:
    """
    track.txt lines에 interval 줄마다 아이템을 '트랙 위에만' 표시해서 반환.

    - lines: track.txt에서 읽은 라인 리스트(줄바꿈 포함/미포함 상관없음)
    - interval: 몇 줄마다 만들지 (기본 8)
    - block_if_contains: 이 문자가 들어간 라인은 아이템 생성 스킵(기본 "═")
    - rng_seed: 랜덤 고정하고 싶으면 값 주기

    반환:
      - new_lines: 아이템이 반영된 라인들
      - item_spots: { line_index: {"x": x, "item": item_dict} }
    """
    if rng_seed is not None:
        random.seed(rng_seed)

    item_spots: Dict[int, dict] = {}
    new_lines: List[str] = []

    for idx, raw in enumerate(lines):
        # 줄바꿈 처리: 원본 스타일 유지
        has_nl = raw.endswith("\n")
        line = raw[:-1] if has_nl else raw

        # interval 조건
        if idx > 0 and idx % interval == 0:
            # 특정 문자 포함이면 스킵
            if block_if_contains and (block_if_contains in line):
                new_lines.append(raw)
                continue

            bounds = _find_track_bounds(line)
            if bounds:
                left, right = bounds
                item = random.choice(ITEM_POOL)
                modified, x = _place_symbol_in_road(line, left, right, item["symbol"])

                if x != -1:
                    item_spots[idx] = {"x": x, "item": item}
                    line = modified

        new_lines.append(line + ("\n" if has_nl else ""))

    return new_lines, item_spots


