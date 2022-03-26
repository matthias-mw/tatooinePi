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
import os

from configparser import ConfigParser

# Modul zum Multithreading
import concurrent.futures

from tatooine_data import AquireData
from tatooine_data import StoreDataToInflux
from tatooine_data import helper
from tatooine_data import Alerting


#=========================================================================
# Konfiguration 
#=========================================================================

# Pfad zum ConfigFile des des MonitorProgramms
TATOOINE_CONF_FILE = "monitor_live.conf"


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


# Get I2C bus
bus = smbus2.SMBus(1)


#=========================================================================
# Main Program 
#=========================================================================
def main(show = FALSE):
    
    # Konfiguration der Messkanäle
    helper.config_channels()
 
    # Initialisierunfg der Verbindung zur InfluxDB
    inflDB = StoreDataToInflux(influx_host, influx_port, influx_admin, \
        influx_passwort,influx_db_name,influx_measurement,influx_tag_location)

    # Initialisierung der Datenerfassung
    data_handle = AquireData(bus)

    # Initialisierung Alarmsystem
    alert_handle = Alerting(Config)

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
                
                alert_handle.calc_alerts(data_handle.get_last_data_measured())
                
                alert_handle.process_alerts(data_handle.get_last_data_measured())
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
                print(chr(27) + "[2J" + helper.show_current_data(data_handle.get_last_data_measured()))
            
            #finish = time.perf_counter()    
            #print(f'Loop finished in {round(finish-start,3)} s')
    

#=========================================================================
# Starten des Hauptprogramms
#=========================================================================
if __name__ == '__main__':


    # ==================================================
    # Auslesen des Config Files
    # ==================================================
    # Einlesen des COnfigfiles
    Config = ConfigParser()
    Config.read(TATOOINE_CONF_FILE)

    print(Config.sections())

    #Zugangsdaten INFLUX_DB auf gleichem Raspberry
    influx_host = helper.getConfigValue(Config,"InfluxDB","HOST")
    influx_port = helper.getConfigValue(Config,"InfluxDB","PORT")
    influx_admin = helper.getConfigValue(Config,"InfluxDB","ADMIN")
    influx_passwort = helper.getConfigValue(Config,"InfluxDB","PASSWORT")
    influx_db_name = helper.getConfigValue(Config,"InfluxDB","DB_NAME")
    influx_measurement = helper.getConfigValue(Config,"InfluxDB","MEASUREMENT")
    influx_tag_location = helper.getConfigValue(Config,"InfluxDB","TAG_LOCATION")
    
    # Logging
    tatooine_log_file = helper.getConfigValue(Config,"Logging","LOG_FILE")
    tatooine_log_dir = helper.getConfigValue(Config,"Logging","LOG_DIR")
    log_file_full_name = os.path.join(tatooine_log_dir, tatooine_log_file)
    
    tmp = helper.getConfigValue(Config,"Logging","LOG_LEVEL")
    if (tmp == "DEBUG"):
        tatooine_log_level = logging.DEBUG
    if (tmp == "INFO"):
        tatooine_log_level = logging.INFO
    if (tmp == "WARNING"):
        tatooine_log_level = logging.WARNING
    if (tmp == "ERROR"):
        tatooine_log_level = logging.ERROR
    
    
   
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
        tatooine_log_level = logging.DEBUG
            
    showData = FALSE
    if args.show:
        print ("Liveausgabe der Daten aktiviert...")
        showData = TRUE


    # Ausgabe der Größe relevanter Verzeichnisse zur Info
    helper.printDiskUsage(Config)
    

    # ==================================================
    # Config Logging
    # ==================================================

    # Konfiguration des Loggings
    logger = logging.getLogger()
    logger.setLevel(tatooine_log_level)

    # Logging - Format
    formatter = logging.Formatter('%(levelname)s %(asctime)s %(name)s %(message)s ')

    # Logging Ausgabeformat
    file_handler = logging.FileHandler(log_file_full_name,"a", \
        encoding = "UTF-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # LogLevel für importierte Module
    logging.getLogger("Adafruit_I2C.Device.Bus.1.Address.0X40").setLevel(logging.INFO)
    logging.getLogger("urllib3.connectionpool").setLevel(logging.INFO)

    # Logging
    logger.info('Python-Script für den TatooineMonitor neu gestartet')
           
    # Starten der Main Loop
    main(showData)
        

