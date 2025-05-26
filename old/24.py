import cv2
import pyrealsense2 as rs
import numpy as np
import math
import scipy.stats
import os
import struct
import time
import socket
import threading
import json
import cv2 as cv
import serial
import sys
import signal
from STservo_sdk import PortHandler, sts, COMM_SUCCESS

# 全局变量定义在最顶部
global_ser = None
exit_flag = False  # 新增一个退出标志
last_command_time = 0
marker_detection_count = 0  # 执行指令的次数

# 初始化串口
# 修改 send_data_to_serial 函数，使其可以发送JSON指令集
def send_data_to_serial(ser, commands):
    global exit_flag
    for cmd in commands:
        json_bytes = json.dumps(cmd).encode('utf-8') + b'\n'
        ser.write(json_bytes)
        print(f"Sent: {cmd}")
        time.sleep(1)  # 根据指令集1和2，每条指令间隔2秒

# 信号处理器
def signal_handler(portHandler):
    print('\nExiting program')
    portHandler.closePort()
    sys.exit(0)

# 移动舵机到指定位置的函数
def move_servo_to_position(packetHandler, STS_ID, position_value, speed, acc):
    sts_comm_result, sts_error = packetHandler.WritePosEx(STS_ID, position_value, speed, acc)
    if sts_comm_result != COMM_SUCCESS or sts_error != 0:
        print("Failed to move to position")

# 在检测到ArUco码时调用的函数
def on_aruco_marker_detected(ser, marker_id):

    def process_marker():
        global last_command_time, marker_detection_count  # 声明全局变量
        current_time = time.time()  # 获取当前时间
        # 第一次识别到24时执行抓取
        if marker_detection_count == 0 and (marker_id == '2' or marker_id == '4'):
            # 保证机械臂爪子在原位
            send_data_to_serial(ser, json_commands_set6)
            move_servo_to_position(packetHandler, STS_ID, STS_MAXIMUM_POSITION_VALUE, STS_MOVING_SPEED,
                                   STS_MOVING_ACC)
            time.sleep(2)
            # 向右转下去
            send_data_to_serial(ser, json_commands_set5)
            time.sleep(2)
            # 机械臂爪子抓取
            send_data_to_serial(ser, json_commands_set4)
            # 驱动板爪子抓取
            move_servo_to_position(packetHandler, STS_ID, STS_MINIMUM_POSITION_VALUE, STS_MOVING_SPEED,
                                   STS_MOVING_ACC)
            time.sleep(2)
            # 复位
            send_data_to_serial(ser, json_commands_set3)
            marker_detection_count = marker_detection_count + 1
            last_command_time = current_time  # 更新最后执行指令的时间

        # 自上次执行指令过去五秒且不是第一次识别到时
        if current_time - last_command_time > 5 and marker_detection_count !=0:
            if marker_id == '2':
                time.sleep(1)
                # 向左机械臂爪子放
                send_data_to_serial(ser, json_commands_set1)
                marker_detection_count = marker_detection_count + 1
            elif marker_id == '4':
                time.sleep(2)
                # 向右下去
                send_data_to_serial(ser, json_commands_set7)
                # 驱动板爪子放
                move_servo_to_position(packetHandler, STS_ID, STS_MAXIMUM_POSITION_VALUE, 1200,
                                               STS_MOVING_ACC)
                time.sleep(0.5)
                # 复位
                send_data_to_serial(ser, json_commands_set3)
                marker_detection_count = marker_detection_count + 1

            last_command_time = current_time  # 更新最后执行指令的时间

    # 创建一个线程来处理 ArUco 码的检测，这样主程序就不会被阻塞
    marker_thread = threading.Thread(target=process_marker)
    marker_thread.start()


# 串行读取函数
def read_serial(ser):
    global exit_flag
    while not exit_flag:
        data = ser.readline().decode('utf-8')
        if data:
            print(f"Received: {data}")

