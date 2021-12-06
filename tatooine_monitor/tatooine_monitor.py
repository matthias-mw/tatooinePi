#!/usr/bin/env python3

import logging
import smbus
import time

#Schnittstelle zur InfluxDB
from influxdb import InfluxDBClient

from aquireData.aquire_data import AquireData

# Get I2C bus
bus = smbus.SMBus(1)

if __name__ == '__main__':

                
    # Konfiguration der InfluxDatenbank
    host = "192.168.1.45"   # IP der Datenbank
    port = 8086             # default port
    user = "admin"          # the user/password created for influxdb
    password = "tatooinedb" 
    dbname = "sensors"      # name der Datenbank
        
        
    # Create the InfluxDB client object
    client = InfluxDBClient(host, port, user, password, dbname)     

    print(client.ping())

    Data = AquireData(bus)

    cnt = 0
    while cnt < 10:
        cnt =1
        Data.aquire_data()
        
        
        for chn in Data.data_last_measured:
        
            tmp = chn.create_json_lastvalue('Signal3','tatooine')
        
            # Schreibe die Daten in die Datenbank
            client.write_points(tmp)
        
        
        
        time.sleep(0.1)
