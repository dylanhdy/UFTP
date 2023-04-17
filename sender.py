import socket
import threading
import time
import math
import os
import struct
from util import *
import conf

class Sender():

    def __init__(self, data_sc, dest_addr, file_path):
        self.sc = data_sc
        self.dest_addr = dest_addr
        self.lock = threading.Lock()
        self.file = open(file_path, 'rb')
        self.size = os.path.getsize(file_path)
        self.st_time = time.time()

    def start(self):
        raw_data, self.dest_addr = self.sc.recvfrom(conf.MSS)
        id, flag, data = unpack(raw_data)
        self.bs, self.rwnd = struct.unpack('ii', data)
        
        self.block_num = math.ceil(self.size / self.bs)
        self.thread_num = min(conf.SEND_THREAD, self.block_num)
        self.send_queue = []
        self.ack_list = [False] * self.block_num
        self.send_num = 0
        self.ack_num = 0

        md5_code = calc_md5(self.file, self.bs)
        data = struct.pack("ii16s", self.size, self.block_num, md5_code)
        self.sc.sendto(pack(0, [0, 1, 0, 0], data), self.dest_addr)
        print(f"ready to send data, blocksize {self.bs}, \
                rwnd {self.rwnd}, file md5: {md5_code}")

        val0 = self.block_num // self.thread_num
        val1 = self.block_num % self.thread_num
        st_block = 0
        for thread_id in range(self.thread_num):
            ed_block = st_block + val0 + (thread_id < val1)
            send_thread = threading.Thread(
                target=self.send_data,
                name=f'send_thread_{thread_id}',
                args=(st_block, ed_block))
            send_thread.start()
            st_block = ed_block

        rec_thread = threading.Thread(
            target=self.rec_data, name='rec_thread')
        rec_thread.start()
        resend_thread = threading.Thread(
            target=self.resend_data, name='resend_thread')
        resend_thread.start()

    def send_data(self, st_block, ed_block):
        for id in range(st_block, ed_block):
            self.file.seek(id * self.bs)
            data = self.file.read(self.bs)
            if id + 1 != self.block_num:
                flag = [0, 0, 0, 0]
            else:
                flag = [0, 0, 1, 0]

            self.lock.acquire()
            self.send_queue.append([id, time.time()])
            self.lock.release()
            self.sc.sendto(pack(id, flag, data), self.dest_addr)
            self.send_num += 1
            # 用于流量整形，避免发送大量数据导致接收方缓存区溢出
            time.sleep(conf.SEND_DELAY)
            if conf.DEBUG:
                print(f"send ID: {id}, {self.send_num} / {self.block_num}")
            elif self.send_num % 500 == 0:
                print(f"send {self.send_num} / {self.block_num}")

        name = threading.current_thread().name
        print(f"{name} finished, block {st_block}~{ed_block-1} have been sent")

    def resend_data(self):
        while self.ack_num < self.block_num:
            flag = False
            self.lock.acquire()
            if len(self.send_queue) > 0:
                id, last_time = self.send_queue[0]
                if self.ack_list[id] == True:
                    del self.send_queue[0]
                elif time.time() - last_time > conf.RTO:
                    flag = True
                    self.send_queue.append([id, time.time()])
                    del self.send_queue[0]
            self.lock.release()

            if flag == True:
                self.file.seek(id * self.bs)
                data = self.file.read(self.bs)
                if id + 1 != self.block_num:
                    flag = [1, 0, 0, 0]
                else:
                    flag = [1, 0, 1, 0]
                self.sc.sendto(pack(id, flag, data), self.dest_addr)
                if conf.DEBUG:
                    print(f"resend ID: {id}")
            time.sleep(conf.SEND_DELAY)

        name = threading.current_thread().name
        print(f"{name} finished, all data have been recieved.")

    def rec_data(self):
        while self.ack_num < self.block_num:
            raw_data, self.dest_addr = self.sc.recvfrom(conf.MSS)
            id, flag, data = unpack(raw_data)
            # self.rwnd = int.from_bytes(data, 'big')

            self.lock.acquire()
            if self.ack_list[id] == False:
                self.ack_list[id] = True
                self.ack_num += 1
            self.lock.release()

        name = threading.current_thread().name
        print(f"{name} finished, use {time.time() - self.st_time}s.")
        self.file.close()
        self.sc.close()
