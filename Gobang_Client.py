# -*- coding: utf-8 -*-

from PyQt5.QtCore import Qt, pyqtSignal, QThread
from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox
from ui.UI_GobangClientWindow import Ui_Gobang_Mainwindow
from network import *
import random
from Gobang_ import *
from Gobang_AI import AI


class ClientMessageHandle(QThread):
    discon = pyqtSignal()
    join = pyqtSignal(int)
    start_game = pyqtSignal(int)
    down = pyqtSignal(int, int, int)
    ban = pyqtSignal(int)
    end = pyqtSignal(int)

    def __init__(self, connection):
        super().__init__()
        self.conn = connection

    def run(self):
        while True:
            message = receive(self.conn)  # 接收消息
            try:
                if message is None:
                    self.discon.emit()
                    break
                type_ = message.get('type')
                if type_ == "info":
                    text = message.get('text')
                    print('info:', text)
                elif type_ == 'join':  #
                    code = message.get('code')
                    self.join.emit(code)
                elif type_ == 'start':  # 获取执子颜色,开始游戏
                    num = message.get('num')
                    self.start_game.emit(num)
                elif type_ == 'go':  # 落子
                    player_num = message.get("num")
                    x = message.get('x')
                    y = message.get('y')
                    self.down.emit(player_num, x, y)
                elif type_ == 'end':  # 结束
                    num = message.get("num")
                    self.end.emit(num)
                elif type_ == 'surrender':  # 认输
                    player_num = message.get("num")
                    self.surrender.emit(player_num)
                elif type_ == 'restart':  # 重开
                    num = message.get("num")
                    self.restart.emit(num)
                elif type_ == 'end':  # 结束游戏
                    self.end.emit()
            except Exception:
                print(traceback.print_exc())
                break


