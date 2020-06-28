# -*- coding: utf-8 -*-

from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import Qt, pyqtSignal, QThread, QObject, QTimer
from random import randint
from network import *


class ServerMessageHandle(QThread):
    join = pyqtSignal(str)
    go_dice = pyqtSignal(int)
    go_chess = pyqtSignal(int, int)

    def __init__(self, server, connection):
        super().__init__()
        self.server = server
        self.conn = connection

    def run(self):
        while True:
            try:
                message = receive(self.conn)  # 接收消息
                if message is None:
                    continue
                type_ = message.get('type')
                if type_ == 'name':  #
                    user_name = message.get("user_name")
                    print("已连接：" + user_name)
                    self.server.clients[user_name] = self.conn
                elif type_ == 'join':  #
                    self.join.emit(user_name)
                elif type_ == 'chess':  # 玩家落子
                    player_num = message.get('player_num')
                    self.go_dice.emit(player_num)
            except ConnectionResetError:  # 掉线
                print(traceback.print_exc())
                break
            except OSError:
                print(traceback.print_exc())
                break


class GameFlyingChessServer(QWidget):
    def __init__(self):
        super().__init__()
        #self.ip = "192.168.31.213"
        self.ip = "10.230.11.57"
        self.port = "9213"
        self.name = '服务器'
        try:
            file = open("config_server.txt", 'rb')
            data = file.read().decode().strip()
            file.close()
            self.ip, self.port = data.split('\r\n')
        except OSError:
            pass
        print('ip ({}), port ({})'.format(self.ip, self.port))

        self.server = None
        self.clients = {}
        self.connections = []

        self.human_players = {}
        self.players = []
        self.dict_chess = {}

        self.current_player_num = 0
        self.count_win = 0
        self.order = []
        #   [type, player_num, chess_num, pos]
        #       type = "move", "terminate", "start", "die", "no"
        #       player_num = int
        #       chess_num = int
        #       pos =  _position

        self.AI = AI(self)
        self.AI.go.connect(self.move_chess)

        self.start_()
        self.initialize()

    def start_(self):
        for p in range(4):
            player = Player(p)
            self.players.append(player)
            for n in range(4):
                chess = Chess(p, n)
                player.chess.append(chess)
                self.dict_chess[(p, n)] = chess
        self.current_player_num = 0

    def send_(self, message, connection):
        if isinstance(connection, str):
            connection = self.clients[connection]
        send(connection, message)

    def send_to_all(self, message):
        for player in self.players:
            if player.user_name != "#computer":
                self.send_(message, player.user_name)

    def initialize(self):
        try:
            self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server.settimeout(60)
            self.server.bind((self.ip, int(self.port)))  # 绑定输入的地址、端口
            self.server.listen(2)
            print('info', "等待连接...")
            self.thread_wait_connection = new_thread(self.connect)
        except Exception:
            print(traceback.print_exc())

    def connect(self):
        while True:
            try:
                conn, addr = self.server.accept()
                self.connections.append(conn)
                message_handle = ServerMessageHandle(self, conn)
                message_handle.join.connect(self.join_room)
                message_handle.go_dice.connect(self.go_dice)
                message_handle.go_chess.connect(self.move_chess)
                message_handle.start()
                print('info', "已连接-地址：{}".format(str(addr)))
                self.send_(to_message('g.fc', command='info', text="已成功连接到服务器\r\n"), conn)
                self.send_(to_message('g.fc', command='name', sender_name=self.name), conn)
            except socket.timeout:
                print("### timeout ###")
            except ConnectionResetError:
                print("### 远程主机关闭连接 ###")
                break
            except OSError:
                print(traceback.print_exc())
                break
        print('info', "退出连接")

    def join_room(self, user_name):
        """加入房间"""
        num_of_players = len(self.human_players)
        if num_of_players == 0:  # 新建房间
            self.send_(to_message("g.fc", command="join", code=0), user_name)
            self.players[0].user_name = user_name
            self.human_players[user_name] = 0
            print("{}加入房间，编号为0".format(user_name))
        elif 1 <= num_of_players <= 1:  # 加入已有的房间
            self.send_(to_message("g.fc", command="join", code=1), user_name)
            self.players[2].user_name = user_name
            self.human_players[user_name] = 2
            print("{}加入房间，编号为2".format(user_name))
            # 开始游戏
            self.send_number()
            QTimer.singleShot(1000, self.send_start_pos)
            QTimer.singleShot(2000, self.start_game)
        else:  # 房间已满
            self.send_(to_message("g.fc", command="join", code=2), user_name)

    def send_number(self):
        """发送玩家对应的编号"""
        lis = []
        for player in self.players:
            lis.append(player.user_name)
        self.send_to_all(to_message("g.fc", command="number", list=lis))

    def send_start_pos(self, positions=None):
        if positions is None:
            positions = [["home", "home", "home", "home"],
                         ["home", "home", "home", "home"],
                         ["home", "home", "home", "home"],
                         ["home", "home", "home", "home"]]
        for p in range(4):
            for num in range(4):
                pos = positions[p][num]
                if pos:
                    self.dict_chess[(p, num)].position = pos
        self.send_to_all(to_message("g.fc", command="positions", list=positions))

    def start_game(self):
        """开始游戏"""
        self.send_to_all(to_message("g.fc", command="start"))
        print("游戏开始")
        self.current_player_num = -1
        self.next_turn()

    def turn_start(self):
        """回合开始"""
        self.send_to_all(to_message("g.fc", command="turn", player_num=self.current_player_num))

    def send_dice_result(self, can_move, point):
        """反馈色子点数"""
        self.send_to_all(to_message("g.fc", command="dice", player_num=self.current_player_num,
                                    can_move=can_move, point=point))

    def send_move_result(self):
        """反馈行动结果"""
        self.send_to_all(to_message("g.fc", command="move", order=self.order))
        self.order = []

    def next_turn(self):
        if self.players[self.current_player_num].diceTime == 0:  # 当前玩家没有掷色子机会则下一玩家开始
            self.current_player_num += 1
            if self.current_player_num > 3:
                self.current_player_num = 0
            player = self.players[self.current_player_num]
            if player.score == 4:
                return self.next_turn()
            player.diceTime += 1  # 回合开始时增加一次掷色子机会
        if self.players[self.current_player_num].point != 6:
            print("\n玩家{}({})回合开始".format(self.current_player_num, self.players[self.current_player_num].user_name))
        else:
            print()
        self.turn_start()
        if self.players[self.current_player_num].user_name == "#computer":  # 电脑回合则AI行动
            print("\t电脑行动，编号", self.current_player_num)
            QTimer.singleShot(1000, self.computer_dice)

    def go_dice(self, player_num):
        """服务器掷色子"""
        player = self.players[player_num]
        if self.current_player_num == player.player_num and player.diceTime > 0:
            player.diceTime -= 1  # 可掷色子次数-1
            point = randint(1, 6)
            player.point = point
            print("\t玩家{}掷出{}".format(player.player_num, player.point), end="\t|\t")
            can_move = player.exam_can_move()  # 判断是否有子可动
            self.send_dice_result(can_move, point)
            if can_move:
                return point
            else:
                QTimer.singleShot(500, self.next_turn)
                return False

    def move_chess(self, player_num, num):
        """服务器移动棋子"""
        print("玩家{}移动棋子{}".format(player_num, num), end="\t|\t")
        player: Player = self.players[player_num]
        try:
            if player_num == self.current_player_num:
                chess: Chess = self.dict_chess[(player_num, num)]
                point = player.point
                current_pos = chess.position
                player_num = chess.player_num
                print("当前位置{}，点数{}，".format(current_pos, point), end="  ")

                if current_pos == "home":  # 家里出发
                    if player.canStart:
                        position = "start"
                        self.order.append(("start", player_num, num, position))
                    else:
                        return self.order.append(("no", player_num, num, "home"))
                else:
                    position = self.get_end_pos(player, chess)
                    if position == "t6":  # 正好到达终点
                        position = "finished"
                        chess.terminate()
                        self.order.append(("terminate", player_num, num, "finished"))
                        player.score += 1
                        if player.score == 4:
                            self.order.append(("win", player_num, num, "finished"))
                            self.count_win += 1
                    else:
                        self.order.append(("move", player_num, num, position))
                player.turn_over()
                print('最终位置', position, end="")
                chess.position = position
                self.exam_eat(chess)
                self.send_move_result()
                if self.count_win < 3:
                    self.next_turn()  # 进入下个回合
                else:
                    print("\n游戏结束")
            else:
                return
        except Exception:
            print(traceback.print_exc())

    def get_end_pos(self, player, chess):
        player_num = chess.player_num
        current_pos = chess.position
        point = player.point
        if current_pos[0] == "t":  # 终点跑道
            pos = int(current_pos[-1])
            pos += point
            if pos > 6:  # 超过终点往回走
                pos = 12 - pos
            position = "t" + str(pos)
            return position
        elif current_pos is "start" or current_pos[0] == "n":
            if current_pos == "start":  # 起点出发
                pos = START[player_num] - 1
            else:  # 环形跑道上
                pos = int(current_pos[-2:])
            pos += point
            if pos - point <= TERMINAL[player_num] < pos:  # 超过终点的入口则转入终点跑道
                position = "t" + str(pos - TERMINAL[player_num])
            else:
                if pos > 51:  # 编号超过一圈重头开始计
                    pos -= 52
                if pos == FLY[player_num]:  # 加油站
                    pos += 12 + 4
                elif pos % 4 == player_num and pos != TERMINAL[player_num]:  # 同色落点飞四格
                    pos += 4
                    if pos == FLY[player_num]:  # 加油站
                        pos += 12
                if pos > 51:  # 编号超过一圈重头开始计
                    pos -= 52
                position = "n{:0>2d}".format(pos)
            return position
        else:
            return current_pos

    def exam_eat(self, chess):
        if chess.position[0] in ("n", "t"):
            for ch in self.dict_chess.values():
                if ch.position == chess.position and ch.player_num != chess.player_num and chess.position[0] == "n":  # 碰到非同色棋子
                    ch.die()
                    self.order.append(("die", ch.player_num, ch.num, "home"))
                # elif ch.position == chess.position and ch.player_num == chess.player_num:  # 碰到同色棋子
                #     ch.overlap(chess)  # 叠子

    def computer_dice(self):
        if self.go_dice(self.current_player_num):
            QTimer.singleShot(1000, self.computer_go)

    def computer_go(self):
        self.AI.computer_go(self.players[self.current_player_num])


