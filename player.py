if __name__ != "__main__":
    def car_frame():
        exhaust = "v"

        car = [
            ".-.",   # 화면 1번째 줄 (Y=0)
            "|_|",   # 화면 2번째 줄 (Y=1)
            "[_]",   # 화면 3번째 줄 (Y=2)
            " " + exhaust + " " # 화면 4번째 줄 (Y=3)
        ]
        return '\n'.join(car)

    # (나머지 바위, 콘, 벽 함수들은 그대로 유지)
    def get_rock():
        return '\n'.join([" .-. ", "(   )", " `-' "])
    def get_cone():
        return '\n'.join(["  ^  ", " / \\ ", "/___\\"])
    def get_wall():
        return '\n'.join(["|=====|", "|_____|"])

    # (나머지 장애물 함수들은 그대로 두셔도 됩니다)

    # (나머지 바위, 콘, 벽 함수들은 그대로 두세요)
    def get_rock():
        rock = [
            "  .-.  ",
            " (   ) ",
            "  `-'  "
        ]
        return '\n'.join(rock)


    def get_cone():
        cone = [
            "  ^  ",
            " / \\ ",
            "/___\\"
        ]
        return '\n'.join(cone)


    def get_wall():
        wall = [
            "|=====|",
            "|_____|"
        ]
        return '\n'.join(wall)