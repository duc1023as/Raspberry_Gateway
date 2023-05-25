import sys

import paho.mqtt.client as mqtt
from ..core import sparkplug_b as sparkplug
from dotenv import load_dotenv

import random
import string
import json
import os
import time


from influxdb import InfluxDBClient

from ..core.sparkplug_b import *
from ..core.mqqt_provider import MQTT

load_dotenv()

url_local = os.getenv("URL_MQTT")
user_local = os.getenv("USER")
passworld_local = os.getenv("PASSWORD")
port_local = os.getenv("PORT")
topic_will = os.getenv("TOPIC_WILL")
msg_will = {
    "status":"OFF",
}

url_AWS = os.getenv("URL_AWS")
user_AWS = os.getenv("USER_AWS")
password_AWS = os.getenv("PWD_AWS")
port_AWS = os.getenv("PORT_AWS")

client = MQTT(
    url=url_local,
    user=user_local,
    password=passworld_local,
    port=port_local,
    id='local',
    mqttKeepAlive=60,
    topic_will=topic_will,
    msg_will=json.dumps(msg_will)
    ).create_connect()

hostDB = os.getenv("INFLUXDB_HOST")
portDB = os.getenv("INFLUXDB_PORT")
userDB= os.getenv("INFLUXDB_USER")
passwordDB= os.getenv("INFLUXDB_PASSWORD")
mydb = os.getenv("INFLUXDB_DB")
area1db = os.getenv("DATABASE_NAME")
tableA1 = os.getenv("TABLE_NAME")
tableA2 = os.getenv("TABLE_NAME_Zb")

print(hostDB)
print(portDB)


clientDB = InfluxDBClient(host=hostDB, port=portDB, username=userDB, password=passwordDB, database=area1db) #test local 27-04-2022


# Set up for MQTT local
topic_DHT = "ESP32/DHT"
topic_LED = "ESP32/LED"
topic_STATUS = "ESP32/STATUS"

# Set up for MQTT local
topic_DHT_Zb = "Zigbee/DHT"
topic_LED_Zb = "Zigbee/LED"
topic_STATUS_Zb = "Zigbee/ON"

# Set up for MQTT AWS and enable Sparkplug
# mqttBrokerAWS ="broker.hivemq.com"
mqttBrokerAWS ="13.115.13.210"
namespace = "spBv1.0"
groupID = "Area1"
groupID2 = "Area2"
edgeNodeId = "Gateway1"
deviceID = "ESP32"
deviceID2 = "Zigbee"

# client_AWS = MQTT(url=url_AWS, id="AWS").create_connectAWS() #change 15/04/2023
client_AWS = MQTT(url=url_AWS,user=user_AWS,password=password_AWS,port=port_AWS, id="AWS").create_connectAWS() #change 15/04/2023

# Alias
class AliasMap:
    Next_Server = 0
    Rebirth = 1
    Reboot = 2
    Hardware_Make = 3
    Hardware_OS = 4
    Supply_Voltage = 5
    Esp32_tem = 6
    Esp32_hum = 7
    Esp32_led = 8
    Zigbee_tem = 9
    Zigbee_hum = 10
    Zigbee_led = 11
    


######################################################################
# The callback for when the client receives a CONNACK response from the server.
######################################################################
def on_connect(clientCB, userdata, flags, rc):
    if rc == 0:
        print("Connected with result code "+str(rc))
    else:
        print("Failed to connect with result code "+str(rc))
        sys.exit()
    client.subscribe(topic_STATUS,0)
    client.subscribe(topic_STATUS_Zb,0)
    client.subscribe(topic_DHT,0)
    client.subscribe(topic_DHT_Zb,0)
######################################################################

def on_connectAWS(clientCB, userdata, flags, rc):
    if rc == 0:
        print("Connected with result code "+str(rc))
    else:
        print("Failed to connect with result code "+str(rc))
        sys.exit()

    client_AWS.subscribe(topic_LED,0)

    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client_AWS.subscribe("spBv1.0/" + groupID + "/NCMD/" + edgeNodeId )
    client_AWS.subscribe("spBv1.0/"+ groupID + "/DCMD/" + edgeNodeId + "/" + deviceID)
    client_AWS.subscribe("spBv1.0/" + groupID2 + "/NCMD/" + edgeNodeId )
    client_AWS.subscribe("spBv1.0/"+ groupID2 + "/DCMD/" + edgeNodeId + "/" + deviceID2)
    client_AWS.subscribe("STATE/IoT2023")

