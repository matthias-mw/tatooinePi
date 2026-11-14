#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Modul zur Verarbeitung von CSV Dateien
import csv
import sys
import os
import logging
from configparser import ConfigParser

# Klasse für die Abspeicherung der Datenpunkte
from .datapoint import DataPoint

DEFAULT_CONF_DIR = "/opt/tatooinePi/tatooine_monitor"
"""Standard-Verzeichnis der Konfigurationsdateien (config_channels.csv, config_alerts.csv, .env)"""

CHANNEL_CONFIG_LIST = []
"""Liste mit allen Messkanälen und Ihren Eigenschaften :doc:`config_channels` """

def load_csv_config(csv_path: str) -> list:
    """Lädt eine CSV-Konfigurationsdatei als Liste von Dicts

    Die erste Zeile der CSV ist der Header und liefert die Keys der Dicts.
    Existiert die Datei nicht, wird das Programm mit Fehlermeldung beendet.

    :param csv_path: Pfad zur CSV-Datei
    :type csv_path: str
    :return: Liste von Dicts (ein Dict pro Datenzeile)
    :rtype: list
    """
    if not os.path.isfile(csv_path):
        print(f"FEHLER: Konfigurationsdatei nicht gefunden: {csv_path}")
        sys.exit(1)

    # Sicheres öffnen der CSV Datei, welche durch With automatisch
    # nach Beendigung des Auslesens geschlossen wird
    rows = []
    with open(csv_path) as csvdatei:
        csv_reader_object = csv.reader(csvdatei)
        header = []
        # Verarbeiten der Daten aus der CSV Zeile für Zeile
        for line_count, row in enumerate(csv_reader_object):
            # Die erste Zeile der CSV repräsentiert die Header
            if line_count == 0:
                header = [colum for colum in row]
            # Zuordnen der Config in ein Dictonary
            else:
                i = 0
                channel_conf = {}
                for y in header:
                    channel_conf[y] = row[i]
                    i += 1
                rows.append(channel_conf)
    return rows


def config_channels(conf_dir: str = DEFAULT_CONF_DIR):
    """Konfiguartion aller Messkanäle
    
    Zu Beginn des Programms wird die Datei :file:`config_channels.csv` gelesen. 
    In Ihr sind alle relevanten Infos pro Kanal Zeilenweise aufgeführt. So
    werden alle Parameter (z.B. Filter, Schellen, Speicherinterval etc.) 
    in die :mod:`~tatooine_data.helper.CHANNEL_CONFIG_LIST` eingelesen und in der Funktion :class:`~tatooine_data.aquire_data.AquireData` in die Beschreibung des jeweiligen Kanals übernommen.
    
    """    
     
    conf_file = os.path.join(conf_dir, "config_channels.csv")
    # CSV parsen (Header = Keys) und in die Kanalliste übernehmen
    for channel_conf in load_csv_config(conf_file):
        CHANNEL_CONFIG_LIST.append(channel_conf)
             
def show_current_data(data_last_measured: list[DataPoint]) -> str:
    """Tabellarische Anzeige der aktuellen Messwerte
    
    Diese Funktion erzeugt einen String mit einer Messwerttabelle der aktuellen Messwerte, welche der Funktion übergeben wurden. 

    :param data_last_measured:  List von Datapoint mit den Messwerten
    :type data_last_measured:   Liste von Datapoint 
    :return: Formatierter String
    :rtype: str
    """
    #-----------------------------------------------------------------------
    #Darstellen der aktuellen Werte
    #-----------------------------------------------------------------------
    
    # Header
    strOutput = ""
    strOutput += DataPoint.print_header()
    
    # Datenzeilen
    for x in data_last_measured:
        strOutput += '\n' + DataPoint.print_data_line(x)             
    
    return strOutput
            
            
            
def getConfigValue (config: ConfigParser, section: str , key: str):
    """Auslesen ein COnfigurationsvalue aus dem Conf File
    
    Mit dieser Methode wird jeweils eine einzeln Konfigurationsvariable aus dem 
    CONF File ausgelesen. Dazu muss die Section und der entsprechende Schlüssel
    angegeben werden. Sollte dieser Schlüssel nicht in dem CONF File vorhanden
    sein, wird das Programm beendet.

    :param config: Config Object bestehend aus dem gesamten CONF File
    :type config: ConfigParser
    :param section: Abschnitt in der Conf
    :type section: String
    :param key: Schlüsselwert der Variable
    :type key: String
    :return: Conf Wert
    :rtype: String
    """
    

    try:
        # Auslesen der Variable
        return config.get(section, key)
        
    except:
        # Ausgabe des ConfigFehlers
        print(f"Fehler beim Auslesen der Config bei Section: {section} und Key: {key}!")
        # Logging
        logging.critical(f"Fehler beim Auslesen der Config bei Section: {section} und Key: {key}! -> Programmabbruch")
    
    # Abbruch des Programms wegen ConfigFehler
    sys.exit("Programmabbruch wegen Configfehler")
    
    return None


