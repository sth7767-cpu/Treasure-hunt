import time

# =====================
# 점수 (1초 = 1점)
# =====================
start_time = time.time()

def get_score():
    return int(time.time() - start_time)

# =====================
# 장애물 클래스
# =====================
class Obstacle:
    def __init__(self, x, y, w, h):
        self.x = x
        self.y = y
        self.w = w
        self.h = h

    def get_hitbox(self):
        return (
            self.x,
            self.y,
            self.x + self.w - 1,
            self.y + self.h - 1
        )

# =====================
# 충돌 판정 (부딪히면 True)
# =====================
def check_collision(player_x, player_y, player_w, player_h, obstacles):
    px1 = player_x
    py1 = player_y
    px2 = player_x + player_w - 1
    py2 = player_y + player_h - 1

    for obs in obstacles:
        ox1, oy1, ox2, oy2 = obs.get_hitbox()

        if (
            px1 <= ox2 and
            px2 >= ox1 and
            py1 <= oy2 and
            py2 >= oy1
        ):
            return True

    return False
