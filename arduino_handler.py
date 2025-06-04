import time
import serial


class ArduinoHandler:
    def __init__(self, port="/dev/ttyUSB0", baud_rate=9600):
        self.port = port
        self.baud_rate = baud_rate
        self.connection = None

    def connect(self):
        try:
            self.connection = serial.Serial(self.port, self.baud_rate, timeout=1)
            time.sleep(2)  
            print("Connected to Arduino")
        except serial.SerialException as e:
            print(f"Serial connection error: {e}")
            self.connection = None

    def send_command(self, command):
        if self.connection:
            self.connection.write(command.encode())
            print(f"Sent command: {command}")
        else:
            print("Connection is not open. Cannot send command.")

    def close(self):
        if self.connection:
            self.connection.close()
            print("Connection closed")
