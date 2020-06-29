# -*- coding: utf-8 -*-

import socket
import threading
from time import time
import traceback
import json


def send(socket_: socket.socket, message):
    content = message.encode()
    length = len(content)
    # print(length)
    head = '#' + str(length).rjust(6, '0') + '#'
    socket_.sendall(head.encode())
    send_len = socket_.send(content)
    print("\t发送：", content)
    # print(send_len)


def receive(socket_: socket.socket):
    try:
        head = socket_.recv(8)
        if not head:  # 空信息说明连接断开
            return None
        print("\t信息头：", head)
        msg_size = int(head.decode().strip('#'))
        received_data = socket_.recv(msg_size)
        if received_data is None:
            return None
        print("\t信息内容：", received_data)
        message: dict = json.loads(received_data)
        # print("信息内容：", message)
        return message
    except OSError:
        print("OSError", traceback.print_exc())
        return None


def to_message(type_, **kw):
    message_dict = {'type': type_, 'time': time()}
    for key in kw.keys():
        if kw[key] is not None:
            message_dict[key] = kw[key]
    return json.dumps(message_dict)


def new_thread(func, *args):
    t = threading.Thread(target=func, args=args, daemon=True)
    t.start()
    return t

