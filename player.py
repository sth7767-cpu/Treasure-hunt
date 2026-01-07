if __name__ != "__main__":

    def car_frame():

        exhaust = " }"

        car = [
            "  .==.  ",
            " //__\\\\ ",
            "[| __ |]",
            " | || | ",
            "[| || |]",
            " \\____/ ",
            "  " + exhaust + exhaust + "   "
        ]
        return '\n'.join(car)


    def get_rock():
        """ 둥근 바위 모양 """
        rock = [
            "   .---.   ",
            "  /     \\  ",
            " (  rock ) ",
            "  `-----'  "
        ]
        return '\n'.join(rock)


    def get_cone():
        """ 공사중 라바콘(고깔) 모양 """
        cone = [
            "     ^     ",
            "    / \\    ",
            "   / _ \\   ",
            "  /_____\\  ",
            " [_______] "
        ]
        return '\n'.join(cone)


    def get_wall():
        """ 가로로 긴 벽돌담 모양 """
        wall = [
            "|WARNING|",
            "|=======|",
            "|_______|"
        ]
        return '\n'.join(wall)




