#!/usr/bin/env python
#
# *********     Sync Read and Sync Write Example      *********
#
#
# 本示例演示如何使用同步读取和同步写入来控制多个 STServo
# 本示例在 STServo 和 URT 设备上测试
#

import sys
import os
import time

# 根据不同的操作系统选择不同的按键读取方式
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
            ch = sys.stdin.read(1)          # 读取一个字符
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)  # 恢复终端设置
        return ch

# 添加 STservo SDK 的路径
sys.path.append("..")
from STservo_sdk import *  # 导入 STServo SDK 库

# -------------------------
# 默认配置
# -------------------------
BAUDRATE                    = 1000000           # STServo 默认波特率：1000000
DEVICENAME                  = 'COM11'           # 串口设备名称
                                                # Windows: "COM1"  Linux: "/dev/ttyUSB0" Mac: "/dev/tty.usbserial-*"

STS_MINIMUM_POSITION_VALUE  = 0                 # SCServo 的最小旋转位置
STS_MAXIMUM_POSITION_VALUE  = 4095              # SCServo 的最大旋转位置
STS_MOVING_SPEED            = 2400              # SCServo 移动速度
STS_MOVING_ACC              = 50                # SCServo 移动加速度

# 初始化目标位置，来回移动
index = 0
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
# 初始化同步读取对象
# -------------------------
groupSyncRead = GroupSyncRead(packetHandler, STS_PRESENT_POSITION_L, 11)

# -------------------------
# 主循环：等待输入并执行同步写入
# -------------------------
while 1:
    print("Press any key to continue! (or press ESC to quit!)")
    if getch() == chr(0x1b):  # 如果按下 ESC，退出循环
        break

    # -------------------------
    # 同步写入：设置目标位置、速度、加速度
    # -------------------------
    for sts_id in range(1, 11):  # 遍历 ID 1 到 10 的舵机
        sts_addparam_result = packetHandler.SyncWritePosEx(
            sts_id, 
            sts_goal_position[index], 
            STS_MOVING_SPEED, 
            STS_MOVING_ACC
        )
        if sts_addparam_result != True:
            print("[ID:%03d] groupSyncWrite addparam failed" % sts_id)

    # 发送同步写入指令
    sts_comm_result = packetHandler.groupSyncWrite.txPacket()
    if sts_comm_result != COMM_SUCCESS:
        print("%s" % packetHandler.getTxRxResult(sts_comm_result))

    # 清除同步写入的参数缓存
    packetHandler.groupSyncWrite.clearParam()
    
    # 等待 2ms 让舵机开始运动
    time.sleep(0.002)

    # -------------------------
    # 同步读取舵机状态，等待所有舵机到达目标位置
    # -------------------------
    while 1:
        sts_last_moving = 0  # 标记是否有舵机仍在移动

        # 遍历所有 ID，添加同步读取的参数
        for sts_id in range(1, 11):
            sts_addparam_result = groupSyncRead.addParam(sts_id)
            if sts_addparam_result != True:
                print("[ID:%03d] groupSyncRead addparam failed" % sts_id)

        # 执行同步读取指令
        sts_comm_result = groupSyncRead.txRxPacket()
        if sts_comm_result != COMM_SUCCESS:
            print("%s" % packetHandler.getTxRxResult(sts_comm_result))

        # 遍历读取到的数据
        for sts_id in range(1, 11):
            # 检查是否可以读取到数据
            sts_data_result, sts_error = groupSyncRead.isAvailable(sts_id, STS_PRESENT_POSITION_L, 11)
            if sts_data_result:
                sts_present_position = groupSyncRead.getData(sts_id, STS_PRESENT_POSITION_L, 2)
                sts_present_speed = groupSyncRead.getData(sts_id, STS_PRESENT_SPEED_L, 2)
                sts_present_moving = groupSyncRead.getData(sts_id, STS_MOVING, 1)

                # 打印当前状态
                print("[ID:%03d] PresPos:%d PresSpd:%d" % (
                    sts_id, 
                    sts_present_position, 
                    packetHandler.sts_tohost(sts_present_speed, 15)
                ))

                # 如果舵机仍在移动，标记未完成
                if sts_present_moving == 1:
                    sts_last_moving = 1
            else:
                print("[ID:%03d] groupSyncRead getdata failed" % sts_id)
                continue

            if sts_error:
                print(packetHandler.getRxPacketError(sts_error))

        # 清除同步读取的参数缓存
        groupSyncRead.clearParam()

        # 如果所有舵机都停止，退出循环
        if sts_last_moving == 0:
            break

    # 切换目标位置
    index = 1 if index == 0 else 0

# 关闭端口
portHandler.closePort()
