import enum
import traceback


class ChessColor(enum.Enum):
    black = 1  # 黑棋
    white = -1  # 白棋
    space = 0  # 空白
    none = None  # 初始值


class Endpoint(enum.Enum):
    """某一棋形直线上端点的情况"""
    border = -1  # 棋盘边缘
    space = 0  # 空白
    self = 1  # 自己的棋
    opponent = 2  # 对手的棋


class ChessType(enum.Enum):
    """棋形"""
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

    def __repr__(self):
        return str(self.name)


def exam(field, player_color: ChessColor, x, y):  # 棋盘，落子方编号，落子坐标
    """判断四个方向上的棋形"""
    try:
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
                                ahead = field[x + d[0] * k][y + d[1] * k]  # 正向判断
                            else:
                                ahead = field[x - d[0] * k][y - d[1] * k]  # 反向判断
                            if ahead == player_color.value:
                                count += 1  # 计数+1
                            elif ahead == 0:  # 端点空白
                                direc[i] = Endpoint.space
                            else:  # 端点被对手阻断
                                direc[i] = Endpoint.opponent
                        except IndexError:
                            direc[i] = Endpoint.border  # 边界
                if direc[0] != Endpoint.self and direc[1] != Endpoint.self:  # 两头都不是自己的棋
                    if 2 <= count < 5:
                        if direc[0].value in (-1, 2) and direc[0].value in (-1, 2):  # 两头堵死
                            type_ = ChessType(count)
                        elif direc[0].value in (-1, 2) and direc[1].value == 0 or \
                                direc[0].value == 0 and direc[1].value in (-1, 2):  # 一头堵死
                            type_ = ChessType(10 + count)
                        elif direc[0].value == 0 and direc[1].value == 0:  # 两头活
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
        # situation: 四个方向上的棋形，可以以此判断禁手、杀棋等等
        return exam_win(player_color, situation)
    except Exception:
        print(traceback.print_exc())


def exam_win(player_color, situation):
    for type_ in situation:
        if type_ == ChessType.five:  # 五连取胜
            return True
        elif type_ == ChessType.long and player_color == ChessColor.white:  # 白棋长连取胜
            return True
        else:
            continue
    return False

