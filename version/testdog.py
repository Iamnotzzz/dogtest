import cv2
import numpy as np
import socket
import threading
import time
import struct

# 视觉参数
cap = cv2.VideoCapture('/dev/video0')
cap.set(cv2.CAP_PROP_FPS, 60)

# 网络配置
HOST_IP = '192.168.123.17'  # 主机 IP 地址
HOST_PORT = 9999
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# 图像尺寸参数
frame_height = 480
frame_width = 640

# 分片大小 (考虑头部长度)
MAX_DGRAM = 60000 - 7  # 7 字节为帧头长度

# ========== 摄像头处理线程 ==========
def vision_processing():
    frame_id = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            print("无法读取摄像头数据")
            continue

        # 调整尺寸
        frame = cv2.resize(frame, (frame_width, frame_height))

        # 编码图像
        _, buffer = cv2.imencode('.jpg', frame)
        data = buffer.tobytes()

        # 分片处理
        num_chunks = len(data) // MAX_DGRAM + 1

        for i in range(num_chunks):
            start = i * MAX_DGRAM
            end = min((i + 1) * MAX_DGRAM, len(data))
            chunk = data[start:end]

            # 包头信息：帧 ID、片 ID、总片数
            header = struct.pack('!HHH', frame_id % 65535, i, num_chunks)
            sock.sendto(header + chunk, (HOST_IP, HOST_PORT))

        frame_id += 1
        time.sleep(0.03)

        # 终端显示
        print(f"已发送帧 {frame_id} 共 {num_chunks} 片")

# ========== 启动线程 ==========
vision_thread = threading.Thread(target=vision_processing)
vision_thread.start()
vision_thread.join()

cap.release()
sock.close()
cv2.destroyAllWindows()