class GobangClient(QMainWindow, Ui_Gobang_Mainwindow):
    sig_send = pyqtSignal()

    def __init__(self):
        super().__init__()
        # ----------------------------------------UI----------------------------------------
        self.setupUi(self)
        self.chess_board.sig_click.connect(self.go_chess)
        self.single_player.triggered.connect(self.start_one_player)
        self.two_player.triggered.connect(self.start_two_player)
        self.online_game.triggered.connect(self.connect_server)
        self.online_game.setEnabled(True)
        # ----------------------------------------GAME----------------------------------------
        self.field = Field()
        self.chess_board.field = self.field
        self.game_type: GameType = None
        self.started = False
        self.can_go = True  # 避免连续多次落子
        self.player_now = ChessColor.black
        self.my_color = ChessColor.none  # 自己的编号
        self.count = 0

    def start_game(self, num):
        self.started = True
        self.my_color = ChessColor(num)
        self.field.clear()
        self.chess_board.clear()
        color = "黑" if num == ChessColor.black.value else "白"
        print("游戏开始,你是{}方".format(color))
        self.statusbar.showMessage("游戏开始,你是{}方".format(color), 5000)
        self.player_now = ChessColor.black  # 黑方先走

    def go_chess(self, x, y):
        """点击棋盘落子"""
        print(self.started, self.can_go, self.player_now, self.my_color)
        if self.started and self.can_go and self.player_now == self.my_color:  # 游戏进行中&&可以行动&&是自己的回合
            width = self.chess_board.width()
            x = x // (width // 15)
            y = y // (width // 15)
            print("坐标", x, y)
            if self.field.get_point(x, y) == 0:
                self.can_go = False
                if self.game_type == GameType.online_game:
                    self.send_chess(x, y)
                elif self.game_type == GameType.one_player:
                    self.chess_down(self.my_color.value, x, y)
                    self.AI_go(x, y)
                elif self.game_type == GameType.two_players:
                    self.chess_down(self.my_color.value, x, y)
                    self.my_color = ChessColor(-self.my_color.value)
                    self.can_go = True

    def chess_down(self, player_num, x, y):
        color = "黑" if player_num == ChessColor.black.value else "白"
        print("{}方落子".format(color))
        self.field.set_point(player_num, x, y)
        self.chess_board.sig_chess_down.emit(x, y)
        if exam(self.field, self.player_now, x, y) is True:
            self.win(player_num)
            return
        self.player_now = ChessColor(-self.player_now.value)  # 玩家切换

    def win(self, player_num):
        color = "黑" if player_num == ChessColor.black.value else "白"
        self.started = False
        print("{}方获胜".format(color))
        self.statusbar.showMessage("{}方获胜".format(color))

    def stop(self):
        self.started = False
        self.statusbar.showMessage("对方断开连接")

    def restart(self):
        if self.started:
            reply = QMessageBox.question(self, "！", "一局游戏没有结束，是否确认重开？")
            if reply == QMessageBox.Yes:
                if self.game_type == GameType.online_game:
                    self.send_quit()
                    self.online_game.setEnabled(True)
                return True  # 重开
            else:
                return False  # 取消
        else:
            return True  # 不在游戏中

    # ----------------------------------------单人游戏----------------------------------------
    def start_one_player(self):
        if self.restart():
            self.game_type = GameType.one_player
            num = random.randint(1, 2)
            self.start_game(num)
            self.AI = AI(self.field)
            if self.my_color == ChessColor.white:  # 玩家执白，AI先走
                self.AI_go(None, None)

    def AI_go(self, x, y):
        if self.started:
            new_x, new_y = self.AI.go(x, y)
            self.chess_down(self.player_now.value, new_x, new_y)
            self.can_go = True

    # ----------------------------------------双人游戏----------------------------------------
    def start_two_player(self):
        if self.restart():
            self.game_type = GameType.two_players
            self.start_game(ChessColor.black.value)

    # ----------------------------------------联机----------------------------------------
    def connect_server(self):
        if self.restart():
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
            self.message_handle.discon.connect(self.disconnect_)
            self.message_handle.join.connect(self.join_room)
            self.message_handle.start_game.connect(self.start_online_game)
            self.message_handle.down.connect(self.get_chess)
            self.message_handle.end.connect(self.end)
            self.message_handle.start()
        except (TimeoutError, ConnectionRefusedError, OSError):
            print(traceback.print_exc())
            self.statusbar.showMessage("无法连接")
            self.online_game.setEnabled(True)

    def disconnect_(self):
        try:
            self.socket.shutdown(2)
            self.socket.close()
            print('disconnected', "已断开连接")
            self.online_game.setEnabled(True)
        except OSError:
            pass

    # ----------------------------------------发送信息----------------------------------------
    def ask_join_room(self):
        """向服务端发送开始游戏请求"""
        send(self.socket, to_message("join"))

    def send_chess(self, x, y):
        """向服务端发送落子位置"""
        message = to_message("go", num=self.my_color.value, x=x, y=y)
        send(self.socket, message)

    def send_quit(self):
        """向服务端发送退出信号"""
        send(self.socket, to_message("quit"))
        self.disconnect_()

    # ----------------------------------------接受信息响应函数----------------------------------------
    def start_online_game(self, num):
        self.game_type = GameType.online_game
        self.start_game(num)

    def join_room(self, code):
        """从服务端接收加入房间信息"""
        if code == 0:  # 新建房间
            print("新建房间成功")
            self.statusbar.showMessage("新建房间成功")
        elif code == 1:  # 加入房间
            print("加入房间成功")
            self.statusbar.showMessage("加入房间成功")
        else:  # 拒绝
            print("房间已满")
            self.statusbar.showMessage("房间已满")

    def get_chess(self, num, x, y):
        """从服务端接收落子信息"""
        self.chess_down(num, x, y)
        if self.my_color == self.player_now:  # 接下来是自己回合则可以行动
            self.can_go = True

    def end(self, num):
        """游戏结束"""
        if num in [-1, 0, 1]:  # 胜/平
            self.win(num)
        elif num == -2:  # 一方断开连接
            self.stop()
        self.disconnect_()

    # ----------------------------------------其他----------------------------------------
    def closeEvent(self, event) -> None:
        if self.started:
            reply = QMessageBox.question(self, "！", "游戏正在进行，是否退出？")
            if reply == QMessageBox.Yes:
                event.accept()
            else:
                event.ignore()


if __name__ == '__main__':
    import sys

    App = QApplication(sys.argv)
    client = GobangClient()
    client.show()
    sys.exit(App.exec_())