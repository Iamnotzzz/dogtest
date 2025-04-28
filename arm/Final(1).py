import serial
import argparse
import threading
import cv2
import numpy as np
import onnxruntime as ort
import time
import random
# import RPi.GPIO as GPIO
import json
import queue

# ----------全局变量----------
pinPUL1 = 26
pinDIR1 = 19
pinPUL2 = 6
pinDIR2 = 5
pinTRAN1 = 21
pinTRAN2 = 20
center_relative_x = 0
distance_number = 0
center_relative_y = 0

# 用于存储识别结果的队列
detection_queue = queue.Queue()

# ----------串口通信函数----------
# read_serial(ser)
# 在新线程中运行，不断读取从串口接收到的数据并打印出来
def read_serial(ser):
    while True:
        data = ser.readline().decode('utf-8')
        if data:
            print(f"Received: {data}", end='')

# setup_serial(port)
# 接受一个端口名称作为输入，配置并返回一个配置好的serial.Serial对象ser
def setup_serial(port):
    ser = serial.Serial(port, baudrate=115200, dsrdtr=None)
    ser.setRTS(False)
    ser.setDTR(False)
    return ser

# start_serial_reading_thread(ser)
# 接受一个serial.Serial对象，创建并启动一个线程用于读取串口数据
def start_serial_reading_thread(ser):
    serial_recv_thread = threading.Thread(target=lambda: read_serial(ser))
    serial_recv_thread.daemon = True
    serial_recv_thread.start()
    return serial_recv_thread

# send_commands(ser)
# 接受用户的输入并将其发送到串口，使用try except结构来优雅地处理KeyboardInterrupt
def send_commands(ser):
    try:
        while True:
            command = input("")
            ser.write(command.encode() + b'\n')
    except KeyboardInterrupt:
        pass

# parse_arguments()
# 使用argparse来解析命令行参数
def parse_arguments():
    parser = argparse.ArgumentParser(description='Serial JSON Communication')
    parser.add_argument('-p', '--port', type=str, default='COM20')
    return parser.parse_args()

# ----------步进电机控制函数----------
# setup()
# GPIO初始化
def setup():
    # 使用BCM编码方式
    GPIO.setmode(GPIO.BCM)

    GPIO.setup(pinPUL1, GPIO.OUT)
    GPIO.setup(pinDIR1, GPIO.OUT)
    GPIO.setup(pinPUL2, GPIO.OUT)
    GPIO.setup(pinDIR2, GPIO.OUT)
    GPIO.setup(pinTRAN1, GPIO.OUT)
    GPIO.setup(pinTRAN2, GPIO.OUT)

    # 电平转换模块DIR端口置低电平，转换方向为B=>A
    GPIO.output(pinTRAN1, GPIO.LOW)
    GPIO.output(pinTRAN2, GPIO.LOW)

    return True

# --车尾--
# |-机舱-|
# |      |
# |      |
# --车头--

# CWPar()
# 横滑轨向车尾移动
def CWPar():
    GPIO.output(pinDIR1, GPIO.LOW)


# CCWPar()
# 横滑轨向车头移动
def CCWPar():
    GPIO.output(pinDIR1, GPIO.HIGH)


# CWVer()
# 竖滑轨向图中右侧移动
def CWVer():
    GPIO.output(pinDIR2, GPIO.LOW)


# CCWVer()
# 竖滑轨向图中左侧移动
def CCWVer():
    GPIO.output(pinDIR2, GPIO.HIGH)


# pulseOncePar(delayMicroS)
# 发射一次脉冲
def pulseOncePar(delayMicroS):
    GPIO.output(pinPUL1, GPIO.HIGH)
    time.sleep(delayMicroS / 1_000_000.0)  # 将微秒转换为秒
    GPIO.output(pinPUL1, GPIO.LOW)
    time.sleep(delayMicroS / 1_000_000.0)


# pulseOnceVer(delayMicroS)
# 发射一次脉冲
def pulseOnceVer(delayMicroS):
    # 发射一次脉冲
    GPIO.output(pinPUL2, GPIO.HIGH)
    time.sleep(delayMicroS / 1_000_000.0)  # 将微秒转换为秒
    GPIO.output(pinPUL2, GPIO.LOW)
    time.sleep(delayMicroS / 1_000_000.0)


