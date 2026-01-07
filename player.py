if __name__ != "__main__":
    
    def car_frame():
        exhaust = " }"

        car = [
            "  _  ",
            " /_\\ ",
            " | | ",
            " \\_/ ",
            "  }} "
        ]
        return '\n'.join(car)


    def get_rock():
        """ 둥근 바위 모양 """
        rock = [
            " (x) "
        ]
        return '\n'.join(rock)


    def get_cone():
        """ 공사중 라바콘(고깔) 모양 """
        cone = [
            "  ^  ",
            " /_\\ "
        ]
        return '\n'.join(cone)


    def get_wall():
        """ 가로로 긴 벽돌담 모양 """
        wall = [
            "|===|"
        ]
        return '\n'.join(wall)
