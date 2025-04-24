import cv2
import numpy as np
# 颜色定义 (HSV范围)
color_ranges = {
    "红色": [
        (np.array([0, 120, 70]), np.array([10, 255, 255])),
        (np.array([170, 120, 70]), np.array([180, 255, 255]))
    ],
    "绿色": [
        (np.array([35, 50, 50]), np.array([85, 255, 255]))
    ],
    "蓝色": [
        (np.array([90, 120, 80]), np.array([120, 255, 255]))
    ],
    "黄色": [
        (np.array([20, 100, 100]), np.array([30, 255, 255]))
    ],
    "紫色": [
        (np.array([125, 50, 50]), np.array([150, 255, 255]))
    ],
    "橙色": [
        (np.array([10, 100, 100]), np.array([20, 255, 255]))
    ],
    "白色": [
        (np.array([0, 0, 200]), np.array([180, 50, 255]))
    ]
}
def detect_colors(image_path):
    img = cv2.imread(image_path)
    if img is None:
        print("错误：无法读取图像！")
        return

    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    hsv = cv2.medianBlur(hsv, 5)  # 中值滤波去噪
    detected_colors = set()
    for color_name, ranges in color_ranges.items():
        combined_mask = np.zeros(hsv.shape[:2], dtype=np.uint8)
        # 合并多个颜色范围
        for (lower, upper) in ranges:
            mask = cv2.inRange(hsv, lower, upper)
            combined_mask = cv2.bitwise_or(combined_mask, mask)
        # 增强形态学处理
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
        combined_mask = cv2.morphologyEx(combined_mask, cv2.MORPH_OPEN, kernel, iterations=1)
        combined_mask = cv2.morphologyEx(combined_mask, cv2.MORPH_CLOSE, kernel, iterations=2)
        # 改进的轮廓检测
        contours, _ = cv2.findContours(combined_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        # 动态面积阈值
        img_area = img.shape[0] * img.shape[1]
        min_area = max(500, img_area * 0.001)  # 至少500像素或图像面积的0.1%
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area > min_area:
                # 计算轮廓紧凑度
                perimeter = cv2.arcLength(cnt, True)
                if perimeter == 0:
                    continue
                compactness = 4 * np.pi * area / (perimeter ** 2)
                if compactness > 0.2:  # 过滤线状噪声
                    detected_colors.add(color_name)
                    break
    print("检测到的颜色：" + ", ".join(detected_colors) if detected_colors else "未检测到显著颜色")
if __name__ == "__main__":
    detect_colors("1.jpg")
