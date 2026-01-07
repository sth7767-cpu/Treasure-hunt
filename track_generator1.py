import random

# ===== 문자 정의 =====
OUTSIDE = " "     # 트랙 바깥
V = "│"           # 수직 벽 (직선)
SLASH = "╱"       # 오른쪽 → 왼쪽 커브
BACK = "╲"        # 왼쪽 → 오른쪽 커브
LINE = "═"        # START / GOAL 가로선

START_TEXT = "START !!!!"
GOAL_TEXT = "GOAL !!!!"


def draw_line(rows, y, left, right):
    """
    y번째 줄에서 left~right 사이를 가로선(═)으로 채움
    """
    if 0 <= y < len(rows):
        for x in range(left + 1, right):
            rows[y][x] = LINE


def write_text(rows, y, x, text):
    """
    rows[y]의 x 위치부터 text를 덮어쓰기
    """
    if 0 <= y < len(rows):
        for i, ch in enumerate(text):
            if 0 <= x + i < len(rows[y]):
                rows[y][x + i] = ch


def generate_long_track(width=90, total_rows=900, road_min=16, road_max=24):
    """
    긴 세로 트랙 생성
    """
    # 전체 맵을 공백으로 초기화
    rows = [[OUTSIDE for _ in range(width)] for _ in range(total_rows)]

    # 초기 도로 폭과 위치
    road_w = random.randint(road_min, road_max)
    left = (width - road_w) // 2
    right = left + road_w

    prev_left, prev_right = left, right

    # 커브 제어용 변수
    drift = 0
    drift_target = 0
    seg_len = random.randint(6, 12)
    seg_cnt = 0

    # START / GOAL 위치
    start_y = 5
    finish_y = total_rows - 8

    start_lr = None
    finish_lr = None

    # START / GOAL 글자가 화면 밖으로 안 나가게 여백 확보
    label_space = max(len(START_TEXT), len(GOAL_TEXT)) + 3

    for y in range(total_rows):
        # 도로 폭 랜덤 변화
        if y % 7 == 0:
            road_w += random.choice([-1, 0, 1])
            road_w = max(road_min, min(road_w, road_max))

        # 커브 목표 설정
        if seg_cnt >= seg_len:
            drift_target = random.choice([-2, -1, 0, 0, 1, 2])
            seg_len = random.randint(6, 12)
            seg_cnt = 0
        seg_cnt += 1

        # drift를 목표값으로 천천히 이동
        if drift < drift_target:
            drift += 1
        elif drift > drift_target:
            drift -= 1

        left += drift

        # 오른쪽에 START / GOAL 텍스트 공간 확보
        left = max(3, min(left, width - road_w - 4 - label_space))
        right = left + road_w

        # 벽 문자 결정 (커브인지 직선인지)
        if left > prev_left:
            left_char = BACK
        elif left < prev_left:
            left_char = SLASH
        else:
            left_char = V

        if right > prev_right:
            right_char = BACK
        elif right < prev_right:
            right_char = SLASH
        else:
            right_char = V

        # 벽 그리기
        rows[y][left] = left_char
        rows[y][right] = right_char

        # ★ 핵심 ★
        # START / GOAL 줄에서는 무조건 직선 벽
        if y == start_y or y == finish_y:
            rows[y][left] = V
            rows[y][right] = V

        prev_left, prev_right = left, right

        # START / GOAL 위치 기억
        if y == start_y:
            start_lr = (left, right)
        if y == finish_y:
            finish_lr = (left, right)

    # ===== START 라인 =====
    if start_lr:
        l, r = start_lr
        draw_line(rows, start_y, l, r)
        write_text(rows, start_y, r + 3, START_TEXT)

    # ===== GOAL 라인 =====
    if finish_lr:
        l, r = finish_lr
        draw_line(rows, finish_y, l, r)
        write_text(rows, finish_y, r + 3, GOAL_TEXT)

    return rows


def save_track(rows, filename="track.txt"):
    """
    track.txt로 저장
    """
    with open(filename, "w", encoding="utf-8") as f:
        for row in rows:
            f.write("".join(row) + "\n")


if __name__ == "__main__":
    track = generate_long_track()
    save_track(track)
    print("track.txt 생성 완료!")
