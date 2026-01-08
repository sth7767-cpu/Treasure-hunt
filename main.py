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


# ==========================================
# 2. 메인 로비 (screen_one)
# ==========================================
def screen_one():
    while True:
        clear_screen()
        # 인트로
        print_centered(get_big_start_text())
        columns, _ = shutil.get_terminal_size()
        print("\n" + "잠시 후 모드 선택 화면으로 이동합니다...".center(columns))
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
                print("     HARD MODE       ".center(columns))
            else:
                print("     NORMAL MODE     ".center(columns))
                print(" >>  HARD MODE    << ".center(columns))

            print("\n" * 5)
            print("[ W: 위 / S: 아래 / SPACE: 선택 ]".center(columns))
            time.sleep(0.15)

            if keyboard.is_pressed('w'):
                selected_index = 0
            elif keyboard.is_pressed('s'):
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
    print_centered(get_big_end_text())

    columns, _ = shutil.get_terminal_size()

    # 점수가 None이면(강제종료 등) 0점으로 처리
    if score is None: score = 0

    print(f"\n[ 최종 점수: {score} ]".center(columns))
    print("\n" + "게임을 계속하시겠습니까? (Y/N)".center(columns))

    while True:
        choice = input("선택 > ".center(columns // 2)).strip().upper()
        if choice == 'Y':
            print("게임을 다시 시작합니다!".center(columns))
            time.sleep(1)
            return True  # 다시 screen_one 루프로 돌아감
        elif choice == 'N':
            print("게임을 종료합니다. 이용해 주셔서 감사합니다.".center(columns))
            return False  # 루프 탈출 -> 종료
        else:
            print("잘못된 입력입니다. Y 또는 N을 입력해주세요.".center(columns))


if __name__ == "__main__":
    screen_one()