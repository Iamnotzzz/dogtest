#!/usr/bin/env python

from .stservo_def import *  # 导入 stservo_def 模块中的所有内容

# 定义一个同步读取的类 GroupSyncRead
class GroupSyncRead:
    def __init__(self, ph, start_address, data_length):
        """
        初始化函数：
        - ph: PacketHandler对象，用于通信协议处理
        - start_address: 起始地址，表示从哪个寄存器开始读取
        - data_length: 读取数据的长度
        """
        self.ph = ph
        self.start_address = start_address
        self.data_length = data_length

        self.last_result = False              # 上一次通信的结果状态
        self.is_param_changed = False         # 参数是否有变化
        self.param = []                       # 参数列表，用于批量读取
        self.data_dict = {}                   # 存放读取到的数据

        self.clearParam()  # 初始化时清空参数

    def makeParam(self):
        """
        创建同步读取的参数列表:
        - 遍历 data_dict，将其中的 ID 逐一添加到 param 列表中
        """
        if not self.data_dict:
            return

        self.param = []

        for scs_id in self.data_dict:
            self.param.append(scs_id)

    def addParam(self, sts_id):
        """
        添加一个舵机的 ID 到读取列表中:
        - sts_id: 舵机的唯一 ID
        - 如果该 ID 已存在，则返回 False
        - 如果添加成功，则返回 True
        """
        if sts_id in self.data_dict:
            return False

        self.data_dict[sts_id] = []  # 初始化一个空列表来存储该 ID 的数据
        self.is_param_changed = True  # 标记参数有变化
        return True

    def removeParam(self, sts_id):
        """
        从读取列表中移除一个舵机 ID
        - sts_id: 要移除的舵机 ID
        """
        if sts_id not in self.data_dict:
            return

        del self.data_dict[sts_id]
        self.is_param_changed = True

    def clearParam(self):
        """
        清空所有同步读取的参数
        """
        self.data_dict.clear()

    def txPacket(self):
        """
        发送同步读取指令:
        - 如果没有任何 ID，返回 COMM_NOT_AVAILABLE 错误
        - 如果参数有更新，重新创建参数包
        - 使用 PacketHandler 发送同步读取命令
        """
        if len(self.data_dict.keys()) == 0:
            return COMM_NOT_AVAILABLE

        if self.is_param_changed is True or not self.param:
            self.makeParam()

        return self.ph.syncReadTx(self.start_address, self.data_length, self.param, len(self.data_dict.keys()))

    def rxPacket(self):
        """
        接收同步读取的返回数据:
        - 尝试读取同步返回的数据包
        - 根据数据包中的信息，解析到对应的舵机 ID 中
        """
        self.last_result = True
        result = COMM_RX_FAIL

        if len(self.data_dict.keys()) == 0:
            return COMM_NOT_AVAILABLE

        result, rxpacket = self.ph.syncReadRx(self.data_length, len(self.data_dict.keys()))

        if len(rxpacket) >= (self.data_length + 6):
            for sts_id in self.data_dict:
                self.data_dict[sts_id], result = self.readRx(rxpacket, sts_id, self.data_length)
                if result != COMM_SUCCESS:
                    self.last_result = False
        else:
            self.last_result = False
        
        return result

    def txRxPacket(self):
        """
        同步发送和接收数据:
        - 先发送同步读取指令
        - 再接收同步读取的返回包
        """
        result = self.txPacket()
        if result != COMM_SUCCESS:
            return result

        return self.rxPacket()

    def readRx(self, rxpacket, sts_id, data_length):
        """
        解析同步读取返回的数据包:
        - rxpacket: 接收到的数据包
        - sts_id: 舵机 ID
        - data_length: 数据长度
        """
        data = []
        rx_length = len(rxpacket)
        rx_index = 0

        # 遍历数据包寻找对应的 ID 以及数据
        while (rx_index + 6 + data_length) <= rx_length:
            headpacket = [0x00, 0x00, 0x00]
            while rx_index < rx_length:
                headpacket[2] = headpacket[1]
                headpacket[1] = headpacket[0]
                headpacket[0] = rxpacket[rx_index]
                rx_index += 1
                # 判断是否匹配到包头和 ID
                if (headpacket[2] == 0xFF) and (headpacket[1] == 0xFF) and headpacket[0] == sts_id:
                    break
            
            if (rx_index + 3 + data_length) > rx_length:
                break

            if rxpacket[rx_index] != (data_length + 2):
                rx_index += 1
                continue

            rx_index += 1
            Error = rxpacket[rx_index]
            rx_index += 1
            calSum = sts_id + (data_length + 2) + Error
            data = [Error]
            data.extend(rxpacket[rx_index:rx_index + data_length])

            for i in range(0, data_length):
                calSum += rxpacket[rx_index]
                rx_index += 1

            calSum = ~calSum & 0xFF

            if calSum != rxpacket[rx_index]:
                return None, COMM_RX_CORRUPT
            return data, COMM_SUCCESS

        return None, COMM_RX_CORRUPT

    def isAvailable(self, sts_id, address, data_length):
        """
        检查指定 ID 的数据是否可用:
        - sts_id: 舵机 ID
        - address: 读取数据的地址
        - data_length: 数据长度
        """
        if sts_id not in self.data_dict:
            return False, 0

        if (address < self.start_address) or (self.start_address + self.data_length - data_length < address):
            return False, 0

        if not self.data_dict[sts_id]:
            return False, 0

        if len(self.data_dict[sts_id]) < (data_length + 1):
            return False, 0

        return True, self.data_dict[sts_id][0]

    def getData(self, sts_id, address, data_length):
        """
        获取同步读取的数据:
        - sts_id: 舵机 ID
        - address: 数据地址
        - data_length: 数据长度
        """
        if data_length == 1:
            return self.data_dict[sts_id][address - self.start_address + 1]
        elif data_length == 2:
            return self.ph.scs_makeword(self.data_dict[sts_id][address - self.start_address + 1],
                                        self.data_dict[sts_id][address - self.start_address + 2])
        elif data_length == 4:
            return self.ph.scs_makedword(
                self.ph.scs_makeword(self.data_dict[sts_id][address - self.start_address + 1],
                                     self.data_dict[sts_id][address - self.start_address + 2]),
                self.ph.scs_makeword(self.data_dict[sts_id][address - self.start_address + 3],
                                     self.data_dict[sts_id][address - self.start_address + 4]))
        else:
            return 0
