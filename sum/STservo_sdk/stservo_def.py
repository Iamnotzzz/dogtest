#!/usr/bin/env python

# ------------------ 广播 ID 和最大 ID 定义 ------------------
BROADCAST_ID = 0xFE      # 254，广播 ID，表示发送给所有伺服
MAX_ID = 0xFC            # 252，伺服的最大可设置 ID 值
STS_END = 0              # 指令结束标记

# ------------------ STS 协议指令集 ------------------
# 以下是 STS 协议中定义的指令操作码
INST_PING = 1            # Ping 指令，用于检测伺服是否在线
INST_READ = 2            # 读取指令，从伺服读取数据
INST_WRITE = 3           # 写入指令，向伺服写入数据
INST_REG_WRITE = 4       # 寄存器写入指令，先写入寄存器，不立即生效
INST_ACTION = 5          # 执行动作，触发之前的 RegWrite 操作
INST_SYNC_WRITE = 131    # 0x83，同步写入，批量向多个伺服写入数据
INST_SYNC_READ = 130     # 0x82，同步读取，批量读取多个伺服的数据

# ------------------ 通信结果定义 ------------------
# 以下是 STS 通信协议中返回的各种结果状态码
COMM_SUCCESS = 0             # 0：数据包发送或接收成功
COMM_PORT_BUSY = -1          # -1：端口忙，正在被占用
COMM_TX_FAIL = -2            # -2：发送数据包失败
COMM_RX_FAIL = -3            # -3：接收状态包失败
COMM_TX_ERROR = -4           # -4：指令包格式错误
COMM_RX_WAITING = -5         # -5：正在等待接收状态包
COMM_RX_TIMEOUT = -6         # -6：接收超时，没有收到状态包
COMM_RX_CORRUPT = -7         # -7：接收到损坏的状态包
COMM_NOT_AVAILABLE = -9      # -9：所请求的数据不可用
