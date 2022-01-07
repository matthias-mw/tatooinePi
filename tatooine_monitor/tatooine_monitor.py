#!/usr/bin/env python3
# coding: ISO-8859-1 

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

# Modul zum Multithreading
import concurrent.futures

from tatooine_data import AquireData
from tatooine_data import StoreDataToInflux
from tatooine_data import helper


#=========================================================================
# Konfiguration 
#=========================================================================

MAIN_LOOP_LENGHT_MS = 250

N_LOOPS_AQUIRE_I2C = 1

N_LOOPS_AQUIRE_1WIRE = 10

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

    cnt_i2c = 0
    cnt_1wire = 0


    # We can use a with statement to ensure threads are cleaned up promptly
    with concurrent.futures.ThreadPoolExecutor(max_workers=5555) as executor:
        future_1w  = concurrent.futures.Future()
        future_i2c  = concurrent.futures.Future()
        
        while True:
            
            cnt_i2c +=1
            cnt_1wire +=1
     
            # Bestimmung der Startzeit der Schleife
            start = time.perf_counter()
            
            # i2c Messen wenn es Zeit ist und der letzte Thread beendet wurde
            if cnt_i2c >= N_LOOPS_AQUIRE_I2C and not(future_i2c.running()):
                # Messen aller Sensoren
                future_i2c = executor.submit(data_handle.aquire_data_i2c)
                cnt_i2c =0

            # 1 Wire Messen wenn es Zeit ist und der letzte Thread beendet wurde
            if cnt_1wire >= N_LOOPS_AQUIRE_1WIRE and not(future_1w.running()):
                # Messen aller Sensoren in separatem thread
                future_1w = executor.submit(data_handle.aquire_data_1wire)
                cnt_1wire =0

            s1 = time.perf_counter()
            # Speichern der Messdaten
            inflDB.store_data(data_handle.data_last_measured)
            s2 = time.perf_counter()
            
            # Bestimmung der noch verbleibenden Schleifenzeit        
            delta = time.perf_counter() - start
            delay = (MAIN_LOOP_LENGHT_MS / 1000) - delta

            if (delay < 0):
                # Die ZEitschleife wurde überschritten
                print("{0:s}: -> Oberrun by {1:0.3f}s Storage {2:0.3f}".format(str(datetime.now()), round(delta,3), round(s2-s1,3)) )

            else:
                # print(f'Loop finished in {round(delta,3)} s')
                time.sleep(delay)
                
            finish = time.perf_counter()    
            #print(f'Loop finished in {round(finish-start,3)} s')
        

