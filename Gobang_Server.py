# -*- coding: utf-8 -*-

from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5.QtCore import Qt, pyqtSignal, QThread, QObject, QTimer
from random import choice
from network import *
from Gobang_ import *
import typing


class ServerMessageHandle(QThread):
    join = pyqtSignal(tuple)
    go_chess = pyqtSignal(int, int, int)
    surrender = pyqtSignal(tuple)
    ready = pyqtSignal(tuple)
    quit_ = pyqtSignal(tuple)

    def __init__(self, server, connection: socket.socket):
        super().__init__()
        self.server = server
        self.conn = connection
        self.addr = self.conn.getpeername()

    def run(self):
        while True:
            message = receive(self.conn)  # 接收消息
            try:
                if message is None:
                    print("<message_handle> null message", self.addr)
                    self.quit_.emit(self.addr)  # 断开连接
                    break
                type_ = message.get('type')
                if type_ == 'name':  #
                    user_name = message.get("user_name")
                    print("已连接用户：" + user_name)
                elif type_ == 'join':  #
                    self.join.emit(self.addr)
                elif type_ == 'go':  # 玩家落子
                    num = message.get('num')
                    x = message.get('x')
                    y = message.get('y')
                    self.go_chess.emit(num, x, y)
                elif type_ == 'surrender':  # 认输
                    self.surrender.emit(self.addr)
                elif type_ == 'ready':  # 准备
                    self.ready.emit(self.addr)
                elif type_ == 'quit':  # 退出
                    self.quit_.emit(self.addr)
            except ConnectionResetError:  # 掉线
                print("<message_handle> 客户端掉线", self.addr)
                break
            except OSError:
                print(traceback.print_exc())
                break


class GameFlyingChessServer(QWidget):
    def __init__(self):
        super().__init__()
        self.ip = "192.168.31.213"
        self.port = "9001"
        self.name = '服务器'
        self.server = None
        self.clients: typing.Dict[tuple, Player] = {}  # key: addr, value: Player
        self.players: typing.Dict[int, Player]  = {}  # key: num, value: Player
        self.keep_listening = True

        self.field = Field()
        self.started = False
        self.player_now = ChessColor.black

        self.start_()
        self.initialize()

    def start_(self):
        pass

    def send_(self, message, addr):
        connection = self.clients[addr].connection
        send(connection, message)

    def send_to_all(self, message):
        for player in self.clients.values():
            send(player.connection, message)

    def initialize(self):
        try:
            self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server.settimeout(60)
            try:
                file = open("config.json", 'rb')
                data = json.load(file)
                file.close()
                self.ip = data["server_address"]
                self.port = data["port"]
            except OSError:
                print("config.json打开失败")
            print('ip ({}), port ({})'.format(self.ip, self.port))
            self.server.bind((self.ip, int(self.port)))  # 绑定输入的地址、端口
            self.server.listen(3)
            self.keep_listening = True
            print('info', "等待连接...")
            self.thread_wait_connection = new_thread(self.connect)
        except Exception:
            print(traceback.print_exc())

    def connect(self):
        while True:
            try:
                conn, addr = self.server.accept()
                self.clients[addr] = Player(conn, addr)
                message_handle = ServerMessageHandle(self, conn)
                message_handle.join.connect(self.join_room)
                message_handle.go_chess.connect(self.go_chess)
                message_handle.quit_.connect(self.client_quit)
                message_handle.start()
                print('info', "已连接-地址：{}".format(str(addr)))

            except socket.timeout:
                print("### timeout ###")
                if not self.keep_listening:
                    break
            except ConnectionResetError:
                print("### 远程主机关闭连接 ###")
                break
            except OSError:
                print(traceback.print_exc())
                break
            except Exception:
                print(traceback.print_exc())
        print('info', "退出连接")

    def disconnect_(self, addr):
        """断开一个连接"""
        try:
            player = self.clients.pop(addr)
            if player:
                print("disconnect", addr)
                player.connection.shutdown(2)  # 关闭连接
                player.connection.close()
        except KeyError:
            return
        except Exception:
            print(traceback.print_exc())

    def game_over(self, winner_num):
        print("游戏结束")
        self.started = False
        if winner_num in [-1, 0, 1]:
            self.send_end(winner_num)
        else:
            self.send_end(-2)

    def join_room(self, addr):
        """加入房间"""
        num_of_players = len(self.clients)
        print("join room", num_of_players)
        if num_of_players == 1:  # 新建房间
            self.send_(to_message("join", code=0), addr)
            self.clients[addr].room_num = 1
            print("{}加入房间".format(addr))
        elif 2 <= num_of_players <= 2:  # 加入已有的房间
            self.send_(to_message("join", code=1), addr)
            self.clients[addr].room_num = 1
            print("{}加入房间".format(addr))
            self.keep_listening = False
            QTimer.singleShot(1000, self.start_game)  # 延时一秒开始游戏
        else:  # 房间已满
            self.send_(to_message("join", code=2), addr)

    def go_chess(self, num, x, y):
        color = "黑" if num == ChessColor.black.value else "白"
        print("{}方落子".format(color))
        self.field.set_point(num, x,y)
        self.send_go(num, x, y)
        if exam(self.field, self.player_now, x, y) is True:
            print("{}方获胜".format(color))
            self.game_over(num)

    def client_quit(self, addr):
        try:
            self.disconnect_(addr)
            if self.started:
                self.game_over(-2)
                for player in self.players.values():
                    self.disconnect_(player.address)
            else:
                pass
        except Exception:
            print(traceback.print_exc())

    def start_game(self):
        """分配并发送玩家的执子颜色"""
        self.field.clear()
        self.player_now = ChessColor.black
        num = choice([1, -1])
        player_list = list(self.clients.values())
        player_list[0].player_num = num
        player_list[1].player_num = -num
        self.players[num] = player_list[0]
        self.players[-num] = player_list[1]
        send(player_list[0].connection, to_message("start", num=num))
        send(player_list[1].connection, to_message("start", num=-num))
        self.started = True

    def send_go(self, num, x, y):
        """发送落子信息"""
        self.send_to_all(to_message("go", num=num, x=x, y=y))

    def send_ban(self, num):
        """发送禁手警告"""
        send(self.players[num].connection, to_message("ban"))

    def send_end(self, num):
        self.send_to_all(to_message("end", num=num))


class Player:
    def __init__(self, conn=None, addr=None, name=""):
        self.address = addr
        self.connection = conn
        self.user_name = name
        self.player_num = 0
        self.room_num = 0
        self.ready = False


if __name__ == '__main__':
    import sys
    try:
        App = QApplication(sys.argv)
        server = GameFlyingChessServer()
        sys.exit(App.exec_())
    except Exception:
        print(traceback.print_exc())

