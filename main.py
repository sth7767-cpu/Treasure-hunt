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

def get_big_end_text():
    return r"""
 ██████╗  █████╗ ███╗   ███╗███████╗    ██████╗ ██╗   ██╗███████╗██████╗ 
██╔════╝ ██╔══██╗████╗ ████║██╔════╝    ██╔═══██╗██║   ██║██╔════╝██╔══██╗
██║  ███╗███████║██╔████╔██║█████╗      ██║   ██║██║   ██║█████╗  ██████╔╝
██║   ██║██╔══██║██║╚██╔╝██║██╔══╝      ██║   ██║╚██╗ ██╔╝██╔══╝  ██╔══██╗
╚██████╔╝██║  ██║██║ ╚═╝ ██║███████╗    ╚██████╔╝ ╚████╔╝ ███████╗██║  ██║
 ╚═════╝ ╚═╝  ╚═╝╚═╝     ╚═╝╚══════╝     ╚═════╝   ╚═══╝  ╚══════╝╚═╝  ╚═╝
    """



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
        while True:
            clear_screen()
            print("\n" * 5)
            print("====== RACING GAME MODE SELECT ======".center(columns))
            print("\n" * 3)

            if selected_index == 0:
                print(" >>  NORMAL MODE  << ".center(columns))
                print()
                print("     HARD MODE       ".center(columns))
            else:
                print("     NORMAL MODE     ".center(columns))
                print()
                print(" >>  HARD MODE    << ".center(columns))

            print("\n" * 5)

            # 조작 가이드 변경: 방향키
            print("[ ↑: 위 / ↓: 아래 / SPACE: 선택 ]".center(columns))
            time.sleep(0.15)

            if keyboard.is_pressed('up'):
                selected_index = 0
            elif keyboard.is_pressed('down'):
                selected_index = 1
            if keyboard.is_pressed('space'): break

        print("\n" + "잠시 후 게임이 시작됩니다...".center(columns))
        time.sleep(1)

        # 게임 실행
        final_score = 0
        if selected_index == 0:
            final_score = normal.screen_two()  # normal.py 실행
        else:
            final_score = hard.screen_two_hard()  # hard.py 실행

        # 게임이 끝나면 엔딩 화면으로 (재시작 여부 확인)
        if not screen_three(final_score):
            break  # N 선택 시 루프 종료 -> 프로그램 종료



# ==========================================
# 3. 엔딩 화면 (screen_three)
# ==========================================
def screen_three(score):
    clear_screen()
    # 로고 출력
    print_centered_end(get_big_end_text())


    columns, _ = shutil.get_terminal_size()

    if columns < 20: columns = 140
    # 점수가 None이면(강제종료 등) 0점으로 처리
    if score is None: score = 0

    # print("\n" + "게임을 계속하시겠습니까? (Y/N)".center(columns))
    print("\n\n")  # <--- 여기서 2줄 띄워줍니다
    print_centered_end("게임을 계속하시겠습니까? (Y/N)")

    while True:
        print("\n\n")  # <--- 여기서 2줄 띄워줍니다

        # 입력창(선택 >)도 중앙 정렬을 위해 padding 계산
        prompt = "선택 >" + "             "

        # (화면 중앙) - (글자 길이 정도) 위치 계산
        # 여기서 숫자 4를 10, 20 등으로 키우면 더 왼쪽으로 이동합니다.
        padding_len = max(0, (columns // 2) - 20)

        # 공백 + "선택 > " 형태의 문자열 생성
        final_prompt = " " * padding_len + prompt

        choice = input(final_prompt).strip().upper()

        if choice == 'Y':
            print("\n\n")  # <--- 여기서 2줄 띄워줍니다
            print_centered_end("게임을 다시 시작합니다!")
            time.sleep(1)
            return True

        elif choice == 'N':
            print("\n\n")  # <--- 여기서 2줄 띄워줍니다
            print_centered_end("게임을 종료합니다. 이용해 주셔서 감사합니다.")
            time.sleep(2)
            return False

        else:
            print("\n\n")  # <--- 여기서 2줄 띄워줍니다
            print_centered_end("잘못된 입력입니다. Y 또는 N을 입력해주세요.")
            print("\n")



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