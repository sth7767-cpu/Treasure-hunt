import time

# =====================
# 게임 상태 클래스
# =====================
class GameState:
    def __init__(self):
        self.start_time = time.time()
        self.last_tick = self.start_time

        self.score = 0
        self.game_over = False

        # 아이템 효과 시간
        self.double_score_until = 0.0

    # =====================
    # 1초에 1점 증가
    # =====================
    def update_score(self):
        now = time.time()
        elapsed = now - self.last_tick

        if elapsed >= 1.0:
            ticks = int(elapsed)
            self.last_tick += ticks

            # 2배 점수 여부
            if now < self.double_score_until:
                self.score += ticks * 2
            else:
                self.score += ticks

    # =====================
    # 아이템 먹기
    # =====================
    def eat_item(self, item_type: str):
        """
        item_type:
          - "double_score"
        """
        if item_type == "double_score":
            self.double_score_until = time.time() + 5  # 5초간 2배

    # =====================
    # 장애물 충돌
    # =====================
    def hit_obstacle(self):
        self.game_over = True

    # =====================
    # 상태 문자열 (출력용)
    # =====================
    def get_status_text(self) -> str:
        status = f"점수: {self.score}"
        if time.time() < self.double_score_until:
            status += " | SCORE x2"
        return status
