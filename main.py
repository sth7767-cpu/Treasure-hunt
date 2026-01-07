import os
import time
import shutil  # 터미널 크기를 구하기 위해 추가
import sys


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
    # 터미널 크기 구하기
    columns, lines = shutil.get_terminal_size()

    # 텍스트를 줄 단위로 분리
    text_lines = text.strip().split('\n')
    text_height = len(text_lines)

    # 수직(세로) 중앙 정렬을 위한 빈 줄 계산
    vertical_padding = (lines - text_height) // 2

    # 위쪽 빈 줄 출력
    print('\n' * vertical_padding)

    # 텍스트 수평(가로) 중앙 정렬 후 출력
    for line in text_lines:
        print(line.center(columns))


def screen_one():
    clear_screen()

    # 큰 글씨 가져오기
    big_text = get_big_start_text()

    # 가운데 정렬해서 출력
    print_centered(big_text)

    # 안내 문구도 가운데 정렬
    columns, _ = shutil.get_terminal_size()
    print("\n" + "잠시 후 게임이 시작됩니다...".center(columns))

    time.sleep(2)
    screen_two()

def screen_two():
    clear_screen()

    # --- [추가된 부분] track.txt 파일 읽기 ---
    filename = "track.txt"

    # 1. track.txt 파일 읽기
    if not os.path.exists(filename):
        print(f"오류: {filename} 파일이 없습니다.")
        return

    with open(filename, 'r', encoding='utf-8') as f:
        # 파일 전체를 읽어서 리스트에 담습니다.
        lines = f.readlines()

    # 2. 설정값
    total_lines = len(lines)
    view_height = 20  # 한 번에 화면에 보여줄 줄 수 (화면 크기에 맞춰 조절하세요)

    # 3. 시작 시간 기록
    start_time = time.time()

    print("3초 후 레이싱을 시작합니다!")
    time.sleep(3)

    # 4. 스크롤 루프
    # 전체 줄 수에서 화면 높이만큼 뺀 만큼만 반복하면 됩니다.
    try:
        # 전체 트랙을 스크롤 (화면 높이만큼 뺀 길이까지)
        for i in range(total_lines - view_height):
            clear_screen()

            # --- [시간 계산 로직] ---
            current_time = time.time()
            elapsed_time = current_time - start_time  # 흘러간 시간(초)

            # 조건에 따라 속도(delay) 변경
            if elapsed_time < 15:
                delay = 1.0  # 0~30초: 1초 간격
                status = "속도: 보통 (1.0s)"
            elif elapsed_time < 30:
                delay = 0.5  # 30~60초: 0.5초 간격
                status = "속도: 빠름 (0.5s)"
            elif elapsed_time < 60:
                delay = 0.2  # 60초 이후: 0.2초 간격 (최고 속도)
                status = "속도: 매우 빠름!! (0.2s)"
            else:
                delay = 0.05
                status = "속도: 엄청나게 빠름!!!!!! (0.05s)"
            # ---------------------

            # 화면 출력
            current_view = lines[i: i + view_height]
            for line in current_view:
                print(line, end='')

            # 현재 상태 정보 출력 (선택 사항)
            print(f"\n[경과 시간: {elapsed_time:.1f}초] | {status}")

            # 계산된 속도만큼 대기
            time.sleep(delay)

        print("\n\n=== GOAL 지점에 도착했습니다! ===")

    except KeyboardInterrupt:
        print("\n게임을 종료합니다.")


    screen_three()


def screen_three():
    clear_screen()

    # 1. 큰 글씨(GAME OVER) 출력
    big_text = get_big_end_text()
    print_centered(big_text)

    # 2. 계속하기 질문 가운데 정렬 출력
    columns, _ = shutil.get_terminal_size()
    question = "게임을 계속하시겠습니까? (Y/N)"
    print("\n" + question.center(columns))
    print()  # 줄바꿈

    # 3. Y/N 입력 받기 (반복문으로 올바른 키 입력 유도)
    while True:
        # 입력 프롬프트도 약간 들여쓰기 하거나 그냥 두어도 됩니다.
        choice = input("선택 > ".center(columns // 2)).strip().upper()

        if choice == 'Y':
            print()
            print("게임을 다시 시작합니다!".center(columns))
            time.sleep(1)  # 잠시 대기 후 전환
            screen_two()  # 화면 2로 이동 (재시작)
            return  # 현재 함수 종료

        elif choice == 'N':
            print()
            print("게임을 종료합니다. 이용해 주셔서 감사합니다.".center(columns))
            sys.exit()  # 프로그램 완전 종료

        else:
            print("잘못된 입력입니다. Y 또는 N을 입력해주세요.".center(columns))



if __name__ == "__main__":
    screen_one()