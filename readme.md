# UFTP

高效率多线程文件传输协议 UFTP

作者：[@DylanHuang](https://github.com/CrazyDaveHDY)

## 特性
- 支持大文件多线程传输
- 基于 UDP 协议，连接建立更快，传输效率更高
- 实现确认应答、超时重传、文件 MD5 校验等可靠性保障机制
- 支持同时间一对多传输

## 安装
点击右上角的 `Clone or download` 下载该项目至服务端和客户端

使用 git 命令行：
```console
$ git clone https://github.com/CrazyDaveHDY/CSUAutoSelect.git
```

## 运行

**服务端**

运行如下命令，服务端将监听传输请求：
```console
$ python3 server.py
```

**客户端**

发送文件向服务器：
```console
$ python3 client.py send <address> <filepath>
```

从服务器接收文件：
```console
$ python3 client.py get <address> <filepath>
```