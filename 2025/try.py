import cv2
import numpy as np
import math
import scipy.stats
import socket
import threading

# 视觉参数：直接打开 /dev/video0 摄像头，设置为 60 FPS
cap = cv2.VideoCapture('/dev/video0')
cap.set(cv2.CAP_PROP_FPS, 60)

# 创建一个 TCP socket，用于将处理结果发送给客户端
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_address = ('0.0.0.0', 12346)  # 监听所有网卡，端口 12346
server_socket.bind(server_address)
server_socket.listen(1)

print("等待连接...")
connection, client_address = server_socket.accept()

# 定义用于 ArUco 检测的参数
lower_yellow = np.array([15, 25, 46])   # HSV 阈值下界
upper_yellow = np.array([50, 255, 255]) # HSV 阈值上界
car_x = 200    # 机器狗在图像中的假定位置（用于车道距离计算）
car_y = 400

# 加载 ArUco 预定义字典和检测参数
dictionary = cv2.aruco.Dictionary_get(cv2.aruco.DICT_4X4_250)
parameters = cv2.aruco.DetectorParameters_create()

# 读取摄像头成功标志检查
if not cap.isOpened():
    print("无法打开摄像头 /dev/video0")
    exit(1)

try:
    print("连接成功:", client_address)
    while True:
        # 从摄像头读取一帧
        ret, frame = cap.read()
        if not ret:
            # 如果读取失败，则跳过本次循环
            continue

        # 将帧缩放到 480x400（与之前 RealSense 缩放保持一致）
        frame = cv2.resize(frame, (480, 400))
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # 检测 ArUco 码
        corners, ids, rejectedImgPoints = cv2.aruco.detectMarkers(
            gray, dictionary, parameters=parameters
        )

        # 如果检测到 ArUco 码，则打印 ID 并在图像上绘制
        if ids is not None and len(ids) > 0:
            marker_id_str = str(ids[0][0])
            print("Detected ArUco markers:")
            print("Marker ID:", marker_id_str)
            cv2.aruco.drawDetectedMarkers(frame, corners, ids)

            # 根据 ArUco 码 ID 判断物块类型
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
            cv2.aruco.drawDetectedMarkers(frame, corners, ids)

        # 对帧进行预处理：高斯模糊 + HSV 转换 + 二值化
        frame_blurred = cv2.GaussianBlur(frame, (13, 13), 10, 20)
        hsv = cv2.cvtColor(frame_blurred, cv2.COLOR_BGR2HSV)
        bin_img = cv2.inRange(hsv, lower_yellow, upper_yellow)

        # 形态学闭运算去噪
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        close = cv2.morphologyEx(bin_img, cv2.MORPH_CLOSE, kernel, iterations=2)

        # 使用 connectedComponentsWithStats() 找到所有连通域（可能的车道区域）
        num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(close, connectivity=8)

        closest_lane_distance = float('inf')
        closest_lane_index = -1

        # 遍历每个连通域，根据面积筛选出可能的车道，计算与“机器狗”位置的距离
        for i in range(1, num_labels):
            area = stats[i, cv2.CC_STAT_AREA]
            if area > 5000:
                cnt = np.where(labels == i, 255, 0).astype(np.uint8)
                cnts = cv2.findContours(cnt, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[0]
                if len(cnts) == 0:
                    continue
                cnt0 = cnts[0]
                rect = cv2.minAreaRect(cnt0)
                cx, cy = centroids[i]
                distance = np.sqrt((cx - car_x) ** 2 + (cy - car_y) ** 2)
                if distance < closest_lane_distance:
                    closest_lane_distance = distance
                    closest_lane_index = i

        # 创建一个空白掩膜，并只保留最近车道对应的像素
        mask = np.zeros_like(close)
        if closest_lane_index != -1:
            mask[labels == closest_lane_index] = 255
            cnt = np.where(labels == closest_lane_index, 255, 0).astype(np.uint8)
            cnts = cv2.findContours(cnt, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[0]
            if len(cnts) > 0:
                cnt0 = cnts[0]
                rect = cv2.minAreaRect(cnt0)
                box = cv2.boxPoints(rect)
                box = np.int0(box)
                # （这里可以添加后续对这条车道区域的具体处理，比如拟合直线、计算角度等）
                # 若要在图像上绘制车道轮廓：
                # cv2.drawContours(frame, [box], 0, (0, 255, 0), 2)

        # 筛选出仅保留最近车道区域后的图像
        filtered = cv2.bitwise_and(frame, frame, mask=mask)

        # 显示原始图和过滤后图像（可根据需要取消注释）
        cv2.imshow("Original Frame", frame)
        # cv2.imshow("Filtered Frame", filtered)

        # 将过滤后图像转为灰度并二值化，以便后续扫描
        gray_f = cv2.cvtColor(filtered, cv2.COLOR_BGR2GRAY)
        _, binary = cv2.threshold(gray_f, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        height, width = binary.shape
        display_frame = cv2.cvtColor(binary, cv2.COLOR_GRAY2BGR)

        # 以下变量在每帧开始时重置，以便双岔路/环岛检测逻辑使用
        jishu = 0
        add_line = False
        lateral_offset = 0
        out_turn_off = 0
        angle = 0.0
        out_left_turnabout = 0
        out_left_turnabout1 = []
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
        marker_id_str = marker_id_str  # 保持上一阶段检测到的 ID
        prev_min_j = 0
        prev_min_j_i = 0
        last_x = None
        is_increasing_then_decreasing = False
        is_increasing_then_decreasing_a = False
        is_increasing_then_decreasing_b = False
        is_increasing_then_decreasing_c = False
        last_dir = None
        black_pixels = []
        white_pixels = []
        upper_turning_point = []
        lower_turning_point1 = []
        lower_turning_point2 = []
        out_upper_turning_point = []
        mid_turn_off = []
        mid_list = []
        left_list = []
        right_list = []
        start = 240
        cuizhi_count = 0
        roundabout_frame = 0
        turn_off_frame = 0
        out_turn_off_frame = 0
        skip_frames = 0
        add_line_points = []  # 用于补线时存储点的列表

        # 如果选择使用水平扫线（示例中始终为 True）
        if True:
            # ****************************** 双岔路检测加补线 ******************************
            if out_turn_off < 1:
                # 右中拐点检测
                for i in range(50, 350):
                    white_found = False
                    for j in range(450, 180, -1):
                        if binary[i][j] == 255:
                            white_found = True
                        elif white_found and binary[i][j] == 0:
                            mid_turn_off.append(j)
                            max_j = j
                            max_j_i = i
                            break

                # 右下拐点检测
                for i in range(280, 399):
                    for j in range(479, 300, -1):
                        if binary[i][j] == 255:
                            lower_turning_point1.append(j)
                            if j < min_j:
                                min_j = j
                                min_j_i = i
                            break

                # 左下拐点检测
                for i in range(280, 390):
                    for j in range(0, 240, 1):
                        if binary[i][j] == 255:
                            lower_turning_point2.append(j)
                            break

                data3 = np.array(lower_turning_point1)
                data4 = np.array(lower_turning_point2)
                data5 = np.array(mid_turn_off)

                # 检查 data3 中是否先单调递减再递增
                if len(data3) > 10:
                    data3 = data3[np.where(data3 != 380)]
                    if len(data3) > 10:
                        min_index = np.argmin(data3)
                        is_increasing_then_decreasing_a = np.all(
                            np.all(np.diff(data3[:min_index]) <= 0) and np.all(np.diff(data3[min_index:]) >= 0)
                        )
                        if min_index == len(data3) - 1 or min_index == 0:
                            is_increasing_then_decreasing_a = False

                # 检查 data4 中是否先单调递增再递减
                if len(data4) > 10:
                    data4 = data4[np.where(data4 != 140)]
                    if len(data4) > 10:
                        max_index = np.argmax(data4)
                        is_increasing_then_decreasing_b = np.all(
                            np.all(np.diff(data4[:max_index]) >= 0) and np.all(np.diff(data4[max_index:]) <= 0)
                        )
                        if max_index == len(data4) - 1 or max_index == 0:
                            is_increasing_then_decreasing_b = False

                # 检查 data5 中是否先单调递增再递减
                if len(data5) > 10:
                    data5 = data5[np.where(data5 != 450)]
                    if len(data5) > 10:
                        max_index = np.argmax(data5)
                        is_increasing_then_decreasing_c = np.all(
                            np.all(np.diff(data5[:max_index]) >= 0) and np.all(np.diff(data5[max_index:]) <= 0)
                        )
                        if max_index == len(data5) - 1 or max_index == 0:
                            is_increasing_then_decreasing_c = False

                # 如果同时满足三个条件，则视为“删除转弯标志”
                if is_increasing_then_decreasing_a and is_increasing_then_decreasing_b and is_increasing_then_decreasing_c:
                    text = "deleted turn off"
                    turn_off += 1
                    turn_off_frame = turn_off
                    cv2.putText(display_frame, text, (100, 100),
                                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

                # ****************************** 进岔路补线 ******************************
                if turn_off >= 1 and (turn_off_frame - turn_off) <= 10 and jishu == 0:
                    # 计算斜率
                    if max_j - min_j != 0:
                        slope_a = (max_j_i - min_j_i) / (max_j - min_j)
                    print("斜率:", slope_a)

                    if slope_a >= 0:
                        cv2.line(display_frame, (max_j, max_j_i), (min_j, min_j_i), (0, 0, 0), 2)
                        add_line = True
                        k = slope_a
                        b = max_j_i - k * max_j
                        if max_j < min_j:
                            for x in range(max_j, min_j + 1):
                                y = k * x + b
                                add_line_points.append((x, y))
                        else:
                            for x in range(min_j, max_j + 1):
                                y = k * x + b
                                add_line_points.append((x, y))

                    if slope_a <= 0:
                        end_j = 399
                        end_j_i = int(max_j_i + prev_slope_a * (end_j - max_j))
                        slope_a = prev_slope_a
                        cv2.line(display_frame, (max_j, max_j_i), (end_j, end_j_i), (0, 0, 0), 2)
                        add_line = True
                        jishu += 1
                        k = slope_a
                        b = max_j_i - k * max_j
                        if max_j < end_j:
                            for x in range(max_j, end_j + 1):
                                y = k * x + b
                                add_line_points.append((x, y))
                        else:
                            for x in range(end_j, max_j + 1):
                                y = k * x + b
                                add_line_points.append((x, y))

        # ****************************** 基础扫线 ******************************
        if (left_roundabout < 1 or
            (left_roundabout == out_left_turnabout == 1) or
            (left_roundabout == out_left_turnabout == 2 and right_roundabout not in (1, 3)) or
            right_roundabout in (2, 4)):

            mid_points = []
            left_points = []
            right_points = []

            # 从 300 行到 329 行，扫描找到左边和右边的白色像素点
            for i in range(300, 330):
                left = -1
                for j in range(5, 340, 2):
                    if binary[i][j] == 255:
                        if left == -1:
                            left = j
                            left_points.append((left, i))
                            cv2.circle(display_frame, (left, i), 2, (0, 255, 0), -1)
                if turn_off >= 1 and (turn_off_frame - turn_off) <= 12:
                    filtered_points = [(x, y) for (x, y) in add_line_points if 310 <= y <= 330]
                    right_points = filtered_points
                elif out_turn_off >= 1 and (out_turn_off_frame - out_turn_off) <= 15:
                    filtered_points = [(x, y) for (x, y) in add_line_points if 310 <= y <= 330]
                    right_points = filtered_points
                else:
                    right = -1
                    for j in range(475, 50, -2):
                        if binary[i][j] == 255:
                            if right == -1:
                                right = j
                                right_points.append((right, i))
                                cv2.circle(display_frame, (right, i), 2, (0, 0, 255), -1)

            # 计算左右对应点的中点
            for (r_x, r_y), (l_x, l_y) in zip(right_points, left_points):
                center = (r_x + l_x) / 2
                mid_points.append((center, r_y))

            mid_points = np.array(mid_points, dtype=np.float32)

            # 如果有足够多的中点，则拟合直线
            if len(mid_points) > 1:
                vx, vy, x, y = cv2.fitLine(mid_points, cv2.DIST_L2, 0, 0.01, 0.01)
                y1 = 300
                y2 = 330
                x1 = int(x - (y - y1) * vx / vy)
                x2 = int(x - (y - y2) * vx / vy)
                cv2.line(display_frame, (x1, y1), (x2, y2), (0, 0, 255), 2)

                angle = 1.57 - np.arctan2(y2 - y1, x2 - x1)
                line_center = (x1 + x2) / 2
                image_center = width / 2
                lateral_offset = line_center - image_center

                cv2.putText(display_frame, f"Angle: {angle:.2f} degrees", (25, 25),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
                cv2.putText(display_frame, f"Lateral Offset: {lateral_offset:.2f} pixels", (25, 50),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

            prev_slope_a = slope_a
            out_prev_slope_a = out_slope_a

        # 根据左右环岛/岔路状态，在图像上显示相应文字提示
        if left_roundabout == 1 and out_left_turnabout < 1:
            txt = "left_roundabout_ing"
            cv2.putText(display_frame, txt, (300, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
        if left_roundabout == 2 and out_left_turnabout < 2:
            txt = "left_roundabout_ing"
            cv2.putText(display_frame, txt, (300, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
        if right_roundabout >= 1 and right_roundabout < 2:
            txt = "right_roundabout_ing"
            cv2.putText(display_frame, txt, (300, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
        if right_roundabout >= 3 and right_roundabout < 4:
            txt = "right_roundabout_ing"
            cv2.putText(display_frame, txt, (300, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

        # 在窗口中显示处理后的二值化图像
        cv2.imshow("Now Frame", display_frame)

        # 将角度、横向偏移等信息拼成字符串，通过 socket 发送给客户端
        float_number_2 = lateral_offset
        float_number_3 = 0
        message_to_send = "{:.2f}|{:.2f}|{:.2f}|{}".format(angle, float_number_2, float_number_3, marker_id_str)
        connection.sendall(message_to_send.encode())
        print("发送浮点数给客户端:", message_to_send)

        # 按 'q' 键退出
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

finally:
    # 关闭资源
    cap.release()
    cv2.destroyAllWindows()
    connection.close()
    server_socket.close()
