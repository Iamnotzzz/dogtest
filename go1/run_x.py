#!/usr/bin/python3

import sys
import time
import math
import socket
import serial  # 导入serial模组

sys.path.append('../lib/python/arm64')
import robot_interface as sdk

d_aerror = 0.0
d_derror = 0.0

# 字符串类型转浮点类型
def s_t_f(s):
    return float(s)


# 得到目标偏转弧度，指导偏航
def tg_angle(a_error, last_aerror):

    global d_aerror
    d_aerror = a_error - last_aerror
    last_aerror = a_error
    if abs(a_error) > 0.5:
        # target = 2.2 * a_error + 0.1 * d_aerror  # PID控制，P太大会导致振荡，D太大导致响应慢
        target = 2.3 * a_error + 0.2 * d_aerror  # PID控制，P太大会导致振荡，D太大导致响应慢
        # 2.2  0.1
    else:
        target = 0.9 * a_error + 0.8 * d_aerror
        # 1.1  0.5
        # target = 0.9 * a_error + 0.5 * d_aerror
    return last_aerror, target


# 得到目标偏移距离，指导侧向速度
def tg_distance(d_error, last_derror):
    global d_derror
    d_derror = d_error - last_derror
    last_derror = d_error
    if abs(d_error) < 0.08:
        #target = 1.9 * d_error + 0 * d_derror
        target = 0.9 * d_error + 2.1 * d_derror
        # 0.9  2.1
    else:
        target = 1.8 * d_error + 0.3 * d_derror  # PID控制，P太大会导致振荡，D太大导致响应慢
        #target = 1.3 * d_error + 0.5 * d_derror  # PID控制，P太大会导致振荡，D太大导致响应慢
        # 1.3  0.4
    return last_derror, target


def tg_action(target_angle, target_distance, velocity):
    #
    action_angle = target_angle
    action_angle = round(action_angle, 2)  # 四舍五入保留两位
    if abs(action_angle) > 2:
        if action_angle > 0:
            action_angle = 2  # 偏航转角速度不可超过57度每秒
        else:
            action_angle = -2
    #
    action_distance = target_distance
    action_distance = round(action_distance, 2)
    if abs(action_distance) > 0.4:
        if action_distance > 0:
            action_distance = 0.4  # 侧向速度不可超过15cm每秒
        else:
            action_distance = -0.4
    #                                 velocity前方视觉空间指导前进速度
    if velocity < 10:
        action_velocity = 0
    elif velocity < 30:
        action_velocity = 0.013 * velocity - 0.15
    elif velocity < 40:
        action_velocity = 0.013 * velocity - 0.15
    elif velocity < 70:
        action_velocity = 0.011 * velocity - 0.07
    elif velocity < 80:
        action_velocity = 0.01 * velocity
    elif velocity < 100:
        action_velocity = 0.01 * velocity
    else:
        action_velocity = 0.01  # 前进速度不可超过0.8 m/s
    #0.013   0.013   0.011

    '''
    if velocity < 10:
        action_velocity = 0
    elif velocity < 30:
        action_velocity = 0.015 * velocity - 0.15
    elif velocity < 40:
        action_velocity = 0.015 * velocity - 0.15
    elif velocity < 70:
        action_velocity = 0.008 * velocity + 0.14
    elif velocity < 80:
        action_velocity = 0.01 * velocity
    elif velocity < 100:
        action_velocity = 0.012 * velocity
    else:
        action_velocity = 0.012  # 前进速度不可超过0.8 m/s
    '''
    tmpk = (abs(d_aerror) + 1) * (abs(d_derror) + 1)  # 最少加1
    action_velocity = round((action_velocity / tmpk), 2)

    return action_angle, action_distance, action_velocity


# 分割数据函数
def get_data(data):
    try:
        li = data.split("/")
        a = li[0]
        d = li[1]
        v = li[2]
        s = li[3]
        z = li[4]
        r = li[5]
        put1 = li[6]
        put2 = li[7]
    except:
        a = "1.57"
        d = "-5"
        v = "0"
        s = "0"
        z = "0"
        r = "0"
        put1 = "0"
        put2 = "0"
    try:
        angle = s_t_f(a)
    except:
        angle = 1.57
    try:
        distance = s_t_f(d)
    except:
        distance = -5
    try:
        velocity = s_t_f(v)
    except:
        velocity = 0
    try:
        signal = s_t_f(s[0])
    except:
        signal = 0
    try:
        bz = s_t_f(z[0])
    except:
        bz = 0
    try:
        ruku = s_t_f(r[0])
    except:
        ruku = 0
    try:
        put1 = int(put1)
    except:
        put1 = 0
    try:
        put2 = int(put2)
    except:
        put2 = 0

    return angle, distance, velocity, signal, bz, ruku, put1, put2


