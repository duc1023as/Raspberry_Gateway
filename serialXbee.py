#pyserial-3.5
#digi-xbee-1.4.1
import sys
from digi.xbee.devices import XBeeDevice
import binascii
import struct
from src.core.mqqt_provider import MQTT
from dotenv import load_dotenv
import os
import json
import time
from threading import Thread
import threading
import serial

# TODO: Replace with the serial port where your local module is connected to.
# PORT = "COM8"
PORT = "/dev/ttyUSB0"
# TODO: Replace with the baud rate of your local module. data.decode("ISO-8859-1")
BAUD_RATE = 9600

ROUTER1_NODE_ID = "Router"
# ROUTER2_NODE_ID = "ROUTER3"
ROUTER2_NODE_ID = "ROUTER3"


load_dotenv()

url_local = os.getenv("URL_MQTT")
user_local = os.getenv("USER")
passworld_local = os.getenv("PASSWORD")
port_local = os.getenv("PORT")
topic_will = os.getenv("TOPIC_WILLZb")
msg_will = {
    "status":"OFF"
}
msg_onl = {
    "status":"ON"
}

# Set up for MQTT local
topic_DHT = "Zigbee/DHT"
topic_LED = "Zigbee/LED"



client = MQTT(
    url=url_local,
    user=user_local,
    password=passworld_local,
    port=port_local,
    id='local_Zigbee',
    mqttKeepAlive=60,
    topic_will=topic_will,
    msg_will=json.dumps(msg_will)
).create_connect()

try:
    device = XBeeDevice(PORT, BAUD_RATE)
    device.open()

except serial.SerialException as ex:
    print("Serial Error: ", str(ex))
    exit(-1)

# except Exception as ex:
#     print("Serial Error: ", str(ex))
#     exit(-1)

######################################################################
# The callback for when the client receives a CONNACK response from the server.
######################################################################
def on_connect(clientCB, userdata, flags, rc):
    if rc == 0:
        print("Connected with result code "+str(rc))
    else:
        print("Failed to connect with result code "+str(rc))
        sys.exit()
    client.subscribe(topic_LED,0)
    #client.publish(topic_will,json.dumps(msg_onl),0,True)
######################################################################
def on_subscribe(mqttc, obj, mid, granted_qos):
    print("Subscribed: " + str(mid) + " " + str(granted_qos))
    print("Subscribe acknowledged.")

def on_publish(clientCB, userdata, mid):
    print("Publish acknowledge.")

def on_log(clientCB, userdata, level, buf):
    print("log: ",buf)
def on_message(clientCB, userdata, msg):
    print("Message arrived from topic: " + msg.topic)
    print(str(msg.payload.decode("utf-8")))
    msg_decode=str(msg.payload.decode("utf-8","ignore"))
    msg_in=json.loads(msg_decode)
    xbee_network = device.get_network()
    # xbee_network.set_discovery_timeout(3.5)
    remote_device = xbee_network.discover_device(ROUTER2_NODE_ID)
    if remote_device is None:
        print("Could not find the remote device")
        # remote_device = xbee_network.discover_device(ROUTER2_NODE_ID) change 20/5/2023
        time.sleep(.3)
        remote_device = xbee_network.discover_device(ROUTER1_NODE_ID)
        if remote_device is None:
            print("Router2 not found")
            client.publish(topic_will,json.dumps(msg_will),0,True)
            return
    if(msg_in["led"] == 1):
        bytes_to_send = struct.pack("BB", 0x02, 0x01)
        print("Sending data to %s >> %s..." % (remote_device.get_64bit_addr(), bytes_to_send))
        device.send_data(remote_device, bytes_to_send)
    else:
        bytes_to_send = struct.pack("BB", 0x02, 0x00)
        print("Sending data to %s >> %s..." % (remote_device.get_64bit_addr(), bytes_to_send))
        device.send_data(remote_device, bytes_to_send)

client.on_connect = on_connect
client.on_subscribe = on_subscribe
client.on_message = on_message
client.on_log = on_log
client.on_publish = on_publish
client.loop_start()


def main2():
    print(" +-----------------------------------------+")
    print(" | XBee Python Library Receive Data Sample |")
    print(" +-----------------------------------------+\n")

    try:
        def data_receive_callback(xbee_message):
            try:
                print("From %s >> %s" % (xbee_message.remote_device.get_64bit_addr(),
                                        xbee_message.data))
                # Convert the bytearray to a hex string
                hex_string = binascii.hexlify(xbee_message.data).decode('utf-8')
                # Convert the hex string to bytes
                if(hex_string[0] == '0'  and hex_string[1] == '1'):
                    temp_string = bytes.fromhex(hex_string[2:10])
                    hum_string = bytes.fromhex(hex_string[10:])
                    # Unpack the bytes as a float
                    temp_value = struct.unpack("f", temp_string)[0]
                    hum_value = struct.unpack("f", hum_string)[0]
                    # Print the float value
                    print(temp_value)
                    print(hum_value)
                    value = {
                        "temp":temp_value,
                        "hum":hum_value,
                    }
                    client.publish(topic_DHT,json.dumps(value),0,False)
                else:
                    print("Type 3")
                    client.publish(topic_will,json.dumps(msg_will),0,True)
                    return
            except serial.SerialException as ex:
                print("Serial Error: ", str(ex))
                exit(-1)

        if device and device.is_open():
            device.add_data_received_callback(data_receive_callback)
        else:
            raise Exception("Not found device")
        
        print("Waiting for data...\n") 

        while True:
            device.read_data()
                

            # print(device)
            
            # response = device.read_data()

    except serial.SerialException as ex:
        print("Serial Error: ", str(ex))
        exit(-1)

    except Exception as ex:
        print("Error : ",str(ex))    
        exit(-1)
    finally:
        if device is not None and device.is_open():
            device.close()
            exit(-1)

t1 = threading.Thread(target=main2)
t1.start()
t1.join()
client.loop_stop()
del t1


# if __name__ == '__main__':
#     main()

