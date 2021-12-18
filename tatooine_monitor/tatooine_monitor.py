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

from tatooine_data import AquireData
from tatooine_data import StoreDataToInflux
from tatooine_data import helper


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

    # Konfiguration der Messkanäle
    helper.config_channels()
    
    # Initialisierunfg der Verbindung zur InfluxDB
    inflDB = StoreDataToInflux(INFLUX_HOST, INFLUX_PORT, INFLUX_ADMIN, \
        INFLUX_PASSWORT,INFLUX_DB_NAME)

    # Initialisierung der Datenerfassung
    data_handle = AquireData(bus)

    # Test der Verbindung zu InfluxDB
    inflDB.check_db_connection()

    while True:
        
        # Bestimmung der Startzeit der Schleife
        start = datetime.now()
        
        # Messen aller Sensoren
        data_handle.aquire_data()
        # Speichern der Messdaten
        inflDB.store_data(data_handle.data_last_measured)
        
        
        # Bestimmung der noch verbleibenden Schleifenzeit        
        delta = datetime.now() - start
        delay = (MAIN_LOOP_LENGHT_MS / 1000) - (delta.seconds + \
            delta.microseconds / 1000000)
        if (delay < 0):
            # Die ZEitschleife wurde überschritten
            print("{0:s}: -> Oberrun by {1:3f}s".format(str(datetime.now()), \
                (delta.seconds + delta.microseconds / 1000000)))
        
        else:
            time.sleep(delay)

