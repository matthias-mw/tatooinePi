#!/usr/bin/env python3


__author__ = "Matthias Werner"
__copyright__ = "Copyright 2021, TatooineMonitor Projekt"
__credits__ = ["Matthias Werner"]
__license__ = "GPL"
__version__ = "0.1"
__maintainer__ = "Matthias Werner"
__email__ = "werner.matthias@web.de"
__status__ = "Development"

from datetime import datetime
import logging
import smbus
import time
import aquireData.helper

from aquireData.aquire_data import AquireData

from aquireData.store_data import StoreDataToInflux


#=========================================================================
# Konfiguration 
#=========================================================================

MAIN_LOOP_LENGHT_MS = 250

#Zugangsdaten INFLUX_DB auf gleichem Raspberry
INFLUX_HOST = "127.0.0.1"
INFLUX_PORT = 8086
INFLUX_ADMIN = "admin"
INFLUX_PASSWORT = "tatooinedb"
INFLUX_DB_NAME = "sensors"


# Get I2C bus
bus = smbus.SMBus(1)

if __name__ == '__main__':
        
    inflDB = StoreDataToInflux(INFLUX_HOST, INFLUX_PORT, INFLUX_ADMIN, \
        INFLUX_PASSWORT,INFLUX_DB_NAME)

    
    aquireData.helper.config_channels()
    Data = AquireData(bus)

    inflDB.check_db_connection()

    cnt = 0
    while True:
        
        start = datetime.now()
        
        cnt +=1
        
        #TODO Debugging Ordentlich machen
        
        Data.aquire_data()
        measured  = datetime.now() - start
        measured = measured.seconds + measured.microseconds / 1000000
        
        inflDB.store_data(Data.data_last_measured)
        
        delta = datetime.now() - start
        delay = delta.seconds + delta.microseconds / 1000000

        
        delay = (MAIN_LOOP_LENGHT_MS / 1000) - (delta.seconds + \
            delta.microseconds / 1000000)
        
        if (delay < 0):
            print(str(delay) + " ----> " + str(measured) + " ----> " + str(datetime.now()))
        
        else:
            time.sleep(delay)

