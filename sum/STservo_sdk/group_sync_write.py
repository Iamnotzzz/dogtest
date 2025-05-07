#!/usr/bin/env python

from .stservo_def import *  # 导入 stservo_def 模块中的所有内容

# 定义一个同步写入的类 GroupSyncWrite
class GroupSyncWrite:
    def __init__(self, ph, start_address, data_length):
        """
        初始化函数：
        - ph: PacketHandler对象，用于处理通信协议
        - start_address: 写入数据的起始地址
        - data_length: 写入数据的长度
        """
        self.ph = ph                            # 通信协议处理对象
        self.start_address = start_address      # 起始地址
        self.data_length = data_length          # 数据长度

        self.is_param_changed = False           # 参数是否有更新
        self.param = []                         # 同步写入的参数列表
        self.data_dict = {}                     # 存储要写入的数据字典

        self.clearParam()                       # 初始化时清空参数

    def makeParam(self):
        """
        构建同步写入的参数列表:
        - 遍历 `data_dict` 中的所有 ID
        - 依次将 ID 和对应的数据添加到 `param` 中
        """
        if not self.data_dict:
            return

        self.param = []  # 先清空列表

        for sts_id in self.data_dict:
            if not self.data_dict[sts_id]:
                return
            # 先添加舵机 ID，再添加对应的数据
            self.param.append(sts_id)
            self.param.extend(self.data_dict[sts_id])

    def addParam(self, sts_id, data):
        """
        添加同步写入参数:
        - sts_id: 舵机 ID
        - data: 要写入的数据
        - 如果 ID 已存在，返回 False
        - 如果数据长度超过设定长度，返回 False
        - 成功添加后，返回 True
        """
        if sts_id in self.data_dict:
            return False  # 如果已经存在，直接返回 False

        if len(data) > self.data_length:
            return False  # 数据长度超过限制，返回 False

        self.data_dict[sts_id] = data  # 将数据存储到字典中
        self.is_param_changed = True   # 标记参数有更新
        return True

    def removeParam(self, sts_id):
        """
        移除指定 ID 的写入参数:
        - sts_id: 要移除的舵机 ID
        - 如果该 ID 不存在，则不执行任何操作
        """
        if sts_id not in self.data_dict:
            return

        del self.data_dict[sts_id]
        self.is_param_changed = True

    def changeParam(self, sts_id, data):
        """
        修改同步写入的参数:
        - sts_id: 舵机 ID
        - data: 新的数据
        - 如果 ID 不存在，返回 False
        - 如果数据长度超过设定长度，返回 False
        - 成功修改后，返回 True
        """
        if sts_id not in self.data_dict:
            return False

        if len(data) > self.data_length:
            return False

        self.data_dict[sts_id] = data
        self.is_param_changed = True
        return True

    def clearParam(self):
        """
        清空所有同步写入的参数:
        - 清空 `data_dict`，相当于重置
        """
        self.data_dict.clear()

    def txPacket(self):
        """
        发送同步写入指令:
        - 先检查是否有要发送的数据
        - 如果参数有变化或 `param` 为空，则重新构建参数列表
        - 使用 PacketHandler 执行同步写入操作
        """
        if len(self.data_dict.keys()) == 0:
            return COMM_NOT_AVAILABLE  # 如果没有任何数据要发送，返回错误状态

        if self.is_param_changed is True or not self.param:
            self.makeParam()  # 如果参数有更新或者为空，则重新构建

        # 调用 PacketHandler 中的 `syncWriteTxOnly` 进行同步发送
        return self.ph.syncWriteTxOnly(
            self.start_address,                  # 起始地址
            self.data_length,                    # 数据长度
            self.param,                          # 构建好的参数列表
            len(self.data_dict.keys()) * (1 + self.data_length)  # 计算包的总长度
        )
