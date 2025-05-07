#!/usr/bin/env python
#
# *********     Sync Write Example      *********
#
# 本示例演示如何使用同步写入 (Sync Write) 方式来控制多个 STServo 的位置
# 适用于所有基于 STS 协议的 STServo
# 本示例在 STServo 和 URT 设备上测试
#

import sys
import os

# 根据不同的操作系统选择合适的 `getch` 函数来获取键盘输入
if os.name == 'nt':  # 如果是 Windows 系统
    import msvcrt
    def getch():
        return msvcrt.getch().decode()
else:  # 如果是 Linux 或 Mac 系统
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
BAUDRATE = 1000000          # STServo 的默认波特率
DEVICENAME = 'COM11'        # 串口设备名称
                            # Windows: "COM1"  Linux: "/dev/ttyUSB0" Mac: "/dev/tty.usbserial-*"

STS_MINIMUM_POSITION_VALUE = 0      # STServo 的最小位置值
STS_MAXIMUM_POSITION_VALUE = 4095   # STServo 的最大位置值
STS_MOVING_SPEED = 2400             # STServo 的移动速度
STS_MOVING_ACC = 50                 # STServo 的加速度

index = 0
# 目标位置数组，舵机将在这两个位置之间来回移动
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
# 主循环：等待用户输入来执行同步写入
# -------------------------
while 1:
    print("Press any key to continue! (or press ESC to quit!)")
    if getch() == chr(0x1b):  # 如果按下 ESC 键，退出循环
        break

    # -------------------------
    # 遍历 ID 为 1 到 10 的舵机，批量写入目标位置、速度和加速度
    # -------------------------
    for sts_id in range(1, 11):
        # `SyncWritePosEx` 是同步写入方法，能够同时写多个舵机的位置、速度和加速度
        sts_addparam_result = packetHandler.SyncWritePosEx(
            sts_id,                          # 舵机 ID
            sts_goal_position[index],        # 目标位置 (0 或 4095)
            STS_MOVING_SPEED,                # 移动速度
            STS_MOVING_ACC                   # 移动加速度
        )
        
        # 检查是否添加成功
        if sts_addparam_result != True:
            print("[ID:%03d] groupSyncWrite addparam failed" % sts_id)

    # -------------------------
    # 同步写入到所有舵机
    # -------------------------
    sts_comm_result = packetHandler.groupSyncWrite.txPacket()
    if sts_comm_result != COMM_SUCCESS:
        print("%s" % packetHandler.getTxRxResult(sts_comm_result))

    # -------------------------
    # 清除同步写入的参数缓存
    # -------------------------
    packetHandler.groupSyncWrite.clearParam()

    # -------------------------
    # 切换目标位置
    # 下一轮循环会将舵机移动到另一端
    # -------------------------
    if index == 0:
        index = 1
    else:
        index = 0

# -------------------------
# 关闭端口
# -------------------------
portHandler.closePort()
