#!/usr/bin/env python3
# -*- coding: utf-8 -*-

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
from pickle import FALSE, TRUE
import sys
import smbus2
import time
import argparse
import sys

# Modul zum Multithreading
import concurrent.futures

from tatooine_data import AquireData
from tatooine_data import StoreDataToInflux
from tatooine_data import helper
from tatooine_data import Alerting


#=========================================================================
# Konfiguration 
#=========================================================================

# Länge der Hauptschleife
MAIN_LOOP_LENGHT_MS = 250
# Anzahl Schleifendurchgänge bis I2C gemessen wird
N_LOOPS_AQUIRE_I2C = 1
# Anzahl Schleifendurchgänge bis I2C gemessen wird
N_LOOPS_AQUIRE_I2C_SLOW = 10
# Anzahl Schleifendurchgänge bis 1-Wire gemessen wird
N_LOOPS_AQUIRE_1WIRE = 10
# Anzahl Schleifendurchgänge Delay AlarmSystem nach Startup
N_LOOPS_DELAY_ALERT_AT_STARTUP = 20

#Zugangsdaten INFLUX_DB auf gleichem Raspberry
INFLUX_HOST = "127.0.0.1"
INFLUX_PORT = 8086
INFLUX_ADMIN = "admin"
INFLUX_PASSWORT = "tatooinedb"
INFLUX_DB_NAME = "sensors"

# Logging
TATOOINE_LOG_FILE = "monitor.log"
TATOOINE_LOG_LEVEL = logging.INFO

# Get I2C bus
bus = smbus2.SMBus(1)


#=========================================================================
# Main Program 
#=========================================================================
def main(show = FALSE):
    
    # Konfiguration der Messkanäle
    helper.config_channels()
 
    # Initialisierunfg der Verbindung zur InfluxDB
    inflDB = StoreDataToInflux(INFLUX_HOST, INFLUX_PORT, INFLUX_ADMIN, \
        INFLUX_PASSWORT,INFLUX_DB_NAME)

    # Initialisierung der Datenerfassung
    data_handle = AquireData(bus)

    alert_handle = Alerting()

    # Test der Verbindung zu InfluxDB
    inflDB.check_db_connection()

    cnt_i2c = 0
    cnt_i2c_slow = 0
    cnt_1wire = 0
    cnt_cycle = 0

    # We can use a with statement to ensure threads are cleaned up promptly
    with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
        future_1w  = concurrent.futures.Future()
        future_i2c  = concurrent.futures.Future()
        future_i2c_slow  = concurrent.futures.Future()
        
        while True:
            
            cnt_i2c +=1
            cnt_i2c_slow +=1
            cnt_1wire +=1

            # Bestimmung der Startzeit der Schleife
            start = time.perf_counter()
            
            # i2c Messen wenn es Zeit ist und der letzte Thread beendet wurde
            if cnt_i2c >= N_LOOPS_AQUIRE_I2C and not(future_i2c.running()):
                # Messen aller Sensoren
                future_i2c = executor.submit(data_handle.aquire_data_i2c)
                cnt_i2c =0
                
            # i2c Messen wenn es Zeit ist und der letzte Thread beendet wurde
            if cnt_i2c_slow >= N_LOOPS_AQUIRE_I2C_SLOW and not(future_i2c_slow.running()):
                # Messen aller Sensoren
                future_i2c_slow = executor.submit(data_handle.aquire_data_i2c_slow)
                cnt_i2c_slow =0
                
            # 1 Wire Messen wenn es Zeit ist und der letzte Thread beendet wurde
            if cnt_1wire >= N_LOOPS_AQUIRE_1WIRE and not(future_1w.running()):
                # Messen aller Sensoren in separatem thread
                future_1w = executor.submit(data_handle.aquire_data_1wire)
                cnt_1wire =0
                
            # Speichern der Messdaten
            inflDB.store_data(data_handle.data_last_measured)
            
            # Alert Notifications
            if (cnt_cycle > N_LOOPS_DELAY_ALERT_AT_STARTUP):
                
                alert_handle.calc_alerts(data_handle.data_last_measured)
                
                alert_handle.process_alerts()
            else:
                cnt_cycle +=1
            
            
            # Bestimmung der noch verbleibenden Schleifenzeit        
            delta = time.perf_counter() - start
            delay = (MAIN_LOOP_LENGHT_MS / 1000) - delta

            if (delay < 0):
                # Die Zeitschleife wurde überschritten
                msg = "Oberrun by {0:0.3f} Sekunden".format(round(delta,3))
                logger.debug(msg)
            else:
                # print(f'Loop finished in {round(delta,3)} s')
                time.sleep(delay)
            
            #Ausgabe der aktuellen Daten über Stdout
            if(show == TRUE):
                print(data_handle.show_current_data())
            
            #finish = time.perf_counter()    
            #print(f'Loop finished in {round(finish-start,3)} s')
    

#=========================================================================
# Starten des Hauptprogramms
#=========================================================================
if __name__ == '__main__':

    # ==================================================
    # Comandline Options
    # ==================================================
    # Define the program description
    dscTxt = 'TatooineMonitor ist ein Programm zur Überwachung einzelner \
        Messgrößen der Segelyacht Tatooine. Alle Messdaten werden in \
        einer InfluxDB abgespeichert. \n Copyright: ' +__copyright__ \
        + '\nAutor: ' + __author__

    # Initialisierung des Parsers
    parser = argparse.ArgumentParser(description=dscTxt)
    parser.add_argument("-v", "--version", help="Anzeige Programversion", \
        action="store_true")
    parser.add_argument("-d", "--debug", help="Aktivierung des Debuglevel \
        für Logging", action="store_true")
    parser.add_argument("-s", "--show", help="Anzeige der aktuellen Werte \
        über stdout", action="store_true")
    args = parser.parse_args()
    
    # Ausgabe der übergebenen Argumente
    if args.version:
        print ("Tatooine Monitor Version " + __version__)
        sys.exit()
    
    if args.debug:
        print ("Debug Logging enabled...")
        TATOOINE_LOG_LEVEL = logging.DEBUG
            
    showData = FALSE
    if args.show:
        print ("Liveausgabe der Daten aktiviert...")
        showData = TRUE

    # ==================================================
    # Config Logging
    # ==================================================

    # Konfiguration des Loggings
    logger = logging.getLogger()
    logger.setLevel(TATOOINE_LOG_LEVEL)

    # Logging - Format
    formatter = logging.Formatter('%(levelname)s %(asctime)s %(name)s %(message)s ')

    # Logging Ausgabeformat
    file_handler = logging.FileHandler(TATOOINE_LOG_FILE,"w",encoding = "UTF-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # LogLevel für importierte Module
    logging.getLogger("Adafruit_I2C.Device.Bus.1.Address.0X40").setLevel(logging.INFO)
    logging.getLogger("urllib3.connectionpool").setLevel(logging.INFO)

    # Logging
    logger.info('Python-Script für den TatooineMonitor neu gestartet')
           
    # Starten der Main Loop
    main(showData)
        

