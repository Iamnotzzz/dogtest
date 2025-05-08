# udp_receiver.py
import socket

# 初始化 Socket
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_ip = "127.0.0.1"  # 本地 IP
server_port = 6011        # 和 `udp_sender.py` 里面一致
server_socket.bind((server_ip, server_port))
server_socket.listen()

print(f"Listening on {server_ip}:{server_port}...")

# 等待连接
client_socket, client_address = server_socket.accept()
print(f"Connected to {client_address}")

while True:
    try:
        # 接收数据
        data = client_socket.recv(1024)
        if data:
            print(f"Received Data: {data.decode()}")
    except Exception as e:
        print(f"Error receiving data: {e}")
        break

client_socket.close()
server_socket.close()
