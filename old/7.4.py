import cv2
import pyrealsense2 as rs
import numpy as np
import math
import scipy.stats
import os
import struct
import socket
import cv2 as cv

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

class PID:
    def __init__(self, Kp, Ki, Kd):
        self.Kp = Kp
        self.Ki = Ki
        self.Kd = Kd
        self.previous_error = 0
        self.integral = 0

    def compute(self, setpoint, measured_value):
        error = setpoint - measured_value
        self.integral += error
        derivative = error - self.previous_error
        output = self.Kp * error + self.Ki * self.integral + self.Kd * derivative
        self.previous_error = error
        return output
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
offset_output = 0
angle_output = 0
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
lower_yellow = np.array([0, 43, 46])  # HSV阈值下界
upper_yellow = np.array([70, 255, 255])  # HSV阈值上界
# 定义机器狗的位置坐标
car_x = 200
car_y = 400
# 定义转弯的阈值
angle_threshold = 90  # 角度
# 加载预定义的字典
dictionary = cv.aruco.Dictionary_get(cv.aruco.DICT_4X4_250)

# 创建 ArUco 检测器
parameters = cv.aruco.DetectorParameters_create()
# PID 参数
Kp_angle = 1.0
Ki_angle = 0.1
Kd_angle = 0.05

Kp_offset = 1.0
Ki_offset = 0.1
Kd_offset = 0.05

# 实例化 PID 控制器
pid_angle = PID(Kp_angle, Ki_angle, Kd_angle)
pid_offset = PID(Kp_offset, Ki_offset, Kd_offset)
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

        # 输出检测到的 ArUco 码的 ID
        if ids is not None and len(ids) > 0:
            marker_id_str = str(ids[0][0])  # 将第一个 ID 转为字符串
            count_huandao = count_huandao + 1 
            print("Detected ArUco markers:")
            print("Marker ID:", marker_id_str)
    # 在图像上绘制检测到的 ArUco 码及其 ID
            cv.aruco.drawDetectedMarkers(frame, corners, ids)
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
                for j in range(450, 150, -1):
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
                for j in range(479, 280, -1):  # (380, 250, -1)
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
            for i in range(280, 380):
                # 从 220 开始，每次减 1，直到 0
                for j in range(0, 300, 1):
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
            if turn_off >= 1 and turn_off_frame - turn_off <= 10 and jishu ==0 :
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

            for i in range(310, 330):
                left = -1

                for j in range(5, 340, 1):
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
                for i in range(310, 330):

                    right = -1
                    for j in range(475, 50, -1):
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

            print("out_turn_off_frame")
            print(out_turn_off_frame)

            print("out_turn_off")
            print(out_turn_off)

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
                y1 = 310
                y2 = 330
                x1 = int(x - (y - y1) * vx / vy)
                x2 = int(x - (y - y2) * vx / vy)
                cv2.line(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
                # 计算偏角（以弧度为单位）
                angle = np.arctan2(y2 - y1, x2 - x1) 
                
                # 计算横向偏移（直线中点与图像中心的距离）
                line_center = (x1 + x2) / 2
                image_center = width / 2
                lateral_offset = line_center - image_center
                angle_output = pid_angle.compute(0, 1.57-angle)  # 设定点为 0，即希望偏角为 0
                offset_output = pid_offset.compute(0, lateral_offset)  # 设定点为 0，即希望横向偏移为 0
		
       		
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
        print("右环岛数目" + str(count))
        prev_slope_a = slope_a
        out_prev_slope_a = out_slope_a
        # 试验颜色
        # cv2.line(frame, (10, 10), (200, 200), (234, 77, 87), 2)
        # 显示原始图像和中线图像

        cv2.imshow("Now Frame", frame)

        # cv2.imshow("Now Binary Frame", binary)
        # cv2.imshow("Centerline Image", centerline)
        # float_number = 12.34

        float_number_2 = lateral_offset
        float_number_3 = 0
        control_message = "{:.2f}|{:.2f}|{:.2f}|{}".format(angle_output, offset_output, float_number_3, marker_id_str)
        connection.sendall(control_message.encode())
        print("发送控制信息给客户端:", control_message)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
        # 及时释放内存

finally:


    # 关闭连接
    # connection.close()
    pipeline.stop()
    # cap.release()
    cv2.destroyAllWindows()
