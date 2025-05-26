import numpy as np
import cv2
import time
import math
import socket
import cv2.aruco as aruco


# 创建UDP socket
client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# 服务器地址和端口
server_address = ('192.168.123.18', 1234)
# 初始化摄像头
cap = cv2.VideoCapture(0)  # 0通常是默认的摄像头

# 二值化阈值设置
lower_yellow = np.array([20, 43, 46])
upper_yellow = np.array([50, 255, 255])

# 启停区颜色阈值
lower_red = np.array([132, 169, 86])
upper_red = np.array([179, 255, 187])


def Reveal(Count, Aru_left, Aru_right):
	print(Count, Aru_left, Aru_right)
	if Count == Aru_left - 1 and Aru_left <= 2:
		return 'L'
	if Count == Aru_left - 1 and Aru_left > 2:
		return 'r'
	if Count == Aru_right - 1 and Aru_right <= 2:
		return 'l'
	if Count == Aru_right - 1 and Aru_right > 2:
		return 'R'


def FlagShow(frame, FlagRound, FlagThr, FlagCross, JumpCross, JumpRound):
	if FlagRound == 1:
		cv2.putText(frame, "Round", (15, 40), cv2.FONT_HERSHEY_PLAIN, 3, (255, 0, 0), 4)
		if JumpRound == 0:
			cv2.putText(frame, "Enter", (15, 65), cv2.FONT_HERSHEY_PLAIN, 2, (0, 255, 0), 3)
		else:
			cv2.putText(frame, "Jump", (15, 65), cv2.FONT_HERSHEY_PLAIN, 2, (0, 0, 255), 3)
	elif FlagThr == 1:
		cv2.putText(frame, "ThreeRoad", (15, 40), cv2.FONT_HERSHEY_PLAIN, 3, (255, 0, 0), 4)
	elif FlagCross == 1:
		cv2.putText(frame, "Cross", (15, 40), cv2.FONT_HERSHEY_PLAIN, 3, (255, 0, 0), 4)
		if JumpCross == 0:
			cv2.putText(frame, "Enter", (15, 65), cv2.FONT_HERSHEY_PLAIN, 2, (0, 255, 0), 3)
		else:
			cv2.putText(frame, "Jump", (15, 65), cv2.FONT_HERSHEY_PLAIN, 2, (0, 0, 255), 3)




def findArucoMarkers(img, markerSize=6, totalMarkers=250, draw=True):
	gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
	arucoDict = aruco.getPredefinedDictionary(aruco.DICT_4X4_250)
	arucoParam = aruco.DetectorParameters()
	corners, ids, rejected = aruco.detectMarkers(gray, arucoDict, parameters=arucoParam)
	if draw:
		aruco.drawDetectedMarkers(img, corners, ids)

	if ids is not None and len(ids) > 0:
		return int(ids[0][0])
	else:
		return None




# PD调控
Kp = 1
Kd = 0
OriArg = 0  # 记录上次打角值（微分）

# 实际打角与理想打角的权重分配
Kt = 1  # 实际权重
Ka = 0  # 理想权重

# 元素识别标志
FlagRound = EnterRound = OutRound = Normal = LeftCir = 0  # 环岛状态机
FlagCross = RightCir = OutCross = FlagSend = 0  # 十字标志
FlagThr = CountThr = 0  # 三岔标志及计数器
BlackRound = LeaveRound = 0  # 跳过环岛状态机
Count = 0  # 倾倒区计数器
JumpCross = JumpRound = 0  # 跳过倾倒区标志
MoveFlag = 0  # 循迹开关
LJP = 1000  # 环岛上角辅助条件
CDP = 0  # 下角出现帧计数器（增强环岛识别稳定性）

MidSta = 60

# 两个物资（展示时先左后右）
Aru_left = Aru_right = 0  # 左右物资aru码序号
AruCount = 0  # aruco计数器

# 计时器
start_time = 0
cross_detect = 0
round_detect = 0
now_time = 0

try:
	while True:
		ret, frame = cap.read()
		if not ret:
			break

		

		# ********************* 开始循迹 ********************** #

		if 1 :
			# 启停区预识别 (执行减速)
			hsv_image = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
			mask = cv2.inRange(hsv_image, lower_red, upper_red)
			red_area = np.count_nonzero(mask)
			if red_area >= 500 and Count != 0:
				print("减速")
			# ***发送减速指令***

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

			# **********************获取边界数组*********************** #

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
			dis = arg = LossNum = 0  # 参数
			DownPoint = UpPoint = MidLoss = 0  # 上下角标志及黑中标志

			# 寻白
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

			# 中点继承法巡线
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

			# **********************元素识别********************
			if FlagRound == 0 and CountThr == 0:
				FindLoss = 0
				if TrueLen >= 60:
					for i in range(0, 45):
						if right_line[i] - left_line[i] != 119:
							break
						if i == 44:
							FindLoss = 1
				if FindLoss == 1:
					Black_staX = int(w / 2)
					r = oriY
					Flag = 0
					while r > endY:
						if img[r, midX] == 0:
							break
						r -= 1
					if r != endY:
						while r > 0:
							Black_Left = Black_Right = Black_staX
							while img[r, Black_Right] == 0:
								Black_Right += 1
								if Black_Right == 119:
									Flag += 1
									break
							while img[r, Black_Left] == 0:
								Black_Left -= 1
								if Black_Left == 0:
									Flag += 1
									break
							Black_staX = int((Black_Right + Black_Left) * 0.5)
							frame[r, Black_staX] = (255, 255, 0)
							if abs(Black_staX - midX) >= 30:
								Flag = -1
								print("斜入三岔")
								break
							r -= 1
						if 0 <= Flag <= 25 and img[0, 0] == 255 and img[0, 119] == 255:
							print("三岔")
							FlagThr = 1
			# 三岔补线
			if FlagThr == 1:
				cv2.line(img, (0, 15), (119, 119), (0, 0, 0), 1)
			# 结束三岔
			if FlagThr == 1 and TrueLen >= 75:
				if right_line[10] - left_line[10] != 119:
					for i in range(15, 75):
						if abs(mid_line[i] - mid_line[i - 1]) >= 15:
							break
						if i == 74:
							CountThr += 1
							FlagThr = 0
							print("离开三岔")

			# 十字

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
			arg = math.atan2(119 - EndY, X - 60) - math.pi * 0.5
			assumed_arg = math.atan2(119 - EndY, X - oriX)
			Final_arg = Kt * arg + Ka * assumed_arg
			err = Final_arg - OriArg
			PD_arg = Kp * arg + Kd * err
			OriArg = Final_arg
			# 转角度方便查看
			# degree = math.degrees(PD_arg)
			# print(degree)
			# 发送横向位移和偏角
			message = f"{dis:.2f}, {PD_arg:.2f}"
			client_socket.sendto(message.encode(), server_address)
			cv2.line(img, (60, oriY), (X, EndY), (0, 0, 255), 1)
			cv2.line(img, (oriX, oriY), (X, EndY), (0, 0, 255), 1)
			# 显示原始图像(调试用)
			frame = cv2.resize(frame, dsize=(350, 350))
			FlagShow(frame, FlagRound, FlagThr, FlagCross, JumpCross, JumpRound)
			cv2.imshow("frame", frame)
			# 显示二值图像
			img = cv2.resize(img, dsize=(350, 350))
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
	print(Count)
	print(end_time - start_time)
