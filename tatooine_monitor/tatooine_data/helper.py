#!/usr/bin/env python3

# Modul zur Verarbeitung von CSV Dateien
import csv


CONF_FILE = "config_channels.csv"
"""Konfigurationsdatei für die Messkanäle als csv mit der Bezeichnung der Eigenschaft in der ersten Zeile"""

CHANNEL_CONFIG_LIST = []
"""Liste mit allen Messkanälen und Ihren Eigenschaften"""

def config_channels():
    """Konfiguartion aller Messkanäle
    
    Zu Beginn des Programms wird die Datei :func: 'CONF_FILE' gelesen. 
    In Ihr sind alle relevanten Infos pro Kanal Zeilenweise aufgeführt. So
    werden alle Parameter (z.B. Filter, Schellen, Speicherinterval etc.) 
    in die :func: 'CHANNEL_CONFIG_LIST' eingelesen und in der Funktion 
    :func: 'AquireData.__init__' in die Beschreibung des jeweiligen Kanals
    übernommen.
    
    
    
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

             
            