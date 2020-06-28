# -*- coding: utf-8 -*-

import random
import enum


class Endpoint(enum.Enum):
    border = -1
    blank = 0
    self = 1
    opponent = 2


class ChessType(enum.Enum):
    none = 0  # 无型
    die2 = 2  # 死二
    die3 = 3  # 死三
    die4 = 4  # 死四
    sleep2 = 12  # 眠二
    sleep3 = 13  # 眠三
    four = 14  # 冲四
    live2 = 22  # 活二
    live3 = 23  # 活三
    live4 = 24  # 活四  **黑白胜手
    five = 5  # 五连  **黑白胜手
    long = 6  # 长连  **白胜手


class AI:
    def __init__(self, field):
        self.field = field  # 15*15二维列表棋盘（0为空，1为黑子，2为白子）

    def go(self, x: int, y: int) -> (int, int):  # 输入当前落子点，返回AI落子点
        """AI执行"""
        new_x, new_y = (-1, -1)

        return new_x, new_y

    def exam(self, player_num, x, y):  # 落子方编号，落子坐标
        """判断四个方向上的棋形"""
        situation = []
        for d in ((1, 0), (1, 1), (0, 1), (1, -1)):
            count = 1  # 记录连成直线的棋子数
            k = 0
            pos = neg = Endpoint.self  # 记录正反两方向的棋子情况
            direc = [pos, neg]
            while True:
                k += 1
                for i in range(2):
                    if direc[i] == Endpoint.self:  # 某一端必须还是自己的棋才会继续检查
                        try:
                            if i == 0:
                                ahead = self.field[x + d[0] * k][y + d[1] * k]  # 正向判断
                            else:
                                ahead = self.field[x - d[0] * k][y - d[1] * k]  # 反向判断
                            if ahead == player_num:
                                count += 1  # 计数+1
                            elif ahead == 0:  # 端点空白
                                direc[i] = Endpoint.blank
                            else:  # 端点被对手阻断
                                direc[i] = Endpoint.opponent
                        except IndexError:
                            direc[i] = Endpoint.border  # 边界
                if pos != Endpoint.self and neg != Endpoint.self:  # 两头都不是自己的棋
                    if 2 <= count < 5:
                        if pos in (-1, 2) and neg in (-1, 2):  # 两头堵死
                            type_ = ChessType(count)
                        elif pos in (-1, 2) and neg == 0 or pos == 0 and neg in (-1, 2):  # 一头堵死
                            type_ = ChessType(10 + count)
                        elif pos == 0 and neg == 0:  # 两头活
                            type_ = ChessType(20 + count)
                        else:
                            type_ = ChessType(0)
                    elif count == 5:
                        type_ = ChessType(5)
                    elif count > 5:
                        type_ = ChessType(6)
                    else:
                        type_ = ChessType(0)
                    situation.append(type_)
                    break  # 跳出这个方向的检验循环
        print(situation)
        return situation
        # return self.exam_win(player_num, situation)

    def exam_win(self, player_num, situation):
        for type_ in situation:
            if type_ == ChessType.five:  # 五连取胜
                return True
            elif type_ == ChessType.long and player_num == 2:  # 白棋长连取胜
                return True
            else:
                continue
        return False