# 一步动作，共0.5秒
def motion1(cmd, udp, state, forward=0, side=0, yaw=0):
    t = 0
    while t < 251:
        t = t + 1
        time.sleep(0.002)
        udp.Recv()
        udp.GetRecv(state)
        cmd.mode = 0  # 0:idle, default stand      1:forced stand     2:walk continuously
        cmd.gaitType = 0
        cmd.speedLevel = 0
        cmd.footRaiseHeight = 0
        cmd.bodyHeight = 0
        cmd.euler = [0, 0, 0]
        cmd.velocity = [0, 0]
        cmd.yawSpeed = 0.0
        cmd.reserve = 0
        if t < 250:
            cmd.mode = 2
            cmd.gaitType = 1
            cmd.yawSpeed=yaw
            #time.sleep(0.002)
            cmd.velocity = [forward, side]
            #cmd.yawSpeed = yaw
        udp.SetSend(cmd)
        udp.Send()

def stand(cmd, udp, state, forward=0, side=0, yaw=0):
    t = 0
    while t < 226:
        t = t + 1
        time.sleep(0.002)
        udp.Recv()
        udp.GetRecv(state)
        cmd.mode = 0  # 0:idle, default stand      1:forced stand     2:walk continuously
        cmd.gaitType = 0
        cmd.speedLevel = 0
        cmd.footRaiseHeight = 0
        cmd.bodyHeight = 0
        cmd.euler = [0, 0, 0]
        cmd.velocity = [0, 0]
        cmd.yawSpeed = 0.0
        cmd.reserve = 0
        if t < 75:
            cmd.mode = 5
            cmd.yawSpeed = yaw
            cmd.velocity = [forward, side]
        elif t < 150:
            cmd.mode = 6
            cmd.yawSpeed = yaw
            cmd.velocity = [forward, side]
        elif t < 225:
            cmd.mode = 1
            cmd.yawSpeed = yaw
            cmd.velocity = [forward, side]
        udp.SetSend(cmd)
        udp.Send()

def sit(cmd, udp, state, forward=0, side=0, yaw=0):
    t = 0
    while t < 1001:
        t = t + 1
        time.sleep(0.002)
        udp.Recv()
        udp.GetRecv(state)
        cmd.mode = 0  # 0:idle, default stand      1:forced stand     2:walk continuously
        cmd.gaitType = 0
        cmd.speedLevel = 0
        cmd.footRaiseHeight = 0
        cmd.bodyHeight = 0
        cmd.euler = [0, 0, 0]
        cmd.velocity = [0, 0]
        cmd.yawSpeed = 0.0
        cmd.reserve = 0
        if t < 250:
            cmd.mode = 2
            cmd.yawSpeed = yaw
            cmd.velocity = [forward, side]
        elif t < 500:
            cmd.mode = 1
            cmd.yawSpeed = yaw
            cmd.velocity = [forward, side]
        elif t < 750:
            cmd.mode = 6
            cmd.yawSpeed = yaw
            cmd.velocity = [forward, side]
        elif t < 1000:
            cmd.mode = 5
            cmd.yawSpeed = yaw
            cmd.velocity = [forward, side]
        udp.SetSend(cmd)
        udp.Send()


# 两步动作，共1秒，前进最大为0.5m,侧向最大为0.5m,偏航最大57度
def motion2(cmd, udp, state, forward1=0, side1=0, yaw1=0, forward2=0, side2=0, yaw2=0):
    motion1(cmd, udp, state, forward1, side1, yaw1)
    motion1(cmd, udp, state, forward2, side2, yaw2)



