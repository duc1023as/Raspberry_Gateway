import requests
import sys
import paho.mqtt.client as mqtt
from src.core.mqqt_provider import MQTT
from dotenv import load_dotenv
import os
import json

from datetime import datetime, timezone

requests.packages.urllib3.disable_warnings()
load_dotenv()

url_local = os.getenv("URL_MQTT")
user_local = os.getenv("USER")
passworld_local = os.getenv("PASSWORD")
port_local = os.getenv("PORT")
topic_will = os.getenv("TOPIC_WILL_LOG")
url_CSharp=os.getenv("URL_CSharp")
msg_will = {
    "status":"OFF"
}
msg_onl = {
    "status":"ON"
}

topic_STATUS = "ESP32/STATUS"
topic_STATUS_Zb = "Zigbee/ON"


# Set up for MQTT local
topic_ZbDHT = "Zigbee/DHT"
topic_Esp_DHT = "ESP32/DHT"


client = MQTT(
    url=url_local,
    user=user_local,
    password=passworld_local,
    port=port_local,
    id='local_LogData',
    mqttKeepAlive=60,
    topic_will=topic_will,
    msg_will=json.dumps(msg_will)
).create_connect()


######################################################################
# The callback for when the client receives a CONNACK response from the server.
######################################################################
def on_connect(clientCB, userdata, flags, rc):
    if rc == 0:
        print("Connected with result code "+str(rc))
    else:
        print("Failed to connect with result code "+str(rc))
        sys.exit()
    client.subscribe(topic_Esp_DHT,0)
    client.subscribe(topic_ZbDHT,0)
    client.subscribe(topic_STATUS,0)
    client.subscribe(topic_STATUS_Zb,0)
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
    print("Message arrived from topic: " + msg.topic)
    print(str(msg.payload.decode("utf-8")))
    msg_decode=str(msg.payload.decode("utf-8","ignore"))
    msg_in=json.loads(msg_decode)
    dt = datetime.now(timezone.utc)
    formatted_dt = dt.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
    headers={
        'Content-type':'application/json', 
        'Accept':'application/json'
    }
    if msg_in["temp"] > 38:
        json_error = {
            "timestamp": formatted_dt,
            "key":"High temperature",
            "value":str(msg_in["temp"]),
            "deviceID": 1
        }
        response = requests.post(url_CSharp+'/Alarms/alarms', data=json.dumps(json_error,default=str),headers=headers,verify=False)
        if response.status_code == 200:
            print('Success')
            print(json_error)
        else:
            print('Error')
    if msg_in["hum"] > 68:
        json_humEr = {
            "timestamp": formatted_dt,
            "key":"High humidity",
            "value":str(msg_in["hum"]),
            "deviceID": 1
        }
        response = requests.post(url_CSharp+'/Alarms/alarms', data=json.dumps(json_humEr,default=str),headers=headers,verify=False)
        if response.status_code == 200:
            print('Success')
            print(json_humEr)
        else:
            print('Error')
    json_body={
    "timestamp": formatted_dt,
    "temperature": msg_in["temp"],
    "humidity": msg_in["hum"],
    "deviceID": 1
    }   
    response = requests.post(url_CSharp+'/TempHum/insertData', data=json.dumps(json_body,default=str),headers=headers,verify=False)
    if response.status_code == 200:
        print('Success')
        print(json_body)
    else:
        print('Error')

def on_messageZb(clientCB, userdata, msg):
    print("Message arrived from topic: " + msg.topic)
    print(str(msg.payload.decode("utf-8")))
    msg_decode=str(msg.payload.decode("utf-8","ignore"))
    msg_in=json.loads(msg_decode)
    dt = datetime.now(timezone.utc)
    formatted_dt = dt.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
    headers={
        'Content-type':'application/json', 
        'Accept':'application/json'
    }
    if msg_in["temp"] > 38:
        json_error = {
            "timestamp": formatted_dt,
            "key":"High temperature",
            "value":str(msg_in["temp"]),
            "deviceID": 2
        }
        response = requests.post(url_CSharp+'/Alarms/alarms', data=json.dumps(json_error,default=str),headers=headers,verify=False)
        if response.status_code == 200:
            print('Success')
            print(json_error)
        else:
            print('Error')
    if msg_in["hum"] > 68:
        json_humEr = {
            "timestamp": formatted_dt,
            "key":"High humidity",
            "value":str(msg_in["hum"]),
            "deviceID": 2
        }
        response = requests.post(url_CSharp+'/Alarms/alarms', data=json.dumps(json_humEr,default=str),headers=headers,verify=False)
        if response.status_code == 200:
            print('Success')
            print(json_humEr)
        else:
            print('Error')
    json_body={
    "timestamp": formatted_dt,
    "temperature": msg_in["temp"],
    "humidity": msg_in["hum"],
    "deviceID": 2
    }
    response = requests.post(url_CSharp+'/TempHum/insertData', data=json.dumps(json_body,default=str),headers=headers,verify=False)
    if response.status_code == 200:
        print('Success')
        print(json_body)
    else:
        print('Error')
def on_message_ONL(clientCB, userdata, msg):
    print("Message arrived from topic: " + msg.topic)
    print(str(msg.payload.decode("utf-8")))
    msg_decode=str(msg.payload.decode("utf-8","ignore"))
    msg_in=json.loads(msg_decode)
    headers={
        'Content-type':'application/json', 
        'Accept':'application/json'
    }
    dt = datetime.now(timezone.utc)
    formatted_dt = dt.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
    if(msg_in["status"] == "ON"):
        print("Status is ON")
    else:
        print("Status is OFF")
        json_error = {
            "timestamp": formatted_dt,
            "key":"Connection errors",
            "value":"Disconnected",
            "deviceID": 1
        }
        response = requests.post(url_CSharp+'/Alarms/alarms', data=json.dumps(json_error,default=str),headers=headers,verify=False)
        if response.status_code == 200:
            print('Success')
            print(json_error)
        else:
            print('Error')

def on_message_ONLZb(clientCB, userdata, msg):
    print("Message arrived from topic: " + msg.topic)
    print(str(msg.payload.decode("utf-8")))
    msg_decode=str(msg.payload.decode("utf-8","ignore"))
    msg_in=json.loads(msg_decode)
    headers={
        'Content-type':'application/json', 
        'Accept':'application/json'
    }
    dt = datetime.now(timezone.utc)
    formatted_dt = dt.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
    if(msg_in["status"] == "ON"):
        print("Status is ON")
    else:
        print("Status is OFF")
        json_error = {
            "timestamp": formatted_dt,
            "key":"Connection errors",
            "value":"Disconnected",
            "deviceID": 2
        }
        response = requests.post(url_CSharp+'/Alarms/alarms', data=json.dumps(json_error,default=str),headers=headers,verify=False)
        if response.status_code == 200:
            print('Success')
            print(json_error)
        else:
            print('Error')

client.on_connect = on_connect
client.on_subscribe = on_subscribe
client.on_message = on_message
client.message_callback_add(topic_ZbDHT,on_messageZb)
client.message_callback_add(topic_STATUS,on_message_ONL)
client.message_callback_add(topic_STATUS_Zb,on_message_ONLZb)
client.on_log = on_log
client.on_publish = on_publish
client.loop_start()

while True:
    pass
