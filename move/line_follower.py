import cv2
import numpy as np
from udp_communicate import UDPClient

# 初始化 UDP 通信
udp_client = UDPClient("192.168.123.13", 6011)

# 定义黑色的 HSV 阈值
lower_black = np.array([0, 0, 0])
upper_black = np.array([180, 255, 50])

# 摄像头初始化
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FPS, 30)

def process_frame(frame):
    """处理单帧图像，提取黑线和中线"""
    # 1️⃣ 高斯模糊减少噪声
    blurred = cv2.GaussianBlur(frame, (5, 5), 0)

    # 2️⃣ 转换为 HSV 颜色空间
    hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)

    # 3️⃣ 颜色过滤，提取黑色
    mask = cv2.inRange(hsv, lower_black, upper_black)

    # 4️⃣ 形态学处理
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

    # 5️⃣ 找到轮廓
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # 初始化左右边界列表
    left_boundaries = []
    right_boundaries = []

    # 遍历所有轮廓，找左右边界
    for cnt in contours:
        if cv2.contourArea(cnt) > 100:  # 排除小的噪声
            for point in cnt:
                x, y = point[0]
                if x < frame.shape[1] // 2:
                    left_boundaries.append((x, y))
                else:
                    right_boundaries.append((x, y))

    # 计算中线
    midline_points = [(int((l[0] + r[0]) / 2), int((l[1] + r[1]) / 2)) 
                      for l, r in zip(left_boundaries, right_boundaries)]

    return midline_points, mask

def calculate_control(midline_points, frame):
    """根据中线计算控制量"""
    if len(midline_points) < 2:
        return 0, 0  # 找不到中线

    # 取首尾两个点计算斜率
    (x1, y1), (x2, y2) = midline_points[0], midline_points[-1]
    
    # 1️⃣ 计算角度
    if x2 - x1 == 0:
        angle = np.pi / 2
    else:
        slope = (y2 - y1) / (x2 - x1)
        angle = np.arctan(slope)
    
    # 2️⃣ 计算偏移量
    frame_center = frame.shape[1] // 2
    mid_x = sum([p[0] for p in midline_points]) // len(midline_points)
    distance = mid_x - frame_center

    # 3️⃣ 可视化
    for point in midline_points:
        cv2.circle(frame, point, 2, (0, 255, 0), -1)  # 绿色点
    cv2.line(frame, (x1, y1), (x2, y2), (255, 0, 0), 2)  # 蓝色线
    cv2.line(frame, (frame_center, 0), (frame_center, frame.shape[0]), (0, 0, 255), 1)

    return angle, distance

# 主循环
while True:
    ret, frame = cap.read()
    if not ret:
        break
    
    # 1️⃣ 获取中线和二值化结果
    midline_points, mask = process_frame(frame)

    # 2️⃣ 计算转向角度和偏移距离
    angle, distance = calculate_control(midline_points, frame)

    # 3️⃣ 发送控制量到机器狗
    udp_client.send_control(angle, distance)

    # 4️⃣ 显示结果
    cv2.imshow("Binary Mask", mask)
    cv2.imshow("Line Detection", frame)

    # 5️⃣ 退出条件
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
udp_client.close()
