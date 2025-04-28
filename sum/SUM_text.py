import serial
import threading
import time
import json
import sys
import signal
from STservo_sdk import PortHandler, sts, COMM_SUCCESS

# 全局变量定义在最顶部
global_ser = None
Secondary_grab = None

# 代码1中的函数和主逻辑
def read_serial(ser):
    while True:
        data = ser.readline().decode('utf-8')
        if data:
            print(f"Received: {data}")

def send_json_commands(ser, commands):
    for cmd in commands:
        json_bytes = json.dumps(cmd).encode('utf-8') + b'\n'
        ser.write(json_bytes)
        print(f"Sent: {cmd}")
        time.sleep(3)  # 延时3秒

def main_code1():
    global Secondary_grab, global_ser

    # 初始化串行端口
    try:
        global_ser = serial.Serial('COM3', baudrate=115200, dsrdtr=None)
    except Exception as e:
        print(f"Failed to open serial port: {e}")
        sys.exit(1)

    global_ser.setRTS(False)
    global_ser.setDTR(False)

    # 创建并启动读取线程
    serial_recv_thread = threading.Thread(target=read_serial, args=(global_ser,))
    serial_recv_thread.daemon = True
    serial_recv_thread.start()

    # 定义JSON指令集
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

    try:
        while True:
            command = input("Enter a number (1 or 2): ")
            if command in json_commands_dict:
                Secondary_grab = command  # 更新 Secondary_grab 变量
                send_json_commands(global_ser, json_commands_dict[command])
                break  # 输入有效命令后退出循环
            else:
                print("Invalid input. Please enter either 1 or 2.")
    except KeyboardInterrupt:
        print("\nExiting program...")

# 代码2中的函数和主逻辑
def signal_handler(portHandler, signal, frame):
    print('\nExiting program...')
    portHandler.closePort()
    if global_ser is not None:
        global_ser.close()
    sys.exit(0)

def move_servo_to_position(packetHandler, STS_ID, position_value, speed, acc):
    sts_comm_result, sts_error = packetHandler.WritePosEx(STS_ID, position_value, speed, acc)
    if sts_comm_result != COMM_SUCCESS or sts_error != 0:
        print("Failed to move to position")

def main_code2():
    global Secondary_grab

    if Secondary_grab != '2':
        print("Secondary_grab is not set to '2'. Exiting main_code2.")
        return

    # 默认设置
    STS_ID = 3  # STServo ID
    BAUDRATE = 1000000  # 波特率
    DEVICENAME = 'COM4'  # 设备名称
    STS_MAXIMUM_POSITION_VALUE = 600  # 舵机最大位置值
    STS_MINIMUM_POSITION_VALUE = 0  # 舵机最小位置值
    STS_MOVING_SPEED = 500  # 移动速度
    STS_MOVING_ACC = 10  # 加速度

    # 初始化端口处理器和数据包处理器
    portHandler = PortHandler(DEVICENAME)
    packetHandler = sts(portHandler)

    # 绑定 SIGINT 信号到信号处理器
    signal.signal(signal.SIGINT, signal_handler)

    try:
        if portHandler.openPort():
            print("Succeeded to open the port")
            if portHandler.setBaudRate(BAUDRATE):
                print("Succeeded to change the baudrate")
                # 移动舵机到最大位置
                move_servo_to_position(packetHandler, STS_ID, STS_MAXIMUM_POSITION_VALUE, STS_MOVING_SPEED, STS_MOVING_ACC)
                # 间隔五秒发送特定的JSON指令
                time.sleep(5)
                final_command = {"T": 122, "b": 0, "s": 0, "e": 160, "h": 171, "spd": 45, "acc": 10}
                send_json_commands(global_ser, [final_command])
                # 最后将舵机移动到最小位置
                move_servo_to_position(packetHandler, STS_ID, STS_MINIMUM_POSITION_VALUE, STS_MOVING_SPEED, STS_MOVING_ACC)
            else:
                print("Failed to change the baudrate")
        else:
            print("Failed to open the port")
    except KeyboardInterrupt:
        print("\nExiting program...")

if __name__ == "__main__":
    # 首先运行代码1以获取用户输入
    main_code1()

    # 检查 Secondary_grab 的值，如果是 '2'，则运行代码2
    if Secondary_grab == '2':
        main_code2()