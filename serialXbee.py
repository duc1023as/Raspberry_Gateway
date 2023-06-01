#pyserial-3.5
#digi-xbee-1.4.1
import sys
from digi.xbee.devices import XBeeDevice
import digi
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
from digi.xbee.models.status import NetworkDiscoveryStatus
import atexit
import datetime



# TODO: Replace with the serial port where your local module is connected to.
#PORT = "COM8"
PORT = "/dev/ttyUSB0"
# TODO: Replace with the baud rate of your local module. data.decode("ISO-8859-1")
BAUD_RATE = 9600

ROUTER1_NODE_ID = "Router"
# ROUTER2_NODE_ID = "ROUTER3"
ROUTER2_NODE_ID = "ROUTER3"
Coordinator_ID = "Coordinator"
check = True
time_request = None
SECONDS = datetime.timedelta(seconds=20)
remote_device = None
check_conflict = False

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
    #time.sleep(10)
    device = XBeeDevice(PORT, BAUD_RATE)
    device.open()
    # xbee_network_init = device.get_network()
    # xbee_network_init.start_discovery_process(deep=True)
    # print("Discovering remote XBee devices...")

    # while xbee_network_init.is_discovery_running():
    #     time.sleep(0.1)

    # devices = xbee_network_init.get_devices()
    # if len(devices) == 0:
    #     print("Not found device")
    #     exit(-1) 

except serial.SerialException as ex:
    print("Serial Error: ", str(ex))
    exit(-1)

def cleanup():
    print("Error and begin cleaning serial")
    if device.is_open():
        device.close()
    
    
atexit.register(cleanup)
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
    # xbee_network_init.clear()
    # if len(xbee_network_init.get_devices()) == 0 :
    #     print("Not found Device")
    #     exit(-1)
    client.publish(topic_will,json.dumps(msg_onl),0,True)
######################################################################
def on_subscribe(mqttc, obj, mid, granted_qos):
    print("Subscribed: " + str(mid) + " " + str(granted_qos))
    print("Subscribe acknowledged.")

def on_publish(clientCB, userdata, mid):
    print("Publish acknowledge.")

def on_log(clientCB, userdata, level, buf):
    print("log: ",buf)
