#!/usr/bin/env python
#
# *********     Gen Write Example      *********
#
# 本示例演示如何使用普通写入 (Gen Write) 的方式来控制单个 STServo 的旋转位置
# 适用于所有基于 STS 协议的 STServo
# 本示例在 STServo 和 URT 设备上测试
#

import sys
import os

# 根据不同的操作系统选择合适的 `getch` 函数来获取键盘输入
if os.name == 'nt':  # Windows 系统
    import msvcrt
    def getch():
        return msvcrt.getch().decode()
        
else:  # Linux 或 Mac 系统
    import sys, tty, termios
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    def getch():
        try:
            tty.setraw(sys.stdin.fileno())  # 设置终端为原始模式
            ch = sys.stdin.read(1)          # 读取单个字符
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)  # 恢复终端模式
        return ch

# 添加 STServo SDK 的路径
sys.path.append("..")
from STservo_sdk import *  # 导入 STServo SDK 库

# -------------------------
# 默认配置
# -------------------------
STS_ID = 3                          # 舵机 ID 设为 3
BAUDRATE = 1000000                  # STServo 的默认波特率
DEVICENAME = 'COM4'                 # 串口设备名称
                                    # Windows: "COM1"  Linux: "/dev/ttyUSB0" Mac: "/dev/tty.usbserial-*"

STS_MINIMUM_POSITION_VALUE = 0      # 舵机的最小位置值
STS_MAXIMUM_POSITION_VALUE = 4095   # 舵机的最大位置值
STS_MOVING_SPEED = 2400             # 舵机的移动速度
STS_MOVING_ACC = 50                 # 舵机的加速度

index = 0
# 目标位置数组：舵机会在最小和最大位置之间来回移动
sts_goal_position = [STS_MINIMUM_POSITION_VALUE, STS_MAXIMUM_POSITION_VALUE]

# -------------------------
# 初始化端口处理器
# -------------------------
portHandler = PortHandler(DEVICENAME)

# -------------------------
# 初始化数据包处理器
# -------------------------
packetHandler = sts(portHandler)
    
# -------------------------
# 打开串口端口
# -------------------------
if portHandler.openPort():
    print("Succeeded to open the port")
else:
    print("Failed to open the port")
    print("Press any key to terminate...")
    getch()
    quit()

# -------------------------
# 设置波特率
# -------------------------
if portHandler.setBaudRate(BAUDRATE):
    print("Succeeded to change the baudrate")
else:
    print("Failed to change the baudrate")
    print("Press any key to terminate...")
    getch()
    quit()

# -------------------------
# 主循环：等待用户输入来执行一般写入
# -------------------------
while 1:
    print("Press any key to continue! (or press ESC to quit!)")
    if getch() == chr(0x1b):  # 如果按下 ESC 键，退出循环
        break

    # -------------------------
    # 写入目标位置、移动速度和加速度到 STServo
    # -------------------------
    sts_comm_result, sts_error = packetHandler.WritePosEx(
        STS_ID,                     # 舵机 ID
        sts_goal_position[index],   # 当前目标位置（0 或 4095）
        STS_MOVING_SPEED,           # 移动速度
        STS_MOVING_ACC              # 加速度
    )
    
    # 检查指令是否成功
    if sts_comm_result != COMM_SUCCESS:
        print("%s" % packetHandler.getTxRxResult(sts_comm_result))
    if sts_error != 0:
        print("%s" % packetHandler.getRxPacketError(sts_error))

    # -------------------------
    # 切换目标位置
    # -------------------------
    if index == 0:
        index = 1
    else:
        index = 0

# -------------------------
# 关闭端口
# -------------------------
portHandler.closePort()
