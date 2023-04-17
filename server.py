import socket
import threading
import sys
sys.path.append('..')
from util import *
import conf
from sender import Sender
from reciever import Reciever

control_sc = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
control_sc.bind(('', conf.CONTROL_PORT))
print(f"Bind UDP on {conf.CONTROL_PORT}")

while True:
    data, addr = control_sc.recvfrom(conf.MSS)
    print(f"recieve \"{data.decode('utf-8')}\" from {addr}")
    data = data.decode('utf-8').split(' ')
    data_sc = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    data_sc.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, conf.BUFFER_SIZE)
    data_sc.bind(('', 0))

    # 对新 socket 在初始化中 bind 后才能发送新的 data_port
    if data[0] == 'get':
        sender = Sender(data_sc, addr, data[1])
        control_sc.sendto(str(data_sc.getsockname()).encode(), addr)
        t = threading.Thread(target=sender.start())
        t.start()
    elif data[0] == 'send':
        reciever = Reciever(data_sc, addr, data[1])
        control_sc.sendto(str(data_sc.getsockname()).encode(), addr)
        t = threading.Thread(target=reciever.start())
        t.start()
    else:
        print(f"unknown error: {data[0]}")