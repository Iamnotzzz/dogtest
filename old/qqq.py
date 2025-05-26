import cv2

# 初始化摄像头
cap = cv2.VideoCapture(0)  # 0是默认的摄像头索引

# 检查摄像头是否成功打开
if not cap.isOpened():
    print("无法打开摄像头")
    exit()

try:
    while True:
        # 读取视频帧
        ret, frame = cap.read()
        if not ret:
            print("无法读取帧")
            break

        # 显示视频帧
        cv2.imshow('Camera Frame', frame)

        # 按下 'q' 键退出循环
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
finally:
    # 释放摄像头和关闭所有窗口
    cap.release()
    cv2.destroyAllWindows()
