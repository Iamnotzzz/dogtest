#!/usr/bin/env python

import time
import serial
import sys
import platform

# 默认波特率
DEFAULT_BAUDRATE = 1000000
LATENCY_TIMER = 50  # 延迟计时，单位是毫秒

# 串口处理类
class PortHandler(object):
    def __init__(self, port_name):
        """
        初始化函数：
        - port_name: 串口名称（如 "COM3" 或 "/dev/ttyUSB0"）
        """
        self.is_open = False                 # 串口是否已打开
        self.baudrate = DEFAULT_BAUDRATE     # 默认波特率：1M
        self.packet_start_time = 0.0         # 数据包发送的起始时间
        self.packet_timeout = 0.0            # 数据包的超时时间
        self.tx_time_per_byte = 0.0          # 每个字节的传输时间

        self.is_using = False                # 标志位，表示是否被占用
        self.port_name = port_name           # 端口名称
        self.ser = None                      # 串口对象

    def openPort(self):
        """
        打开串口：
        - 实际是调用 `setBaudRate` 来设置波特率并打开端口
        """
        return self.setBaudRate(self.baudrate)

    def closePort(self):
        """
        关闭串口：
        - 关闭串口连接，并设置状态为未打开
        """
        self.ser.close()
        self.is_open = False

    def clearPort(self):
        """
        清空串口缓冲区：
        - 调用 `flush` 清除缓存，避免残留数据
        """
        self.ser.flush()

    def setPortName(self, port_name):
        """
        设置端口名称
        - port_name: 端口名称字符串
        """
        self.port_name = port_name

    def getPortName(self):
        """
        获取端口名称
        """
        return self.port_name

    def setBaudRate(self, baudrate):
        """
        设置波特率:
        - baudrate: 要设置的波特率值
        - 首先检查是否是支持的波特率，通过 `getCFlagBaud` 函数
        - 如果支持则调用 `setupPort` 进行串口配置
        """
        baud = self.getCFlagBaud(baudrate)

        if baud <= 0:
            # 如果波特率不被支持，返回 False
            return False
        else:
            # 设置波特率并配置串口
            self.baudrate = baudrate
            return self.setupPort(baud)

    def getBaudRate(self):
        """
        获取当前波特率
        """
        return self.baudrate

    def getBytesAvailable(self):
        """
        获取串口缓冲区中可读取的字节数:
        - 使用 `in_waiting` 属性查询
        """
        return self.ser.in_waiting

    def readPort(self, length):
        """
        从串口读取数据:
        - length: 要读取的字节数
        - 根据 Python 版本选择读取方式
        - Python 3 直接读取
        - Python 2 逐字符读取并转换为 ASCII
        """
        if (sys.version_info > (3, 0)):
            return self.ser.read(length)  # Python 3 直接返回字节数据
        else:
            return [ord(ch) for ch in self.ser.read(length)]  # Python 2 需要转 ASCII

    def writePort(self, packet):
        """
        向串口写入数据:
        - packet: 要发送的数据包
        """
        return self.ser.write(packet)

    def setPacketTimeout(self, packet_length):
        """
        设置数据包的超时时间:
        - packet_length: 数据包的长度
        - 根据波特率和延迟时间计算超时
        """
        self.packet_start_time = self.getCurrentTime()
        self.packet_timeout = (self.tx_time_per_byte * packet_length) + (self.tx_time_per_byte * 3.0) + LATENCY_TIMER

    def setPacketTimeoutMillis(self, msec):
        """
        直接设置超时时间（毫秒）:
        - msec: 超时时间
        """
        self.packet_start_time = self.getCurrentTime()
        self.packet_timeout = msec

    def isPacketTimeout(self):
        """
        检测数据包是否超时:
        - 如果当前时间超过了超时设定，返回 True
        - 否则返回 False
        """
        if self.getTimeSinceStart() > self.packet_timeout:
            self.packet_timeout = 0  # 清空超时计时
            return True

        return False

    def getCurrentTime(self):
        """
        获取当前时间 (单位：毫秒):
        - 使用 `time.time()` 获取当前时间戳并转换为毫秒
        """
        return round(time.time() * 1000000000) / 1000000.0

    def getTimeSinceStart(self):
        """
        获取从数据包开始发送到现在的时间差:
        - 如果时间差为负数，重新获取当前时间
        """
        time_since = self.getCurrentTime() - self.packet_start_time
        if time_since < 0.0:
            self.packet_start_time = self.getCurrentTime()

        return time_since

    def setupPort(self, cflag_baud):
        """
        初始化串口:
        - 配置端口的波特率，数据位，停止位等信息
        - 使用 `serial.Serial` 打开串口
        """
        if self.is_open:
            self.closePort()

        # 初始化串口配置
        self.ser = serial.Serial(
            port=self.port_name,      # 端口名称
            baudrate=self.baudrate,   # 波特率
            bytesize=serial.EIGHTBITS, # 8位数据位
            timeout=0                 # 无阻塞超时
        )

        self.is_open = True  # 设置状态为打开

        self.ser.reset_input_buffer()  # 清空输入缓存

        # 计算每个字节的传输时间
        self.tx_time_per_byte = (1000.0 / self.baudrate) * 10.0

        return True

    def getCFlagBaud(self, baudrate):
        """
        获取支持的波特率:
        - 如果传入的波特率在支持列表中，则返回该值
        - 否则返回 -1 表示不支持
        """
        if baudrate in [4800, 9600, 14400, 19200, 38400, 57600, 115200, 128000, 250000, 500000, 1000000]:
            return baudrate
        else:
            return -1