def load_env_file(env_path: str) -> int:
    """Lädt Zugangsdaten aus einer .env Datei in die Umgebungsvariablen

    Format pro Zeile: KEY=VALUE (# Kommentare und leere Zeilen werden ignoriert).
    Bereits vorhandene Umgebungsvariablen werden nicht überschrieben.

    :param env_path: Pfad zur .env Datei
    :type env_path: str
    :return: Anzahl der neu gesetzten Variablen
    :rtype: int
    """
    count = 0
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value
                count += 1
    return count


def get_secret(env_name: str, config: ConfigParser = None, \
               section: str = None, key: str = None) -> str:
    """Liest ein Secret (Token, Passwort) aus der Umgebung / .env

    Vorrang hat die Umgebungsvariable env_name (ggf. aus .env geladen).
    Fallback: Eintrag key in section der conf-Datei (Legacy).
    Ist nirgends ein Wert gesetzt, wird das Programm mit Fehlermeldung beendet.

    :param env_name: Name der Umgebungsvariable
    :type env_name: str
    :param config: Config Object, defaults to None
    :type config: ConfigParser, optional
    :param section: Abschnitt in der Conf, defaults to None
    :type section: str, optional
    :param key: Schlüssel in der Conf, defaults to None
    :type key: str, optional
    :return: Wert des Secrets
    :rtype: str
    """
    value = os.environ.get(env_name, "").strip()
    if value:
        return value

    if config is not None and section is not None and key is not None:
        try:
            value = config.get(section, key).strip()
        except Exception:
            value = ""
        if value:
            return value

    print(f"FEHLER: Secret '{env_name}' nicht gefunden (weder Umgebungsvariable/.env noch conf [{section}] {key})!")
    sys.exit("Programmabbruch wegen fehlendem Secret")


def getFolderSize (folder: str, unit = "mb"):
    """Ausgabe der Größe eines Verzeichnisses
    
    Mit dieser Methode wird die Größe eines Verzeichnisses ermittelt und
    ausgegeben. Dabei ist es möglich verschiedene Einheiten vorzugeben.

    :param folder: Pfad des Verzeichnisses
    :type folder: str
    :param unit: Einheit, defaults to "mb"
    :type unit: str, optional
    :return: Verzeichnisgrösse
    :rtype: float
    """
    
    size = 0
    # Iterieren durch alle Files (ein File kann während des Laufs verschwinden)
    for path, dirs, files in os.walk(folder):
        for f in files:
            fp = os.path.join(path, f)
            try:
                size += os.path.getsize(fp)
            except OSError:
                pass
    
    if (unit.lower() == "mb"):
        # Ausgabe der Größe in MB
        return float(size / 1024 / 1024)
    elif (unit.lower() == "gb"):
        # Ausgabe der Größe in GB
        return float(size / 1024 / 1024 / 1024)
    else:
        # Ausgabe der Größe in Bytes
        return float(size)
   

def printDiskUsage(config: ConfigParser) -> str:
    """Ausgabe der Verzeichnisgröße
    
    Diese Methode gibt relevante Verzeichnisgrößen aus. Die Verzeichnisse wurden
    in der CONF Datei spezifiziert.

    :param config: Config
    :type config: ConfigParser
    """
    
    tmp = ""
    # bestimmen der zu überwachenden Pfade
    influx_size = getFolderSize(getConfigValue(config,"COMMON",\
        "INFLUX_DB_PATH"))
    motion_size = getFolderSize(getConfigValue(config,"COMMON",\
        "VIDEO_PATH"))
    
    # Ausgabestring erstellen
    tmp += f"Datenbankgröße InfluxDB:  {influx_size :0.2f} Mb"
    tmp += f"\nDatenbankgröße MotionEye:  {motion_size :0.2f} Mb"
    
    return (tmp)