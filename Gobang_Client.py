# -*- coding: utf-8 -*-

from PyQt5.QtCore import Qt, pyqtSignal, QThread
from PyQt5.QtWidgets import QApplication, QMainWindow
from ui.UI_GobangClientWindow import Ui_Gobang_Mainwindow
from network import *
import random
from Gobang_ import *
from Gobang_AI import AI


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
                elif type_ == 'go':  # 落子
                    player_num = message.get("num")
                    x = message.get('x')
                    y = message.get('y')
                    self.down.emit(player_num, x, y)
                elif type_ == 'win':
                    player_num = message.get("num")
                    self.win.emit(player_num)
            except Exception:
                print(traceback.print_exc())
                break


class GobangClient(QMainWindow, Ui_Gobang_Mainwindow):
    sig_send = pyqtSignal()

    def __init__(self):
        super().__init__()

        self.setupUi(self)
        self.chess_board.sig_click.connect(self.go_chess)
        self.single_player.triggered.connect(self.start_one_player)
        self.two_player.triggered.connect(self.start_two_player)
        self.online_game.triggered.connect(self.connect_server)
        self.online_game.setEnabled(True)

        self.field = [[0 for i in range(15)] for j in range(15)]
        self.chess_board.field = self.field
        self.game_type = None  # one, two, online
        self.started = False
        self.can_go = True  # 避免连续多次落子
        self.player_now = ChessColor.black
        self.my_color = ChessColor.none  # 自己的编号
        self.count = 0

    def start_game(self, num):
        self.started = True
        self.my_color = ChessColor(num)
        for x in range(15):
            for y in range(15):
                self.field[x][y] = 0
        self.chess_board.clear()
        color = "黑" if num == ChessColor.black.value else "白"
        print("游戏开始,你是{}方".format(color))
        self.statusbar.showMessage("游戏开始,你是{}方".format(color), 5000)
        self.player_now = ChessColor.black  # 黑方先走
        if self.game_type == "one":  # 单人游戏
            self.AI = AI(self.field)
            if self.my_color == ChessColor.white:  # 玩家执白，AI先走
                self.AI_go(None, None)

    def go_chess(self, x, y):
        print(self.started, self.can_go, self.player_now, self.my_color)
        if self.started and self.can_go and self.player_now == self.my_color:
            width = self.chess_board.width()
            x = x // (width // 15)
            y = y // (width // 15)
            print("坐标", x, y)
            if not self.field[x][y]:
                self.can_go = False
                if self.game_type == "online":
                    self.send_chess(x, y)
                elif self.game_type == "one":
                    self.chess_down(self.my_color.value, x, y)
                    self.player_now = ChessColor(-self.player_now.value)  # 玩家切换
                    self.AI_go(x, y)
                elif self.game_type == "two":
                    self.chess_down(self.my_color.value, x, y)
                    self.player_now = ChessColor(-self.player_now.value)  # 玩家切换
                    self.my_color = ChessColor(-self.my_color.value)
                    self.can_go = True

    def chess_down(self, player_num, x, y):
        color = "黑" if player_num == ChessColor.black.value else "白"
        print("{}方落子".format(color))
        self.field[x][y] = player_num
        self.chess_board.sig_chess_down.emit(x, y)
        if exam(self.field, self.player_now, x, y) is True:
            self.started = False
            print("{}方获胜".format(color))
            self.statusbar.showMessage("{}方获胜".format(color))

    # ----------------------------------------单人游戏----------------------------------------
    def start_one_player(self):
        self.game_type = "one"
        num = random.randint(1, 2)
        self.start_game(num)

    def AI_go(self, x, y):
        if self.started:
            new_x, new_y = self.AI.go(x, y)
            self.chess_down(self.player_now.value, new_x, new_y)
            self.player_now = ChessColor(-self.player_now.value)  # 玩家切换
            self.can_go = True

    # ----------------------------------------双人游戏----------------------------------------
    def start_two_player(self):
        self.game_type = "two"
        self.start_game(ChessColor.black.value)

    # ----------------------------------------联机----------------------------------------
    def connect_server(self):
        self.online_game.setEnabled(False)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            file = open("config.json", 'rb')
            data = json.load(file)
            file.close()
            self.ip = data["server_address"]
            self.port = data["port"]
            self.user_name = data["user_name"]
        except OSError:
            print("config.json打开失败")
            self.statusbar.showMessage("config.json打开失败")
            self.online_game.setEnabled(True)
        print('ip ({}), port ({}), 用户名: {}'.format(self.ip, self.port, self.user_name))
        new_thread(self.try_connect)

    def try_connect(self):
        try:
            ip = str(self.ip)
            port = int(self.port)
            self.socket.connect((ip, port))
            send(self.socket, to_message("name", user_name=self.user_name))
            self.statusbar.showMessage("已连接服务端")
            self.ask_join_room()
            self.message_handle = ClientMessageHandle(self.socket)
            self.message_handle.start_game.connect(self.start_online_game)
            self.message_handle.down.connect(self.get_chess)
            self.message_handle.win.connect(self.win)
            self.message_handle.start()
        except (TimeoutError, ConnectionRefusedError, OSError):
            print(traceback.print_exc())
            self.statusbar.showMessage("无法连接")
            self.online_game.setEnabled(True)

    def ask_join_room(self):
        """向服务端发送开始游戏请求"""
        send(self.socket, to_message("join"))

    def send_chess(self, x, y):
        """向服务端发送落子位置"""
        message = to_message("go", num=self.my_color.value, x=x, y=y)
        send(self.socket, message)

    def start_online_game(self, num):
        self.game_type = "online"
        self.start_game(num)

    def get_chess(self, num, x, y):
        """从服务端接收落子信息"""
        self.chess_down(num, x, y)
        self.player_now = ChessColor(-self.player_now.value)  # 玩家切换
        if self.my_color == self.player_now:  # 接下来是自己回合则可以行动
            self.can_go = True

    def win(self, player_num):
        color = "黑" if player_num == ChessColor.black.value else "白"
        self.started = False
        print("{}方获胜".format(color))
        self.statusbar.showMessage("{}方获胜".format(color))


if __name__ == '__main__':
    import sys

    App = QApplication(sys.argv)
    client = GobangClient()
    client.show()
    sys.exit(App.exec_())

