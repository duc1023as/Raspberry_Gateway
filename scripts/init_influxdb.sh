#!/bin/bash

if [[ -z $(influx -execute "SHOW MEASUREMENTS ON $DATABASE_NAME" | grep $TABLE_NAME) ]]; then
echo "Table '$TABLE_NAME' not found. Creating new table...";
influx -host $INFLUX_HOST -port $INFLUX_PORT -username $INFLUXDB_USER -password $INFLUXDB_USER_PASSWORD  -execute "CREATE DATABASE IF NOT EXISTS $DATABASE_NAME";
influx -host $INFLUX_HOST -port $INFLUX_PORT -username $INFLUXDB_USER -password $INFLUXDB_USER_PASSWORD -execute "CREATE RETENTION POLICY one_day ON $DATABASE_NAME DURATION 1d REPLICATION 1 DEFAULT";
#   influx -execute "CREATE CONTINUOUS QUERY cq_temperature ON $DATABASE_NAME BEGIN SELECT MEAN(temperature) AS temperature_mean, MEAN(humidity) AS humidity_mean INTO one_day.temperature_humidity FROM $DATABASE_NAME.autogen.temperature GROUP BY time(1h) END"
influx -host $INFLUX_HOST -port $INFLUX_PORT -username $INFLUXDB_USER -password $INFLUXDB_USER_PASSWORD -execute "CREATE TABLE $TABLE_NAME (temperature FLOAT, humidity FLOAT)";
echo "Table '$TABLE_NAME' created successfully.";
else
echo "Table '$TABLE_NAME' already exists.";
fi
