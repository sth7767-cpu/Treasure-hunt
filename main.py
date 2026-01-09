import shutil  # 상단에 import 확인
import keyboard
import os
import time
import shutil  # 터미널 크기를 구하기 위해 추가
import sys
import player
import game
import normal
import hard
import unicodedata


def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')


def get_big_start_text():
    return r"""
███████╗████████╗ █████╗ ██████╗ ████████╗
██╔════╝╚══██╔══╝██╔══██╗██╔══██╗╚══██╔══╝
███████╗   ██║   ███████║██████╔╝   ██║   
╚════██║   ██║   ██╔══██║██╔══██╗   ██║   
███████║   ██║   ██║  ██║██║  ██║   ██║   
╚══════╝   ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝   ╚═╝   
    """

# =================================================
# 터미널 표시 폭(한글=2칸) 유틸
# =================================================
def disp_width(s: str) -> int:
    """터미널 표시 폭 기준 길이(동아시아 Wide/Fullwidth=2칸)"""
    w = 0
    for ch in s:
        if unicodedata.east_asian_width(ch) in ("W", "F"):
            w += 2
        else:
            w += 1
    return w


def truncate_to_width(s: str, max_w: int) -> str:
    """표시 폭 max_w를 넘지 않게 자르기"""
    out = []
    w = 0
    for ch in s:
        ch_w = 2 if unicodedata.east_asian_width(ch) in ("W", "F") else 1
        if w + ch_w > max_w:
            break
        out.append(ch)
        w += ch_w
    return "".join(out)


def pad_right_to_width(s: str, target_w: int) -> str:
    """표시 폭 target_w가 되도록 오른쪽 공백 채우기"""
    cur = disp_width(s)
    if cur >= target_w:
        return s
    return s + (" " * (target_w - cur))





