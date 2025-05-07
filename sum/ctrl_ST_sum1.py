#!/usr/bin/env python
#
# *********     Gen Write Example      *********
#

import sys
import os
import signal
import time

# ------------------ 操作系统特定的 getch 定义 ------------------
# Windows 系统下使用 msvcrt 获取键盘输入
if os.name == 'nt':
    import msvcrt
    def getch():
        return msvcrt.getch().decode()
# Linux 或 Mac 系统下使用 tty 和 termios
else:
    import tty, termios
    fd = sys.stdin.fileno()                              # 获取标准输入的文件描述符
    old_settings = termios.tcgetattr(fd)                 # 备份终端设置
    def getch():
        try:
            tty.setraw(sys.stdin.fileno())              # 设置终端为原始模式
            ch = sys.stdin.read(1)                      # 读取一个字符
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)  # 恢复终端设置
        return ch

# ------------------ 初始化 SDK 路径和导入 ------------------
sys.path.append("..")              # 添加 SDK 的路径
from STservo_sdk import *          # 导入 SDK 中的所有模块

# ------------------ 默认设置 ------------------
STS_ID = 3                         # 伺服电机的 ID
BAUDRATE = 1000000                 # 波特率设置为 1Mbps
DEVICENAME = 'COM4'                # 设备端口名称
STS_MINIMUM_POSITION_VALUE = 0     # 伺服的最小位置
STS_MAXIMUM_POSITION_VALUE = 600   # 伺服的最大位置
STS_MOVING_SPEED = 500             # 运动速度
STS_MOVING_ACC = 50                # 加速度

# Secondary_grab 用于控制伺服的动作
Secondary_grab = 2                 # 1 表示抓取动作，2 表示放下动作

# ------------------ 初始化端口处理器 ------------------
portHandler = PortHandler(DEVICENAME)

# ------------------ 初始化数据包处理器 ------------------
packetHandler = sts(portHandler)

# ------------------ 信号处理器定义 ------------------
def signal_handler(signal, frame):
    """
    当检测到 Ctrl+C (SIGINT) 信号时触发：
    - 打印退出信息
    - 关闭端口
    - 退出程序
    """
    print('\nExiting program...')
    portHandler.closePort()
    sys.exit(0)

# ------------------ 绑定 SIGINT 信号到信号处理器 ------------------
signal.signal(signal.SIGINT, signal_handler)

# ------------------ 尝试打开串口 ------------------
if portHandler.openPort():
    print("Succeeded to open the port")
    
    # 尝试设置波特率
    if portHandler.setBaudRate(BAUDRATE):
        print("Succeeded to change the baudrate")
        
        # ------------------ 判断抓取模式 ------------------
        if Secondary_grab == 1:
            # ----------- 模式 1：抓取动作 -----------
            print("Moving the servo to maximum position...")
            # 写入最大位置命令
            sts_comm_result, sts_error = packetHandler.WritePosEx(STS_ID, STS_MAXIMUM_POSITION_VALUE, STS_MOVING_SPEED, STS_MOVING_ACC)
            
            # 判断执行是否成功
            if sts_comm_result != COMM_SUCCESS or sts_error != 0:
                print("Failed to move to maximum position")
            
            # 等待 2 秒
            time.sleep(2)

            # 写入最小位置命令
            print("Moving the servo to minimum position...")
            sts_comm_result, sts_error = packetHandler.WritePosEx(STS_ID, STS_MINIMUM_POSITION_VALUE, STS_MOVING_SPEED, STS_MOVING_ACC)
            
            if sts_comm_result != COMM_SUCCESS or sts_error != 0:
                print("Failed to move to minimum position")
        
        elif Secondary_grab == 2:
            # ----------- 模式 2：放下动作 -----------
            print("Moving the servo to maximum position...")
            sts_comm_result, sts_error = packetHandler.WritePosEx(STS_ID, STS_MAXIMUM_POSITION_VALUE, STS_MOVING_SPEED, STS_MOVING_ACC)
            
            if sts_comm_result != COMM_SUCCESS or sts_error != 0:
                print("Failed to move to maximum position")
        
        else:
            # 如果 Secondary_grab 设置不对，输出错误信息
            print("Error: Invalid value for Secondary_grab. Please set it to 1 or 2.")
    else:
        print("Failed to change the baudrate")
else:
    print("Failed to open the port")

# ------------------ 程序结束，关闭端口 ------------------
portHandler.closePort()
