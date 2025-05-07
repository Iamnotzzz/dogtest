#!/usr/bin/env python
#
# *********     Gen Write Example      *********
#
#
# Available STServo model on this example : All models using Protocol STS
# This example is tested with a STServo and an URT
#

import sys
import os

# ------------------ 跨平台的 getch 实现 ------------------
# Windows 系统下使用 msvcrt
if os.name == 'nt':
    import msvcrt
    def getch():
        return msvcrt.getch().decode()
# Linux 和 Mac 使用 tty 和 termios
else:
    import sys, tty, termios
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    def getch():
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch

# ------------------ 初始化 SDK 路径和导入 ------------------
sys.path.append("..")             # 添加上级目录到系统路径
from STservo_sdk import *         # 导入 STServo SDK 库

# ------------------ 默认设置 ------------------
STS_ID = 15                        # 目标 STServo 的 ID
BAUDRATE = 1000000                 # 设置串口波特率为 1 Mbps
DEVICENAME = 'COM4'                # 设置设备名称
                                  # Windows: "COM1", "COM2", "COM3"...
                                  # Linux: "/dev/ttyUSB0"
                                  # Mac: "/dev/tty.usbserial-*"
STS_MINIMUM_POSITION_VALUE = 0     # 伺服的最小位置
STS_MAXIMUM_POSITION_VALUE = 4095  # 伺服的最大位置
STS_MOVING_SPEED = 2400            # 伺服的移动速度
STS_MOVING_ACC = 50                # 伺服的加速度

# ------------------ 初始化目标位置和状态 ------------------
index = 0
# 定义目标位置，包含最小和最大位置
sts_goal_position = [STS_MINIMUM_POSITION_VALUE, STS_MAXIMUM_POSITION_VALUE]

# ------------------ 初始化端口处理器实例 ------------------
portHandler = PortHandler(DEVICENAME)

# ------------------ 初始化数据包处理器实例 ------------------
packetHandler = sts(portHandler)

# ------------------ 尝试打开串口端口 ------------------
if portHandler.openPort():
    print("Succeeded to open the port")    # 打开成功
else:
    print("Failed to open the port")       # 打开失败
    print("Press any key to terminate...") 
    getch()  # 等待用户按键
    quit()   # 终止程序

# ------------------ 设置波特率 ------------------
if portHandler.setBaudRate(BAUDRATE):
    print("Succeeded to change the baudrate")  # 设置成功
else:
    print("Failed to change the baudrate")     # 设置失败
    print("Press any key to terminate...") 
    getch()  # 等待用户按键
    quit()   # 终止程序

# ------------------ 主循环 ------------------
while True:
    print("Press any key to continue! (or press ESC to quit!)")
    # 等待用户输入，如果是 ESC 则退出
    if getch() == chr(0x1b):  # 0x1b 是 ESC 键的 ASCII 值
        break

    # ------------------ 写入目标位置、速度和加速度 ------------------
    # 使用 WritePosEx 向伺服写入目标位置、速度和加速度
    sts_comm_result, sts_error = packetHandler.WritePosEx(
        STS_ID, 
        sts_goal_position[index], 
        STS_MOVING_SPEED, 
        STS_MOVING_ACC
    )

    # ------------------ 错误处理 ------------------
    if sts_comm_result != COMM_SUCCESS:
        print("%s" % packetHandler.getTxRxResult(sts_comm_result))
    elif sts_error != 0:
        print("%s" % packetHandler.getRxPacketError(sts_error))

    # ------------------ 监控位置和速度 ------------------
    while True:
        # 读取当前的位置和速度
        sts_present_position, sts_present_speed, sts_comm_result, sts_error = packetHandler.ReadPosSpeed(STS_ID)

        # 如果通信失败，打印错误信息
        if sts_comm_result != COMM_SUCCESS:
            print(packetHandler.getTxRxResult(sts_comm_result))
        else:
            # 如果通信成功，显示当前目标位置、当前位置和速度
            print("[ID:%03d] GoalPos:%d PresPos:%d PresSpd:%d" % (
                STS_ID, 
                sts_goal_position[index], 
                sts_present_position, 
                sts_present_speed
            ))

        if sts_error != 0:
            print(packetHandler.getRxPacketError(sts_error))

        # ------------------ 读取伺服是否仍在运动 ------------------
        moving, sts_comm_result, sts_error = packetHandler.ReadMoving(STS_ID)
        if sts_comm_result != COMM_SUCCESS:
            print(packetHandler.getTxRxResult(sts_comm_result))

        # 如果伺服不再运动，跳出循环
        if moving == 0:
            break

    # ------------------ 切换目标位置 ------------------
    # 如果当前是最小位置，切换到最大位置，反之亦然
    if index == 0:
        index = 1
    else:
        index = 0

# ------------------ 程序结束，关闭串口 ------------------
portHandler.closePort()