class AI(QObject):
    go = pyqtSignal(int, int)

    _unable = -100
    _start = -1
    _eat_enemy = 5
    _eat_friend = -5
    _overlap = 0  # 4
    _jump = 1
    _fly = 3
    _in_ter = -2  # 在终点跑道
    _enter_ter = 2  # 进入终点跑道
    _finish = 2

    def __init__(self, app: GameFlyingChessServer):
        super().__init__()
        self.app = app

    def computer_go(self, player):
        point = player.point
        current_positions = []
        end_positions = []

        try:
            if point == 6:
                if self.leave_home(player):  # 能出门就出门
                    return
            for chess in player.chess:
                current_positions.append(chess.position)
                end_positions.append(self.app.get_end_pos(player, chess))
            options = [0, 0, 0, 0]
            for i in range(4):
                if player.chess[i].position in ("home", "finished"):
                    options[i] += self._unable
                    continue
                d1 = self.exam_eat(player.chess[i], end_positions[i])  # 检查吃子
                d2 = self.exam(current_positions[i], end_positions[i], point)  # 检查跳、飞、进入终点等
                options[i] += d1+d2
            num = options.index(max(options))
            self.go.emit(player.player_num, num)
        except Exception:
            print(traceback.print_exc())

    def exam_eat(self, chess, end_pos):
        if end_pos[0] == "n":
            for ch in self.app.dict_chess.values():
                if ch.position == end_pos and ch.player_num - chess.player_num not in (-2, 2):  # 碰到非同队棋子
                    return self._eat_enemy*ch.quantity
                elif ch.position == end_pos and ch.player_num - chess.player_num in (-2, 2):  # 碰到队友棋子
                    return self._eat_friend*ch.quantity
                elif ch.position == end_pos and ch.player_num == chess.player_num:  # 碰到自己棋子
                    return self._overlap
        return 0

    def exam(self, current_pos, end_pos, point):
        d = 0
        if current_pos == "start":  # 起点出发
            d += self._start
        elif end_pos in ("t6", "finished"):  # 到达终点
            d += self._finish
        elif current_pos[0] == "t":  # 在终点跑道且没到终点
            d += self._in_ter
        elif end_pos[0] == "t":  # 进入终点跑道且没到终点
            d += self._enter_ter
        else:  # 环形跑道上
            distance = int(end_pos[-2:]) - int(current_pos[-2:]) - point
            if distance == 4 or distance == 4 - 52:  # 跳
                d += self._jump
            elif distance == 12 or distance == 12 - 52:  # 飞
                d += self._fly
            elif distance == 16 or distance == 16 - 52:  # 跳+飞
                d += self._fly + self._jump
        return d

    def leave_home(self, player):
        """出门"""
        for chess in player.chess:
            if chess.position == "home":
                self.go.emit(player.player_num, chess.num)
                return True
        return False


