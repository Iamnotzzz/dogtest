import socket
import cv2
import numpy as np
import struct

# 网络配置
HOST_IP = "0.0.0.0"
HOST_PORT = 9999
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((HOST_IP, HOST_PORT))

print(f"Listening for video stream on {HOST_IP}:{HOST_PORT}...")

# 存储帧分片
frame_buffer = {}
expected_chunks = {}

while True:
    # 接收数据
    packet, _ = sock.recvfrom(65536)

    # 确保包的长度足够大
    if len(packet) < 7:
        print("接收到的数据包不完整，丢弃...")
        continue

    # 解包头部信息
    frame_id, chunk_id, total_chunks = struct.unpack('!HHH', packet[:6])
    data = packet[6:]

    # 初始化帧缓冲区
    if frame_id not in frame_buffer:
        frame_buffer[frame_id] = [None] * total_chunks

    # 存储分片
    frame_buffer[frame_id][chunk_id] = data

    # 检查是否收齐所有分片
    if all(part is not None for part in frame_buffer[frame_id]):
        # 拼接完整帧
        complete_frame = b''.join(frame_buffer[frame_id])

        # 显示图像
        frame = cv2.imdecode(np.frombuffer(complete_frame, dtype=np.uint8), cv2.IMREAD_COLOR)
        if frame is not None:
            cv2.imshow('Go2 Camera Stream', frame)

        # 清除缓冲区
        del frame_buffer[frame_id]

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

sock.close()
cv2.destroyAllWindows()

