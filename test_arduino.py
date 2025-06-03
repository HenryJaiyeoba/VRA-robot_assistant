import time

import serial

SERIAL_PORT = "/dev/ttyUSB0"
BAUD_RATE = 9600


def test_arduino_connection():
    try:
        with serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1) as conn:
            time.sleep(2)
            conn.write(b"Hello Arduino\n")
            print("Sent message to Arduino")
    except serial.SerialException as e:
        print(f"Serial connection error: {e}")

    else:
        print("Arduino connection test passed")


if __name__ == "__main__":
    test_arduino_connection()