# pulsePar(count, delayMicroS)
# 发射count次脉冲
def pulsePar(count, delayMicroS):
    for _ in range(count):
        pulseOncePar(delayMicroS)


# pulseVer(count, delayMicroS)
# 发射count次脉冲
def pulseVer(count, delayMicroS):
    for _ in range(count):
        pulseOnceVer(delayMicroS)


# ----------图像识别部分----------
# plot_one_box(x, img, color=None, label=None, line_thickness=None)
# 在图像上绘制一个边界框，并显示框的中心坐标、框的像素高度和物体的估计距离
def plot_one_box(x, img, color=None, label=None, line_thickness=None):

    sign_ppx = 130
    sign_dis = 50  # 在50cm处的像素高为131ppx
    actual_height = 10  # 甜椒实际高度：10cm
    camera_f = (sign_ppx * sign_dis) / actual_height  # 相机焦距

    tl = (
            line_thickness or round(0.002 * (img.shape[0] + img.shape[1]) / 2) + 1
    )  # line/font thickness
    color = color or [random.randint(0, 255) for _ in range(3)]
    c1, c2 = (int(x[0]), int(x[1])), (int(x[2]), int(x[3]))

    label_height = c2[1] - c1[1]  # 计算框的像素高

    cv2.rectangle(img, c1, c2, color, thickness=tl, lineType=cv2.LINE_AA)
    if label:
        tf = max(tl - 1, 1)  # font thickness
        t_size = cv2.getTextSize(label, 0, fontScale=tl / 3, thickness=tf)[0]
        c2 = c1[0] + t_size[0], c1[1] - t_size[1] - 3
        cv2.rectangle(img, c1, c2, color, -1, cv2.LINE_AA)  # filled
        cv2.putText(
            img,
            label,
            (c1[0], c1[1] - 2),
            0,
            tl / 3,
            [225, 255, 255],
            thickness=tf,
            lineType=cv2.LINE_AA,
        )

        # 计算中心坐标
        center_x = (c1[0] + c2[0]) // 2
        center_y = (c1[1] + c2[1]) // 2

        # 获取画面中心坐标
        img_center_x = img.shape[1] // 2
        img_center_y = img.shape[0] // 2

        # 计算每个框中心相对于画面中心的偏移量
        center_offset_x = center_x - img_center_x
        center_offset_y = center_y - img_center_y

        # 计算相对于画面中心的中心坐标
        global center_relative_x
        global center_relative_y
        center_relative_x = center_offset_x
        center_relative_y = center_offset_y

        # 绘制相对于画面中心的中心坐标
        center_label = f"Center: ({center_relative_x}, {center_relative_y})"
        cv2.putText(
            img,
            center_label,
            (center_x, c2[1]),  # 使中心坐标显示在框的最下端
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (255, 255, 255),
            2,
            cv2.LINE_AA,
        )

        # 计算框的像素高
        height_label = f"H: {label_height}"
        # 绘制框的像素高
        cv2.putText(
            img,
            height_label,
            (c2[0], c1[1] + 2 * t_size[1]),  # 微调垂直位置，确保不重叠
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (255, 255, 255),
            2,
            cv2.LINE_AA,
        )

        # 计算距离
        global distance_number
        distance_number = int(camera_f * actual_height / label_height)
        distance = f"Dis: {distance_number}"
        # 绘制距离
        cv2.putText(
            img,
            distance,
            (c2[0], c1[1] + t_size[1]),  # 微调垂直位置，确保不重叠
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (255, 255, 255),
            2,
            cv2.LINE_AA,
        )
        return center_relative_x, distance, center_relative_y  # 返回计算得到的坐标和距离
    return None, None, None

# _make_grid(nx, ny)
# 生成网格，用于校正输出坐标
def _make_grid(nx, ny):
    xv, yv = np.meshgrid(np.arange(ny), np.arange(nx))
    return np.stack((xv, yv), 2).reshape((-1, 2)).astype(np.float32)

