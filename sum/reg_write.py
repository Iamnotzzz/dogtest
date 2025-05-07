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
BAUDRATE = 1000000                 # 设置串口波特率为 1 Mbps
DEVICENAME = 'COM11'               # 设置设备名称
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

    # ------------------ 写入多个伺服的目标位置 ------------------
    # 遍历 ID 从 1 到 10 的所有伺服
    for sts_id in range(1, 11):
        # 使用 RegWritePosEx 进行寄存器写入
        # 这个写入是立即生效的，伺服电机会移动到指定位置
        sts_comm_result, sts_error = packetHandler.RegWritePosEx(
            sts_id, 
            sts_goal_position[index], 
            STS_MOVING_SPEED, 
            STS_MOVING_ACC
        )

        # ------------------ 错误处理 ------------------
        if sts_comm_result != COMM_SUCCESS:
            print("%s" % packetHandler.getTxRxResult(sts_comm_result))
        if sts_error != 0:
            print("%s" % packetHandler.getRxPacketError(sts_error))

    # ------------------ 发送 RegAction 指令 ------------------
    # RegWrite 是延迟执行的，必须调用 `RegAction` 才会真正执行
    packetHandler.RegAction()

    # ------------------ 切换目标位置 ------------------
    # 如果当前是最小位置，切换到最大位置，反之亦然
    if index == 0:
        index = 1
    else:
        index = 0

# ------------------ 程序结束，关闭串口 ------------------
portHandler.closePort()
