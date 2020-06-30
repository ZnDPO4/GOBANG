# -*- coding: utf-8 -*-

__author__ = "zhongx0x20"
__credits__ = ["zhongx0x20", "jxhpdt"]
# __license__ = "GPL"
__version__ = "0.0.1"
__maintainer__ = "zhongx0x20"
__status__ = "Development"

import random
from Gobang_ import *
from enum import Enum


class player(Enum):
    MONDAY = 0
    TUESDAY = 1
    WEDNESDAY = 2
    THURSDAY = 3
    FRIDAY = 4
    SATURDAY = 5
    SUNDAY = 6

class AI:

    myField = None

    def __init__(self, field):
        self.field = field  # 15*15二维列表棋盘（0为空，1为黑子，2为白子）

        for x in range(15):
            for y in range(15):
                self.field[x][y] = 0

    def updateMyFiled(self, x, y, player):
        # TODO
        pass

    def go(self, x: int, y: int) -> (int, int):  # 参数为当前落子点, 返回AI落子点, 参数x==None, y==None说明棋盘无子
        """AI执行"""
        new_x, new_y = (1, 1)

        return new_x, new_y
        # AI落子会跳过落子位置重复的检查，所以要自己做判断
