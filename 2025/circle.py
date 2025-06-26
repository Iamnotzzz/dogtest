import cv2
import numpy as np
import socket

# 初始化 socket 连接（替换为你实际的服务器IP和端口）
connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
connection.connect(('0.0.0.0', 12346))  # 示例IP和端口
# ArUco 字典和参数初始化
aruco_dict = cv2.aruco.Dictionary_get(cv2.aruco.DICT_4X4_50)
aruco_params = cv2.aruco.DetectorParameters_create()

car_x, car_y = 320, 240
lower_black = np.array([0, 0, 0])
upper_black = np.array([180, 255, 60])
width = 640
height = 480
add_line_points = []

def normal_tracking(binary_thresh, frame):
    left_points, right_points, mid_points = [], [], []

    # 左边界
    for i in range(300, 330):
        for j in range(5, 340, 2):
            if binary_thresh[i, j] == 255:
                left_points.append((j, i))
                break

    # 右边界
    for i in range(300, 330):
        for j in range(475, 50, -2):
            if binary_thresh[i, j] == 255:
                right_points.append((j, i))
                break

    # 中线计算
    for (l, y), (r, _) in zip(left_points, right_points):
        mid = (l + r) / 2
        mid_points.append((mid, y))

    angle, offset = 0.0, 0.0
    if len(mid_points) > 1:
        mid_points = np.array(mid_points, dtype=np.float32)
        [vx, vy, x, y] = cv2.fitLine(mid_points, cv2.DIST_L2, 0, 0.01, 0.01)
        y1, y2 = 300, 330
        x1 = int(x - (y - y1) * vx / vy)
        x2 = int(x - (y - y2) * vx / vy)
        cv2.line(frame, (x1, y1), (x2, y2), (0, 255, 255), 2)
        angle = 1.57 - np.arctan2(y2 - y1, x2 - x1)
        line_center = (x1 + x2) / 2
        image_center = width / 2
        offset = line_center - image_center
    return angle, offset

def special_turn_tracking(binary_thresh, frame):
    right_points, left_points, mid_points = [], [], []

    # 左边界
    for i in range(300, 330):
        for j in range(5, 340, 2):
            if binary_thresh[i, j] == 255:
                left_points.append((j, i))
                break

    # 右边界（带补线滑动处理）
    raw_right = []
    for i in range(300, 330):
        for j in range(475, 50, -2):
            if binary_thresh[i, j] == 255:
                raw_right.append((j, i))
                break

    # 滑动窗口平滑
    if len(raw_right) >= 5:
        raw_right.sort(key=lambda pt: pt[1])
        kernel_size = 5
        for i in range(len(raw_right)):
            start = max(0, i - kernel_size // 2)
            end = min(len(raw_right), i + kernel_size // 2 + 1)
            window = raw_right[start:end]
            avg_x = np.mean([pt[0] for pt in window])
            y = raw_right[i][1]
            right_points.append((int(avg_x), y))
    else:
        right_points = raw_right

    # 中线计算
    for (l, y), (r, _) in zip(left_points, right_points):
        mid = (l + r) / 2
        mid_points.append((mid, y))

    angle, offset = 0.0, 0.0
    if len(mid_points) > 1:
        mid_points = np.array(mid_points, dtype=np.float32)
        [vx, vy, x, y] = cv2.fitLine(mid_points, cv2.DIST_L2, 0, 0.01, 0.01)
        y1, y2 = 300, 330
        x1 = int(x - (y - y1) * vx / vy)
        x2 = int(x - (y - y2) * vx / vy)
        cv2.line(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
        angle = 1.57 - np.arctan2(y2 - y1, x2 - x1)
        line_center = (x1 + x2) / 2
        image_center = width / 2
        offset = line_center - image_center
    return angle, offset

def process_frame(frame):
    global current_marker_id

    # ArUco检测
    gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    corners, ids, _ = cv2.aruco.detectMarkers(gray_frame, aruco_dict, parameters=aruco_params)

    marker_id = 0  # 默认初始化为 0
    if ids is not None and len(ids) > 0:
        marker_id = int(ids[0][0])
        if marker_id >= current_marker_id:
            current_marker_id =marker_id
        cv2.aruco.drawDetectedMarkers(frame, corners, ids)
    # 图像预处理
    frame_blurred = cv2.GaussianBlur(frame, (13, 13), 10, 20)
    hsv = cv2.cvtColor(frame_blurred, cv2.COLOR_BGR2HSV)
    binary = cv2.inRange(hsv, lower_black, upper_black)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    close = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel, iterations=2)

    # 提取主车道
    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(close, connectivity=8)
    closest_lane_index = -1
    closest_lane_distance = float('inf')
    for i in range(1, num_labels):
        if stats[i, cv2.CC_STAT_AREA] > 5000:
            cx, cy = centroids[i]
            distance = np.sqrt((cx - car_x)**2 + (cy - car_y)**2)
            if distance < closest_lane_distance:
                closest_lane_index = i
                closest_lane_distance = distance

    mask = np.zeros_like(close)
    if closest_lane_index != -1:
        mask[labels == closest_lane_index] = 255
    filtered = cv2.bitwise_and(frame, frame, mask=mask)
    gray = cv2.cvtColor(filtered, cv2.COLOR_BGR2GRAY)
    _, binary_thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # 调用对应追踪逻辑
    angle_normal, offset_normal = normal_tracking(binary_thresh, frame)
    angle_special, offset_special = special_turn_tracking(binary_thresh, frame)

    if marker_id == 0:
        message = "{:.2f}|{:.2f}|124".format(angle_normal, offset_normal)
        connection.sendall(message.encode())
    elif marker_id == 1:
        message = "{:.2f}|{:.2f}|124".format(angle_normal, offset_normal)
        connection.sendall(message.encode())
    elif marker_id == 2:
        message = "{:.2f}|{:.2f}|124".format(angle_normal, offset_normal)
        connection.sendall(message.encode())
    elif marker_id == 4:
        message = "{:.2f}|{:.2f}|124".format(angle_normal, offset_normal)
        connection.sendall(message.encode())
    elif marker_id == 3:
        message = "{:.2f}|{:.2f}|3".format(angle_special, offset_special)
        connection.sendall(message.encode())

    # 显示调试信息
    cv2.putText(frame, f"Angle (N): {angle_normal:.2f}", (25, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
    cv2.putText(frame, f"Offset (N): {offset_normal:.2f}", (25, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
    cv2.putText(frame, f"Angle (S): {angle_special:.2f}", (25, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
    cv2.putText(frame, f"Offset (S): {offset_special:.2f}", (25, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
    cv2.putText(frame, f"ID: {marker_id}", (25, 150), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)

    cv2.imshow("Frame", frame)

if __name__ == "__main__":
    cap = cv2.VideoCapture(0)
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        process_frame(frame)
        if cv2.waitKey(1) & 0xFF == 27:
            break
    cap.release()
    cv2.destroyAllWindows()
    connection.close()