def on_message(clientCB, userdata, msg):
    print("Message arrived from topic: " + msg.topic)
    print(str(msg.payload.decode("utf-8")))
    msg_decode=str(msg.payload.decode("utf-8","ignore"))
    msg_in=json.loads(msg_decode)
    publishDeviceData(msg_in)
    json_body = [
    {
        "measurement": tableA1,
        "tags": {
            "location":"Area1",
            "device": "ESP32"
        },
        "fields": {
            "temperature": float(msg_in["temp"]),
            "humidity": float(msg_in["hum"])
        }
    },
]
    clientDB.write_points(json_body)  #test local 27-04-2022
    # client_AWS.publish(topic_DHT,msg.payload)


def on_message_Zigbee(clientCB, userdata, msg):
    print("Message arrived from topic: " + msg.topic)
    print(str(msg.payload.decode("utf-8")))
    msg_decode=str(msg.payload.decode("utf-8","ignore"))
    msg_in=json.loads(msg_decode)
    publishDeviceDataZb(msg_in)
    json_body = [
    {
        "measurement": tableA2,
        "tags": {
            "location":"Area2",
            "device": "Zigbee"
        },
        "fields": {
            "temperature": float(msg_in["temp"]),
            "humidity": float(msg_in["hum"])
        }
    },
    ]
    clientDB.write_points(json_body)  #test local 27-04-2022
    # client_AWS.publish(topic_DHT,msg.payload)


def on_messageAWS(clientCB, userdata, msg):
    print("Message arrived from topic: " + msg.topic)
    tokens = msg.topic.split("/")
    if msg.topic == 'spBv1.0/Area1/DCMD/Gateway1/ESP32':
        inboundPayload = sparkplug_b_pb2.Payload()
        inboundPayload.ParseFromString(msg.payload)
        for metric in inboundPayload.metrics:
            if metric.name == "output/Led" or metric.alias == AliasMap.Esp32_led:
                newValue = metric.boolean_value
                if(newValue):
                    newValue = 1
                else:
                    newValue = 0
                print( "CMD message for output/Led - New Value: {}".format(newValue))
                newValue_Local = {
                    "led" : newValue
                }
                payload_Local = str(newValue_Local)
                client.publish(topic_LED,payload_Local,1,False) 
                # Create the DDATA payload - Use the alias because this isn't the DBIRTH
                payload = sparkplug.getDdataPayload()
                addMetric(payload, "output/Led", AliasMap.Esp32_led, MetricDataType.Boolean, newValue)

                # Publish a message data
                byteArray = bytearray(payload.SerializeToString())
                client_AWS.publish("spBv1.0/" + groupID + "/DDATA/" + edgeNodeId + "/" + deviceID, byteArray, 0, True) # change 7/4
            # else:
            #     print( "Unknown command: " + metric.name)

    elif msg.topic == 'spBv1.0/Area2/DCMD/Gateway1/Zigbee':
        inboundPayload = sparkplug_b_pb2.Payload()
        inboundPayload.ParseFromString(msg.payload)
        for metric in inboundPayload.metrics:
            if metric.name == "output/Led" or metric.alias == AliasMap.Zigbee_led:
                newValue = metric.boolean_value
                if(newValue):
                    newValue = 1
                else:
                    newValue = 0
                print( "CMD message for output/Led - New Value: {}".format(newValue))
                newValue_Local = {
                    "led" : newValue
                }
                # payload_Local = str(newValue_Local)
                client.publish(topic_LED_Zb,json.dumps(newValue_Local),1,False)
                # Create the DDATA payload - Use the alias because this isn't the DBIRTH
                payload = sparkplug.getDdataPayload()
                addMetric(payload, "output/Led", AliasMap.Zigbee_led, MetricDataType.Boolean, newValue)

                # Publish a message data
                byteArray = bytearray(payload.SerializeToString())
                client_AWS.publish("spBv1.0/" + groupID2 + "/DDATA/" + edgeNodeId + "/" + deviceID2, byteArray, 0, True) # change 7/4
            # else:
            #     print( "Unknown command: " + metric.name)
    elif msg.topic == 'STATE/IoT2023':
        print("Hi")
        msg_decode=str(msg.payload.decode("utf-8","ignore"))
        msg_in=json.loads(msg_decode)
        if(msg_in['status'] == 'ON'):
            publishNodeBirth()
    else:
        print( "Unknown command...")

    print( "Done publishing")
##########################################################################################

