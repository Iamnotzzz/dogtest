#!/usr/bin/env python
#
# *********     Gen Write Example      *********
#
# 本示例演示如何使用一般写入 (Gen Write) 的方式来控制单个 STServo 的轮模式速度
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

# 添加 STservo SDK 的路径
sys.path.append("..")
from STservo_sdk import *  # 导入 STServo SDK 库

# -------------------------
# 默认配置
# -------------------------
STS_ID = 1                       # STServo 的 ID 设为 1
BAUDRATE = 1000000               # STServo 的默认波特率
DEVICENAME = 'COM11'             # 串口设备名称
                                 # Windows: "COM1"  Linux: "/dev/ttyUSB0" Mac: "/dev/tty.usbserial-*"

STS_MOVING_SPEED0 = 2400         # 正转速度
STS_MOVING_SPEED1 = -2400        # 反转速度
STS_MOVING_ACC = 50              # 移动加速度

index = 0
# 速度模式的数组：正转、停止、反转、停止
sts_move_speed = [STS_MOVING_SPEED0, 0, STS_MOVING_SPEED1, 0]

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
# 设置舵机进入轮模式 (Wheel Mode)
# -------------------------
sts_comm_result, sts_error = packetHandler.WheelMode(STS_ID)

# 检查是否进入轮模式成功
if sts_comm_result != COMM_SUCCESS:
    print("%s" % packetHandler.getTxRxResult(sts_comm_result))
elif sts_error != 0:
    print("%s" % packetHandler.getRxPacketError(sts_error))

# -------------------------
# 主循环：等待用户输入来切换速度
# -------------------------
while 1:
    print("Press any key to continue! (or press ESC to quit!)")
    if getch() == chr(0x1b):  # 如果按下 ESC 键，退出循环
        break

    # -------------------------
    # 写入目标速度和加速度
    # -------------------------
    # WriteSpec 方法用于写入目标速度和加速度
    sts_comm_result, sts_error = packetHandler.WriteSpec(
        STS_ID,                # 舵机 ID
        sts_move_speed[index], # 当前的速度值
        STS_MOVING_ACC         # 加速度值
    )

    # 检查指令是否成功
    if sts_comm_result != COMM_SUCCESS:
        print("%s" % packetHandler.getTxRxResult(sts_comm_result))
    if sts_error != 0:
        print("%s" % packetHandler.getRxPacketError(sts_error))

    # -------------------------
    # 循环切换速度模式
    # 从正转 → 停止 → 反转 → 停止 → 正转，依次循环
    # -------------------------
    index += 1
    if index == 4:  # 如果超过数组的索引范围，重置为 0
        index = 0

# -------------------------
# 关闭端口
# -------------------------
portHandler.closePort()
