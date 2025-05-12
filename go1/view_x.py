import cv2
import numpy as np
import time
import socket

cap = cv2.VideoCapture(1)  # 读取摄像头
cap.set(cv2.CAP_PROP_FPS, 100)

lower_red1 = np.array([0, 70, 100])
upper_red1 = np.array([14, 255, 255])
lower_red2 = np.array([156, 70, 100])
upper_red2 = np.array([180, 255, 255])
lower_yellow = np.array([15, 26, 46])
#lower_yellow = np.array([15, 20, 46])
upper_yellow = np.array([55, 255, 255])
lower_blue = np.array([90, 60, 70])
upper_blue = np.array([110, 255, 255])
lower_green = np.array([56, 91, 60])
upper_green = np.array([80, 255, 255])
lower_purple = np.array([111, 40, 70])
upper_purple = np.array([155, 255, 255])
lower_black = np.array([0, 0, 0])
upper_black = np.array([180, 255, 80])

def color_find(img):
    """找到原图像最多的颜色
        img：原图像"""
    kernel = np.ones((35, 35), np.uint8)
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    Open = cv2.morphologyEx(hsv, cv2.MORPH_OPEN, kernel)
    hist = cv2.calcHist([Open], [0], None, [180], [0, 180])
    hist_max = np.where(hist == np.max(hist))
    if lower_purple[0] < hist_max[0] < upper_purple[0]:
        print('purple')
        return 2
    elif lower_red1[0] < hist_max[0] < upper_red1[0]:
        print('red')
        return 3
    elif lower_red2[0] < hist_max[0] < upper_red2[0]:
        print('red')
        return 3
    elif lower_green[0] < hist_max[0] < upper_green[0]:
        print('green')
        return 4
    elif lower_yellow[0] < hist_max[0] < upper_yellow[0]:
        print('yellow')
        return 1
    else:
        return 0

def ruku_find(img):
    frame = cv2.GaussianBlur(img, (13, 13), 10, 20)
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    bin1 = cv2.inRange(hsv, lower_blue, upper_blue)
    bin2 = bin1[300:420, 200:350]
    white_pixels = np.sum(bin2 == 255)
    print(white_pixels)
    return white_pixels


# 两个物资识别，编号
print("start")
while True:
    flag, frame = cap.read()
    frame = frame[100:260, 160:320]
    put1 = color_find(frame)
    if put1 == 0:
        continue
    else:
        break
time.sleep(5)
while True:
    flag, frame = cap.read()
    frame = frame[100:260, 160:320]
    put2 = color_find(frame)
    if put2 == put1 or put2 == 0:
        continue
    else:
        break
data2 = str(put1) + "/" + str(put2) + "/"
print(data2)
'''
put1 = 1
put2 = 3
data2 = str(put1) + "/" + str(put2) + "/"
'''
'''
*******************************************************************************************
通信
*******************************************************************************************
'''
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_ip = '192.168.123.13'
server_port = 6011
server_socket.bind((server_ip, server_port))
server_socket.listen()
print('waiting for client')
client_socket, client_address = server_socket.accept()
print('connecting!!')
cv2.setNumThreads(1)

point_centre_up = 220  # 所取直线的的上中点
point_centre_down = 220  # 所取直线的下中点
angle = 1.57  # 弧度
distance = 0  # 横向偏差
extent = 0  # 上中点到界外的垂直距离
scan1 = -4  # 扫线起点偏移量
point_left_down_state = 0  # 左下拐点状态
sum_left = 0  # 上（下）最终左边线横坐标和
sum_right = 0  # 上（下）最终右边线横坐标和
area = 0  # 特殊颜色的面积
count_point = 0  # 拐点识别次数
avoid_count = 0  # 避障次数统计
co = 0
corner = 0
count = 0
counter = 0
c0 = 30
c1 = 350
c2 = 120
c3 = 120
c4 = 70

rightConer = False
rightroundabout = 0
start_time = time.time()

if put1 == 1:
    c1 == 450
if put1 == 2 or put2 == 2:
    c2 = 200
if put1 == 3 or put2 == 3:
    c3 = 220
if put2 == 4:
    c4 = 180


