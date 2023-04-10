#!/bin/bash

if [[ -z $(influx -host $INFLUX_HOST -port $INFLUX_PORT -username $INFLUXDB_USER -password $INFLUXDB_USER_PASSWORD -execute "SHOW MEASUREMENTS ON $DATABASE_NAME" | grep $TABLE_NAME) ]]; then echo "Table '$TABLE_NAME' not found. Creating new table..."
  influx -host $INFLUX_HOST -port $INFLUX_PORT -username $INFLUXDB_USER -password $INFLUXDB_USER_PASSWORD  -execute "CREATE DATABASE $DATABASE_NAME" 
  influx -host $INFLUX_HOST -port $INFLUX_PORT -username $INFLUXDB_USER -password $INFLUXDB_USER_PASSWORD -execute "CREATE RETENTION POLICY one_day ON $DATABASE_NAME DURATION 1d REPLICATION 1 DEFAULT"
  influx -host $INFLUX_HOST -port $INFLUX_PORT -username $INFLUXDB_USER -password $INFLUXDB_USER_PASSWORD -execute "CREATE TABLE $TABLE_NAME (temperature FLOAT, humidity FLOAT)"
  echo "Table '$TABLE_NAME' created successfully."
else
echo "Table '$TABLE_NAME' already exists."
fi
