import paho.mqtt.client as mqtt

class MQTT():
    def __init__(self, url=None, user=None, password=None, port=1883, id=None, mqttKeepAlive=60) -> None:
        self.id = id
        self.mqttKeepAlive = mqttKeepAlive
        self.url = url
        self.user = user
        self.password = password
        self.port = port
        self.client = mqtt.Client(client_id=self.id)
    

    def create_connect(self):
        self.client.username_pw_set(self.user,self.password)
        self.client.connect(self.url, int(self.port), self.mqttKeepAlive)
        return self.client