while True:
    ret, frame = cap.read()
    imgCopy = frame
    if not ret:
        break

    counter += 1
    print("counter: " + str(counter))
    frame = cv2.GaussianBlur(frame, (13, 13), 10, 20)
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    now_time = time.time()
    if corner == 4 and ruku_find(frame) > 1500 and counter > c4:
        sentmes = "1.57/0/0/0/0/1/" + data2
        print("Final : " + sentmes)
        while True:
            sentmes = "1.57/0/0/0/0/1/" + data2
            #print("Final : " + sentmes)
            client_socket.send(sentmes.encode())

    else:
        cv2.putText(imgCopy, "avo= 0", (5, 150), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (255, 255, 255), 2)
        '''
        *******************************************************************************************
        图像处理，得到img
        *******************************************************************************************
        '''
        # 得到二值化图像bin
        bin = cv2.inRange(hsv, lower_yellow, upper_yellow)
        # 膨胀+腐蚀图像img
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        close = cv2.morphologyEx(bin, cv2.MORPH_CLOSE, kernel, iterations=1)

        '''背景过滤'''
        # 寻找连通区域
        num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(close, connectivity=8)
        # 过滤
        image_filtered = np.zeros_like(close)
        for (i, label) in enumerate(np.unique(labels)):
            # 如果是背景，忽略
            if label == 0:
                continue
            if (stats[i][1] + stats[i][3]) > 350:
                image_filtered[labels == i] = 255
                # break
        #frame1 = image_filtered
        _,frame1 = cv2.threshold(image_filtered, 0, 255 ,cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        '''道路过滤'''
        # 寻找连通区域
        num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(~frame1, connectivity=8)
        # 过滤
        image_filtered = np.zeros_like(close)
        for (i, label) in enumerate(np.unique(labels)):
            # 如果是背景，忽略
            if label == 0:
                continue
            if stats[i][-1] > 1500:  # 10000
                image_filtered[labels == i] = 255
        img = ~image_filtered

        if (img[0][0] == 255) and (img[399][479] == 255):
            print("Out of road: 1")
            point_centre_down = 220
            point_centre_up = 220
            #sentmes = "1.57/0/0/0/1/0/" + data2
            #client_socket.send(sentmes.encode())
            continue

        point_left_down_state = 0
        if (corner == 0 and counter > c0) or (corner == 1 and counter > c1):
            '''
            *******************************************************************************************
            找左下拐点，看边线落差
            *******************************************************************************************
            '''
            # 以上一次的point_centre_down作为起点，向左边扫描，找第一个边线点
            point_left_down_state = 0
            s = 330
            lc = 0  # last_c
            for c in range(point_centre_down + scan1, 40, -1):  # 左
                if c == 41:
                    lc = c
                    break
                if img[s][c] == 0:
                    lc = c
                    break
            # 以上一个边线点为起点，向上面一个点找边线
            dif = 0
            for r in range(s - 1, 280, -1):
                if img[r][lc] == 255:
                    for c in range(lc, lc - 25, -1):
                        if (img[r][c] == 0) or (c < (lc - 23)):
                            dif = lc - c
                            lc = c
                            break
                    if dif > 15:
                        point_left_down_state = 1
                        cv2.circle(imgCopy, (lc, r), 10, (100, 255, 255), -1)
                        cv2.putText(imgCopy, "Find A Corner", (120, 200), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 255), 5)
                        break
                    else:
                        continue

                if img[r][lc] == 0:
                    for c in range(lc, lc + 150, 2):
                        if (img[r][c] == 255) or (c > (lc + 70)):
                            dif = c - lc
                            lc = c
                            break
                    if dif > 20:
                        break
                    else:
                        continue
        rightConer = 0
        white_point = 0
        if (counter > c2 and corner == 2) or (counter > c3 and corner == 3) or (counter > c4 and corner == 4):
            for i in range(248, 252):
                for j in range(0, 400, 1):
                    if img[i][j] == 255:
                        white_point += 1
            if white_point > 800:
                rightConer = 1
        if point_left_down_state == 1:
            corner += 1
            half_time = time.time()
            counter = 0
            '''**********通讯发送'''
            sentmes = "1.57/0/0/1/0/0/" + data2
            print("corner corner" + str(corner) + "   " + sentmes)
            client_socket.send(sentmes.encode())
        if rightConer and corner < 4:
            corner += 1
            half_time = time.time()
            counter = 0
            '''**********通讯发送'''
            sentmes = "1.57/0/0/1/0/0/" + data2
            print("corner corner" + str(corner) + "   " + sentmes)
            client_socket.send(sentmes.encode())
        '''bizhang'''
        if avoid_count == 0:
            # 得到二值化图像bin
            bin = cv2.inRange(hsv, lower_green, upper_green)
            cnts = cv2.findContours(bin, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)[0]
            area = 0
            for c in cnts:
                tmp = cv2.contourArea(c)
                if tmp > area:
                    area = tmp
        if (avoid_count == 0) and (area > 4000):
            avoid_count = 1
            counter -= 60
            cv2.putText(imgCopy, "avo= 1", (5, 150), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (255, 255, 255), 2)
            '''**********通讯发送'''
            sentmes = "1.57/0/0/0/1/0/"+data2
            print("avoid : " + sentmes)
            client_socket.send(sentmes.encode())
        else:
            '''
            *******************************************************************************************
            提取中线，找左右边线，然后找中线
            *******************************************************************************************
            '''
            sum_left = 0
            sum_right = 0
            '''**********上方中点扫线'''
            for r in range(299, 302):
                cr = False
                cl = False
                # 特殊扫线（三岔等），如果中间是黑的，往左（右）找白色，先找到的是右（左）线
                if img[r][point_centre_up] == 0:
                    for c in range(point_centre_up + scan1, 50, -2):
                        if (not cr) and (not cl) and (img[r][c] == 255):  # 往左找，且没找到左边的右边线，同时右边没找到左边线
                            sum_right += c
                            cr = True
                            continue
                        if (not cl) and (not cr) and (img[r][440 - c] == 255):  # 往右找，且没找到右边的左边线，同时左边没找到右边线
                            sum_left += 440 - c
                            cl = True
                            continue
                        if cr and (img[r][c] == 0):  # 在左边找到右边线，然后找到左边线
                            sum_left += c
                            break
                        if cl and (img[r][440 - c] == 0):  # 在右边找到左边线，然后找到右边线
                            sum_right += 440 - c
                            break
                        if (c < 60) and (not cl) and (not cr):
                            print("No line_ left/right")
                            cv2.putText(imgCopy, "No line_ left/right", (120, 300), cv2.FONT_HERSHEY_SIMPLEX, 1.5,
                                        (200, 200, 200), 5)
                            break
                    continue
                # 常规扫线
                for c in range(point_centre_up + scan1, 80, -3):
                    if c <= 85:
                        sum_left += c
                        break
                    if img[r][c] == 0:
                        sum_left += c
                        break
                for c in range(point_centre_up + scan1, 360, 3):
                    if c >= 355:
                        sum_right += c
                        break
                    if img[r][c] == 0:
                        sum_right += c
                        break
            '''根据上点周围五行中点位置，计算平均值'''
            point_centre_up = int((sum_right + sum_left) / 6)

            '''**********下方中点扫线'''
            sum_left = 0
            sum_right = 0
            for r in range(349, 352):
                cr = False
                cl = False
                # 特殊扫线，如果中间是黑的，往左（右）找白色，先找到的是右（左）线
                if img[r][point_centre_down] == 0:
                    for c in range(point_centre_down, 50, -3):
                        if (not cr) and (not cl) and (img[r][c] == 255):  # 往左找，且没找到左边的右边线，同时右边没找到左边线
                            sum_right += c
                            cr = True
                            continue
                        if (not cl) and (not cr) and (img[r][440 - c] == 255):  # 往右找，且没找到右边的左边线，同时左边没找到右边线
                            sum_left += 440 - c
                            cl = True
                            continue
                        if cr and (img[r][c] == 0):  # 在左边找到右边线，然后找到左边线
                            sum_left += c
                            break
                        if cl and (img[r][440 - c] == 0):  # 在右边找到左边线，然后找到右边线
                            sum_right += 440 - c
                            break
                        if (c < 60) and (not cl) and (not cr):
                            print("No line_ left/right")
                            cv2.putText(imgCopy, "No line_ left/right", (120, 300), cv2.FONT_HERSHEY_SIMPLEX, 1.5,
                                        (200, 200, 200), 5)
                            break
                    continue
                # 正常扫线
                for c in range(point_centre_down, 0, -3):
                    if c <= 10:
                        sum_left += c
                        break
                    if img[r][c] == 0:
                        sum_left += c
                        break
                for c in range(point_centre_down, 480, 3):
                    if c >= 470:
                        sum_right += c
                        break
                    if img[r][c] == 0:
                        sum_right += c
                        break
            '''根据下点周围五行中点位置，计算平均值'''
            point_centre_down = int((sum_right + sum_left) / 6)

            '''**********计算angle和distance'''
            if abs(point_centre_down - point_centre_up) < 2:
                angle = 1.57
            else:
                k = - 50 / (point_centre_down - point_centre_up)
                angle = np.arctan(k)  # 弧度

            distance = int(220 - point_centre_down)

            '''**********计算上中点到界外的垂直距离extent'''
            extent = 0
            for r in range(300, 0, -2):
                if img[r][point_centre_up] == 0:
                    break
                extent += 2
            for r in range(300, 0, -2):
                if img[r][point_centre_up + 3] == 0:
                    break
                extent += 2
            for r in range(300, 0, -2):
                if img[r][point_centre_up - 3] == 0:
                    break
                extent += 2
            extent /= 3
            if (extent <= 15) and ((1.39 < angle) or (angle < -1.39)):
                cv2.putText(imgCopy, "Find A Fork", (120, 100), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 255), 5)
                angle = -0.57
                print("fork*************")
                point_centre_up = 120

            '''**********通讯发送'''
            sentmes = str(angle) + "/" + str(distance) + "/" + str(extent) + "/0/0/0/" + data2
            #print("common: " + sentmes)
            client_socket.send(sentmes.encode())

    '''输出窗口'''
    # cv2.imshow("imgCopy", imgCopy)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

'''通信结束代码'''
cap.release()
client_socket.shutdown(2)
client_socket.close()
cv2.destroyAllWindows()
