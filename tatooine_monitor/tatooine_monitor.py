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
from dataclasses import dataclass

# Modul zum Multithreading
import concurrent.futures

from tatooine_data import AquireData
from tatooine_data import StoreDataToInflux
from tatooine_data import helper
from tatooine_data import Alerting


#=========================================================================
# Konfiguration 
#=========================================================================

# Standard-Pfad zum ConfigFile des MonitorProgramms
# (wird verwendet, wenn kein -c/--config Argument übergeben wird)
TATOOINE_CONF_FILE = "/opt/tatooinePi/tatooine_monitor/monitor_live.conf"

# Verzeichnis der verwendeten Konfigurationsdatei (wird in __main__ ermittelt und
# im MonitorConfig-Objekt an main() übergeben; alle weiteren Configs wie
# config_channels.csv, config_alerts.csv und .env liegen dort)


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


#=========================================================================
# Laufzeit-Konfiguration
#=========================================================================
@dataclass
class MonitorConfig:
    """Bündelt alle Laufzeit-Parameter des Monitors (statt globaler Variablen)"""
    conf: ConfigParser
    conf_dir: str
    influx_host: str
    influx_port: int
    influx_token: str
    influx_org: str
    influx_bucket: str
    influx_measurement: str
    influx_tag_location: str
    influx_developer_mode: bool
    log_file_full_name: str
    log_level: int


