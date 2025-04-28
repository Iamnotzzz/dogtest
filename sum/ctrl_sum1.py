import serial
import threading
import time
import json

# 定义Secondary_grab变量
Secondary_grab = 2

def read_serial():
    while True:
        data = ser.readline().decode('utf-8')
        if data:
            print(f"Received: {data}")

def send_json_commands(ser, commands):
    for cmd in commands:
        json_bytes = json.dumps(cmd).encode('utf-8') + b'\n'
        ser.write(json_bytes)
        print(f"Sent: {cmd}")
        time.sleep(3)  # 延时2秒

def main():
    global ser, Secondary_grab

    # 打开串行端口（这里需要根据实际情况填写正确的端口和波特率）
    ser = serial.Serial('COM3', baudrate=115200, dsrdtr=None)
    ser.setRTS(False)
    ser.setDTR(False)

    # 创建并启动读取线程
    serial_recv_thread = threading.Thread(target=read_serial)
    serial_recv_thread.daemon = True
    serial_recv_thread.start()

    # 定义JSON指令集
    json_commands_dict = {
        '1': [
            {"T": 121, "joint": 1, "angle": 90, "spd": 45, "acc": 10},
            {"T": 122, "b": -90, "s": 50, "e": 75, "h": 229, "spd": 45, "acc": 10},
            {"T": 106, "cmd": 3, "spd": 800, "acc": 0},
            {"T": 122, "b": 0, "s": 0, "e": 160, "h": 171, "spd": 45, "acc": 10}
        ],
        '2': [
            {"T": 121, "joint": 1, "angle": 90, "spd": 45, "acc": 10},
            {"T": 122, "b": -90, "s": 50, "e": 75, "h": 171, "spd": 45, "acc": 10}
        ]
    }

    try:
        while True:
            command = input("Enter a number (1 or 2): ")
            if command in json_commands_dict:
                Secondary_grab = 2  # 根据要求设置Secondary_grab为2
                send_json_commands(ser, json_commands_dict[command])
            else:
                print("Invalid input. Please enter either 1 or 2.")
    except KeyboardInterrupt:
        print("\nExiting program...")
    finally:
        ser.close()

if __name__ == "__main__":
    main()