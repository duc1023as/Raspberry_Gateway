import paho.mqtt.client as mqtt
from ..core import sparkplug_b as sparkplug

class MQTT():
    def __init__(self, url=None, user=None, password=None, port=1883, id=None, mqttKeepAlive=60,topic_will = None,msg_will = None) -> None:
        self.id = id
        self.mqttKeepAlive = mqttKeepAlive
        self.url = url
        self.user = user
        self.password = password
        self.port = port
        self.topic_will = topic_will
        self.msg_will = msg_will
        self.client = mqtt.Client(client_id=self.id)
    

    def create_connect(self):
        self.client.username_pw_set(self.user,self.password)
        self.client.will_set(self.topic_will,self.msg_will,0,True)
        self.client.connect(self.url, int(self.port), self.mqttKeepAlive)
        return self.client

    def create_connectAWS(self):
        self.client.username_pw_set(self.user,self.password)    
        deathPayload = sparkplug.getNodeDeathPayload()
        deathByteArray = bytearray(deathPayload.SerializeToString())
        self.client.will_set('spBv1.0/Area1/NDEATH/Gateway1', deathByteArray, 1, False)
        self.client.connect(self.url, int(self.port), self.mqttKeepAlive)
        return self.client

