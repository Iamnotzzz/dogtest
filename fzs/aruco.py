import cv2
import numpy as np
# 加载Aruco字典
aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_6X6_250)  # 选择一种Aruco字典
parameters = cv2.aruco.DetectorParameters()  # 使用DetectorParameters()替代create()
# 打开摄像头（如果你有摄像头设备）
cap = cv2.VideoCapture(0)  # 0代表默认摄像头，如果有多个摄像头，可以调整数字

if not cap.isOpened():
    print("无法打开摄像头")
    exit()

while True:
    ret, frame = cap.read()  # 读取摄像头帧
    if not ret:
        print("无法读取摄像头帧")
        break

    # 转换为灰度图
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # 检测Aruco标记
    corners, ids, rejectedImgPoints = cv2.aruco.detectMarkers(gray, aruco_dict, parameters=parameters)

    # 如果检测到标记
    if len(corners) > 0:
        # 在图像中绘制检测到的标记
        frame = cv2.aruco.drawDetectedMarkers(frame, corners, ids)

        # 标记ID的显示
        for i in range(len(ids)):
            # 获取标记的ID
            id = ids[i][0]
            # 在每个标记的中心绘制ID
            center = np.mean(corners[i][0], axis=0).astype(int)
            cv2.putText(frame, str(id), tuple(center), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

    # 显示图像
    cv2.imshow("Aruco Markers Detection", frame)

    # 按'q'键退出
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# 释放摄像头并关闭窗口
cap.release()
cv2.destroyAllWindows()
