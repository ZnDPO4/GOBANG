from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5.QtCore import Qt, pyqtSignal, QThread, QObject, QTimer
from random import choice
from network import *
from Gobang_ import *


class ServerMessageHandle(QThread):
    join = pyqtSignal(tuple)
    go_chess = pyqtSignal(int, int, int)

    def __init__(self, server, connection: socket.socket):
        super().__init__()
        self.server = server
        self.conn = connection

    def run(self):
        while True:
            try:
                message = receive(self.conn)  # 接收消息
                if message is None:
                    break
                type_ = message.get('type')
                if type_ == 'name':  #
                    user_name = message.get("user_name")
                    addr = self.conn.getpeername()
                    print("已连接用户：" + user_name)
                elif type_ == 'join':  #
                    addr= self.conn.getpeername()
                    self.join.emit(addr)
                elif type_ == 'go':  # 玩家落子
                    num = message.get('num')
                    x = message.get('x')
                    y = message.get('y')
                    self.go_chess.emit(num, x, y)
            except ConnectionResetError:  # 掉线
                print(traceback.print_exc())
                break
            except OSError:
                print(traceback.print_exc())
                break


class GameFlyingChessServer(QWidget):
    def __init__(self):
        super().__init__()
        self.ip = "10.230.11.57"
        self.port = "9213"
        self.name = '服务器'
        self.server = None
        self.clients = {}
        self.players = []
        self.keep_listening = True

        self.field = [[0 for i in range(15)] for j in range(15)]
        self.started = False
        self.player_now = ChessColor.black

        self.start_()
        self.initialize()

    def start_(self):
        pass

    def send_(self, message, addr):
        connection = self.clients[addr]
        send(connection, message)

    def send_to_all(self, message):
        for addr in self.players:
            self.send_(message, addr)

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
                self.clients[addr] = conn
                message_handle = ServerMessageHandle(self, conn)
                message_handle.join.connect(self.join_room)
                message_handle.go_chess.connect(self.go_chess)
                message_handle.start()
                print('info', "已连接-地址：{}".format(str(addr)))
                self.send_(to_message('info', text="已成功连接到服务器\r\n"), addr)
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
        print('info', "退出连接")

    def join_room(self, addr):
        """加入房间"""
        num_of_players = len(self.players)
        if num_of_players == 0:  # 新建房间
            self.send_(to_message("join", code=0), addr)
            self.players.append(addr)
            print("{}加入房间".format(addr))
        elif 1 <= num_of_players <= 1:  # 加入已有的房间
            self.send_(to_message("join", code=1), addr)
            self.players.append(addr)
            print("{}加入房间".format(addr))
            self.keep_listening = False
            QTimer.singleShot(1000, self.start_game)  # 延时一秒开始游戏
        else:  # 房间已满
            self.send_(to_message("join", code=2), addr)

    def go_chess(self, num, x, y):
        color = "黑" if num == ChessColor.black.value else "白"
        print("{}方落子".format(color))
        self.field[x][y] = num
        if exam(self.field, self.player_now, x, y) is True:
            self.started = False
            print("{}方获胜".format(color))
            self.send_win(num)
        self.send_go(num, x, y)

    def start_game(self):
        """发送玩家的执子颜色"""
        for x in range(15):
            for y in range(15):
                self.field[x][y] = 0
        self.player_now = ChessColor.black
        num = choice([1, -1])
        self.send_(to_message("start", number=num), self.players[0])
        self.send_(to_message("start", number=-num), self.players[1])

    def send_go(self, num, x, y):
        """发送落子信息"""
        self.send_to_all(to_message("go", num=num, x=x, y=y))

    def send_ban(self):
        """发送禁手警告"""

    def send_win(self, num):
        """发送获胜消息"""
        self.send_to_all(to_message("win", num=num))


if __name__ == '__main__':
    import sys
    App = QApplication(sys.argv)
    server = GameFlyingChessServer()
    sys.exit(App.exec_())