def print_centered(text):
    """ 여러 줄의 텍스트를 화면 정중앙에 예쁘게 출력 """
    columns, lines = shutil.get_terminal_size()
    t_lines = text.strip("\n").split("\n")

    # 세로 중앙 정렬을 위한 빈 줄 계산
    pad_y = max(0, (lines - len(t_lines)) // 2)
    print("\n" * pad_y)

    # 가로 중앙 정렬
    for ln in t_lines:
        print(ln.center(columns))

def print_centered_end(text):
    """ 여러 줄의 텍스트를 한글 너비 보정하여 화면 정중앙에 출력 """
    columns, lines = shutil.get_terminal_size()
    # 터미널 창이 제대로 안잡힐 때를 대비
    if columns < 20: columns = 140

    t_lines = text.strip("\n").split("\n")

    for ln in t_lines:
        # 한글(가~힣) 개수를 세서 그만큼 너비를 더해줌
        k_count = sum(1 for c in ln if ord('가') <= ord(c) <= ord('힣'))
        visual_width = len(ln) + k_count
        padding = max(0, (columns - visual_width) // 2)
        print(" " * padding + ln)


# =================================================
# ✅ 박스 렌더링: 박스는 중앙 고정, 내용은 왼쪽 정렬(한글폭 대응)
# =================================================
def build_info_box_left(box_w: int, content_lines: list[str], left_pad: int = 2) -> str:
    inner_w = box_w - 2

    top = "+" + ("-" * inner_w) + "+"
    bottom = "+" + ("-" * inner_w) + "+"

    def make_line(text: str) -> str:
        if text == "":
            return "|" + (" " * inner_w) + "|"

        usable = max(0, inner_w - left_pad)
        trimmed = truncate_to_width(text, usable)  # ✅ 표시폭 기준 자르기

        left = (" " * left_pad) + trimmed
        left = pad_right_to_width(left, inner_w)   # ✅ 표시폭 기준 패딩
        return "|" + left + "|"

    block_lines = [top]
    for t in content_lines:
        block_lines.append(make_line(t))
    block_lines.append(bottom)
    return "\n".join(block_lines)


def print_block_centered(block: str, columns: int):
    """
    블록을 표시폭 기준으로 중앙 정렬 출력 (세로선 안 흔들림)
    """
    lines = block.split("\n")
    max_w = max(disp_width(ln) for ln in lines) if lines else 0
    left_pad = max(0, (columns - max_w) // 2)
    pad = " " * left_pad
    print("\n".join(pad + ln for ln in lines), end="")





# ==========================================
# 2. 메인 로비 (screen_one)
# ==========================================
def screen_one():
    while True:
        clear_screen()

        # 1. 로고 출력
        print_centered(get_big_start_text())

        columns, _ = shutil.get_terminal_size()

        # 2. 안내 문구 출력 (오른쪽에 공백 추가해서 위치 조절)
        # "    " 공백을 추가하면 그만큼 전체 길이가 길어져서, 글자는 왼쪽으로 이동합니다.
        message = "잠시 후 모드 선택 화면으로 이동합니다..." + "                "

        print("\n" + message.center(columns))

        time.sleep(2)

        # 난이도 선택 메뉴
        selected_index = 0

        def draw_menu():
            clear_screen()
            columns, rows = shutil.get_terminal_size()

            title = "================== SPACE DASH GAME MODE SELECT =================="

            # ✅ 박스 폭: (1) 터미널 폭 제한 + (2) 타이틀 표시폭 기반 최소 폭
            min_box_w = disp_width(title) + 2  # | | 포함 (표시폭 기준)
            box_w = min(72, columns - 4)       # 너무 커지지 않게
            box_w = max(box_w, 46)             # 너무 작아지지 않게
            box_w = max(box_w, min_box_w)      # 타이틀이 절대 줄바꿈 안 나게

            inner_w = box_w - 2

            lines = []
            # ✅ title도 혹시 모를 환경 대비: 표시폭 기준으로 안전하게 잘라 넣기
            lines.append(truncate_to_width(title, inner_w))
            lines.append("")

            if selected_index == 0:
                lines.append(">>  NORMAL MODE  <<")
                lines.append("    HARD MODE")
            else:
                lines.append("    NORMAL MODE")
                lines.append(">>  HARD MODE  <<")

            lines.append("")
            lines.append("-" * inner_w)  # ✅ 내부폭과 정확히 일치 (대충 금지)

            lines.append("난이도 선택")
            lines.append("↑ : 위 , ↓ : 아래")
            lines.append("선택 후 Space")
            lines.append("")
            lines.append("게임 내 조작키")
            lines.append("A: 오른쪽. D: 왼쪽 ← / → 도 가능")

            block = build_info_box_left(box_w=box_w, content_lines=lines, left_pad=3)

            # ✅ 세로 중앙 배치
            block_lines = block.split("\n")
            pad_y = max(0, (rows - len(block_lines)) // 2)

            print("\n" * pad_y, end="")
            print_block_centered(block, columns)

        draw_menu()

        # ✅ 키 입력 있을 때만 갱신(깜빡임 최소)
        while True:
            if keyboard.is_pressed('up') and selected_index != 0:
                selected_index = 0
                draw_menu()
                time.sleep(0.15)

            elif keyboard.is_pressed('down') and selected_index != 1:
                selected_index = 1
                draw_menu()
                time.sleep(0.15)

            elif keyboard.is_pressed('space'):
                break

            time.sleep(0.01)

        clear_screen()
        columns, rows = shutil.get_terminal_size((80, 24))

        # 세로 중앙 계산
        message = "잠시 후 게임이 시작됩니다..."
        top_pad = max(0, rows // 2)

        print("\n" * top_pad + message.center(columns))
        time.sleep(1)

        # 게임 실행
        final_score = 0
        if selected_index == 0:
            final_score = normal.screen_two_normal()
        else:
            final_score = hard.screen_two_hard()  # hard.py 실행

        if final_score == "menu":
            continue

        # 게임이 끝나면 엔딩 화면으로 (재시작 여부 확인)
        if not screen_three(final_score):
            break  # N 선택 시 루프 종료 -> 프로그램 종료



# ==========================================
# 3. 엔딩 화면 (screen_three)
# ==========================================
def screen_three(score):
    clear_screen()
    columns, rows = shutil.get_terminal_size((80, 24))

    if score is None: score = 0

    # 1. 출력할 텍스트 구성 (로고 제외)
    question = "게임을 종료하시겠습니까? (Y/N)"

    # 출력할 총 줄 수 (점수 1줄 + 간격 1줄 + 질문 1줄)
    total_content_h = 3

    # 2. 세로 여백 계산 (전체 높이의 절반에서 내용 절반을 뺌)
    top_pad = max(0, (rows - total_content_h) // 2)

    # 3. 출력 시작
    print("\n" * top_pad)

    # 점수와 질문 출력 (한글 보정 함수 사용)
    print("\n")  # 점수와 질문 사이 한 줄 띄움
    print_centered_end(question)

    while True:
        # 입력창(선택 >) 중앙 정렬 위치 계산
        prompt = "선택 > "
        # 120칸 기준 혹은 터미널 기준 중앙으로 배치
        padding_len = max(0, (columns // 2) - 10)
        final_prompt = " " * padding_len + prompt

        # input 앞에 살짝 줄바꿈을 주어 가독성 향상
        choice = input("\n" + final_prompt).strip().upper()

        if choice == 'N':
            print("\n")
            print_centered_end("게임을 다시 시작합니다!")
            time.sleep(1)
            return True

        elif choice == 'Y':
            print("\n")
            print_centered_end("게임을 종료합니다. 이용해 주셔서 감사합니다.")
            time.sleep(2)
            return False

        else:
            # 잘못 입력했을 때도 중앙에 표시
            print_centered_end("잘못된 입력입니다. Y 또는 N을 입력해주세요.")



if __name__ == "__main__":
    try:
        screen_one()
    except KeyboardInterrupt:
        # 사용자가 Ctrl+C로 강제 종료했을 때
        pass
    finally:
        # [핵심] 프로그램이 어떤 이유로든 종료되면
        # keyboard 라이브러리가 잡고 있는 키보드 후킹을 모두 해제합니다.
        keyboard.unhook_all()