import socket
from pynput import keyboard

server_ip = "192.168.1.9"  
server_port = 9990  # 选择合适的端口号

# 创建 UDP 套接字
udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)


print("控制小乌龟的运动：")
print("w - 向上移动")
print("s - 向下移动")
print("a - 向左旋转")
print("d - 向右旋转")
print("q - 停止")
print("按 ESC 键退出")


def on_press(key):
    try:
        if key.char == 'w':
            message = "move_up"
        elif key.char == 's':
            message = "move_down"
        elif key.char == 'a':
            message = "move_left"
        elif key.char == 'd':
            message = "move_right"
        elif key.char == 'q':
            message = "stop"
        else:
            return  # 忽略其他按键
        
        # 发送消息到 ROS 端
        udp_socket.sendto(message.encode(), (server_ip, server_port))
        print(f"发送命令: {message}")
        
    except AttributeError:
        if key == keyboard.Key.esc:  # 按 ESC 键退出
            print("退出程序")
            return False

# 监听键盘按键
with keyboard.Listener(on_press=on_press) as listener:
    listener.join()

# 关闭套接字
udp_socket.close()
