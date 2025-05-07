import serial
import threading
import time
import json
import sys
import signal
from STservo_sdk import PortHandler, sts, COMM_SUCCESS

# ------------------ 全局变量声明 ------------------
global_ser = None           # 保存串口实例
Secondary_grab = None       # 用于存储用户输入的选择，1 或 2

# ------------------ 代码1: 串口数据读取与 JSON 发送 ------------------

def read_serial(ser):
    """
    串口读取线程：
    - 不断监听串口并输出接收到的信息
    """
    while True:
        data = ser.readline().decode('utf-8')
        if data:
            print(f"Received: {data}")

def send_json_commands(ser, commands):
    """
    发送 JSON 命令到串口
    参数：
    - ser: 串口对象
    - commands: JSON 格式的指令列表
    """
    for cmd in commands:
        json_bytes = json.dumps(cmd).encode('utf-8') + b'\n'  # 转换为字节流并加上换行符
        ser.write(json_bytes)                                 # 写入串口
        print(f"Sent: {cmd}")
        time.sleep(3)  # 延时 3 秒

def main_code1():
    """
    主逻辑：
    1. 初始化串口
    2. 启动读取线程
    3. 等待用户输入指令
    """
    global Secondary_grab, global_ser

    # ------------------ 初始化串口 ------------------
    try:
        global_ser = serial.Serial('COM3', baudrate=115200, dsrdtr=None)
    except Exception as e:
        print(f"Failed to open serial port: {e}")
        sys.exit(1)

    # 关闭硬件流控，避免串口阻塞
    global_ser.setRTS(False)
    global_ser.setDTR(False)

    # ------------------ 启动串口读取线程 ------------------
    serial_recv_thread = threading.Thread(target=read_serial, args=(global_ser,))
    serial_recv_thread.daemon = True  # 设置为守护线程
    serial_recv_thread.start()

    # ------------------ 定义 JSON 指令集 ------------------
    json_commands_dict = {
        '1': [
            {"T": 121, "joint": 1, "angle": -90, "spd": 45, "acc": 10},
            {"T": 122, "b": -90, "s": 50, "e": 75, "h": 229, "spd": 45, "acc": 10},
            {"T": 106, "cmd": 3, "spd": 800, "acc": 0},
            {"T": 122, "b": 0, "s": 0, "e": 160, "h": 171, "spd": 45, "acc": 10}
        ],
        '2': [
            {"T": 121, "joint": 1, "angle": -90, "spd": 45, "acc": 10},
            {"T": 122, "b": -90, "s": 50, "e": 75, "h": 171, "spd": 45, "acc": 10}
        ]
    }

    # ------------------ 等待用户输入 ------------------
    try:
        while True:
            command = input("Enter a number (1 or 2): ")
            if command in json_commands_dict:
                Secondary_grab = command  # 更新全局变量
                send_json_commands(global_ser, json_commands_dict[command])
                break
            else:
                print("Invalid input. Please enter either 1 or 2.")
    except KeyboardInterrupt:
        print("\nExiting program...")

# ------------------ 代码2: 舵机控制与动作执行 ------------------

def signal_handler(portHandler, signal, frame):
    """
    信号处理器：
    - 捕获 Ctrl+C 信号
    - 安全关闭串口资源
    """
    print('\nExiting program...')
    portHandler.closePort()
    if global_ser is not None:
        global_ser.close()
    sys.exit(0)

def move_servo_to_position(packetHandler, STS_ID, position_value, speed, acc):
    """
    移动伺服到目标位置
    参数：
    - packetHandler: 数据包处理器
    - STS_ID: 舵机 ID
    - position_value: 目标位置
    - speed: 移动速度
    - acc: 加速度
    """
    sts_comm_result, sts_error = packetHandler.WritePosEx(STS_ID, position_value, speed, acc)
    if sts_comm_result != COMM_SUCCESS or sts_error != 0:
        print("Failed to move to position")

def main_code2():
    """
    主逻辑：
    1. 初始化串口与数据包处理器
    2. 发送位置移动指令
    3. 延迟 5 秒发送 JSON 指令
    4. 移动到初始位置
    """
    global Secondary_grab

    if Secondary_grab != '2':
        print("Secondary_grab is not set to '2'. Exiting main_code2.")
        return

    # ------------------ 初始化设置 ------------------
    STS_ID = 3
    BAUDRATE = 1000000
    DEVICENAME = 'COM4'
    STS_MAXIMUM_POSITION_VALUE = 600
    STS_MINIMUM_POSITION_VALUE = 0
    STS_MOVING_SPEED = 500
    STS_MOVING_ACC = 10

    # ------------------ 初始化端口和数据包处理器 ------------------
    portHandler = PortHandler(DEVICENAME)
    packetHandler = sts(portHandler)

    # 捕获信号
    signal.signal(signal.SIGINT, signal_handler)

    # ------------------ 打开端口并设置波特率 ------------------
    if portHandler.openPort() and portHandler.setBaudRate(BAUDRATE):
        print("Succeeded to open the port and set baudrate")
        
        # 移动到最大位置
        move_servo_to_position(packetHandler, STS_ID, STS_MAXIMUM_POSITION_VALUE, STS_MOVING_SPEED, STS_MOVING_ACC)

        # 等待 5 秒
        time.sleep(5)

        # 发送最后一个 JSON 指令
        final_command = {"T": 122, "b": 0, "s": 0, "e": 160, "h": 171, "spd": 45, "acc": 10}
        send_json_commands(global_ser, [final_command])

        # 移动回到最小位置
        move_servo_to_position(packetHandler, STS_ID, STS_MINIMUM_POSITION_VALUE, STS_MOVING_SPEED, STS_MOVING_ACC)

# ------------------ 程序入口 ------------------
if __name__ == "__main__":
    # 先执行 JSON 指令输入
    main_code1()
    # 如果选择了模式 2，则启动伺服控制
    if Secondary_grab == '2':
        main_code2()
