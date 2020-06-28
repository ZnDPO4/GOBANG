# -*- coding: utf-8 -*-

from PyQt5.QtCore import Qt, pyqtSignal, QThread
from PyQt5.QtWidgets import QApplication, QMainWindow
from ui.UI_GobangClientWindow import Ui_Gobang_Mainwindow
from network import *
import random


class ClientMessageHandle(QThread):
    start_game = pyqtSignal(int)
    down = pyqtSignal(int, int, int)
    ban = pyqtSignal(int)
    win = pyqtSignal(int)

    def __init__(self, connection):
        super().__init__()
        self.conn = connection

    def run(self):
        while True:
            try:
                message = receive(self.conn)  # 接收消息
                if message is None:
                    raise ConnectionResetError
                type_ = message.get('type')
                if type_ == "info":
                    text = message.get('text')
                    print('info:', text)
                elif type_ == 'join':  #
                    code = message.get('code')
                    if code == 0:  # 新建房间
                        print("新建房间")
                    elif code == 1:  # 加入房间
                        print("加入房间成功")
                    else:  # 拒绝
                        pass
                elif type_ == 'start':  # 获取执子颜色,开始游戏
                    num = message.get('number')
                    self.start_game.emit(num)
                elif type_ == 'down':  # 落子
                    player_num = message.get("num")
                    x = message.get('x')
                    y = message.get('y')
                    self.down.emit(player_num, x, y)
            except Exception:
                print(traceback.print_exc())


class GobangClient(QMainWindow, Ui_Gobang_Mainwindow):
    sig_send = pyqtSignal()

    def __init__(self):
        super().__init__()

        self.setupUi(self)
        self.chess_board.sig_click.connect(self.go_chess)
        self.single_player.triggered.connect(self.start_one_player)
        self.two_player.setEnabled(False)
        # self.double_player.triggered.connect()
        self.menu_socket.triggered.connect(self.connect_server)

        self.field = [[0 for i in range(15)] for j in range(15)]
        self.chess_board.field = self.field
        self.game_type = None  # one, two, online
        self.can_go = True  # 避免连续多次落子
        self.player_now = None  # 当前行动回合的玩家编号，两玩家分别1，2表示
        self.my_num = 0  # 自己的编号
        self.count = 0

    def start_game(self, num):
        self.my_num = num
        for x in range(15):
            for y in range(15):
                self.field[x][y] = 0
        self.chess_board.clear()
        color = "黑" if num == 1 else "白"
        print("游戏开始,你是{}方".format(color))
        self.statusbar.showMessage("游戏开始,你是{}方".format(color), 10000)
        self.player_now = 1  # 黑方先走
        if self.game_type == "one" and self.my_num != 1:
            self.AI_go()

    def go_chess(self, x, y):
        if self.player_now == self.my_num and self.can_go:
            width = self.chess_board.width()
            x = x // (width // 15)
            y = y // (width // 15)
            print("坐标", x, y)
            if not self.field[x][y]:
                self.can_go = False
                if self.game_type == "online":
                    self.send_chess(x, y)
                elif self.game_type == "one":
                    self.chess_down(self.my_num, x, y)
                    self.player_now = 3 - self.player_now  # 玩家切换
                    self.AI_go()
                elif self.game_type == "two":
                    pass

    def chess_down(self, player_num, x, y):
        self.field[x][y] = player_num
        self.chess_board.sig_chess_down.emit(x, y)

    # ----------------------------------------单人游戏----------------------------------------
    def start_one_player(self):
        self.game_type = "one"
        num = random.randint(1, 2)
        self.start_game(num)

    def AI_go(self):
        # x, y = self.AI.go()
        self.count += 1
        x, y = (self.count, 2)
        self.chess_down(self.player_now, x, y)
        self.player_now = 3 - self.player_now  # 玩家切换
        self.can_go = True

    # ----------------------------------------联机----------------------------------------
    def connect_server(self):
        self.menu_socket.setEnabled(False)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            file = open("config.json", 'r')
            data = json.load(file)
            file.close()
            self.ip = data["server_address"]
            self.port = data["port"]
            self.user_name = data["user_name"]
        except OSError:
            print("config.json打开失败")
            self.statusbar.showMessage("config.json打开失败")
            self.menu_socket.setEnabled(True)
        print('ip ({}), port ({}), 用户名: {}'.format(self.ip, self.port, self.user_name))
        new_thread(self.try_connect)

    def try_connect(self):
        try:
            ip = str(self.ip)
            port = int(self.port)
            self.socket.connect((ip, port))
            self.send_(to_message("name", user_name=self.user_name))
            self.ask_join_room()
            self.message_handle = ClientMessageHandle(self.socket)
            self.message_handle.start_game.connect(self.start_game)
            self.message_handle.down.connect(self.opponent_go)
            self.message_handle.start()
        except (TimeoutError, ConnectionRefusedError, OSError):
            print(traceback.print_exc())
            self.statusbar.showMessage("无法连接")
            self.menu_socket.setEnabled(True)

    def ask_join_room(self):
        """向服务端发送开始游戏请求"""
        send(self.socket, to_message("join"))

    def send_chess(self, x, y):
        """向服务端发送落子位置"""
        message = to_message("chess", num=self.my_num, x=x, y=y)
        send(self.socket, message)

    def get_chess(self, num, x, y):
        """从服务端接收落子信息"""
        self.chess_down(num, x, y)
        self.player_now = 3 - num  # 玩家切换
        if self.my_num == self.player_now:  # 接下来是自己回合则可以行动
            self.can_go = True


if __name__ == '__main__':
    import sys

    App = QApplication(sys.argv)
    client = GobangClient()
    client.show()
    sys.exit(App.exec_())