def on_message(clientCB, userdata, msg):
    globals()["check_conflict"] = True
    print("Conflicting ....")
    print("Message arrived from topic: " + msg.topic)
    print(str(msg.payload.decode("utf-8")))
    msg_decode=str(msg.payload.decode("utf-8","ignore"))
    msg_in=json.loads(msg_decode)

    print("Start request at: ",  datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    # if globals()['time_request'] is None:
    #     globals()['time_request'] = datetime.datetime.now() - datetime.timedelta(minutes=5)

    # xbee_network = device.get_network()
    # xbee_network.clear()
    # # if xbee_network.is_discovery_running():
    # #     xbee_network.stop_discovery_process()
    # #xbee_network.set_discovery_timeout(3.5)
    # globals()['remote_device'] = xbee_network.discover_device(ROUTER2_NODE_ID)
    # print(globals()['remote_device'] is None)

    # if globals()['remote_device'] is None:
    #     if datetime.datetime.now() - globals()['time_request'] > SECONDS or globals()['remote_device'] is None:
    #         print("Could not find the remote device")
    #         # remote_device = xbee_network.discover_device(ROUTER2_NODE_ID) change 20/5/2023
    #         globals()['remote_device'] = xbee_network.discover_device(ROUTER1_NODE_ID)
    #         if globals()['remote_device'] is None:
    #             print("Router2 not found")
    #             client.publish(topic_will,json.dumps(msg_will),0,True)
    #             globals()['check']  = False
    #             return
    try:
        if globals()['remote_device']:
            if(msg_in["led"] == 1):
                bytes_to_send = struct.pack("BB", 0x02, 0x01)
                print("Sending data to %s >> %s..." % (globals()['remote_device'].get_64bit_addr(), bytes_to_send))
                device.send_data(globals()['remote_device'], bytes_to_send)
                #client.publish(topic_will,json.dumps(msg_onl),0,True)
            elif(msg_in["led"] == 0):
                bytes_to_send = struct.pack("BB", 0x02, 0x00)
                print("Sending data to %s >> %s..." % (globals()['remote_device'].get_64bit_addr(), bytes_to_send))
                device.send_data(globals()['remote_device'], bytes_to_send)
                #client.publish(topic_will,json.dumps(msg_onl),0,True)
        globals()['check_conflict'] = False  
        print("Not Conflict ....")
        globals()['time_request'] = datetime.datetime.now()
        print("End request at: ",  globals()['time_request'].strftime("%Y-%m-%d %H:%M:%S")) 

    except Exception as ex:
        print("Erorr: ",str(ex))
        client.publish(topic_will,json.dumps(msg_will),0,True)
        globals()['check']  = False
        # exit(-1)

client.on_connect = on_connect
client.on_subscribe = on_subscribe
client.on_message = on_message
client.on_log = on_log
client.on_publish = on_publish
client.loop_start()

def callback_device_discovered(remote):
    print("Device discovered: %s" % remote)

def get_devices():
    try:
        #xbee_network.set_discovery_timeout(3.5)  # 15 seconds.
        if not globals()['check']:
            return
        if not globals()["check_conflict"]:
            xbee_network = device.get_network()
            xbee_network.clear()
            devices = xbee_network.discover_devices([ROUTER2_NODE_ID, ROUTER1_NODE_ID])
            print("List devices: ", devices)
            nodes_device = [d.get_node_id() for d in devices]
            print("Found devices: ", nodes_device)
            if ROUTER2_NODE_ID in nodes_device:
                globals()['remote_device'] = devices[nodes_device.index(ROUTER2_NODE_ID)]   
            elif ROUTER1_NODE_ID in nodes_device:
                print("Check Router2 not found")
                globals()['remote_device'] = devices[nodes_device.index(ROUTER1_NODE_ID)]
                
            else:
                print("Check Router1 not found")
                client.publish(topic_will,json.dumps(msg_will),0,True)
                # time.sleep(1)
                return

            # globals()['remote_device'] = xbee_network.discover_device(ROUTER2_NODE_ID)
            # if globals()['remote_device'] is None:
            #     print("Could not check the remote device")
            #     # remote_device = xbee_network.discover_device(ROUTER2_NODE_ID) change 20/5/2023
            #     time.sleep(5)
            #     if not globals()["check_conflict"]:
            #         globals()['remote_device'] = xbee_network.discover_device(ROUTER1_NODE_ID)
            #         if globals()['remote_device'] is None:
            #             print("Check Router2 not found")
            #             client.publish(topic_will,json.dumps(msg_will),0,True)
            #             return
        if not globals()['check']:
            return
        #client.publish(topic_will,json.dumps(msg_onl),0,True)
        # time.sleep(1)



        # Callback for discovered devices.
        # def callback_device_discovered(remote):
        #     print("Device discovered: %s" % remote)

        # # Callback for discovery finished.
        # def callback_discovery_finished(status):
        #     if status == NetworkDiscoveryStatus.SUCCESS:
        #         print("Discovery process finished successfully.")
        #         xbee_network.clear()
        #         devices_check = xbee_network.discover_devices([ROUTER1_NODE_ID, ROUTER2_NODE_ID])
        #         print(devices_check)
        #         if len(devices_check) == 0:
        #             print("Not Found Router")
        #             client.publish(topic_will,json.dumps(msg_will),0,True)
        #         else:
        #             client.publish(topic_will,json.dumps(msg_onl),0,True)
        #     else:
        #         print("There was an error discovering devices: %s" % status.description)
        #         client.publish(topic_will,json.dumps(msg_will),0,True)
                 

        # xbee_network.add_device_discovered_callback(callback_device_discovered)

        # xbee_network.add_discovery_process_finished_callback(callback_discovery_finished)
        # xbee_network.start_discovery_process()

        # while xbee_network.is_discovery_running:
        #     time.sleep(0.1)   

            
    except RuntimeError:
        print("fail runtime")
        exit(-1)
    except digi.xbee.exception.TimeoutException:
        print("fail TimeoutException")
        exit(-1)
    except Exception as ex:
        print("error", str(ex))
        exit(-1)



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
                print("HEX STRING: ", hex_string)
                # Convert the hex string to bytes
                if not globals()['check']:
                    return
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
                    # globals()['check'] = True
                elif(hex_string[0] == '0'  and hex_string[1] == '3'):
                    print("Type 3")
                    client.publish(topic_will,json.dumps(msg_will),0,True)
                    globals()['check']  = False
            except serial.SerialException as ex:
                print("Serial Error: ", str(ex))
                exit(-1)

        if device and device.is_open():
            device.add_data_received_callback(data_receive_callback)
        else:
            raise Exception("Not found device")  
        print("Waiting for data...\n") 

        while True:
            
            # respone=device.read_data()
            # if respone is None:
            #     print("Can not read date")
                
            # print(respone)
            if not globals()['check']:
                break

            if not device.is_open():
                print("Not connect to device")
                client.publish(topic_will,json.dumps(msg_will),0,True)
                break  

            get_devices()
            
        
    except serial.SerialException as ex:
        print("Serial Error: ", str(ex))
        device.close()
        exit(-1)

    except Exception as ex:
        print("Error : ",str(ex))    
        device.close()
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

