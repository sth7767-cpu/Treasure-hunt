import keyboard


def get_next_move(x, y):
    next_x, next_y = x, y

    # 상하 조작(w, s) 부분은 삭제하고 좌우(a, d)만 남깁니다.
    if keyboard.is_pressed('a'):
        next_x -= 1  # 왼쪽 이동
    elif keyboard.is_pressed('d'):
        next_x += 1  # 오른쪽 이동

    # w, s 키 관련 코드가 사라졌으므로 next_y는 항상 기존 y와 같습니다.
    return next_x, next_y


def draw_on_canvas(canvas, img_data, x, y):
    for i, line in enumerate(img_data):
        for j, char in enumerate(line):
            if 0 <= y + i < len(canvas) and 0 <= x + j < len(canvas[0]):
                canvas[y + i][x + j] = char
    return canvas