# cal_outputs(outs, nl, na, model_w, model_h, anchor_grid, stride)
# 对模型的输出进行坐标转换和缩放
def cal_outputs(outs, nl, na, model_w, model_h, anchor_grid, stride):
    row_ind = 0
    grid = [np.zeros(1)] * nl
    for i in range(nl):
        h, w = int(model_w / stride[i]), int(model_h / stride[i])
        length = int(na * h * w)
        if grid[i].shape[2:4] != (h, w):
            grid[i] = _make_grid(w, h)

        outs[row_ind:row_ind + length, 0:2] = (outs[row_ind:row_ind + length, 0:2] * 2. - 0.5 + np.tile(
            grid[i], (na, 1))) * int(stride[i])
        outs[row_ind:row_ind + length, 2:4] = (outs[row_ind:row_ind + length, 2:4] * 2) ** 2 * np.repeat(
            anchor_grid[i], h * w, axis=0)
        row_ind += length
    return outs

# post_process_opencv(outputs, model_h, model_w, img_h, img_w, thred_nms, thred_cond)
# 进行非极大值抑制（NMS）来筛选重叠的边界框，并最终确定检测框
def post_process_opencv(outputs, model_h, model_w, img_h, img_w, thred_nms, thred_cond):
    conf = outputs[:, 4].tolist()
    c_x = outputs[:, 0] / model_w * img_w
    c_y = outputs[:, 1] / model_h * img_h
    w = outputs[:, 2] / model_w * img_w
    h = outputs[:, 3] / model_h * img_h
    p_cls = outputs[:, 5:]
    if len(p_cls.shape) == 1:
        p_cls = np.expand_dims(p_cls, 1)
    cls_id = np.argmax(p_cls, axis=1)

    p_x1 = np.expand_dims(c_x - w / 2, -1)
    p_y1 = np.expand_dims(c_y - h / 2, -1)
    p_x2 = np.expand_dims(c_x + w / 2, -1)
    p_y2 = np.expand_dims(c_y + h / 2, -1)
    areas = np.concatenate((p_x1, p_y1, p_x2, p_y2), axis=-1)

    areas = areas.tolist()
    ids = cv2.dnn.NMSBoxes(areas, conf, thred_cond, thred_nms)
    if len(ids) > 0:
        return np.array(areas)[ids], np.array(conf)[ids], cls_id[ids]
    else:
        return [], [], []

# infer_img(img0, net, model_h, model_w, nl, na, stride, anchor_grid, thred_nms=0.4, thred_cond=0.5)
# 对输入图像进行预处理，通过模型进行推理，并对输出进行后处理
def infer_img(img0, net, model_h, model_w, nl, na, stride, anchor_grid, thred_nms=0.4, thred_cond=0.5):
    # 图像预处理
    img = cv2.resize(img0, [model_w, model_h], interpolation=cv2.INTER_AREA)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img = img.astype(np.float32) / 255.0
    blob = np.expand_dims(np.transpose(img, (2, 0, 1)), axis=0)

    # 模型推理
    outs = net.run(None, {net.get_inputs()[0].name: blob})[0].squeeze(axis=0)

    # 输出坐标矫正
    outs = cal_outputs(outs, nl, na, model_w, model_h, anchor_grid, stride)

    # 检测框计算
    img_h, img_w, _ = np.shape(img0)
    boxes, confs, ids = post_process_opencv(outs, model_h, model_w, img_h, img_w, thred_nms, thred_cond)

    # 处理每个检测框
    for box, score, id in zip(boxes, confs, ids):
        # 从box中提取或计算出x, y, z坐标
        x, y, z = center_relative_x, distance_number, center_relative_y
        detection_queue.put({"x": x, "y": y + 100, "z": z + 180, "t": random.uniform(3.5, 4)})
        # args = parse_arguments()
        # ser = setup_serial(args.port)
        # start_serial_reading_thread(ser)
        # send_command(ser)
        # ser.close()

    return boxes, confs, ids

# ----------综合函数----------

