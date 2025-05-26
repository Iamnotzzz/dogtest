import numpy as np
import cv2
import time
import math
import socket
import cv2 as cv
import threading
from STservo_sdk import PortHandler, sts, COMM_SUCCESS
import serial
import sys
import signal
import json

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
        # 第一次识别到12时执行抓取
        if marker_detection_count == 0 and (marker_id == '1' or marker_id == '2'):
            # 保证机械臂爪子在原位
            send_data_to_serial(ser, json_commands_set6)
            move_servo_to_position(packetHandler, STS_ID, STS_MAXIMUM_POSITION_VALUE, STS_MOVING_SPEED,
                                   STS_MOVING_ACC)
            time.sleep(2)
            # 向右转下去(松)
            send_data_to_serial(ser, json_commands_set5)
            time.sleep(2)
            # 机械臂爪子抓取
            send_data_to_serial(ser, json_commands_set4)
            # 驱动板爪子抓取
            move_servo_to_position(packetHandler, STS_ID, STS_MINIMUM_POSITION_VALUE, STS_MOVING_SPEED,
                                   STS_MOVING_ACC)
            time.sleep(2)
            # 复位（抓）
            send_data_to_serial(ser, json_commands_set3)
            marker_detection_count = marker_detection_count + 1
            last_command_time = current_time  # 更新最后执行指令的时间

        # 自上次执行指令过去五秒且不是第一次识别到时
        if current_time - last_command_time > 5 and marker_detection_count != 0:
            if marker_id == '1':
                time.sleep(2)
                # 向左机械臂爪子放
                send_data_to_serial(ser, json_commands_set1)
                marker_detection_count = marker_detection_count + 1
            elif marker_id == '2':
                time.sleep(1)
                # 向左下去(放)
                send_data_to_serial(ser, json_commands_set7)
                # 驱动板爪子放
                move_servo_to_position(packetHandler, STS_ID, STS_MAXIMUM_POSITION_VALUE, 1000,
                                       STS_MOVING_ACC)
                time.sleep(0.5)
                # 复位（放）
                send_data_to_serial(ser, json_commands_set2)
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

# 设置黄色的HSV范围
lower_yellow = np.array([20, 43, 46])
upper_yellow = np.array([50, 255, 255])

# 创建UDP socket
udp_client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# 服务器地址和端口
server_address = ('192.168.123.18', 1234)

# 初始化摄像头
camera = cv2.VideoCapture(0)  # 0通常是默认的摄像头
marker_id_int = 789
# PID参数
Kp = 1
Kd = 0
previous_angle = 0

# ArUco字典和检测器参数
aruco_dictionary = cv.aruco.Dictionary_get(cv.aruco.DICT_4X4_250)
aruco_parameters = cv.aruco.DetectorParameters_create()

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
STS_MAXIMUM_POSITION_VALUE = 3900  # 假定的舵机最大位置值
STS_MINIMUM_POSITION_VALUE = 3400  # 假定的舵机最小位置值
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