def on_message_ONL(clientCB, userdata, msg):
    print("Message arrived from topic: " + msg.topic)
    print(str(msg.payload.decode("utf-8")))
    msg_decode=str(msg.payload.decode("utf-8","ignore"))
    msg_in=json.loads(msg_decode)
    if(msg_in["status"] == "ON"):
        print("Status is ON")
        publishDeviceBirth()
    else:
        print("Status is OFF")
        publishDeviceDeath()

def on_message_ONLZb(clientCB, userdata, msg):
    print("Message arrived from topic: " + msg.topic)
    print(str(msg.payload.decode("utf-8")))
    msg_decode=str(msg.payload.decode("utf-8","ignore"))
    msg_in=json.loads(msg_decode)
    if(msg_in["status"] == "ON"):
        print("Status is ON")
        publishDeviceBirthZb()
    else:
        print("Status is OFF")
        publishDeviceDeathZb()

def on_subscribe(mqttc, obj, mid, granted_qos):
    print("Subscribed: " + str(mid) + " " + str(granted_qos))
    print("Subscribe acknowledged.")

def on_publish(clientCB, userdata, mid):
    print("Publish acknowledge.")

def on_log(clientCB, userdata, level, buf):
    print("log: ",buf)

######################################################################
# Publish the NBIRTH certificate
######################################################################
def publishNodeBirth():
    print( "Publishing Node Birth")

    # Create the node birth payload
    payload = sparkplug.getNodeBirthPayload()

    # Set up the Node Controls
    addMetric(payload, "Node Control/Next Server", AliasMap.Next_Server, MetricDataType.Boolean, False)
    addMetric(payload, "Node Control/Rebirth", AliasMap.Rebirth, MetricDataType.Boolean, False)
    addMetric(payload, "Node Control/Reboot", AliasMap.Reboot, MetricDataType.Boolean, False)

    # Add some regular node metrics
    addMetric(payload, "Properties/Hardware Make", AliasMap.Hardware_Make, MetricDataType.String, "Raspberry Pi")
    addMetric(payload, "Properties/OS", AliasMap.Hardware_OS, MetricDataType.String, "Raspberian")
    addMetric(payload, "Supply Voltage", AliasMap.Supply_Voltage, MetricDataType.Float,12.1)

    # Publish the node birth certificate
    byteArray = bytearray(payload.SerializeToString())
    client_AWS.publish("spBv1.0/" + groupID + "/NBIRTH/" + edgeNodeId, byteArray, 1, False)
######################################################################


######################################################################
# Publish the DBIRTH certificate
######################################################################
def publishDeviceBirth():
    print( "Publishing Device Birth")

    # Get the payload
    payload = sparkplug.getDeviceBirthPayload()

    # Add some device metrics
    addNullMetric(payload, "input/Temperature", AliasMap.Esp32_tem, MetricDataType.Float)
    addNullMetric(payload, "input/Humidity", AliasMap.Esp32_hum, MetricDataType.Float)
    addNullMetric(payload, "output/Led", AliasMap.Esp32_led, MetricDataType.Boolean)


    # Publish the initial data with the Device BIRTH certificate
    totalByteArray = bytearray(payload.SerializeToString())
    client_AWS.publish("spBv1.0/" + groupID + "/DBIRTH/" + edgeNodeId + "/" + deviceID, totalByteArray, 1, False)
######################################################################

######################################################################
# Publish the DBIRTH certificate
######################################################################
def publishDeviceBirthZb():
    print( "Publishing Device Birth")

    # Get the payload
    payload = sparkplug.getDeviceBirthPayload()

    # Add some device metrics
    addNullMetric(payload, "input/Temperature", AliasMap.Zigbee_tem, MetricDataType.Float)
    addNullMetric(payload, "input/Humidity", AliasMap.Zigbee_hum, MetricDataType.Float)
    addNullMetric(payload, "output/Led", AliasMap.Zigbee_led, MetricDataType.Boolean)


    # Publish the initial data with the Device BIRTH certificate
    totalByteArray = bytearray(payload.SerializeToString())
    client_AWS.publish("spBv1.0/" + groupID2 + "/DBIRTH/" + edgeNodeId + "/" + deviceID2, totalByteArray, 1, False)
######################################################################


######################################################################
# Publish the DDEATH certificate
######################################################################
def publishDeviceDeath():
    print( "Publishing Device Death")

    # Get the payload
    payload = sparkplug.getDdataPayload()

    # Publish the initial data with the Device DEATH certificate
    totalByteArray = bytearray(payload.SerializeToString())
    client_AWS.publish("spBv1.0/" + groupID + "/DDEATH/" + edgeNodeId + "/" + deviceID, totalByteArray, 1, False)
