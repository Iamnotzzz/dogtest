import serial
import argparse
import threading
import json


def read_serial():
    while True:
        data = ser.readline().decode('utf-8').strip()
        if data:
            print(f"Received: {data}")


def main():
    global ser
    parser = argparse.ArgumentParser(description='Serial JSON Communication')
    parser.add_argument('port', type=str, help='Serial port name (e.g., COM1 or /dev/ttyUSB0)')

    args = parser.parse_args()

    ser = serial.Serial(args.port, baudrate=115200, dsrdtr=None)
    ser.setRTS(False)
    ser.setDTR(False)

    # 发送JSON指令
    json_command = {"T": 121, "joint": 1, "angle": 0, "spd": 90, "acc": 10}
    json_bytes = json.dumps(json_command).encode('utf-8') + b'\n'
    ser.write(json_bytes)

    serial_recv_thread = threading.Thread(target=read_serial)
    serial_recv_thread.daemon = True
    serial_recv_thread.start()

    try:
        while True:
            command = input("Enter command (or leave blank to continue): ")
            if command:
                ser.write(command.encode() + b'\n')
    except KeyboardInterrupt:
        pass
    finally:
        ser.close()


if __name__ == "__main__":
    main()