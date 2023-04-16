#pyserial-3.5
import serial

ser = serial.Serial('COM8', baudrate=9600, bytesize=serial.EIGHTBITS, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE)

while True:
    if ser.in_waiting > 0:
        data = ser.read(ser.in_waiting).decode().rstrip()
        print(data)