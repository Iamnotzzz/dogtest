import numpy as np
import cv2
import time
import math
import socket
import cv2 as cv

# 创建UDP socket
client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# 服务器地址和端口
server_address = ('192.168.123.18', 1234)
# 初始化摄像头
cap = cv2.VideoCapture(0)  # 0通常是默认的摄像头
# 二值化阈值设置
lower_yellow = np.array([20, 43, 46])
upper_yellow = np.array([50, 255, 255])
# PID参数
Kp = 1
Kd = 0
OriAngle = 0
# 元素识别标志
FlagThr = CountThr = 0  # 三岔标志及计数器
MidSta = 60
# 计时器
start_time = 0
cross_detect = 0
round_detect = 0
now_time = 0
dictionary = cv.aruco.Dictionary_get(cv.aruco.DICT_4X4_250)

# 创建 ArUco 检测器
parameters = cv.aruco.DetectorParameters_create()
try:
	while True:
		ret, frame = cap.read()
		if not ret:
			break

		# ********************* 开始循迹 ********************** #

		if 1:
			gray = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)

			# 检测 ArUco 码
			corners, ids, rejectedImgPoints = cv.aruco.detectMarkers(gray, dictionary, parameters=parameters)

			# 输出检测到的 ArUco 码的 ID
			if ids is not None and len(ids) > 0:
				marker_id_str = str(ids[0][0])  # 将第一个 ID 转为字符串
				print("Detected ArUco markers:")
				print("Marker ID:", marker_id_str)
				# 在图像上绘制检测到的 ArUco 码及其 ID
				cv.aruco.drawDetectedMarkers(frame, corners, ids)
			else:
				marker_id_str = "0"
				cv.aruco.drawDetectedMarkers(frame, corners, ids)

			# 进行二值化及噪声消除
			frame = cv2.resize(frame, dsize=(120, 120))  # 缩小图像

			# 高斯模糊
			frame = cv2.GaussianBlur(frame, (7, 7), 3)
			# 转换成hsv格式
			hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
			# 得到二值化图像bin
			binary = cv2.inRange(hsv, lower_yellow, upper_yellow)
			# 腐蚀图像img
			kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
			img = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel, iterations=2)
			# 消除噪点
			reverse_img = cv2.bitwise_not(img)
			contours, _ = cv2.findContours(reverse_img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
			area_thresh = 240  # 设置面积阈值
			for contour in contours:
				area = cv2.contourArea(contour)
				if area < area_thresh:
					# 对小于阈值的连通域进行填充
					cv2.drawContours(img, [contour], -1, (255, 255, 255), thickness=cv2.FILLED)
			h = frame.shape[0]
			w = frame.shape[1]
			oriX = midX = EndX = staX = int(w / 2)
			staY = oriY = Y = 119  # 统一起点
			endY = 0  # 元素中线止
			EndY = 100  # 参数中线
			TrueLen = Len = oriY - endY + 1  # 理想元素中线长
			LEFT = RIGHT = MidSta  # 起始行寻白使用
			left = right = 0  # 道路边线的左右
			left_line = []  # 左边线坐标数组
			right_line = []  # 右边线坐标数组
			mid_line = []  # 中点坐标数组
			dis = angle = LossNum = 0  # 参数
			DownPoint = UpPoint = MidLoss = 0  # 上下角标志及黑中标志
			# 寻找边界
			while True:
				if RIGHT >= img.shape[1]:
					break
				if img[staY, LEFT] == 255:
					staX = LEFT
					break
				if img[staY, RIGHT] == 255:
					staX = RIGHT
					break
				LEFT = LEFT - 1
				RIGHT = RIGHT + 1
			X = staX
			# 从中间往两边
			while staY >= endY:
				if img[staY, staX] == 0 and len(left_line) > 5:  # 保证元素前瞻视野有效
					for i in range(left_line[-1], right_line[-1]):
						if img[staY, i] == 255:
							staX = i
							break
						if i == right_line[-1] - 1:
							MidLoss = 1
					if MidLoss == 1:
						break
				right = left = staX
				while img[staY, right] == 255 and right < w - 1:
					right += 1
				right_line.append(right)
				while img[staY, left] == 255 and left > 0:
					left -= 1
				left_line.append(left)
				staX = int((left + right) / 2)
				mid_line.append(staX)
				frame[staY, left] = (255, 0, 0)
				frame[staY, right] = (0, 0, 255)
				frame[staY, staX] = (0, 255, 0)
				if staY == oriY:
					MidSta = staX
				staY -= 1
			TrueLen = len(left_line)
			
			while Y >= EndY:
				right = left = X
				while img[Y, right] == 255 and right < w - 1:
					right += 1
				while img[Y, left] == 255 and left > 0:
					left -= 1
				X = int((left + right) / 2)
				if Y == oriY:
					oriX = X
				Y -= 1
			# 处理参数并发送
			dis = (w / 2 - oriX) * 0.02
			angle = math.atan2(119 - EndY, X - 60) - math.pi * 0.5
			Final_angle = angle
			err = Final_angle - OriAngle
			PD_angle = Kp * angle + Kd * err
			OriAngle = Final_angle
			message = f"{dis:.2f}, {PD_angle:.2f}"
			client_socket.sendto(message.encode(), server_address)
			cv2.line(img, (60, oriY), (X, EndY), (0, 0, 255), 1)
			cv2.line(img, (oriX, oriY), (X, EndY), (0, 0, 255), 1)
			# 显示原始图像(调试用)
			frame = cv2.resize(frame, dsize=(400, 400))
			cv2.imshow("frame", frame)
			# 显示二值图像
			img = cv2.resize(img, dsize=(400, 400))
			cv2.imshow("img", img)
		if cv2.waitKey(1) & 0xFF == ord('q'):
			break
# ***************************** 结束操作 ***************************** #

finally:
	cap.release()
	cv2.destroyAllWindows()
	client_socket.close()
	end_time = time.time()
	client_socket.close()
