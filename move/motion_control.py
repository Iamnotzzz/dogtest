# motion_control.py
import socket
import time
import sys
import math
import robot_interface as sdk

# ========== 初始化 UDP 接收 ==========
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_ip = "127.0.0.1"   # 这里改成机器狗的 IP 地址
server_port = 6011
server_socket.bind((server_ip, server_port))
server_socket.listen()
print(f"Waiting for connection on {server_ip}:{server_port}...")

# 等待连接
client_socket, client_address = server_socket.accept()
print(f"Connected to {client_address}")

# ========== 初始化机器狗 UDP 控制 ==========
HIGHLEVEL = 0xee
LOWLEVEL = 0xff
udp = sdk.UDP(HIGHLEVEL, 8080, "192.168.123.13", 8082)
cmd = sdk.HighCmd()
state = sdk.HighState()
udp.InitCmdData(cmd)

# ========== PID 控制参数 ==========
d_aerror = 0.0
d_derror = 0.0
last_aerror = 0
last_derror = 0

def tg_angle(a_error, last_aerror):
    """PID 控制计算目标转向角度"""
    global d_aerror
    d_aerror = a_error - last_aerror
    last_aerror = a_error
    if abs(a_error) > 0.5:
        target = 2.3 * a_error + 0.2 * d_aerror
    else:
        target = 0.9 * a_error + 0.8 * d_aerror
    return last_aerror, target

def tg_distance(d_error, last_derror):
    """PID 控制计算目标横向偏移"""
    global d_derror
    d_derror = d_error - last_derror
    last_derror = d_error
    if abs(d_error) < 0.08:
        target = 0.9 * d_error + 2.1 * d_derror
    else:
        target = 1.8 * d_error + 0.3 * d_derror
    return last_derror, target

def tg_action(target_angle, target_distance, velocity):
    """计算运动目标的矫正量"""
    action_angle = round(target_angle, 2)
    action_distance = round(target_distance, 2)

    if abs(action_angle) > 2:
        action_angle = 2 if action_angle > 0 else -2

    if abs(action_distance) > 0.4:
        action_distance = 0.4 if action_distance > 0 else -0.4

    action_velocity = max(min(0.01 * velocity, 0.8), 0.1)
    return action_angle, action_distance, action_velocity

def motion_control(cmd, udp, state, forward=0, side=0, yaw=0):
    """发送运动指令给机器狗"""
    t = 0
    while t < 251:
        t = t + 1
        time.sleep(0.002)
        udp.Recv()
        udp.GetRecv(state)
        cmd.mode = 0
        cmd.gaitType = 0
        cmd.speedLevel = 0
        cmd.footRaiseHeight = 0
        cmd.bodyHeight = 0
        cmd.euler = [0, 0, 0]
        cmd.velocity = [forward, side]
        cmd.yawSpeed = yaw
        cmd.reserve = 0
        
        if t < 250:
            cmd.mode = 2
            cmd.gaitType = 1
            cmd.yawSpeed = yaw
            cmd.velocity = [forward, side]

        udp.SetSend(cmd)
        udp.Send()

# ========== 主循环 ==========
print("运动控制已启动...")
while True:
    try:
        # 接收数据
        data = client_socket.recv(1024).decode()
        if data:
            # 解析数据
            angle, distance, *_ = map(float, data.split('/'))

            # PID 控制计算矫正量
            last_aerror, target_angle = tg_angle(angle, last_aerror)
            last_derror, target_distance = tg_distance(distance, last_derror)
            
            # 计算运动矫正
            action_angle, action_distance, action_velocity = tg_action(target_angle, target_distance, 0.2)

            # 执行运动
            motion_control(cmd, udp, state, action_velocity, action_distance, action_angle)
            print(f"运动指令 -> 角度: {action_angle}, 偏移: {action_distance}, 速度: {action_velocity}")
    except Exception as e:
        print(f"接收错误: {e}")
        break

client_socket.close()
server_socket.close()
