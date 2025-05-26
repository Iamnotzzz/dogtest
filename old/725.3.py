import numpy as np
import cv2
import time
import math
import socket
import cv2 as cv

# 设置黄色的HSV范围
lower_yellow = np.array([20, 43, 46])
upper_yellow = np.array([50, 255, 255])

# 创建UDP socket
udp_client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# 服务器地址和端口
server_address = ('192.168.123.18', 1234)

# 初始化摄像头
camera = cv2.VideoCapture(0)  # 0通常是默认的摄像头

# PID参数
Kp = 1
Kd = 0
previous_angle = 0

# ArUco字典和检测器参数
aruco_dictionary = cv.aruco.Dictionary_get(cv.aruco.DICT_4X4_250)
aruco_parameters = cv.aruco.DetectorParameters_create()

try:
    while True:
        ret, frame = camera.read()
        if not ret:
            break
        
        gray_frame = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)
        corners, ids, _ = cv.aruco.detectMarkers(gray_frame, aruco_dictionary, parameters=aruco_parameters)

        if ids is not None and len(ids) > 0:
            marker_id_str = str(ids[0][0])
            marker_id_int = int(marker_id_str)  # 转换为整形
            print("Detected ArUco markers:")
            print("Marker ID:", marker_id_str)
            cv.aruco.drawDetectedMarkers(frame, corners, ids)
        else:
            marker_id_str = "0"
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
        message = f"{distance:.2f}, {pd_angle:.2f}, {marker_id_int}"  # 包含转换后的整形数
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
