import sys
# sys.path.insert(0, "../core/")
# print(sys.path)

import paho.mqtt.client as mqtt
from ..core import sparkplug_b as sparkplug
from dotenv import load_dotenv

import random
import string
import json
import os
import time

# from influxdb_client import InfluxDBClient, Point, WritePrecision
# from influxdb_client.client.write_api import SYNCHRONOUS

from influxdb import InfluxDBClient

from ..core.sparkplug_b import *
from ..core.mqqt_provider import MQTT

load_dotenv()

url_local = os.getenv("URL_MQTT")
user_local = os.getenv("USER")
passworld_local = os.getenv("PASSWORD")
port_local = os.getenv("PORT")

url_AWS = os.getenv("URL_AWS")
user_AWS = os.getenv("USER_AWS")
password_AWS = os.getenv("PWD_AWS")

client = MQTT(
    url=url_local,
    user=user_local,
    password=passworld_local,
    port=port_local,
    id='local',
    mqttKeepAlive=60
    ).create_connect()

# Set up for InfuxDB
# You can generate a Token from the "Tokens Tab" in the UI

# org = os.getenv("ORG")
# token= os.getenv("TOKEN")
# bucket= os.getenv("BUCKET")

# url = os.getenv("URL")

# clientDB = InfluxDBClient(url=url, token=token,org=org)
# # clientDB = InfluxDBClient(url=url, token=token)

# write_api = clientDB.write_api(write_options=SYNCHRONOUS)

hostDB = os.getenv("INFLUXDB_HOST")
portDB = os.getenv("INFLUXDB_PORT")
userDB= os.getenv("INFLUXDB_USER")
passwordDB= os.getenv("INFLUXDB_PASSWORD")
mydb = os.getenv("INFLUXDB_DB")
area1db = os.getenv("DATABASE_NAME")
tableA1 = os.getenv("TABLE_NAME")

print(hostDB)
print(portDB)


clientDB = InfluxDBClient(host=hostDB, port=portDB, username=userDB, password=passwordDB, database=area1db) #test local 15-04-2022


# Set up for MQTT local
topic_DHT = "ESP32/DHT"
topic_LED = "ESP32/LED"
topic_STATUS = "ESP32/STATUS"

# Set up for MQTT AWS and enable Sparkplug
# mqttBrokerAWS ="broker.hivemq.com"
mqttBrokerAWS ="13.115.13.210"
namespace = "spBv1.0"
groupID = "Area1"
edgeNodeId = "Gateway1"
deviceID = "ESP32"

# client_AWS = MQTT(url=url_AWS, id="AWS").create_connectAWS() #change 15/04/2023
client_AWS = MQTT(url=url_AWS,user=user_AWS,password=password_AWS, id="AWS").create_connectAWS() #change 15/04/2023

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
    client.subscribe(topic_DHT,0)
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

def on_message(clientCB, userdata, msg):
    print("Message arrived from topic: " + msg.topic)
    print(str(msg.payload.decode("utf-8")))
    msg_decode=str(msg.payload.decode("utf-8","ignore"))
    msg_in=json.loads(msg_decode)
    publishDeviceData(msg_in)

    # p = Point("DataArea1").tag("location", "Area 1").tag("device","ESP32").field("temperature", msg_in["temp"]).field("humidity",msg_in["hum"])
    # write_api.write(bucket=bucket, org=org, record=p)
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
    clientDB.write_points(json_body)  #test local 15-04-2022
    # client_AWS.publish(topic_DHT,msg.payload)

def on_messageAWS(clientCB, userdata, msg):
    print("Message arrived from topic: " + msg.topic)
    tokens = msg.topic.split("/")
    if tokens[0] == "spBv1.0" and tokens[1] == groupID and (tokens[2] == "NCMD" or tokens[2] == "DCMD") and tokens[3] == edgeNodeId:
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
                client.publish(topic_LED,payload_Local,0,False)
                # Create the DDATA payload - Use the alias because this isn't the DBIRTH
                payload = sparkplug.getDdataPayload()
                addMetric(payload, "output/Led", AliasMap.Esp32_led, MetricDataType.Boolean, newValue)

                # Publish a message data
                byteArray = bytearray(payload.SerializeToString())
                client_AWS.publish("spBv1.0/" + groupID + "/DDATA/" + edgeNodeId + "/" + deviceID, byteArray, 0, True) # change 7/4
            else:
                print( "Unknown command: " + metric.name)
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
# Publish the DDATA certificate
######################################################################
def publishDeviceData(data):
    print( "Publishing Data Device")

    # Get the payload
    payload = sparkplug.getDdataPayload()

    addMetric(payload, "input/temperature", AliasMap.Esp32_tem, MetricDataType.Float,data["temp"])
    addMetric(payload, "input/humidity", AliasMap.Esp32_hum, MetricDataType.Float,data["hum"])

    # Publish the initial data with the Device DEATH certificate
    totalByteArray = bytearray(payload.SerializeToString())
    client_AWS.publish("spBv1.0/" + groupID + "/DDATA/" + edgeNodeId + "/" + deviceID, totalByteArray, 0, False)
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
    client.loop()
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
    client_AWS.loop()

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
        # Sit and wait for inbound or outbound events
        for _ in range(5):
            time.sleep(.1)
            client.loop()
            client_AWS.loop()