class Chess:
    def __init__(self, player_num, chess_num):
        self.player_num = player_num
        self.num = chess_num
        self.position = "home"  # {"home", "start", "finished", "overlap", "n00"-"n51", "t1"-"t6"}
        self.quantity = 1
        self.overlapped_chess=[]

    def start(self):
        self.position = 'start'

    def overlap(self, other):
        self.quantity += other.quantity
        self.overlapped_chess.append(other)
        other.position = 'overlap'

    def terminate(self):
        self.position = 'finished'
        for ch in self.overlapped_chess:
            ch.die()

    def die(self):
        self.position = 'home'
        for ch in self.overlapped_chess:
            ch.die()


class Player:
    def __init__(self, player_num):
        self.user_name = "#computer"
        self.player_num = player_num
        self.point = 0
        self.diceTime = 0
        self.canStart = False
        self.chess = []
        self.score = 0

    def exam_can_move(self):
        if self.point == 6:  # 6点一定可动
            self.canStart = True
            self.diceTime += 1
            return True
        else:
            for chess in self.chess:
                # print(chess.position)
                if chess.position not in ("home", "finished"):
                    return True  # 有可动的子
            else:  # 无子可动
                return False

    def turn_over(self):
        self.canStart = False


if __name__ == '__main__':
    import sys
    App = QtWidgets.QApplication(sys.argv)
    server = GameFlyingChessServer()
    sys.exit(App.exec_())
