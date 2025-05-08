import cv2
import numpy as np
import math


# 计算中线点，给定左侧和右侧边界，返回每一行的中线坐标
def calculate_midline_points(left_boundaries, right_boundaries):
    return [(int((l[0] + r[0]) / 2), int((l[1] + r[1]) / 2)) 
            for l, r in zip(left_boundaries, right_boundaries)] if left_boundaries and right_boundaries else []


# 计算中线的角度（斜率转换为角度），通过中线的首尾点来估算
def calculate_angle(midline_points):
    if len(midline_points) < 2:
        return 0  # 如果中线点不足两点，返回0
    x1, y1 = midline_points[0]
    x2, y2 = midline_points[-1]
    slope = (y2 - y1) / (x2 - x1) if x2 != x1 else float('inf')  # 防止除以0的情况
    return math.degrees(math.atan(slope))  # 将斜率转为角度


# 计算横向偏移量，即中线在图像宽度中心的偏离程度
def calculate_lateral_offset(midline_points, width):
    return sum(p[0] for p in midline_points) / len(midline_points) - (width / 2) if midline_points else 0


# 在图像上绘制文本信息，通常用于显示角度和横向偏移量
def draw_text(frame, text, position=(50, 50), font_scale=1, color=(255, 255, 255), thickness=2):
    cv2.putText(frame, text, position, cv2.FONT_HERSHEY_SIMPLEX, font_scale, color, thickness)


# 处理每一帧图像，提取出道路边界，并返回相关数据
def process_frame(frame, lower_yellow, upper_yellow):
    # 高斯模糊减少噪点
    frame_blurred = cv2.GaussianBlur(frame, (13, 13), 10, 20)
    # 转换为HSV色彩空间，便于颜色提取
    hsv = cv2.cvtColor(frame_blurred, cv2.COLOR_BGR2HSV)
    # 提取黄色区域的二值化图像
    bin_img = cv2.inRange(hsv, lower_yellow, upper_yellow)
    # 进行形态学操作，填补空洞
    cleaned = cv2.morphologyEx(bin_img, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3)), iterations=2)
    
    # 获取图像中连通区域的信息
    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(cleaned, connectivity=8)
    # 找到面积最大的连通区域标签
    max_area_label = np.argmax(stats[1:, cv2.CC_STAT_AREA]) + 1
    largest_area = stats[max_area_label, cv2.CC_STAT_AREA]
    
    # 保留最大连通区域
    cleaned = np.where(labels == max_area_label, 255, 0).astype(np.uint8)
    # 获取轮廓信息
    contours, _ = cv2.findContours(cleaned, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    main_road_mask = np.zeros_like(cleaned)
    left_boundaries, right_boundaries = [], []
    
    if contours:
        # 找到最大的轮廓，假设是道路区域
        largest_contour = max(contours, key=cv2.contourArea)
        cv2.drawContours(main_road_mask, [largest_contour], -1, 255, thickness=cv2.FILLED)
        height, width = main_road_mask.shape[:2]
        
        # 从底部往上遍历，寻找左右道路边界
        for row in range(height - 1, (5 * height) // 6 - 1, -1):
            cols = np.where(main_road_mask[row, :] == 255)[0]
            if cols.size > 0:
                left_boundaries.append((cols[0], row))  # 左边界点
                right_boundaries.append((cols[-1], row))  # 右边界点

    return left_boundaries, right_boundaries, width, cleaned


# 主函数，读取视频并处理每一帧
def main():
    cap = cv2.VideoCapture("D:\\some_important\\aruco\\demo2.avi")
    if not cap.isOpened():
        print("Error: Could not open video.")
        return

    lower_yellow = np.array([20, 43, 46])  # 黄色的HSV范围
    upper_yellow = np.array([50, 255, 255])

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # 处理当前帧，提取左右边界和宽度信息
        left_boundaries, right_boundaries, width, cleaned = process_frame(frame, lower_yellow, upper_yellow)
        # 计算中线点
        midline_points = calculate_midline_points(left_boundaries, right_boundaries)

        if midline_points:
            # 绘制中线点
            for point in midline_points:
                cv2.circle(frame, point, 1, (0, 0, 255), -1)

            # 计算角度和横向偏移量
            angle = calculate_angle(midline_points)
            lateral_offset = calculate_lateral_offset(midline_points, width)

            # 在帧上绘制角度和偏移量信息
            draw_text(frame, f"Angle: {angle:.2f} degrees")
            draw_text(frame, f"Lateral Offset: {lateral_offset:.2f} pixels", position=(50, 80))

        # 显示清理过的二值图像
        cv2.imshow("Cleaned Image", cleaned)
        # 显示带中线标记的原始图像
        cv2.imshow('Processed Frame', frame)
        
        # 按'q'退出
        if cv2.waitKey(25) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
