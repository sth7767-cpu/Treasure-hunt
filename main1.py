import os
import time

def clear():
    os.system("cls" if os.name == "nt" else "clear")

def load_lines(filename="track.txt"):
    with open(filename, "r", encoding="utf-8") as f:
        return [line.rstrip("\n") for line in f]

if __name__ == "__main__":
    lines = load_lines("track.txt")

    SCREEN_H = 28     # 화면에 보이는 줄 수
    speed = 0.03      # 작을수록 빠름

    for start in range(0, max(1, len(lines) - SCREEN_H)):
        clear()
        window = lines[start:start + SCREEN_H]
        print("\n".join(window))
        time.sleep(speed)

    # 마지막 화면 고정
    clear()
    print("\n".join(lines[-SCREEN_H:]))
    print("\n(끝)")
    input("엔터 누르면 종료")