# peel_queue(q)
# 查看队列内容的函数
def peek_queue(q):
    temp_stack = []
    # 将队列中的元素暂时移出，存到另一个列表中
    while not q.empty():
        data = q.get()
        print(data)
        temp_stack.append(data)
    # 把数据重新放回队列
    for item in reversed(temp_stack):
        q.put(item)

# send_command(serial_obj)
# 不断从队列中读取位置信息，并发送JSON格式的指令
def send_command(serial_obj):
    while True:
        if not detection_queue.empty():
            data = detection_queue.get()
            command = json.dumps({"T": 1041, "x": data["x"], "y": data["y"], "z": data["z"], "t": data["t"]})
            serial_obj.write(command.encode() + b'\n')
            print(f"Sent: {command}")

def run_model_inference():
    # 模型加载
    model_pb_path = "sweet_pepper_lite.onnx"
    so = ort.SessionOptions()
    net = ort.InferenceSession(model_pb_path, so)

    # 标签字典
    dic_labels = {0: 'Pimiento'}

    # 模型参数
    model_h = 320
    model_w = 320
    nl = 3
    na = 3
    stride = [8., 16., 32.]
    anchors = [[10, 13, 16, 30, 33, 23], [30, 61, 62, 45, 59, 119], [116, 90, 156, 198, 373, 326]]
    anchor_grid = np.asarray(anchors, dtype=np.float32).reshape(nl, -1, 2)

    video = 0
    cap = cv2.VideoCapture(video)
    flag_det = True

    while True:
        success, img0 = cap.read()
        if success:

            if flag_det:
                t1 = time.time()
                det_boxes, scores, ids = infer_img(img0, net, model_h, model_w, nl, na, stride, anchor_grid,
                                                   thred_nms=0.4, thred_cond=0.5)
                t2 = time.time()

                for box, score, id in zip(det_boxes, scores, ids):
                    id = int(id)
                    label = '%s:%.2f' % (dic_labels[id], score)
                    # print(label)

                    # print("Content of box:", box)
                    c1, c2 = (int(box[0][0]), int(box[0][1])), (int(box[0][2]), int(box[0][3]))
                    plot_one_box(np.array([c1[0], c1[1], c2[0], c2[1]]), img0, color=(255, 0, 0), label = label, line_thickness = None)

                str_FPS = "FPS: %.2f" % (1. / (t2 - t1))

                cv2.putText(img0, str_FPS, (50, 50), cv2.FONT_HERSHEY_COMPLEX, 1, (0, 255, 0), 3)

            cv2.imshow("video", img0)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):

            break
        elif key & 0xFF == ord('s'):
            flag_det = not flag_det
            print(flag_det)

def run_motors_randomly():
    if not setup():
        return 1

    # 创建一个列表，包含所有可能的方向控制函数
    direction_functions = [CWVer, CWPar, CCWVer, CCWPar]

    # 随机选择并执行函数，使用多线程来控制电机的脉冲发送
    for _ in range(4):  # 假设我们想随机执行4次
        # 随机选择一个方向控制函数
        direction_func = random.choice(direction_functions)
        direction_func()

        # 根据选择的方向函数确定使用哪个脉冲函数
        if direction_func in [CWVer, CCWVer]:
            pulse_func = pulseVer
        else:
            pulse_func = pulsePar

        # 创建并启动线程
        thread = threading.Thread(target=pulse_func, args=(1600 * 2, 100))
        thread.start()
        thread.join()

    # main
def main():
    # 解析命令行参数
    args = parse_arguments()

    # 设置串口并启动读取线程
    ser = setup_serial(args.port)
    serial_thread = start_serial_reading_thread(ser)

    # 创建图像识别线程
    model_thread = threading.Thread(target=run_model_inference)
    model_thread.daemon = True
    model_thread.start()

    # 创建并启动串口发送命令线程
    command_thread = threading.Thread(target=send_command, args=(ser,))
    command_thread.daemon = True
    command_thread.start()

    # 等待图像识别线程结束
    model_thread.join()

    # 关闭串口
    ser.close()

if __name__ == "__main__":
    main()
