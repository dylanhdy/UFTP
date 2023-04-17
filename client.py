import socket
import threading
import sys
sys.path.append('..')
from util import *
import conf
from sender import Sender
from reciever import Reciever

sc = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sc.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, conf.BUFFER_SIZE)
addr = (sys.argv[2], conf.CONTROL_PORT)

sc.sendto(f"{sys.argv[1]} {sys.argv[3]}".encode('utf-8'), addr)
rec_data, addr = sc.recvfrom(conf.MSS)
addr = (sys.argv[2], eval(rec_data.decode('utf-8'))[1])
print(f"data socket: {addr}")

# 收到新的 socket 地址后再进行初始化
if sys.argv[1] == 'get':
    reciever = Reciever(sc, addr, sys.argv[3])
    t = threading.Thread(target=reciever.start())
    t.start()
elif sys.argv[1] == 'send':
    sender = Sender(sc, addr, sys.argv[3])
    t = threading.Thread(target=sender.start())
    t.start()
else:
    print(f"wrong command: {sys.argv[1]}")