######################################################################

######################################################################
# Publish the DDEATH certificate
######################################################################
def publishDeviceDeathZb():
    print( "Publishing Device Death")

    # Get the payload
    payload = sparkplug.getDdataPayload()

    # Publish the initial data with the Device DEATH certificate
    totalByteArray = bytearray(payload.SerializeToString())
    client_AWS.publish("spBv1.0/" + groupID2 + "/DDEATH/" + edgeNodeId + "/" + deviceID2, totalByteArray, 1, False)
######################################################################


######################################################################
# Publish the DDATA certificate
######################################################################
def publishDeviceData(data):
    print( "Publishing Data Device")

    # Get the payload
    payload = sparkplug.getDdataPayload()

    addMetric(payload, "input/temperature", AliasMap.Esp32_tem, MetricDataType.Float,data["temp"]+random.uniform(0, 3))
    addMetric(payload, "input/humidity", AliasMap.Esp32_hum, MetricDataType.Float,data["hum"]+random.uniform(0, 3))

    # Publish the initial data with the Device DEATH certificate
    totalByteArray = bytearray(payload.SerializeToString())
    client_AWS.publish("spBv1.0/" + groupID + "/DDATA/" + edgeNodeId + "/" + deviceID, totalByteArray, 0, False)
######################################################################


######################################################################
# Publish the DDATA certificate
######################################################################
def publishDeviceDataZb(data):
    print( "Publishing Data Device")

    # Get the payload
    payload = sparkplug.getDdataPayload()

    addMetric(payload, "input/temperature", AliasMap.Zigbee_tem, MetricDataType.Float,data["temp"]+random.uniform(0, 3))
    addMetric(payload, "input/humidity", AliasMap.Zigbee_hum, MetricDataType.Float,data["hum"]+random.uniform(0, 3))

    # Publish the initial data with the Device DEATH certificate
    totalByteArray = bytearray(payload.SerializeToString())
    client_AWS.publish("spBv1.0/" + groupID2 + "/DDATA/" + edgeNodeId + "/" + deviceID2, totalByteArray, 0, False)
######################################################################


######################################################################
# Main Application
######################################################################

def handle_process():

    print("Starting main application")

    # For local broker
    # client = mqtt.Client("local")
    client.on_connect = on_connect
    client.on_subscribe = on_subscribe
    client.on_message = on_message
    client.on_log = on_log
    client.message_callback_add(topic_STATUS,on_message_ONL)
    client.message_callback_add(topic_DHT_Zb,on_message_Zigbee)
    client.message_callback_add(topic_STATUS_Zb,on_message_ONLZb)
    client.loop_start()
    # client.username_pw_set(myUsername,myPassword)
    # client.connect(serverUrl, mqttPORT, mqttKeepAlive)


    # For AWS broker
    # client_AWS = mqtt.Client("AWS")
    client_AWS.on_connect = on_connectAWS
    client_AWS.on_subscribe = on_subscribe
    client_AWS.on_message = on_messageAWS
    client_AWS.on_log = on_log

    # deathPayload = sparkplug.getNodeDeathPayload()
    # deathByteArray = bytearray(deathPayload.SerializeToString())
    # client_AWS.will_set("spBv1.0/" + groupID + "/NDEATH/" + edgeNodeId, deathByteArray, 1, False) # change 10/4

    # client_AWS.connect(mqttBrokerAWS, mqttPORT, mqttKeepAlive)
    time.sleep(.1)
    client_AWS.loop_start()

    #Publish Birth
    publishNodeBirth()

    time.sleep(2)
    # Periodically publish some new data
    payloadNDATA = sparkplug.getDdataPayload()
    addMetric(payloadNDATA, "Supply Voltage", AliasMap.Supply_Voltage, MetricDataType.Float,12.3)
    byteArrayNDATA = bytearray(payloadNDATA.SerializeToString())
    client_AWS.publish("spBv1.0/" + groupID + "/NDATA/" + edgeNodeId, byteArrayNDATA, 0, False)

def main():
    handle_process()
    while True:
        pass
    # while True:    28/4/2023
    #     # Sit and wait for inbound or outbound events
    #     for _ in range(5):
    #         time.sleep(.1)
    #         client.loop()
    #         client_AWS.loop()