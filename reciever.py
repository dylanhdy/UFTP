import socket
import threading
import conf
import time
import struct
from util import *

class Reciever():

    def __init__(self, data_sc, dest_addr, file_path):
        self.sc = data_sc
        self.dest_addr = dest_addr
        self.file = open(file_path, 'w+b')
        self.lock = threading.Lock()
        self.st_time = time.time()

    def start(self):
        data = struct.pack("ii", conf.BLOCK_SIZE, conf.WINDOW_SIZE)
        self.sc.sendto(pack(0, [0, 1, 0, 1], data), self.dest_addr)

        raw_data, self.dest_addr = self.sc.recvfrom(conf.MSS)
        id, flag_list, data = unpack(raw_data)
        self.size, self.block_num, self.md5 = struct.unpack("ii16s", data)
        self.thread_num = min(conf.RECIEVE_THREAD, self.block_num)
        print(f"ready to recieve data, {self.size} bytes, {self.block_num} blocks")

        self.rec_queue = []
        self.rec_list = [False] * self.block_num
        self.rec_num = 0
        self.write_num = 0

        for thread_id in range(self.thread_num):
            self.rec_thread = threading.Thread(
                target=self.rec_data, name=f'rec_thread_{thread_id}')
            self.rec_thread.start()
        self.write_thread = threading.Thread(
            target=self.write_data, name='write_thread')
        self.write_thread.start()

    def rec_data(self):
        while True:
            # rwnd = conf.BUFFER_SIZE - (self.rec_num - self.write_num)
            # if rwnd == 0:
            #     continue

            # 接收数据包
            try:
                rec_data, self.dest_addr = self.sc.recvfrom(conf.MSS)
                id, flag_list, data = unpack(rec_data)
            except socket.error:
                break
            self.lock.acquire()
            if self.rec_list[id] == False:
                self.rec_queue.append([id, data])
                self.rec_list[id] = True
                self.rec_num += 1
                if conf.DEBUG:
                    print(f'get ID: {id}, {self.rec_num} / {self.block_num}')
                # elif self.rec_num % 500 == 0:
                #    print(f'get {self.rec_num} / {self.block_num}, use {time.time() - self.st_time}s.')
            self.lock.release()
            
            # rwnd = conf.BUFFER_SIZE - (self.rec_num - self.write_num)
            # data = rwnd.to_bytes(8, 'big')
            data = b''
            self.sc.sendto(pack(id, [0, 0, 0, 1], data), self.dest_addr)
        
        name = threading.current_thread().name
        print(f"{name} finished")

    def write_data(self):
        while self.write_num < self.block_num:
            flag = False
            self.lock.acquire()
            if len(self.rec_queue) > 0:
                flag = True
                id, data = self.rec_queue[0]
                del self.rec_queue[0]
            self.lock.release()

            if flag == True:
                self.file.seek(id * conf.BLOCK_SIZE)
                self.file.write(data)
                self.write_num += 1

        print(f"All data has benn received, use {time.time() - self.st_time}s.")
        md5_code = calc_md5(self.file, conf.BLOCK_SIZE)
        print(self.md5)
        if self.md5 == md5_code:
            print(f"md5 check successed: {md5_code}")
        else:
            print(f"md5 check failed: {md5_code}")
        self.file.close()
        self.sc.close()