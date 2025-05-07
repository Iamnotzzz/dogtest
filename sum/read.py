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
            tty.setraw(sys.stdin.fileno())              # 设置终端为原始模式
            ch = sys.stdin.read(1)                       # 读取一个字符
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)  # 恢复终端设置
        return ch

# ------------------ 初始化 SDK 路径和导入 ------------------
sys.path.append("..")             # 添加上级目录到系统路径
from STservo_sdk import *         # 导入 STServo SDK 库

# ------------------ 默认设置 ------------------
STS_ID = 1                         # 目标 STServo 的 ID
BAUDRATE = 1000000                 # 设置串口波特率为 1 Mbps
DEVICENAME = 'COM4'                # 设置设备名称
                                  # Windows: "COM1", "COM2", "COM3"...
                                  # Linux: "/dev/ttyUSB0"
                                  # Mac: "/dev/tty.usbserial-*"

# ------------------ 初始化端口处理器实例 ------------------
# PortHandler 是一个串口通信的管理类
portHandler = PortHandler(DEVICENAME)

# ------------------ 初始化数据包处理器实例 ------------------
# sts 是协议处理类，用来和 STServo 进行数据交互
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
    # 等待用户按键，如果是 ESC 则退出循环
    if getch() == chr(0x1b):  # 0x1b 是 ESC 键的 ASCII 值
        break
    
    # ------------------ 读取伺服当前位置和速度 ------------------
    # 通过 ReadPosSpeed 读取 STServo 的当前位置和速度
    sts_present_position, sts_present_speed, sts_comm_result, sts_error = packetHandler.ReadPosSpeed(STS_ID)

    # ------------------ 错误处理 ------------------
    # 如果通信失败，打印错误信息
    if sts_comm_result != COMM_SUCCESS:
        print(packetHandler.getTxRxResult(sts_comm_result))
    else:
        # 如果通信成功，显示当前的位置和速度
        print("[ID:%03d] PresPos:%d PresSpd:%d" % (STS_ID, sts_present_position, sts_present_speed))
    
    # 如果读取数据包中有错误信息
    if sts_error != 0:
        print(packetHandler.getRxPacketError(sts_error))

# ------------------ 程序结束，关闭串口 ------------------
portHandler.closePort()
