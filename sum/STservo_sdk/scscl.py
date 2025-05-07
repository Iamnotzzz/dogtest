#!/usr/bin/env python

# 导入必要的模块，包含伺服电机的定义、协议处理器、同步写操作
from .stservo_def import *
from .protocol_packet_handler import *
from .group_sync_write import *

# ------------------ 波特率定义 ------------------
# 这里定义了几种常用的波特率对应的枚举值
SCSCL_1M = 0         # 1 Mbps
SCSCL_0_5M = 1       # 0.5 Mbps
SCSCL_250K = 2       # 250 Kbps
SCSCL_128K = 3       # 128 Kbps
SCSCL_115200 = 4     # 115200 bps
SCSCL_76800 = 5      # 76800 bps
SCSCL_57600 = 6      # 57600 bps
SCSCL_38400 = 7      # 38400 bps

# ------------------ 内存表定义 ------------------
# EPROM (只读)
SCSCL_MODEL_L = 3            # 低字节 - 伺服电机型号
SCSCL_MODEL_H = 4            # 高字节 - 伺服电机型号

# EPROM (读写)
scs_id = 5                    # 伺服电机的 ID
SCSCL_BAUD_RATE = 6           # 波特率设置
SCSCL_MIN_ANGLE_LIMIT_L = 9   # 最小角度限制（低字节）
SCSCL_MIN_ANGLE_LIMIT_H = 10  # 最小角度限制（高字节）
SCSCL_MAX_ANGLE_LIMIT_L = 11  # 最大角度限制（低字节）
SCSCL_MAX_ANGLE_LIMIT_H = 12  # 最大角度限制（高字节）
SCSCL_CW_DEAD = 26            # 顺时针死区
SCSCL_CCW_DEAD = 27           # 逆时针死区

# SRAM (读写)
SCSCL_TORQUE_ENABLE = 40         # 启用/禁用扭矩
SCSCL_GOAL_POSITION_L = 42       # 目标位置（低字节）
SCSCL_GOAL_POSITION_H = 43       # 目标位置（高字节）
SCSCL_GOAL_TIME_L = 44           # 目标时间（低字节）
SCSCL_GOAL_TIME_H = 45           # 目标时间（高字节）
SCSCL_GOAL_SPEED_L = 46          # 目标速度（低字节）
SCSCL_GOAL_SPEED_H = 47          # 目标速度（高字节）
SCSCL_LOCK = 48                  # 锁定状态

# SRAM (只读)
SCSCL_PRESENT_POSITION_L  = 56   # 当前伺服电机位置（低字节）
SCSCL_PRESENT_POSITION_H = 57    # 当前伺服电机位置（高字节）
SCSCL_PRESENT_SPEED_L = 58       # 当前伺服电机速度（低字节）
SCSCL_PRESENT_SPEED_H = 59       # 当前伺服电机速度（高字节）
SCSCL_PRESENT_LOAD_L = 60        # 当前负载（低字节）
SCSCL_PRESENT_LOAD_H = 61        # 当前负载（高字节）
SCSCL_PRESENT_VOLTAGE = 62       # 当前电压
SCSCL_PRESENT_TEMPERATURE = 63   # 当前温度
SCSCL_MOVING = 66                # 是否在运动状态
SCSCL_PRESENT_CURRENT_L = 69     # 当前电流（低字节）
SCSCL_PRESENT_CURRENT_H = 70     # 当前电流（高字节）


# ------------------ scscl 类定义 ------------------
class scscl(protocol_packet_handler):

    # 初始化构造函数
    def __init__(self, portHandler):
        protocol_packet_handler.__init__(self, portHandler, 1)
        self.groupSyncWrite = GroupSyncWrite(self, SCSCL_GOAL_POSITION_L, 6)

    # 写入目标位置、时间和速度
    def WritePos(self, scs_id, position, time, speed):
        txpacket = [
            self.scs_lobyte(position), self.scs_hibyte(position), 
            self.scs_lobyte(time), self.scs_hibyte(time), 
            self.scs_lobyte(speed), self.scs_hibyte(speed)
        ]
        return self.writeTxRx(scs_id, SCSCL_GOAL_POSITION_L, len(txpacket), txpacket)

    # 读取当前的位置
    def ReadPos(self, scs_id):
        scs_present_position, scs_comm_result, scs_error = self.read2ByteTxRx(scs_id, SCSCL_PRESENT_POSITION_L)
        return scs_present_position, scs_comm_result, scs_error

    # 读取当前速度
    def ReadSpeed(self, scs_id):
        scs_present_speed, scs_comm_result, scs_error = self.read2ByteTxRx(scs_id, SCSCL_PRESENT_SPEED_L)
        return self.scs_tohost(scs_present_speed, 15), scs_comm_result, scs_error

    # 同时读取当前位置和速度
    def ReadPosSpeed(self, scs_id):
        scs_present_position_speed, scs_comm_result, scs_error = self.read4ByteTxRx(scs_id, SCSCL_PRESENT_POSITION_L)
        scs_present_position = self.scs_loword(scs_present_position_speed)
        scs_present_speed = self.scs_hiword(scs_present_position_speed)
        return scs_present_position, self.scs_tohost(scs_present_speed, 15), scs_comm_result, scs_error

    # 判断伺服是否在移动
    def ReadMoving(self, scs_id):
        moving, scs_comm_result, scs_error = self.read1ByteTxRx(scs_id, SCSCL_MOVING)
        return moving, scs_comm_result, scs_error

    # 同步写入目标位置
    def SyncWritePos(self, scs_id, position, time, speed):
        txpacket = [
            self.scs_lobyte(position), self.scs_hibyte(position), 
            self.scs_lobyte(time), self.scs_hibyte(time), 
            self.scs_lobyte(speed), self.scs_hibyte(speed)
        ]
        return self.groupSyncWrite.addParam(scs_id, txpacket)

    # 寄存器写入目标位置（延迟生效）
    def RegWritePos(self, scs_id, position, time, speed):
        txpacket = [
            self.scs_lobyte(position), self.scs_hibyte(position), 
            self.scs_lobyte(time), self.scs_hibyte(time), 
            self.scs_lobyte(speed), self.scs_hibyte(speed)
        ]
        return self.regWriteTxRx(scs_id, SCSCL_GOAL_POSITION_L, len(txpacket), txpacket)

    # 广播执行延迟指令
    def RegAction(self):
        return self.action(BROADCAST_ID)

    # 进入 PWM 模式
    def PWMMode(self, scs_id):
        txpacket = [0, 0, 0, 0]
        return self.writeTxRx(scs_id, SCSCL_MIN_ANGLE_LIMIT_L, len(txpacket), txpacket)

    # 写入 PWM 模式的时间
    def WritePWM(self, scs_id, time):
        return self.write2ByteTxRx(scs_id, SCSCL_GOAL_TIME_L, self.scs_toscs(time, 10))

    # 锁定 EPROM
    def LockEprom(self, scs_id):
        return self.write1ByteTxRx(scs_id, SCSCL_LOCK, 1)

    # 解锁 EPROM
    def unLockEprom(self, scs_id):
        return self.write1ByteTxRx(scs_id, SCSCL_LOCK, 0)