# 发送JSON指令集函数
def send_json_commands(ser, commands):
    for cmd in commands:
        json_bytes = json.dumps(cmd).encode('utf-8') + b'\n'
        ser.write(json_bytes)
        print(f"发送json指令: {cmd}")
        time.sleep(1)  # 延时2秒

pipeline = rs.pipeline()
config = rs.config()
config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)

# 创建一个TCP socket
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# 定义服务器地址和端口
server_address = ('0.0.0.0', 12346)  # 使用任意地址 0.0.0.0，端口为 12345

# 绑定服务器地址和端口
server_socket.bind(server_address)

# 监听连接请求
server_socket.listen(1)

print("等待连接...")
connection, client_address = server_socket.accept()
# 启动摄像头
pipeline.start(config)

# 初始化串行端口
try:
    global_ser = serial.Serial('/dev/ttyUSB0', baudrate=115200, dsrdtr=None)
except Exception as e:
    print(f"Failed to open serial port: {e}")
    sys.exit(1)

global_ser.setRTS(False)
global_ser.setDTR(False)

# 创建并启动读取线程
serial_recv_thread = threading.Thread(target=read_serial, args=(global_ser,))
serial_recv_thread.daemon = True
serial_recv_thread.start()

# 默认设置
STS_ID = 14  # 假定的STServo ID
BAUDRATE = 1000000  # 假定的波特率
DEVICENAME = '/dev/ttyACM0'  # 假定的设备名称
STS_MAXIMUM_POSITION_VALUE = 1400  # 假定的舵机最大位置值
STS_MINIMUM_POSITION_VALUE = 600  # 假定的舵机最小位置值
STS_MOVING_SPEED = 800  # 假定的移动速度
STS_MOVING_ACC = 10  # 假定的加速度

# 初始化端口处理器和数据包处理器
portHandler = PortHandler(DEVICENAME)
packetHandler = sts(portHandler)

# 绑定 SIGINT 信号到信号处理器
signal.signal(signal.SIGINT, signal_handler)

# 打开串口及设置波特率
if portHandler.openPort():
    print("成功打开串口")
    if portHandler.setBaudRate(BAUDRATE):
        print("成功设置波特率")

def can_be_enclosed_in_circle(points, radius):
    """检查给定的点是否可以被一个指定半径的圆包裹"""
    for i in range(len(points)):
        for j in range(i + 1, len(points)):
            if np.linalg.norm(np.array(points[i]) - np.array(points[j])) > 2 * radius:
                return False
    return True

jishu = 0
add_line = False
lateral_offset = 0
count_huandao = 0
# 离开双岔路的计数器
out_turn_off = 0
angle = 0.0
out_left_turnabout = 0
# 储存识别离开左环岛的右下拐点的列表
out_left_turnabout1 = []
# 储存识别离开左环岛的上拐点的列表
out_left_turnabout2 = []
out_max_i = 0
start_up = 220
start_down = 220
upper_point_x = 0
upper_point_y = 0
lower_point_x = 0
lower_point_y = 0
turn_off = 0
min_j = 500
error_prev = 0
min_j_i = 500
slope_a = 0
prev_slope_a = 0
out_slope_a = 0
adjusted_angle = 0
out_prev_slope_a = 0
end_j = 0
end_j_i = 0
points = np.zeros(400)
isline = False
left_roundabout = 0
right_roundabout = 0
max_j = 0
marker_id_str = "None"
prev_min_j = 0
prev_min_j_i = 0
# 创建一个变量，用于记录上一次的横坐标
last_x = None
is_increasing_then_decreasing = False
is_increasing_then_decreasing_a = False
is_increasing_then_decreasing_b = False
is_increasing_then_decreasing_c = False
# 创建一个变量，用于记录上一次的变化方向
last_dir = None
black_pixels = []
white_pixels = []
upper_turning_point = []
lower_turning_point1 = []
lower_turning_point2 = []
out_upper_turning_point = []
mid_turn_off = []
# 岔路中拐点
mid_list = []
# 定义两个列表，用于存储左右像素点的横坐标
left_list = []
right_list = []
start = 240
# 定义一个变量，用于存储"cuizhi"出现的次数
cuizhi_count = 0
# 新增一个变量，用于记录检测到环岛的帧数
roundabout_frame = 0
turn_off_frame = 0
out_turn_off_frame = 0
# 定义一个变量，用于存储跳过的帧数
skip_frames = 0
lower_yellow = np.array([15, 25, 46])  # HSV阈值下界
upper_yellow = np.array([50, 255, 255])  # HSV阈值上界
# 定义机器狗的位置坐标
car_x = 200
hei = 0
car_y = 400
# 定义转弯的阈值
angle_threshold = 90  # 角度
# 加载预定义的字典
dictionary = cv.aruco.Dictionary_get(cv.aruco.DICT_4X4_250)