try:
    while True:
        ret, frame = camera.read()
        if not ret:
            break

        gray_frame = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)
        corners, ids, _ = cv.aruco.detectMarkers(gray_frame, aruco_dictionary, parameters=aruco_parameters)

        # 向左放下
        json_commands_set1 = [
            {"T": 121, "joint": 1, "angle": 90, "spd": 90, "acc": 10},
            {"T": 122, "b": 90, "s": 100, "e": 75, "h": 155, "spd": 90, "acc": 10},
            {"T": 106, "cmd": 3.5, "spd": 800, "acc": 10},
            {"T": 121, "joint": 2, "angle": 30, "spd": 90, "acc": 10},
            {"T": 122, "b": 0, "s": 0, "e": 160, "h": 201, "spd": 90, "acc": 10}
        ]

        # 复位（throw）
        json_commands_set2 = [
            {"T": 121, "joint": 2, "angle": 30, "spd": 90, "acc": 10},
            {"T": 122, "b": 0, "s": 0, "e": 160, "h": 201, "spd": 90, "acc": 10}
         ]

        # 复位(grab)
        json_commands_set3 = [
            {"T": 121, "joint": 2, "angle": 30, "spd": 90, "acc": 10},
            {"T": 122, "b": 0, "s": 0, "e": 160, "h": 155, "spd": 90, "acc": 10}
        ]

        # 机械臂爪子抓取
        json_commands_set4 = [
            {"T": 106, "cmd": 2.7, "spd": 800, "acc": 10}
        ]

        # 向右转抓取下(throw)
        json_commands_set5 = [
            {"T": 121, "joint": 1, "angle": -90, "spd": 90, "acc": 10},
            {"T": 122, "b": -90, "s": 78, "e": 90, "h": 201, "spd": 90, "acc": 10}
        ]

        # 保证机械臂在原位(throw)
        json_commands_set6 = [
            {"T": 122, "b": 0, "s": 0, "e": 160, "h": 201, "spd": 90, "acc": 10}
        ]

        # 向左转并下去(quickly)
        json_commands_set7 = [
            {"T": 121, "joint": 1, "angle": 90, "spd": 120, "acc": 10},
            {"T": 122, "b": 90, "s": 100, "e": 75, "h": 201, "spd": 100, "acc": 10},
        ]

        if ids is not None and len(ids) > 0:
            marker_id_str = str(ids[0][0])
            marker_id_int = int(marker_id_str)  # 转换为整形
            print("Detected ArUco markers:")
            print("Marker ID:", marker_id_str)
            on_aruco_marker_detected(global_ser, marker_id_str)
            cv.aruco.drawDetectedMarkers(frame, corners, ids)
        else:
            marker_id_str = "789"
            marker_id_int = int(marker_id_str)  # 转换为整形
            cv.aruco.drawDetectedMarkers(frame, corners, ids)

        resized_frame = cv2.resize(frame, dsize=(120, 120))
        blurred_frame = cv2.GaussianBlur(resized_frame, (7, 7), 3)
        hsv_frame = cv2.cvtColor(blurred_frame, cv2.COLOR_BGR2HSV)
        binary_frame = cv2.inRange(hsv_frame, lower_yellow, upper_yellow)
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        morph_frame = cv2.morphologyEx(binary_frame, cv2.MORPH_CLOSE, kernel, iterations=2)

        inverted_frame = cv2.bitwise_not(morph_frame)
        contours, _ = cv2.findContours(inverted_frame, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        area_threshold = 240

        for contour in contours:
            area = cv2.contourArea(contour)
            if area < area_threshold:
                cv2.drawContours(morph_frame, [contour], -1, (255, 255, 255), thickness=cv2.FILLED)

        frame_height, frame_width = resized_frame.shape[:2]
        mid_x = start_x = end_x = int(frame_width / 2)
        start_y = original_y = 119
        end_y = 0
        end_y_param = 100
        expected_length = length = original_y - end_y + 1
        left_bound = right_bound = mid_x
        left_edge = right_edge = 0
        left_line_points = []
        right_line_points = []
        mid_line_points = []
        distance = angle = loss_count = 0
        upper_bound_reached = lower_bound_reached = mid_loss_detected = 0

        while True:
            if right_bound >= morph_frame.shape[1]:
                break
            if morph_frame[start_y, left_bound] == 255:
                start_x = left_bound
                break
            if morph_frame[start_y, right_bound] == 255:
                start_x = right_bound
                break
            left_bound -= 1
            right_bound += 1

        x = start_x

        while start_y >= end_y:
            if morph_frame[start_y, start_x] == 0 and len(left_line_points) > 5:
                for i in range(left_line_points[-1], right_line_points[-1]):
                    if morph_frame[start_y, i] == 255:
                        start_x = i
                        break
                    if i == right_line_points[-1] - 1:
                        mid_loss_detected = 1
                if mid_loss_detected == 1:
                    break

            right_edge = left_edge = start_x
            while morph_frame[start_y, right_edge] == 255 and right_edge < frame_width - 1:
                right_edge += 1
            right_line_points.append(right_edge)

            while morph_frame[start_y, left_edge] == 255 and left_edge > 0:
                left_edge -= 1
            left_line_points.append(left_edge)

            start_x = int((left_edge + right_edge) / 2)
            mid_line_points.append(start_x)
            resized_frame[start_y, left_edge] = (255, 0, 0)
            resized_frame[start_y, right_edge] = (0, 0, 255)
            resized_frame[start_y, start_x] = (0, 255, 0)

            if start_y == original_y:
                mid_x = start_x
            start_y -= 1

        expected_length = len(left_line_points)
        y = original_y

        while y >= end_y_param:
            right_edge = left_edge = x
            while morph_frame[y, right_edge] == 255 and right_edge < frame_width - 1:
                right_edge += 1
            while morph_frame[y, left_edge] == 255 and left_edge > 0:
                left_edge -= 1
            x = int((left_edge + right_edge) / 2)
            if y == original_y:
                original_x = x
            y -= 1

        distance = (frame_width / 2 - original_x) * 0.02
        angle = math.atan2(119 - end_y_param, x - 60) - math.pi * 0.5
        final_angle = angle
        error = final_angle - previous_angle
        pd_angle = Kp * angle + Kd * error
        previous_angle = final_angle
        message = f"{distance:.2f}, {pd_angle:.2f},{marker_id_int}"
        udp_client_socket.sendto(message.encode(), server_address)

        cv2.line(morph_frame, (60, original_y), (x, end_y_param), (0, 0, 255), 1)
        cv2.line(morph_frame, (original_x, original_y), (x, end_y_param), (0, 0, 255), 1)

        resized_frame = cv2.resize(resized_frame, dsize=(400, 400))
        cv2.imshow("Frame", resized_frame)

        morph_frame = cv2.resize(morph_frame, dsize=(400, 400))
        cv2.imshow("Binary Image", morph_frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

finally:
    camera.release()
    cv2.destroyAllWindows()
    udp_client_socket.close()
    end_time = time.time()
    udp_client_socket.close()

    # 关闭串口
    if global_ser.isOpen():
        global_ser.close()
        print("机械臂串口已关闭")

    if portHandler.openPort():
        portHandler.closePort()  # 确保端口在使用后被关闭
        print("驱动板串口已关闭")
