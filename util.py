import socket
import hashlib
import struct

def find_port():
    tmp_sc = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    tmp_sc.bind(("", 0))
    tmp_addr, tmp_port = tmp_sc.getsockname()
    tmp_sc.close()
    return tmp_port

def pack(id, flag, data):
    flag_val = 0
    for i in range(4):
        flag_val = flag_val | (flag[i] << i)
    header = struct.pack('ih', id, flag_val)
    return header + data

def unpack(raw_data):
    id, flag_val = struct.unpack("ih", raw_data[0:6])
    flag = []
    for i in range(4):
        flag.append((flag_val >> i) & 1)
    return id, flag, raw_data[6:]

def calc_md5(file, bs):
    md5 = hashlib.md5()
    file.seek(0)
    for block in iter(lambda: file.read(bs), b''):
        md5.update(block)
    return md5.digest()