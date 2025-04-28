#!/usr/bin/env python
#
# *********     Gen Write Example      *********
#

import sys
import os
import signal
import time

# 根据操作系统不同，定义getch函数
if os.name == 'nt':
    import msvcrt
    def getch():
        return msvcrt.getch().decode()
else:
    import tty, termios
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    def getch():
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch

# 添加SDK路径和导入
sys.path.append("..")
from STservo_sdk import *

# 默认设置
STS_ID = 3  # STServo ID
BAUDRATE = 1000000  # 波特率
DEVICENAME = 'COM4'  # 设备名称
STS_MINIMUM_POSITION_VALUE = 0  # 最小位置值
STS_MAXIMUM_POSITION_VALUE = 600  # 最大位置值
STS_MOVING_SPEED = 500  # 移动速度
STS_MOVING_ACC = 50  # 加速度

# 定义Secondary_grab变量
Secondary_grab = 2  # 根据需要设置这个值

# 初始化端口处理器
portHandler = PortHandler(DEVICENAME)

# 初始化数据包处理器
packetHandler = sts(portHandler)

# 定义信号处理器
def signal_handler(signal, frame):
    print('\nExiting program...')
    portHandler.closePort()
    sys.exit(0)

# 绑定SIGINT信号到信号处理器
signal.signal(signal.SIGINT, signal_handler)

# 尝试打开端口
if portHandler.openPort():
    print("Succeeded to open the port")
    # 尝试设置波特率
    if portHandler.setBaudRate(BAUDRATE):
        print("Succeeded to change the baudrate")
        # 根据Secondary_grab变量的值执行相应操作
        if Secondary_grab == 1:
            #抓取
            print("Moving the servo to maximum position...")
            sts_comm_result, sts_error = packetHandler.WritePosEx(STS_ID, STS_MAXIMUM_POSITION_VALUE, STS_MOVING_SPEED, STS_MOVING_ACC)
            if sts_comm_result != COMM_SUCCESS or sts_error != 0:
                print("Failed to move to maximum position")
            time.sleep(2)  # 等待2秒

            print("Moving the servo to minimum position...")
            sts_comm_result, sts_error = packetHandler.WritePosEx(STS_ID, STS_MINIMUM_POSITION_VALUE, STS_MOVING_SPEED, STS_MOVING_ACC)
            if sts_comm_result != COMM_SUCCESS or sts_error != 0:
                print("Failed to move to minimum position")
        elif Secondary_grab == 2:
            #放下
            print("Moving the servo to maximum position...")
            sts_comm_result, sts_error = packetHandler.WritePosEx(STS_ID, STS_MAXIMUM_POSITION_VALUE, STS_MOVING_SPEED, STS_MOVING_ACC)
            if sts_comm_result != COMM_SUCCESS or sts_error != 0:
                print("Failed to move to maximum position")
        else:
            print("Error: Invalid value for Secondary_grab. Please set it to 1 or 2.")
    else:
        print("Failed to change the baudrate")
else:
    print("Failed to open the port")

# 关闭端口
portHandler.closePort()