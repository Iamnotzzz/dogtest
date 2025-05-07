import serial
import threading
import time
import json

# ------------------ 定义Secondary_grab变量 ------------------
Secondary_grab = 2  # 默认设置为2

# ------------------ 串口读取线程 ------------------
def read_serial():
    """
    循环读取串口接收到的数据，并将其打印出来。
    """
    while True:
        data = ser.readline().decode('utf-8')  # 从串口读取一行数据并解码
        if data:
            print(f"Received: {data}")         # 如果有数据则打印出来

# ------------------ 发送JSON指令 ------------------
def send_json_commands(ser, commands):
    """
    将一组 JSON 格式的指令逐条发送到串口，并等待 3 秒。
    
    参数：
    - ser: 串口对象
    - commands: 需要发送的 JSON 指令列表
    """
    for cmd in commands:
        json_bytes = json.dumps(cmd).encode('utf-8') + b'\n'  # 将 JSON 转换为字节流并加上换行符
        ser.write(json_bytes)                                # 通过串口发送
        print(f"Sent: {cmd}")
        time.sleep(3)  # 延时 3 秒，避免指令过快导致串口溢出

# ------------------ 主程序入口 ------------------
def main():
    global ser, Secondary_grab

    # ------------------ 初始化串口 ------------------
    # 打开串行端口（这里使用 'COM3' 和 115200 波特率）
    ser = serial.Serial('COM3', baudrate=115200, dsrdtr=None)
    ser.setRTS(False)   # 设置RTS信号
    ser.setDTR(False)   # 设置DTR信号

    # ------------------ 启动串口读取线程 ------------------
    # 创建一个独立线程来持续读取串口数据，避免主线程阻塞
    serial_recv_thread = threading.Thread(target=read_serial)
    serial_recv_thread.daemon = True   # 设置为守护线程，主程序退出时线程自动销毁
    serial_recv_thread.start()         # 启动线程

    # ------------------ 定义 JSON 指令集 ------------------
    json_commands_dict = {
        '1': [  # 如果输入 '1' 执行以下动作
            {"T": 121, "joint": 1, "angle": 90, "spd": 45, "acc": 10},          # 关节1 移动到90度，速度45，加速度10
            {"T": 122, "b": -90, "s": 50, "e": 75, "h": 229, "spd": 45, "acc": 10},  # 多个轴的同步移动
            {"T": 106, "cmd": 3, "spd": 800, "acc": 0},                         # 发送命令 3，速度800，不设加速度
            {"T": 122, "b": 0, "s": 0, "e": 160, "h": 171, "spd": 45, "acc": 10}   # 多轴回到初始状态
        ],
        '2': [  # 如果输入 '2' 执行以下动作
            {"T": 121, "joint": 1, "angle": 90, "spd": 45, "acc": 10},          # 关节1 移动到90度
            {"T": 122, "b": -90, "s": 50, "e": 75, "h": 171, "spd": 45, "acc": 10}  # 多轴移动到指定位置
        ]
    }

    try:
        # ------------------ 主循环 ------------------
        while True:
            command = input("Enter a number (1 or 2): ")  # 等待用户输入 '1' 或 '2'
            
            # 检查输入是否合法
            if command in json_commands_dict:
                Secondary_grab = 2  # 根据要求设置 Secondary_grab 为 2
                send_json_commands(ser, json_commands_dict[command])  # 发送对应的 JSON 指令
            else:
                print("Invalid input. Please enter either 1 or 2.")  # 如果输入不合法则提示
    except KeyboardInterrupt:
        # ------------------ 捕获 Ctrl + C 中断信号 ------------------
        print("\nExiting program...")
    finally:
        # ------------------ 程序结束时关闭串口 ------------------
        ser.close()

# ------------------ 程序入口 ------------------
if __name__ == "__main__":
    main()
