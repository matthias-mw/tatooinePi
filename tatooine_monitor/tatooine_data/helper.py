#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Modul zur Verarbeitung von CSV Dateien
import csv

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
             
def show_current_data(data_last_measured: DataPoint) -> str:
    """Tabellarische Anzeige der aktuellen Messwerte
    
    Diese Funktion erzeugt einen String mit einer Messwerttabelle der aktuellen Messwerte, welche der Funktion übergeben wurden. 

    :param data_last_measured:  List von Datapoint mit den Messwerten
    :type data_last_measured:   Datapoint List
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
             