#=========================================================================
# Main Program
#=========================================================================
def main(show = FALSE, cfg: MonitorConfig = None):

    # I2C-Bus erst hier öffnen (nicht beim Import), damit das Modul auch
    # ohne /dev/i2c-1 importierbar bleibt (z.B. für Tests oder -t/--testemail)
    try:
        bus = smbus2.SMBus(1)
    except Exception as e:
        logger.error(f"I2C-Bus /dev/i2c-1 konnte nicht geöffnet werden: {e} "
                     "(i2c-dev aktivieren: raspi-config -> Interface Options -> I2C)")
        sys.exit(1)

    # Konfiguration der Messkanäle
    helper.config_channels(cfg.conf_dir)

    # Initialisierunfg der Verbindung zur InfluxDB (V2 API)
    inflDB = StoreDataToInflux(cfg.influx_host, cfg.influx_port, cfg.influx_token, \
        cfg.influx_org, cfg.influx_bucket, cfg.influx_measurement, \
        cfg.influx_tag_location, cfg.influx_developer_mode)

    # Initialisierung der Datenerfassung
    data_handle = AquireData(bus)

    # Initialisierung Alarmsystem
    alert_handle = Alerting(cfg.conf, cfg.conf_dir)

    # Test der Verbindung zu InfluxDB; beim Start hart abbrechen, wenn die
    # DB nicht erreichbar ist (systemd startet das Programm neu)
    if not inflDB.check_db_connection():
        logger.error("InfluxDB beim Start nicht erreichbar - Programm wird beendet (systemd startet neu)")
        sys.exit(1)

    cnt_i2c = 0
    cnt_i2c_slow = 0
    cnt_1wire = 0
    cnt_cycle = 0

    # We can use a with statement to ensure threads are cleaned up promptly
    with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
        future_1w  = concurrent.futures.Future()
        future_i2c  = concurrent.futures.Future()
        future_i2c_slow  = concurrent.futures.Future()
        
        def check_future_exception(future, name):
            """Prüft ob ein Future eine Exception hatte und loggt sie."""
            if future.done() and not future.cancelled():
                exc = future.exception()
                if exc is not None:
                    logger.error(f"Exception in {name}: {exc}")
        
        while True:
            
            cnt_i2c +=1
            cnt_i2c_slow +=1
            cnt_1wire +=1

            # Prüfe vorherige Futures auf Exceptions
            check_future_exception(future_i2c, "aquire_data_i2c")
            check_future_exception(future_i2c_slow, "aquire_data_i2c_slow")
            check_future_exception(future_1w, "aquire_data_1wire")

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
    # Vorab-Parser zur Auswahl der Konfigurationsdatei (-c/--config)
    pre_parser = argparse.ArgumentParser(add_help=False)
    pre_parser.add_argument("-c", "--config", default=TATOOINE_CONF_FILE)
    pre_args, _ = pre_parser.parse_known_args()
    tatooine_conf_file = pre_args.config

    # Einlesen des COnfigfiles
    print("Verwendete Konfigurationsdatei: " + tatooine_conf_file)
    if not os.path.isfile(tatooine_conf_file):
        print("FEHLER: Konfigurationsdatei nicht gefunden: " + tatooine_conf_file)
        sys.exit(1)

    Config = ConfigParser()
    try:
        files_read = Config.read(tatooine_conf_file)
    except Exception as e:
        print("FEHLER: Konfigurationsdatei konnte nicht geparst werden: " \
            + tatooine_conf_file + " (" + str(e) + ")")
        sys.exit(1)

    if tatooine_conf_file not in files_read:
        print("FEHLER: Konfigurationsdatei konnte nicht gelesen werden: " \
            + tatooine_conf_file)
        sys.exit(1)

    print(Config.sections())

    # Verzeichnis der conf bestimmen (CSV-Configs und .env liegen dort)
    tatooine_conf_dir = os.path.dirname(os.path.abspath(tatooine_conf_file))

    # Zugangsdaten aus .env laden (liegt im selben Verzeichnis wie die conf);
    # bereits gesetzte Umgebungsvariablen haben Vorrang vor der .env
    env_file = os.path.join(tatooine_conf_dir, ".env")
    if os.path.isfile(env_file):
        n_env = helper.load_env_file(env_file)
        print(f"{n_env} Variablen aus .env geladen: {env_file}")
    else:
        print(f"Hinweis: keine .env gefunden ({env_file}) - Secrets müssen über die Umgebung gesetzt sein")

    #Zugangsdaten INFLUX_DB (V2 API - Token-basiert)
    influx_host = helper.getConfigValue(Config,"InfluxDB","HOST")
    influx_port = helper.getConfigValue(Config,"InfluxDB","PORT")
    # Token kommt aus .env/Umgebung (INFLUXDB_TOKEN), Fallback: conf
    influx_token = helper.get_secret("INFLUXDB_TOKEN", Config, "InfluxDB", "TOKEN")
    influx_org = helper.getConfigValue(Config,"InfluxDB","ORG")
    influx_bucket = helper.getConfigValue(Config,"InfluxDB","BUCKET")
    influx_measurement = helper.getConfigValue(Config,"InfluxDB","MEASUREMENT")
    influx_tag_location = helper.getConfigValue(Config,"InfluxDB","TAG_LOCATION")
    
    # Developer Mode: true = speichert zusatzliche Debug-Felder in InfluxDB
    dev_mode_str = helper.getConfigValue(Config,"InfluxDB","DEVELOPER_MODE")
    influx_developer_mode = (dev_mode_str.lower() == "true")
    
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
    parser.add_argument("-c", "--config", default=TATOOINE_CONF_FILE, \
        help="Pfad zur Konfigurationsdatei (Default: %(default)s)")
    parser.add_argument("-t", "--testemail", help="Test-Alarm-E-Mail \
        versenden und Programm beenden", action="store_true")
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
    print (helper.printDiskUsage(Config))
    

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
    logging.getLogger("urllib3.connectionpool").setLevel(logging.INFO)

    # Logging
    logger.info('=============================================================')
    logger.info('Python-Script für den TatooineMonitor neu gestartet')
    logger.info('=============================================================')

    # Test-Alarm-E-Mail versenden und Programm beenden
    if args.testemail:
        print("Sende Test-Alarm-E-Mail...")
        try:
            alert_test = Alerting(Config, tatooine_conf_dir)
            alert_test.send_test_email()
        except Exception as e:
            logger.error(f"Test-Alarm-E-Mail fehlgeschlagen: {e}")
            print("FEHLER: Test-Alarm-E-Mail konnte nicht versendet werden: " + str(e))
            sys.exit(1)
        sys.exit(0)

    # Alle Laufzeit-Parameter in einem Config-Objekt bündeln (statt Globals)
    monitor_cfg = MonitorConfig(
        conf=Config,
        conf_dir=tatooine_conf_dir,
        influx_host=influx_host,
        influx_port=int(influx_port),
        influx_token=influx_token,
        influx_org=influx_org,
        influx_bucket=influx_bucket,
        influx_measurement=influx_measurement,
        influx_tag_location=influx_tag_location,
        influx_developer_mode=influx_developer_mode,
        log_file_full_name=log_file_full_name,
        log_level=tatooine_log_level,
    )

    # Starten der Main Loop
    main(showData, monitor_cfg)
        

