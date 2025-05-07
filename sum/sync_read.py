#!/usr/bin/env python
#
# *********     Sync Read Example      *********
#
# 本示例演示如何使用同步读取 (Sync Read) 方式来获取多个 STServo 的位置和速度信息
# 适用于所有基于 STS 协议的 STServo
# 本示例在 STServo 和 URT 设备上测试
#

import sys
import os

# 判断操作系统类型，选择合适的 `getch` 函数读取键盘输入
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
            ch = sys.stdin.read(1)          # 读取单个字符输入
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)  # 恢复终端模式
        return ch

# 添加 STservo SDK 的路径
sys.path.append("..")
from STservo_sdk import *  # 导入 STServo SDK 库

# -------------------------
# 默认配置
# -------------------------
BAUDRATE = 1000000          # SCServo 的默认波特率
DEVICENAME = 'COM11'        # 串口设备名称
                            # Windows: "COM1"  Linux: "/dev/ttyUSB0" Mac: "/dev/tty.usbserial-*"

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
# GroupSyncRead 用于批量读取多个设备的相同数据
# STS_PRESENT_POSITION_L 是读取起始地址，4 是读取的字节长度
# 这里同步读取的是位置（Position）和速度（Speed）
# -------------------------
groupSyncRead = GroupSyncRead(packetHandler, STS_PRESENT_POSITION_L, 4)

# -------------------------
# 主循环：等待用户输入来进行同步读取
# -------------------------
while 1:
    print("Press any key to continue! (or press ESC to quit!)")
    if getch() == chr(0x1b):  # 如果按下 ESC 键，退出循环
        break

    # -------------------------
    # 遍历 1 到 10 号舵机，将其加入同步读取
    # -------------------------
    for sts_id in range(1, 11):
        # 将当前 ID 的读取请求添加到同步读取列表中
        sts_addparam_result = groupSyncRead.addParam(sts_id)
        if sts_addparam_result != True:
            print("[ID:%03d] groupSyncRead addparam failed" % sts_id)

    # -------------------------
    # 发送同步读取的指令，批量读取数据
    # -------------------------
    sts_comm_result = groupSyncRead.txRxPacket()
    if sts_comm_result != COMM_SUCCESS:
        print("%s" % packetHandler.getTxRxResult(sts_comm_result))

    # -------------------------
    # 遍历所有读取到的数据并打印
    # -------------------------
    for sts_id in range(1, 11):
        # 注意这里有一个错误：`scs_id` 应该是 `sts_id`
        sts_data_result, sts_error = groupSyncRead.isAvailable(sts_id, STS_PRESENT_POSITION_L, 4)
        
        # 如果数据有效，开始读取
        if sts_data_result == True:
            # 读取当前舵机的位置值 (2 字节)
            sts_present_position = groupSyncRead.getData(sts_id, STS_PRESENT_POSITION_L, 2)
            # 读取当前舵机的速度值 (2 字节)
            sts_present_speed = groupSyncRead.getData(sts_id, STS_PRESENT_SPEED_L, 2)

            # 打印舵机的当前位置和速度
            print("[ID:%03d] PresPos:%d PresSpd:%d" % (
                sts_id, 
                sts_present_position, 
                packetHandler.sts_tohost(sts_present_speed, 15)
            ))
        else:
            print("[ID:%03d] groupSyncRead getdata failed" % sts_id)
            continue

        # 如果读取过程中出现错误，打印错误信息
        if sts_error != 0:
            print("%s" % packetHandler.getRxPacketError(sts_error))

    # -------------------------
    # 清除同步读取的参数缓存，准备下次读取
    # -------------------------
    groupSyncRead.clearParam()

# -------------------------
# 关闭端口
# -------------------------
portHandler.closePort()
