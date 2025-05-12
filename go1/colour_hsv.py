# -*- coding:utf-8 -*-

import cv2
import numpy as np

"""
功能：读取一张图片，显示出来，转化为HSV色彩空间
     并通过滑块调节HSV阈值，实时显示
"""

image = cv2.imread("D:/111/camera1.jpg")  # 根据路径读取一张图片，opencv读出来的是BGR模式
down_width = 300
down_height = 200
down_points = (down_width, down_height)
image = cv2.resize(image, down_points, interpolation=cv2.INTER_LINEAR)
cv2.imshow("BGR", image)  # 显示图片

hsv_low = np.array([0, 0, 0])
hsv_high = np.array([0, 0, 0])


# 下面几个函数，写得有点冗余

def h_low(value):
    hsv_low[0] = value


def h_high(value):
    hsv_high[0] = value


def s_low(value):
    hsv_low[1] = value


def s_high(value):
    hsv_high[1] = value


def v_low(value):
    hsv_low[2] = value


def v_high(value):
    hsv_high[2] = value


cv2.namedWindow('image', cv2.WINDOW_AUTOSIZE)

# H low：
#    0：指向整数变量的可选指针，该变量的值反映滑块的初始位置。
#  179：表示滑块可以达到的最大位置的值为179，最小位置始终为0。
# h_low：指向每次滑块更改位置时要调用的函数的指针，指针指向h_low元组，有默认值0。

cv2.createTrackbar('H low', 'image', 15, 179, h_low)
cv2.createTrackbar('H high', 'image', 55, 179, h_high)
cv2.createTrackbar('S low', 'image', 40, 255, s_low)
cv2.createTrackbar('S high', 'image', 255, 255, s_high)
cv2.createTrackbar('V low', 'image', 46, 255, v_low)
cv2.createTrackbar('V high', 'image', 255, 255, v_high)

while True:
    dst = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)  # BGR转HSV
    dst = cv2.inRange(dst, hsv_low, hsv_high)  # 通过HSV的高低阈值，提取图像部分区域up_width = 600

    down_width = 300
    down_height = 200
    down_points = (down_width, down_height)
    dst = cv2.resize(dst, down_points, interpolation=cv2.INTER_LINEAR)

    cv2.imshow('dst', dst)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break
cv2.destroyAllWindows()