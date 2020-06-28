# -*- coding: utf-8 -*-

import random
from Gobang_ import *


class AI:
    def __init__(self, field):
        self.field = field  # 15*15二维列表棋盘（0为空，1为黑子，2为白子）

    def go(self, x: int, y: int) -> (int, int):  # 参数为当前落子点, 返回AI落子点, 参数x==None, y==None说明棋盘无子
        """AI执行"""
        new_x, new_y = (1, 1)

        return new_x, new_y
        # AI落子会跳过落子位置重复的检查，所以要自己做判断
