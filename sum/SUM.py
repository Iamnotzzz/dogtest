import serial          # 导入串行通信库
import threading       # 导入线程库
import time            # 导入时间处理库
import json            # 导入JSON序列化和反序列化库
import sys             # 导入系统相关操作库
import signal          # 导入信号处理库
from STservo_sdk import PortHandler, sts, COMM_SUCCESS  # 导入STServo SDK相关模块

# 全局变量定义在最顶部
global_ser = None        # 全局串口对象
Secondary_grab = None    # 全局变量，标识用户输入的指令

# 代码1中的函数和主逻辑
def read_serial(ser):
    """串口读取函数，实时接收数据"""
    while True:
        data = ser.readline().decode('utf-8')  # 从串口读取一行数据并解码为UTF-8格式
        if data:
            print(f"Received: {data}")  # 打印接收到的数据

def send_json_commands(ser, commands):
    """发送JSON指令到串口"""
    for cmd in commands:
        # 将命令转换为JSON格式字节流并通过串口发送
        json_bytes = json.dumps(cmd).encode('utf-8') + b'\n'
        ser.write(json_bytes)
        print(f"Sent: {cmd}")  # 打印已发送的指令
        time.sleep(3)  # 延时3秒，避免过快发送

def main_code1():
    """代码1：串口初始化及指令输入"""
    global Secondary_grab, global_ser

    # 初始化串行端口
    try:
        global_ser = serial.Serial('COM3', baudrate=115200, dsrdtr=None)  # 打开串口COM3，波特率115200
    except Exception as e:
        print(f"Failed to open serial port: {e}")  # 打开串口失败时打印错误信息
        sys.exit(1)  # 退出程序

    # 关闭RTS和DTR信号线
    global_ser.setRTS(False)
    global_ser.setDTR(False)

    # 创建并启动读取线程
    serial_recv_thread = threading.Thread(target=read_serial, args=(global_ser,))
    serial_recv_thread.daemon = True  # 设置为守护线程
    serial_recv_thread.start()

    # 定义JSON指令集，包含两组命令
    json_commands_dict = {
        '1': [
            {"T": 121, "joint": 1, "angle": -90, "spd": 45, "acc": 10},
            {"T": 122, "b": -90, "s": 75, "e": 75, "h": 171, "spd": 45, "acc": 10},
            {"T": 106, "cmd": 4, "spd": 800, "acc": 0},
            {"T": 122, "b": 0, "s": 0, "e": 160, "h": 229, "spd": 45, "acc": 10}
        ],
        '2': [
            {"T": 121, "joint": 1, "angle": -90, "spd": 45, "acc": 10},
            {"T": 122, "b": -90, "s": 90, "e": 75, "h": 171, "spd": 45, "acc": 10}
        ]
    }

    # 持续等待用户输入
    while True:
        try:
            command = input("Enter a number (1 or 2): ")  # 获取用户输入
            if command in json_commands_dict:
                Secondary_grab = command  # 更新用户输入值
                send_json_commands(global_ser, json_commands_dict[command])  # 发送对应指令
                if Secondary_grab == '2':
                    break  # 如果输入为2，退出循环
            else:
                print("Invalid input. Please enter either 1 or 2.")
        except KeyboardInterrupt:
            print("\nExiting program...")
            break

# 代码2中的函数和主逻辑
def signal_handler(portHandler, frame):
    """信号处理函数，安全关闭端口"""
    print('\nExiting program...')
    portHandler.closePort()  # 关闭端口
    if global_ser is not None:
        global_ser.close()  # 关闭串口
    sys.exit(0)

def move_servo_to_position(packetHandler, STS_ID, position_value, speed, acc):
    """移动舵机到指定位置"""
    sts_comm_result, sts_error = packetHandler.WritePosEx(STS_ID, position_value, speed, acc)
    if sts_comm_result != COMM_SUCCESS or sts_error != 0:
        print("Failed to move to position")  # 打印失败信息

def main_code2():
    """代码2：舵机控制及串口操作"""
    STS_ID = 3
    BAUDRATE = 1000000
    DEVICENAME = 'COM4'
    STS_MAXIMUM_POSITION_VALUE = 600
    STS_MINIMUM_POSITION_VALUE = 0
    STS_MOVING_SPEED = 500
    STS_MOVING_ACC = 10

    # 初始化端口和数据包处理器
    portHandler = PortHandler(DEVICENAME)
    packetHandler = sts(portHandler)

    # 捕获SIGINT信号，调用信号处理函数
    signal.signal(signal.SIGINT, signal_handler)

    try:
        if portHandler.openPort():
            print("Succeeded to open the port")
            if portHandler.setBaudRate(BAUDRATE):
                print("Succeeded to change the baudrate")
                move_servo_to_position(packetHandler, STS_ID, STS_MAXIMUM_POSITION_VALUE, STS_MOVING_SPEED, STS_MOVING_ACC)
                time.sleep(5)
                final_command = {"T": 122, "b": 0, "s": 0, "e": 160, "h": 171, "spd": 45, "acc": 10}
                send_json_commands(global_ser, [final_command])
                move_servo_to_position(packetHandler, STS_ID, STS_MINIMUM_POSITION_VALUE, STS_MOVING_SPEED, STS_MOVING_ACC)
            else:
                print("Failed to change the baudrate")
        else:
            print("Failed to open the port")
    except KeyboardInterrupt:
        print("\nExiting program...")

if __name__ == "__main__":
    """程序入口"""
    main_code1()  # 首先运行代码1获取用户输入
    if Secondary_grab == '2':  # 如果输入为'2'，运行代码2
        main_code2()
