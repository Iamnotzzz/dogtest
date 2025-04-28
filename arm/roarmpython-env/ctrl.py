import serial
import argparse
import threading
import time
import json


def read_serial():
    while True:
        data = ser.readline().decode('utf-8')
        if data:
            print(f"Received: {data}", end='')


def send_json_commands(ser, commands):
    for cmd in commands:
        json_bytes = json.dumps(cmd).encode('utf-8') + b'\n'
        ser.write(json_bytes)
        print(f"Sent: {json_bytes.decode('utf-8').strip()}")
        time.sleep(2)  # 延时3秒


def main():
    global ser
    parser = argparse.ArgumentParser(description='Serial JSON Communication')
    parser.add_argument('port', type=str, help='Serial port name (e.g., COM1 or /dev/ttyUSB0)')

    args = parser.parse_args()

    ser = serial.Serial(args.port, baudrate=115200, dsrdtr=None)
    ser.setRTS(False)
    ser.setDTR(False)

    serial_recv_thread = threading.Thread(target=read_serial)
    serial_recv_thread.daemon = True
    serial_recv_thread.start()

    # 定义要发送的JSON指令字典，键是用户输入的数字，值是对应的指令列表
    json_commands_dict = {
        # 抓取（松）
        '1': [
            # 底座转90度
        {"T": 122, "b": -90, "s": 90, "e": 75, "h": 171, "spd": 45, "acc": 10},
            # 机械爪抓取
            {"T": 121, "joint": 1, "angle": -90, "spd": 45, "acc": 10},
            # 机械臂伸下去，爪子不动

            {"T": 106, "cmd": 4, "spd": 800, "acc": 0},
            # 机械臂回原位，机械爪不动
            {"T": 122, "b": 0, "s": 0, "e": 160, "h": 229, "spd":45, "acc": 10}
        ],
        # 放下（右）
        '2': [
            {"T": 121, "joint": 1, "angle": -90, "spd": 45, "acc": 10},
            {"T": 122, "b": -90, "s": 50, "e": 75, "h": 229, "spd": 45, "acc": 10},
            {"T": 106, "cmd": 3, "spd": 800, "acc": 0},
            {"T": 122, "b": 0, "s": 0, "e": 160, "h": 171, "spd": 45, "acc": 10}
        ],
        #抓取（紧）
        '3': [
            # 底座转90度
            {"T": 121, "joint": 1, "angle": -90, "spd": 45, "acc": 10},
            # 机械臂伸下去，爪子不动
            {"T": 122, "b": -90, "s": 50, "e": 75, "h": 171, "spd": 45, "acc": 10},
            # 机械爪抓取
            {"T": 106, "cmd": 4.5, "spd": 800, "acc": 0},
            # 机械臂回原位，机械爪不动
            {"T": 122, "b": 0, "s": 0, "e": 160, "h": 259, "spd": 45, "acc": 10}
        ],
        #放下（左）
        '4': [
            {"T": 121, "joint": 1, "angle": 90, "spd": 45, "acc": 10},
            {"T": 122, "b": -90, "s": 50, "e": 75, "h": 229, "spd": 45, "acc": 10},
            {"T": 106, "cmd": 3, "spd": 800, "acc": 0},
            {"T": 122, "b": 0, "s": 0, "e": 160, "h": 171, "spd": 45, "acc": 10}
        ],
    }

    try:
        while True:
            command = input("Enter a number (1-4, or leave blank to exit): ")
            if not command:
                break  # 如果用户输入为空，则退出循环
            if command in json_commands_dict:
                send_json_commands(ser, json_commands_dict[command])
            else:
                print("Invalid input. Please enter a number between 1 and 4.")
    except KeyboardInterrupt:
        pass
    finally:
        ser.close()


if __name__ == "__main__":
    main()