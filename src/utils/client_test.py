from datetime import datetime

from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS

# You can generate a Token from the "Tokens Tab" in the UI
token = "DtBwUZy5EgIBiK-9LASY9XAxKpVflq7_jT7eb_r-oSabet9czvHUbPGZQeRuIwbb7-k1wCK9qesaC-coZnzyTA=="
org = "HCMUT"
bucket = "Test"

client = InfluxDBClient(url="http://localhost:8086", token=token,org=org)

write_api = client.write_api(write_options=SYNCHRONOUS)

p = Point("my_measurement2").tag("location", "Prague").tag("device", "esp32").field("temperature", 11.68)
p1 = Point("my_measurement2").tag("location", "Prague").tag("device", "esp32").field("hum", 55)
write_api.write(bucket=bucket, org=org, record=[p,p1])

print("Test")