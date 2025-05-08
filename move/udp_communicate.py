import socket

class UDPClient:
    def __init__(self, ip, port):
        """初始化 UDP 客户端"""
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect((ip, port))
        self.client_socket.settimeout(1)
        print(f"Connected to {ip}:{port}")

    def send_control(self, angle, distance):
        """
        发送控制量到机器狗
        - angle: 目标偏航角度
        - distance: 目标偏移距离
        """
        message = f"{angle:.2f}/{distance:.2f}/0/0/0/0/0/0/"
        try:
            self.client_socket.send(message.encode())
            print(f"Sent: {message}")
        except Exception as e:
            print(f"Send failed: {e}")

    def close(self):
        """关闭连接"""
        self.client_socket.close()