# 创建 ArUco 检测器
parameters = cv.aruco.DetectorParameters_create()
try:
    print("连接成功:", client_address)
    while True:

        out_left_turnabout2.clear()
        out_left_turnabout1.clear()
        is_increasing_then_decreasing_out_b = False
        is_increasing_then_decreasing_out_a = False
        black_pixels.clear()
        white_pixels.clear()
        upper_turning_point.clear()
        lower_turning_point1.clear()
        lower_turning_point2.clear()
        out_upper_turning_point.clear()
        mid_turn_off.clear()
        isline = False
        max_j = 0
        min_j = 500
        out_max_i = 0
        is_increasing_then_decreasing = 0
        is_increasing_then_decreasing_a = False
        is_increasing_then_decreasing_b = False
        is_increasing_then_decreasing_c = False
        # 从管道读取JPEG数据的大小
        frames = pipeline.wait_for_frames()
        color_frame = frames.get_color_frame()
        if not color_frame:
            continue
        frame2 = np.asanyarray(color_frame.get_data())
        frame = cv2.resize(frame2, (480, 400))
        gray = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)

        # 检测 ArUco 码
        corners, ids, rejectedImgPoints = cv.aruco.detectMarkers(gray, dictionary, parameters=parameters)

        # 向左放下
        json_commands_set1 = [
            {"T": 121, "joint": 1, "angle": 90, "spd": 90, "acc": 10},
            {"T": 122, "b": 90, "s": 100, "e": 75, "h": 229, "spd": 90, "acc": 10},
            {"T": 106, "cmd": 3.4, "spd": 800, "acc": 0},
            {"T": 121, "joint": 2, "angle": 30, "spd": 90, "acc": 10},
            {"T": 122, "b": 0, "s": 0, "e": 160, "h": 190, "spd": 90, "acc": 10}
        ]

        # 向右转并下去
        json_commands_set2 = [
            {"T": 121, "joint": 1, "angle": -90, "spd": 90, "acc": 10},
            {"T": 122, "b": -90, "s": 100, "e": 75, "h":229, "spd": 90, "acc": 10},
            {"T": 106, "cmd": 4, "spd": 800, "acc": 0}
        ]

        # 复位(grab)
        json_commands_set3 = [
            {"T": 121, "joint": 2, "angle": 30, "spd": 90, "acc": 10},
            {"T": 122, "b": 0, "s": 0, "e": 160, "h": 229, "spd": 90, "acc": 10}
        ]

        # 机械臂爪子抓取
        json_commands_set4 = [
            {"T": 106, "cmd": 4, "spd": 800, "acc": 0}
        ]

        # 向右转抓取下(throw)
        json_commands_set5 = [
            {"T": 121, "joint": 1, "angle": -90, "spd": 90, "acc": 10},
            {"T": 122, "b": -90, "s": 100, "e": 75, "h": 190, "spd": 90, "acc": 10},
        ]

        # 保证机械臂在原位(throw)
        json_commands_set6 = [
            {"T": 122, "b": 0, "s": 0, "e": 160, "h": 190, "spd": 90, "acc": 10}
        ]

        # 向右转并下去(quickly)
        json_commands_set7 = [
            {"T": 121, "joint": 1, "angle": -90, "spd": 120, "acc": 10},
            {"T": 122, "b": -90, "s": 100, "e": 75, "h": 229, "spd": 100, "acc": 10},
        ]


        # 输出检测到的 ArUco 码的 ID
        if ids is not None and len(ids) > 0:
            marker_id_str = str(ids[0][0])  # 将第一个 ID 转为字符串
            count_huandao = count_huandao + 1
            print("Detected ArUco markers:")
            print("Marker ID:", marker_id_str)
            on_aruco_marker_detected(global_ser, marker_id_str)
            # 在图像上绘制检测到的 ArUco 码及其 ID
            cv.aruco.drawDetectedMarkers(frame, corners, ids)
            # 根据 ArUco 码 ID 输出物块类型
            if marker_id_str == "1":
                print("球")
            elif marker_id_str == "2":
                print("正方体")
            elif marker_id_str == "3":
                print("三棱锥")
            elif marker_id_str == "4":
                print("圆柱")
        else:
            marker_id_str = "0"
            cv.aruco.drawDetectedMarkers(frame, corners, ids)
        # 在这里对帧进行图像处理...
        frame_blurred = cv2.GaussianBlur(frame, (13, 13), 10, 20)
        # 转换成HSV格式
        hsv = cv2.cvtColor(frame_blurred, cv2.COLOR_BGR2HSV)
        # 得到二值化图像
        bin = cv2.inRange(hsv, lower_yellow, upper_yellow)
        # 形态学操作：闭运算
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        close = cv2.morphologyEx(bin, cv2.MORPH_CLOSE, kernel, iterations=2)
        # 使用 connectedComponentsWithStats() 函数找出所有连通域
        num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(close, connectivity=8)
        # 初始化最近车道的信息
        closest_lane_distance = float('inf')
        closest_lane_index = -1
        # 遍历每个连通域
        for i in range(1, num_labels):
            # 计算连通区域的面积
            area = stats[i, cv2.CC_STAT_AREA]
            if area > 5000:  # 根据面积筛选车道
                cnt = np.where(labels == i, 255, 0).astype(np.uint8)
                cnt = cv2.findContours(cnt, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[0][0]
                rect = cv2.minAreaRect(cnt)
                # 计算矩形的中心点坐标
                cx, cy = centroids[i]
                # 计算与机器狗位置的距离
                distance = np.sqrt((cx - car_x) ** 2 + (cy - car_y) ** 2)
                # 更新最近车道信息
                if distance < closest_lane_distance:
                    closest_lane_distance = distance
                    closest_lane_index = i
        # 创建一个空白的掩膜
        mask = np.zeros_like(close)
        # 处理最近的车道
        if closest_lane_index != -1:
            # 提取最近车道的信息
            mask[labels == closest_lane_index] = 255
            cnt = np.where(labels == closest_lane_index, 255, 0).astype(np.uint8)
            cnt = cv2.findContours(cnt, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[0][0]
            rect = cv2.minAreaRect(cnt)
            box = cv2.boxPoints(rect)
            box = np.int0(box)
            # 循迹功能
            # [这里添加计算转弯角度和控制电机的代码]
        # 使用掩膜和原始图像进行按位与操作，得到过滤后的图像
        filtered = cv2.bitwise_and(frame, frame, mask=mask)
        # 显示原始图像
        cv2.imshow("Original Frame", frame)
        # 显示过滤后的图像
        # cv2.imshow("Filtered Frame", filtered)
        # 转换过滤后的图像为灰度图像
        gray = cv2.cvtColor(filtered, cv2.COLOR_BGR2GRAY)
        # 使用自动阈值选择方法
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        # 获取图像的高度和宽度
        height, width = binary.shape
        frame = cv2.cvtColor(binary, cv2.COLOR_GRAY2BGR)
        # 如果选择水平方向
        if True:
            '''******************************双岔路检测加补线************************************************************'''
        if out_turn_off < 1:

            '''******************************右中拐点检测************************************************************'''
            for i in range(50, 350):
                # 从 220 开始，每次减 1，直到 0
                white_found = False
                for j in range(450, 180, -1):
                    # 如果遇到白色像素点，就把它的横坐标添加到数组中，并跳出循环
                    if binary[i][j] == 255:
                        # upper_turning_point.append(i)
                        # lower_turning_point1.append(j)
                        white_found = True

                        # cv2.circle(frame, (j, i), 2, (0, 0, 255), -1)
                    elif white_found and binary[i][j] == 0:
                        # lower_turning_point2.append(j)
                        mid_turn_off.append(j)

                        max_j = j
                        max_j_i = i

                        # cv2.circle(frame, (j, i), 5, (0, 255, 255), -1)
                        # 表示找到了拐点，跳出循环
                        break
            # cv2.circle(frame, (max_j, max_j_i), 2, (97, 97, 255), -1)

            '''******************************右下拐点检测************************************************************'''
            for i in range(280, 399):
                # 从 220 开始，每次减 1，直到 0
                for j in range(479, 300, -1):  # (380, 250, -1)
                    # 如果遇到白色像素点，就把它的横坐标添加到数组中，并跳出循环
                    if binary[i][j] == 255:
                        # upper_turning_point.append(i)
                        lower_turning_point1.append(j)
                        # 如果当前的 j 值比最小的 j 值小，就更新最小的 j 值，并画出这个点
                        if j < min_j:
                            min_j = j
                            min_j_i = i

                        # cv2.circle(frame, (j, i), 2, (0, 0, 255), -1)
                        break
            # cv2.circle(frame, (min_j, min_j_i), 10, (97, 97, 255), -1)
            # 画一条黑色的线，连接两个点 (max_j, max_j) 和 (min_j, min_j_i)

            '''******************************左下拐点检测************************************************************'''
            for i in range(280, 390):
                # 从 220 开始，每次减 1，直到 0
                for j in range(0, 240, 1):
                    # 如果遇到白色像素点，就把它的横坐标添加到数组中，并跳出循环
                    if binary[i][j] == 255:
                        # upper_turning_point.append(i)
                        lower_turning_point2.append(j)

                        # cv2.circle(frame, (j, i), 2, (97, 0, 255), -1)
                        break

            data3 = np.array(lower_turning_point1)

            data4 = np.array(lower_turning_point2)

            data5 = np.array(mid_turn_off)
            # print(data3)
            # 新增一个 if 语句，检查 data3 是否为空
            if len(data3) > 10:
                # 去除值为380的数据
                data3 = data3[np.where(data3 != 380)]
                if len(data3) > 10:
                    min_index = np.argmin(data3)
                    is_increasing_then_decreasing_a = np.all(
                        np.all(np.diff(data3[:min_index]) <= 0) and np.all(np.diff(data3[min_index:]) >= 0))
                    if min_index == len(data3) - 1 or min_index == 0:
                        is_increasing_then_decreasing_a = False

            # 新增一个 if 语句，检查 data4 是否为空
            if len(data4) > 10:
                # 去除值为140的数据
                data4 = data4[np.where(data4 != 140)]
                if len(data4) > 10:
                    max_index = np.argmax(data4)
                    is_increasing_then_decreasing_b = np.all(
                        np.all(np.diff(data4[:max_index]) >= 0) and np.all(np.diff(data4[max_index:]) <= 0))
                    if max_index == len(data4) - 1 or max_index == 0:
                        is_increasing_then_decreasing_b = False

            if len(data5) > 10:
                # 去除值为140的数据
                data5 = data5[np.where(data5 != 450)]
                if len(data5) > 10:
                    max_index = np.argmax(data5)
                    is_increasing_then_decreasing_c = np.all(
                        np.all(np.diff(data5[:max_index]) >= 0) and np.all(np.diff(data5[max_index:]) <= 0))
                    if max_index == len(data5) - 1 or max_index == 0:
                        is_increasing_then_decreasing_c = False

            if is_increasing_then_decreasing_a == True and is_increasing_then_decreasing_b == True and is_increasing_then_decreasing_c == True:
                text = "deleted turn off"
                turn_off += 1
                turn_off_frame = turn_off
                cv2.putText(frame, text, (100, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

            '''******************************进岔路补线************************************************************'''
            if turn_off >= 1 and turn_off_frame - turn_off <= 10 and jishu == 0:
                # 计算斜率
                if max_j - min_j != 0:
                    slope_a = (max_j_i - min_j_i) / (max_j - min_j)
                print("斜率")
                print(slope_a)
                # if roundabout_frame - turn_off < 1000 and turn_off == 1:
                add_line = False
                if slope_a >= 0:
                    cv2.line(frame, (max_j, max_j_i), (min_j, min_j_i), (0, 0, 0), 2)
                    add_line = True
                    # 计算线段的斜率和截距
                    k = slope_a
                    b = max_j_i - k * max_j
                    # 创建一个空的列表来存储点的坐标
                    add_line_points = []
                    # 用一个循环来遍历 x 坐标
                    if max_j < min_j:
                        for x in range(max_j, min_j + 1):
                            # 计算对应的 y 坐标
                            y = k * x + b
                            # 将 x 和 y 组成一个元组并添加到列表中
                            add_line_points.append((x, y))
                    if max_j >= min_j:
                        for x in range(min_j, max_j + 1):
                            # 计算对应的 y 坐标
                            y = k * x + b
                            # 将 x 和 y 组成一个元组并添加到列表中
                            add_line_points.append((x, y))

                if slope_a <= 0:
                    end_j = 399
                    end_j_i = max_j_i + prev_slope_a * (end_j - max_j)
                    end_j_i = int(end_j_i)
                    slope_a = prev_slope_a
                    cv2.line(frame, (max_j, max_j_i), (end_j, end_j_i), (0, 0, 0), 2)
                    add_line = True
                    jishu = jishu + 1
                    # 计算线段的斜率和截距
                    k = slope_a
                    b = max_j_i - k * max_j
                    # 创建一个空的列表来存储点的坐标
                    add_line_points = []
                    # 用一个循环来遍历 x 坐标
                    if max_j < end_j:
                        for x in range(max_j, end_j + 1):
                            # 计算对应的 y 坐标
                            y = k * x + b
                            # 将 x 和 y 组成一个元组并添加到列表中
                            add_line_points.append((x, y))
                    if max_j >= end_j:
                        for x in range(end_j, max_j + 1):
                            # 计算对应的 y 坐标
                            y = k * x + b
                            # 将 x 和 y 组成一个元组并添加到列表中
                            add_line_points.append((x, y))
        '''******************************基础扫线************************************************************'''
        if left_roundabout < 1 or left_roundabout == out_left_turnabout == 1 or left_roundabout == out_left_turnabout == 2 and right_roundabout != 1 and right_roundabout != 3 or right_roundabout == 2 or right_roundabout == 4:

            mid_points = []
            left_points = []
            right_points = []

            for i in range(300, 330):
                left = -1

                for j in range(5, 340, 2):
                    if binary[i][j] == 255:
                        if left == -1:
                            left = j
                            left_points.append((left, i))
                            cv2.circle(frame, (left, i), 2, (0, 255, 0), -1)  # 绿色表示右像素点

            if turn_off >= 1 and turn_off_frame - turn_off <= 12:
                filtered_points = [(x, y) for (x, y) in add_line_points if 310 <= y <= 330]
                right_points = filtered_points

            elif out_turn_off >= 1 and out_turn_off_frame - out_turn_off <= 15:
                filtered_points = [(x, y) for (x, y) in add_line_points if 310 <= y <= 330]
                right_points = filtered_points


            else:
                for i in range(300, 330):

                    right = -1
                    for j in range(475, 50, -2):
                        if binary[i][j] == 255:
                            if right == -1:
                                right = j
                                right_points.append((right, i))
                                cv2.circle(frame, (right, i), 2, (0, 0, 255), -1)  # 绿色表示右像素点
            for (right, a), (left, b) in zip(right_points, left_points):
                # 计算中点的 x 坐标，即 right 和 left 的平均值
                center = (right + left) / 2
                # 把中点的坐标和 y 坐标（假设是 i）放到一个元组里，然后添加到 mid_points
                mid_points.append((center, a))


            # print("左边线")
            # print(left_points)
            # print("右边线")
            # print(right_points)
            # 遍历 right_points 和 left_points 的元素

            # print("中点")
            # print(mid_points)

            # 将点转换为numpy数组
            mid_points = np.array(mid_points, dtype=np.float32)

            # 检查是否有足够的点进行线性拟合
            if len(mid_points) > 1:
                # 使用最小二乘法拟合一条线
                [vx, vy, x, y] = cv2.fitLine(mid_points, cv2.DIST_L2, 0, 0.01, 0.01)

                # 计算用于绘制直线的两个点
                y1 = 300
                y2 = 330
                x1 = int(x - (y - y1) * vx / vy)
                x2 = int(x - (y - y2) * vx / vy)
                cv2.line(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
                angle = 1.57 - np.arctan2(y2 - y1, x2 - x1)

                # 计算横向偏移（直线中点与图像中心的距离）
                line_center = (x1 + x2) / 2
                image_center = width / 2
                lateral_offset = line_center - image_center

                # 在图像上显示偏角和横向偏移
                cv2.putText(frame, f"Angle: {angle:.2f} degrees", (25, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0),
                            1)
                cv2.putText(frame, f"Lateral Offset: {lateral_offset:.2f} pixels", (25, 50), cv2.FONT_HERSHEY_SIMPLEX,
                            0.5,
                            (0, 255, 0), 1)

                # print(data3)
                # print("data3" + str(is_increasing_then_decreasing_a))
                # print(data4)
                # print("data4" + str(is_increasing_then_decreasing_b))

            # min_index = np.argmin(data)

            # 判断数据是否在变化点之前递增，在变化点之后递减
            # is_increasing_then_decreasing_point = np.all(
            # np.all(np.diff(data2[:max_index_point]) >= 0) and np.all(np.diff(data2[max_index_point:]) <= 0))
        count = int((right_roundabout + 1) / 2)
        prev_slope_a = slope_a
        out_prev_slope_a = out_slope_a
        # 试验颜色
        # cv2.line(frame, (10, 10), (200, 200), (234, 77, 87), 2)

        if left_roundabout == 1 and out_left_turnabout < 1:
            txt = "left_roundabout_ing"
            cv2.putText(frame, txt, (300, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
        if left_roundabout == 2 and out_left_turnabout < 2:
            txt = "left_roundabout_ing"
            cv2.putText(frame, txt, (300, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
        if right_roundabout >= 1 and right_roundabout < 2:
            txt = "right_roundabout_ing"
            cv2.putText(frame, txt, (300, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
        if right_roundabout >= 3 and right_roundabout < 4:
            txt = "right_roundabout_ing"
            cv2.putText(frame, txt, (300, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
        # 显示原始图像和中线图像

        cv2.imshow("Now Frame", frame)

        # cv2.imshow("Now Binary Frame", binary)
        # cv2.imshow("Centerline Image", centerline)
        # float_number = 12.34

        data1 = marker_id_str
        float_number_2 = lateral_offset
        float_number_3 = 0
        message_to_send = "{:.2f}|{:.2f}|{:.2f}|{}".format(angle, float_number_2, float_number_3, marker_id_str)
        # message_to_send = "{:.2f}".format(float_number)
        connection.sendall(message_to_send.encode())
        print("发送浮点数给客户端:", message_to_send)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
        # 及时释放内存

finally:

    # 关闭连接
    # connection.close()
    pipeline.stop()
    # cap.release()
    cv2.destroyAllWindows()

    # 关闭串口
    if global_ser.isOpen():
        global_ser.close()
        print("机械臂串口已关闭")

    if portHandler.openPort():
        portHandler.closePort()  # 确保端口在使用后被关闭
        print("驱动板串口已关闭")
