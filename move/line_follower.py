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
        return 0
    x1, y1 = midline_points[0]
    x2, y2 = midline_points[-1]
    slope = (y2 - y1) / (x2 - x1) if x2 != x1 else float('inf')
    return math.degrees(math.atan(slope))


# 计算横向偏移量，即中线在图像宽度中心的偏离程度
def calculate_lateral_offset(midline_points, width):
    return sum(p[0] for p in midline_points) / len(midline_points) - (width / 2) if midline_points else 0


# 在图像上绘制文本信息
def draw_text(frame, text, position=(50, 50), font_scale=1, color=(255, 255, 255), thickness=2):
    cv2.putText(frame, text, position, cv2.FONT_HERSHEY_SIMPLEX, font_scale, color, thickness)


# 处理每一帧图像，提取出道路边界，并返回相关数据
def process_frame(frame, lower_black, upper_black):
    # 高斯模糊去噪
    frame_blurred = cv2.GaussianBlur(frame, (13, 13), 10, 20)

    # 转换为 HSV 颜色空间
    hsv = cv2.cvtColor(frame_blurred, cv2.COLOR_BGR2HSV)
    
    # 提取黑色区域，二值化
    bin_img = cv2.inRange(hsv, lower_black, upper_black)
    
    # 闭操作消除噪点
    cleaned = cv2.morphologyEx(bin_img, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3)), iterations=2)
    
    # 连接区域标记
    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(cleaned, connectivity=8)
    
    # 如果没有检测到任何区域，直接返回空列表
    if num_labels <= 1:
        return [], [], frame.shape[1], cleaned

    # 找到面积最大的连通区域，假设是道路区域
    max_area_label = np.argmax(stats[1:, cv2.CC_STAT_AREA]) + 1
    
    # 提取最大的连通区域
    cleaned = np.where(labels == max_area_label, 255, 0).astype(np.uint8)
    
    # 找到轮廓
    contours, _ = cv2.findContours(cleaned, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    main_road_mask = np.zeros_like(cleaned)
    left_boundaries, right_boundaries = [], []

    if contours:
        # 找到最大的轮廓，假设是主道路
        largest_contour = max(contours, key=cv2.contourArea)
        
        # 在掩码上填充道路区域
        cv2.drawContours(main_road_mask, [largest_contour], -1, 255, thickness=cv2.FILLED)
        
        # 获取图像的高度和宽度
        height, width = main_road_mask.shape[:2]
        
        # 从底部开始寻找道路左右边界
        for row in range(height - 1, (5 * height) // 6 - 1, -1):
            cols = np.where(main_road_mask[row, :] == 255)[0]
            if cols.size > 0:
                left_boundaries.append((cols[0], row))
                right_boundaries.append((cols[-1], row))

    return left_boundaries, right_boundaries, width, cleaned


# 主函数，读取视频并处理每一帧
def main():
    # 打开视频文件
    cap = cv2.VideoCapture("D:\\竞赛\\睿抗\\4cf213eee7a05ac580f33807f75bc5e3.mp4")
    
    # 如果无法打开视频，输出错误信息并退出
    if not cap.isOpened():
        print("Error: Could not open video.")
        return

    # 设置黑色的HSV范围
    lower_black = np.array([0, 0, 0])
    upper_black = np.array([180, 255, 60])

    # 循环处理每一帧
    while True:
        ret, frame = cap.read()
        
        # 如果读取失败，退出循环
        if not ret:
            break

        # 处理当前帧，提取左右边界和图像宽度信息
        left_boundaries, right_boundaries, width, cleaned = process_frame(frame, lower_black, upper_black)
        
        # 计算中线点
        midline_points = calculate_midline_points(left_boundaries, right_boundaries)

        if midline_points:
            # 绘制中线点
            for point in midline_points:
                cv2.circle(frame, point, 1, (0, 0, 255), -1)

            # 计算角度和横向偏移量
            angle = calculate_angle(midline_points)
            lateral_offset = calculate_lateral_offset(midline_points, width)

            # 在帧上显示角度和横向偏移量信息
            draw_text(frame, f"Angle: {angle:.2f} degrees")
            draw_text(frame, f"Lateral Offset: {lateral_offset:.2f} pixels", position=(50, 80))
        else:
            # 如果未检测到道路，在屏幕上显示提示信息
            draw_text(frame, "No Road Detected", position=(50, 50), color=(0, 0, 255))

        # 显示清理后的二值化图像
        cv2.imshow("Cleaned Image", cleaned)
        # 显示带有中线标记的原始图像
        cv2.imshow('Processed Frame', frame)
        
        # 按 'q' 键退出
        if cv2.waitKey(25) & 0xFF == ord('q'):
            break

    # 释放视频资源并关闭窗口
    cap.release()
    cv2.destroyAllWindows()


# 程序入口
if __name__ == "__main__":
    main()
