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

CONF_FILE = "config_channels.csv"
"""Konfigurationsdatei für die Messkanäle als csv mit der Bezeichnung der Eigenschaft in der ersten Zeile"""

CHANNEL_CONFIG_LIST = []
"""Liste mit allen Messkanälen und Ihren Eigenschaften :doc:`config_channels` """

def config_channels():
    """Konfiguartion aller Messkanäle
    
    Zu Beginn des Programms wird die Datei :file:`config_channels.csv` gelesen. 
    In Ihr sind alle relevanten Infos pro Kanal Zeilenweise aufgeführt. So
    werden alle Parameter (z.B. Filter, Schellen, Speicherinterval etc.) 
    in die :mod:`~tatooine_data.helper.CHANNEL_CONFIG_LIST` eingelesen und in der Funktion :class:`~tatooine_data.aquire_data.AquireData` in die Beschreibung des jeweiligen Kanals übernommen.
    
    """    
     
    # Sicheres öffnen der CSV Datei, welche durch With automatisch
    # nach Beendigung des Auslesen geschlossen wird
    with open(CONF_FILE) as csvdatei:
        
        # Auslesen der Daten aus der CSV
        csv_reader_object = csv.reader(csvdatei)
        
        line_count = 0
        header = []
        # Verarbeiten der Daten aus der CSV Zeile für Zeile
        for row in csv_reader_object:
            # Die erste Zeile der CSV repäsentiert die Header
            if line_count == 0:
                header = [colum for colum in row]
                line_count +=1
            # Zuordnen der Config eines jeden Kanals in ein Dictonary
            else:
                i=0
                channel_conf = {}
                for y in header:
                    channel_conf[y] = row[i]
                    i +=1
                # Abspeichern in der Kanal Config Liste
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
    # Iterieren durch alle Files
    for path, dirs, files in os.walk(folder): 
        for f in files: 
            fp = os.path.join(path, f) 
            size += os.path.getsize(fp) 
    
    if (unit.lower() == "mb"):
        # Ausgabe der Größe in MB
        return float(size / 1024 / 1024)
    elif (unit.lower() == "gb"):
        # Ausgabe der Größe in GB
        return float(size / 1024 / 1024 / 1024)
    else:
        # Ausgabe der Größe in Bytes
        return float(size)
   

def printDiskUsage(config: ConfigParser) -> None:
    """Ausgabe der Verzeichnisgröße
    
    Diese Methode gibt relevante Verzeichnisgrößen aus. Die Verzeichnisse wurden
    in der CONF Datei spezifiziert.

    :param config: Config
    :type config: ConfigParser
    """
    
    influx_size = getFolderSize(getConfigValue(config,"COMMON",\
        "INFLUX_DB_PATH"))
    
    print(f"Datenbankgröße InfluxDB:  {influx_size :0.2f} Mb")
    