if __name__ == '__main__':
    HIGHLEVEL = 0xee
    LOWLEVEL = 0xff
    # 运动控制模块的udp通信，使用高层控制
    udp = sdk.UDP(HIGHLEVEL, 8080, "192.168.123.161", 8082)
    cmd = sdk.HighCmd()
    state = sdk.HighState()
    udp.InitCmdData(cmd)

    # 串口
    port = "/dev/ttyACM0"  # Arduino串口地址
    rates = 9600  # 设置波特率
    ser = serial.Serial(port, rates)  # 设置串口
    ser.flushInput()  # 清空缓存器


    print("start")
    user_input1 = input()

    print("stand")
    stand(cmd, udp, state, 0, 0, 0)
    user_input2 = input()
    motion1(cmd, udp, state, 0, 0.9, 0)

    # 视觉与运动socket通信的建立
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_ip = "192.168.123.13"  # 服务器地址
    server_port = 6011  # 定义端口号
    client_socket.connect((server_ip, server_port))
    client_socket.settimeout(1)

    action_angle = 0
    action_distance = 0
    action_velocity = 0
    last_aerror = 0
    last_derror = 0
    a_error = 0
    d_error = 0
    velocity = 0
    global a
    global b
    global attack
    time1 = 0
    time3 = 0
    time2 = 0
    time4 = 0
    time5 = 0
    tine6 = 0
    count = 0
    a = 0
    b = 0
    flag = 1
    attack = 0
    time.now = 0
    avi_count = 0
    time_start = time.time()
    while True:
        data="0/0/0/0/0/0/0/0/"
        data1 = "1/1/"
        time2 = time.time()
        time4 = time2
        if a > 1 or b > 1:
            if (time2 - time1) >= 3:
                a = 0
            if (time4-time3) >= 3:
                b = 0
        try:
            data = client_socket.recv(1024).decode()
        except socket.timeout:
            data = "0.1/-1/0/0/0/0/" + data1
            print('chaoshiiiiiiii')

        angle, distance, velocity, signal, bz, ruku, put1, put2 = get_data(data) # 对接收的数据进行分割

        #print(data)
        if flag == 1:
            flag = 0
            if (put1 == 1 and put2 == 2):
                data1 = "4"
                ser.write(data1.encode('utf-8'))
            if (put1 == 3 and put2 == 4):
                data1 = "5"
                ser.write(data1.encode('utf-8'))
            else:
                data1 = "6"
                ser.write(data1.encode('utf-8'))
            print(data1)
        if ruku == 1 and (time.time() - time_start) > 46:
            print("finish : " + str(time2 - time_start))
            motion1(cmd, udp, state, 1.0, 0, 0)
            motion2(cmd, udp, state, 0, -0.8, 0, 0, -0.7, 0)
            break
        if count == 1 and (time.time() - time5) > 4:
            motion1(cmd, udp, state, 0.8, 0.1, 0)
            count = 0
            datax = client_socket.recv(32768).decode()
            print("11111111111111111111111111")
        if signal == 1:
            if attack < 1:
                print("Corner 1 : " + str(time2 - time_start))
                if put1 == 1:
                    data1 = "2"
                    ser.write(data1.encode('utf-8'))
                    motion2(cmd, udp, state, 0.9, 0, 0.8, 0.6, 0, 0.5)  # 前进120cm，旋转60度
                    motion1(cmd, udp, state, 0.5, 0, 1.3)
                    print("put1")
                    datax = client_socket.recv(32768).decode()
                else:
                    motion2(cmd, udp, state, 0.8, 0, 0, 0.8,0,0)
                    print("pass 1")
                    datax = client_socket.recv(32768).decode()
                time1 = time.time()
                tim2 = time1
                attack = attack + 1
                continue
            if attack == 1:
                time1 = time.time()
                time2 = time1
                attack += 1
                print("Corner 2 : " + str(time2 - time_start))
                if put1 == 2:
                    data1 = "2"
                    ser.write(data1.encode('utf-8'))
                    motion2(cmd, udp, state, 0.8, 0, 0.3, 0.8, 0, 0)
                    motion2(cmd, udp, state, 0.2, 0, 1.5,0.5,0,1.1) # 1.65
                    motion1(cmd, udp, state, 0.3, 0 , 0.9)
                    print("put 2")
                    count = 1
                    time5 =time.time()
                    datax = client_socket.recv(32768).decode()
                elif put2 == 2:
                    data1 = "3"
                    ser.write(data1.encode('utf-8'))
                    motion2(cmd, udp, state, 0.8, 0, 0.3, 0.8, 0, 0)
                    motion2(cmd, udp, state, 0.2, 0, 1.5,0.5,0,1.1) # 1.65
                    motion1(cmd, udp, state, 0.3,0,0.9)
                    print("put 2")
                    count = 1
                    time5 = time.time()
                    datax = client_socket.recv(32768).decode()
                else:
                    motion2(cmd, udp, state, 0.6,0,0,1,0,0)
                    print("pass 2")
                    datax = client_socket.recv(32768).decode()
                continue
            if attack == 2:
                attack += 1
                print("Corner 3 : " + str(time.time() - time_start))
                if put1 == 3:
                    data1 = "2"
                    ser.write(data1.encode('utf-8'))
                    motion1(cmd, udp, state, 1, 0, 0)
                    motion1(cmd, udp, state, 0.2, 0, 0)
                    print("put 3")
                    datax = client_socket.recv(32768).decode()
                elif put2 == 3:
                    data1 = "3"
                    ser.write(data1.encode('utf-8'))
                    motion1(cmd, udp, state, 1, 0, 0)
                    print("put 3")
                    datax = client_socket.recv(32768).decode()
                else:
                    motion1(cmd, udp, state, 0.7, 0, 0)
                    motion2(cmd, udp, state, 0, 0, 1.5,0,0,1.5)
                    print("pass 3")
                    datax = client_socket.recv(32768).decode()
                continue
            if attack == 3:
                attack += 1
                print("Corner 4 : " + str(time.time() - time_start))
                if put2 == 4:
                    data1 = "3"
                    motion2(cmd, udp, state, 0, -0.1, -0.5,1,0,0)
                    ser.write(data1.encode('utf-8'))
                    print("put 4")
                    datax = client_socket.recv(32768).decode()
                else:
                    motion1(cmd, udp, state, 0.7, 0, 0)
                    motion2(cmd, udp, state, 0, 0, 1.5,0,0,1.2)
                    print("pass 4")
                    datax = client_socket.recv(32768).decode()
                continue
            else:
                continue
        if bz == 1 and avi_count==0:
            print("Avoid : " + str(time2 - time_start))
            # 一号环岛直道
            
            motion1(cmd, udp, state, 0, 1.0,0)
            motion2(cmd, udp, state, 1,0,0,1.1,0,0)
            motion1(cmd, udp, state, 0,-1.4,0)
            # 左弯拐角
            '''
            motion1(cmd, udp, state, 0, 1.0,0)
            motion2(cmd, udp, state, 1.2,0,0,0,0,1.5)
            # 四号环岛前左弯增加延时
            time.sleep(1)
            '''
            # 出三岔
            '''
            motion2(cmd, udp, state, 0,0,1.3,0, 0.8,0)
            motion2(cmd, udp, state, 1.2,0,0,1.2,0,0)
            motion1(cmd, udp, state, 0,0,1.5)
            time.sleep(1)
            '''
            # 三号环岛斜道
            '''
            motion1(cmd, udp, state, 0, 0.6,0)
            motion2(cmd, udp, state, 1.5,0,0,0, 0,-1.5)
            motion1(cmd, udp, state, 0.7,0,0)
            '''
            datax = client_socket.recv(32768).decode()
            avi_count = 1
        else:
            # 数据初步处理
            if angle > 0:
                a_error = angle - 1.57
            else:
                a_error = 1.57 + angle
            a_error += 0.08
            if abs(a_error) > 2:
                continue
            # d_error = (distance + 3) * 0.0022
            d_error = (distance + 5) * 0.0022

            last_aerror, target_angle = tg_angle(a_error, last_aerror)
            last_derror, target_distance = tg_distance(d_error, last_derror)
            # 得到动作值
            action_angle, action_distance, action_velocity = tg_action(target_angle, target_distance, velocity)

            udp.Recv()
            udp.GetRecv(state)
            # 初始化
            cmd.mode = 0
            cmd.gaitType = 0
            cmd.speedLevel = 0
            cmd.footRaiseHeight = 0
            cmd.bodyHeight = 0
            cmd.euler = [0, 0, 0]
            cmd.velocity = [0, 0]
            cmd.yawSpeed = 0.0
            cmd.reserve = 0

            cmd.mode = 2
            cmd.gaitType = 1
            time2 = time.time()
            if (time1 is not 0) and ((time2 - time1) <= 4.4):
                action_velocity = 0.45
                # print("set velocity")
            cmd.yawSpeed = action_angle
            time.sleep(0.002)
            cmd.velocity = [action_velocity, action_distance]
            udp.SetSend(cmd)
            udp.Send()
            time.sleep(0.002)
            # print("action_angle:" + str(action_angle))
            # print("action_distance:" + str(action_distance))
            # print("action_velocity:" + str(action_velocity))

    #client_socket.terminate()
    client_socket.close()
    #ser.close()
