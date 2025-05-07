#!/usr/bin/env python

# 导入必要的模块，包含伺服电机的定义、协议处理器、同步读写操作
from .stservo_def import *
from .protocol_packet_handler import *
from .group_sync_read import *
from .group_sync_write import *

# ------------------ 波特率定义 ------------------
# 这里定义了几种常用的波特率对应的枚举值
STS_1M = 0         # 1 Mbps
STS_0_5M = 1       # 0.5 Mbps
STS_250K = 2       # 250 Kbps
STS_128K = 3       # 128 Kbps
STS_115200 = 4     # 115200 bps
STS_76800 = 5      # 76800 bps
STS_57600 = 6      # 57600 bps
STS_38400 = 7      # 38400 bps

# ------------------ 内存表定义 ------------------
# EPROM (只读) ---------------------------------
STS_MODEL_L = 3            # 低字节 - 伺服电机型号
STS_MODEL_H = 4            # 高字节 - 伺服电机型号

# EPROM (读写) ---------------------------------
STS_ID = 5                 # 伺服电机的 ID
STS_BAUD_RATE = 6          # 波特率设置
STS_MIN_ANGLE_LIMIT_L = 9  # 最小角度限制（低字节）
STS_MIN_ANGLE_LIMIT_H = 10 # 最小角度限制（高字节）
STS_MAX_ANGLE_LIMIT_L = 11 # 最大角度限制（低字节）
STS_MAX_ANGLE_LIMIT_H = 12 # 最大角度限制（高字节）
STS_CW_DEAD = 26           # 顺时针死区
STS_CCW_DEAD = 27          # 逆时针死区
STS_OFS_L = 31             # 偏移量（低字节）
STS_OFS_H = 32             # 偏移量（高字节）
STS_MODE = 33              # 伺服电机的运行模式

# SRAM (读写) ---------------------------------
STS_TORQUE_ENABLE = 40         # 启用/禁用扭矩
STS_ACC = 41                   # 加速度设置
STS_GOAL_POSITION_L = 42       # 目标位置（低字节）
STS_GOAL_POSITION_H = 43       # 目标位置（高字节）
STS_GOAL_TIME_L = 44           # 目标时间（低字节）
STS_GOAL_TIME_H = 45           # 目标时间（高字节）
STS_GOAL_SPEED_L = 46          # 目标速度（低字节）
STS_GOAL_SPEED_H = 47          # 目标速度（高字节）
STS_LOCK = 55                  # EEPROM 锁定状态

# SRAM (只读) ---------------------------------
STS_PRESENT_POSITION_L = 56    # 当前伺服电机位置（低字节）
STS_PRESENT_POSITION_H = 57    # 当前伺服电机位置（高字节）
STS_PRESENT_SPEED_L = 58       # 当前伺服电机速度（低字节）
STS_PRESENT_SPEED_H = 59       # 当前伺服电机速度（高字节）
STS_PRESENT_LOAD_L = 60        # 当前负载（低字节）
STS_PRESENT_LOAD_H = 61        # 当前负载（高字节）
STS_PRESENT_VOLTAGE = 62       # 当前电压
STS_PRESENT_TEMPERATURE = 63   # 当前温度
STS_MOVING = 66                # 是否在运动状态
STS_PRESENT_CURRENT_L = 69     # 当前电流（低字节）
STS_PRESENT_CURRENT_H = 70     # 当前电流（高字节）


# ------------------ sts 类定义 ------------------
class sts(protocol_packet_handler):

    # 初始化构造函数
    def __init__(self, portHandler):
        # 继承父类 protocol_packet_handler 的初始化，协议版本为0
        protocol_packet_handler.__init__(self, portHandler, 0)
        # 初始化同步写对象，写入地址为 STS_ACC，加速度起始地址，长度为 7
        self.groupSyncWrite = GroupSyncWrite(self, STS_ACC, 7)

    # 写入目标位置、速度和加速度
    def WritePosEx(self, sts_id, position, speed, acc):
        txpacket = [
            acc,
            self.sts_lobyte(position), self.sts_hibyte(position),
            0, 0, 
            self.sts_lobyte(speed), self.sts_hibyte(speed)
        ]
        return self.writeTxRx(sts_id, STS_ACC, len(txpacket), txpacket)

    # 读取当前的位置
    def ReadPos(self, sts_id):
        sts_present_position, sts_comm_result, sts_error = self.read2ByteTxRx(sts_id, STS_PRESENT_POSITION_L)
        return self.sts_tohost(sts_present_position, 15), sts_comm_result, sts_error

    # 读取当前速度
    def ReadSpeed(self, sts_id):
        sts_present_speed, sts_comm_result, sts_error = self.read2ByteTxRx(sts_id, STS_PRESENT_SPEED_L)
        return self.sts_tohost(sts_present_speed, 15), sts_comm_result, sts_error

    # 同时读取当前位置和速度
    def ReadPosSpeed(self, sts_id):
        sts_present_position_speed, sts_comm_result, sts_error = self.read4ByteTxRx(sts_id, STS_PRESENT_POSITION_L)
        sts_present_position = self.sts_loword(sts_present_position_speed)
        sts_present_speed = self.sts_hiword(sts_present_position_speed)
        return self.sts_tohost(sts_present_position, 15), self.sts_tohost(sts_present_speed, 15), sts_comm_result, sts_error

    # 判断伺服是否在移动
    def ReadMoving(self, sts_id):
        moving, sts_comm_result, sts_error = self.read1ByteTxRx(sts_id, STS_MOVING)
        return moving, sts_comm_result, sts_error

    # 同步写入目标位置、速度和加速度
    def SyncWritePosEx(self, sts_id, position, speed, acc):
        txpacket = [
            acc,
            self.sts_lobyte(position), self.sts_hibyte(position),
            0, 0, 
            self.sts_lobyte(speed), self.sts_hibyte(speed)
        ]
        return self.groupSyncWrite.addParam(sts_id, txpacket)

    # 寄存器写入（延迟生效）
    def RegWritePosEx(self, sts_id, position, speed, acc):
        txpacket = [
            acc,
            self.sts_lobyte(position), self.sts_hibyte(position),
            0, 0, 
            self.sts_lobyte(speed), self.sts_hibyte(speed)
        ]
        return self.regWriteTxRx(sts_id, STS_ACC, len(txpacket), txpacket)

    # 广播执行延迟指令
    def RegAction(self):
        return self.action(BROADCAST_ID)

    # 设置为轮式模式
    def WheelMode(self, sts_id):
        return self.write1ByteTxRx(sts_id, STS_MODE, 1)

    # 写入速度和加速度
    def WriteSpec(self, sts_id, speed, acc):
        speed = self.sts_toscs(speed, 15)
        txpacket = [acc, 0, 0, 0, 0, self.sts_lobyte(speed), self.sts_hibyte(speed)]
        return self.writeTxRx(sts_id, STS_ACC, len(txpacket), txpacket)

    # 锁定 EPROM
    def LockEprom(self, sts_id):
        return self.write1ByteTxRx(sts_id, STS_LOCK, 1)

    # 解锁 EPROM
    def unLockEprom(self, sts_id):
        return self.write1ByteTxRx(sts_id, STS_LOCK, 0)
