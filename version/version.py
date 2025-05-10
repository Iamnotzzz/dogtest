import cv2
import numpy as np

# 初始化摄像头
cap = cv2.VideoCapture('/dev/video0')
cap.set(cv2.CAP_PROP_FPS, 60)  # 设置帧率为30fps

# 定义黑色阈值
lower_black = np.array([0, 0, 0])  # 黑色下界
upper_black = np.array([180, 255, 80])  # 黑色上界

# 图像尺寸参数
frame_height = 480
frame_width = 640

# 计算中线与图像中心的横向偏移量
def calculate_offset(left, right, img_center):
    # 计算中线
    middle = (left + right) // 2
    # 计算横向偏移量
    offset = middle - img_center
    return middle, offset

# 循迹主循环
while True:
    ret, frame = cap.read()
    if not ret:
        break

    # 图像预处理
    frame = cv2.resize(frame, (frame_width, frame_height))  # 调整为合适尺寸
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)  # 转换为HSV色彩空间
    bin_image = cv2.inRange(hsv, lower_black, upper_black)  # 二值化处理，提取黑线

    # 扩张和腐蚀，去除噪声
    kernel = np.ones((5, 5), np.uint8)
    processed_image = cv2.morphologyEx(bin_image, cv2.MORPH_CLOSE, kernel)

    # 寻找黑线的左右边界
    left = None
    right = None

    for row in range(frame_height - 1, -1, -1):  # 从下往上扫描每一行
        row_pixels = processed_image[row, :]
        
        # 寻找左边界
        if left is None:
            for col in range(0, frame_width):
                if row_pixels[col] == 255:
                    left = col
                    break
        
        # 寻找右边界
        if right is None:
            for col in range(frame_width - 1, -1, -1):
                if row_pixels[col] == 255:
                    right = col
                    break
        
        if left is not None and right is not None:
            break  # 找到左右边界就停止

    # 计算中线和横向偏移量
    if left is not None and right is not None:
        middle, offset = calculate_offset(left, right, frame_width // 2)
        print(f"中线位置: {middle}, 横向偏移量: {offset}")

        # 在图像中绘制左右边界和中线
        cv2.line(frame, (left, row), (left, row), (0, 255, 0), 2)
        cv2.line(frame, (right, row), (right, row), (0, 255, 0), 2)
        cv2.line(frame, (middle, 0), (middle, frame_height), (0, 0, 255), 2)

    # 显示图像
    cv2.imshow('Tracking', frame)

    # 按'q'键退出循环
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# 释放摄像头资源
cap.release()
cv2.destroyAllWindows()
