# udp_sender.py
import socket
import time
import random

# 初始化 TCP 连接
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect(("127.0.0.1", 6011))
print("Connected to receiver...")

# 模拟发送数据
try:
    while True:
        # 随机生成角度和偏移量
        angle = round(random.uniform(-1.0, 1.0), 2)
        distance = round(random.uniform(-50, 50), 2)
        
        # 构造消息并发送
        message = f"{angle}/{distance}/0/0/0/0/0/0/"
        client_socket.send(message.encode())
        print(f"Sent: {message}")
        
        # 等待1秒再发送
        time.sleep(1)

except KeyboardInterrupt:
    print("终止发送")
finally:
    client_socket.close()
