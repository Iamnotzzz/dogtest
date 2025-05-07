#!/usr/bin/env python
#
# *********     Ping Example      *********
#
#
# Available STServo model on this example : All models using Protocol STS
# This example is tested with a STServo and an URT
#

import sys
import os

# ------------------ 定义 getch 方法用于跨平台获取单个字符输入 ------------------
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
STS_ID = 3                        # 目标 STServo 的 ID
BAUDRATE = 1000000                # 设置串口波特率为 1 Mbps
DEVICENAME = 'COM4'               # 设置设备名称
                                  # Windows: "COM1", "COM2", "COM3"...
                                  # Linux: "/dev/ttyUSB0"
                                  # Mac: "/dev/tty.usbserial-*"

# ------------------ 初始化端口处理器实例 ------------------
# 设置端口名称并获取相应的方法
portHandler = PortHandler(DEVICENAME)

# ------------------ 初始化数据包处理器实例 ------------------
# 使用 `sts` 类来控制 STServo
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

# ------------------ 发送 Ping 指令 ------------------
# Ping 操作用于检测伺服电机是否在线，并获取其型号编号
sts_model_number, sts_comm_result, sts_error = packetHandler.ping(STS_ID)

# ------------------ 判断 Ping 结果 ------------------
if sts_comm_result != COMM_SUCCESS:
    # 如果通信不成功，打印错误信息
    print("%s" % packetHandler.getTxRxResult(sts_comm_result))
else:
    # 如果通信成功，输出伺服的 ID 和型号编号
    print("[ID:%03d] ping Succeeded. STServo model number : %d" % (STS_ID, sts_model_number))

# ------------------ 检查是否有错误 ------------------
if sts_error != 0:
    print("%s" % packetHandler.getRxPacketError(sts_error))

# ------------------ 关闭串口端口 ------------------
portHandler.closePort()
