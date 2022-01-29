#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Modul zur Verarbeitung von Regular Expressions
import re

# Modul zur Bearbeitung der Zeitstempel
import datetime

# Module zur Bearbeitung von Files
from os import listdir, path
from os.path import isfile, join

# Import Logging Modul
import logging

class OneWire:
    """Schnittstellenklasse zur Auslesung von 1-Wire Sensoren
    
    Aktuelle stellt die Klasse alle Methoden zur Verfügung, um über den 1-Wire
    Bus die DS18220 Sensoren auslesen zu können. Dabei ist zu beachten, dass
    diese Sensoren eine hohe Latenz besitzen und daher die Auslesung über
    Multithreading erfolgen sollte.
    
    .. code-block:: python
    
        sensor.show_all_devices()
        with concurrent.futures.ThreadPoolExecutor() as executor:
            results = [executor.submit(sensor.read_1w_sensor_ds18s20,i) for i in sensor.list_all_devices()]
            for f in concurrent.futures.as_completed(results):
                print(f.result())
    
    Dabei wird vorausgesetzt, dass zuvor mit raspi-config die 1Wire
    Intergration aktiviert wurde und ein entsprechender GPIO definiert
    wurde.
    
    .. note:: 
        Aktuell wird damit nur der Sensor DS18S20 unterstützt. Es werden zwar
        alle 1-Wire Sensoren gefunden und aufgelistet, aber nur der DS18S20 kann gelesen werden.
    """
    
    # Festlegen des Systempfades für die 1-Wire Sensoren
    _path_to_1W_sensors = "/sys/bus/w1/devices"
    """Pfad zu dem 1-Wire Sensoren auf dem RaspberryPi"""
    
    # Filename mit den Sensorwerten
    _temp_sensor_1w_filename = "-"
    """Dateiname mit dem Messwert des DS18S20 Temperatursensors"""

    def __init__(self, path_to_1wire = "/sys/bus/w1/devices", 
                 ds18s20_fname = "w1_slave"):
        """Initialisierung der 1 Wire Treiber Klasse

        :param path_to_1wire: Systempfades für die 1-Wire Sensoren, defaults to "/sys/bus/w1/devices"
        :type path_to_1wire: str, optional
        :param ds18s20_fname: Filename mit den Sensorwerten des DS18s20, defaults to "w1_slave"
        :type ds18s20_fname: str, optional
        """
        
        # ============================================
        # Konfiguration des Logging
        # ============================================
        self.logger = logging.getLogger(__name__)
        #self.logger.setLevel(logging.INFO)
        self.logger.addHandler(logging.NullHandler())
        
        # Name des Messfiles vom DS18S20
        self._temp_sensor_1w_filename = ds18s20_fname
        # Festlegen des Systempfades für die 1-Wire Sensoren
        self._path_to_1W_sensors = path_to_1wire
    
        # Logging Info
        self.logger.info(f'Folgende 1-wire Sensoren wurden unter {path_to_1wire} gefunden: \n{self.list_all_devices()}')
        
        
    def list_all_devices(self) -> list:
        """Auflistung aller 1-Wire Sensoren die im System gefunden werden
        
        Die Funktion listet alle 1-Wire sensoren auf, die im Systemverzeichnis :mod:`~driver.one_wire.OneWire._path_to_1W_sensors` gefunden werden. 

        .. note:: 
            Die Funktion nutzt dazu Regularexpressions und untersucht, ob die Files in diesem Verzeichnis eine 1-Wire typischen Name besitzen. Der Filename entspricht den SensorIDs. (z.B. 28-0121131907b3, 
            3a-0000003820a6 ... )
        
        
        :return: Auflistung aller 1-Wire Sensoren
        :rtype: list
        """

        # Alle Files der 1Wire Sensoren extrahieren
        # typischer Aufbau des Filenamens (3a-0000003820a6)
        sensors = [f for f in listdir(self._path_to_1W_sensors) \
            if re.match(r"[0-9a-f]{2}-[0-9a-f]{12}", f)]
        
        return sensors    

    def list_ds18s20_devices(self) -> list:
        """Auflistung aller DS18S20 Sensoren die über 1-Wire im System gefunden werden

        Die Funktion entspricht der :mod:`~driver.one_wire.OneWire.list_all_devices`, beschränkt sich aber auf die Ausgabe der DS18S20 Sensoren.
        
        .. note::
            Die DS18S20 Sensoren beginnen in Ihrer ID immer mit der 28
                
        :return: Auflistung aller DS18S20 Sensoren
        :rtype: list
        """

        # Alle Files der 1Wire Sensoren extrahieren
        # typischer Aufbau des Filenamens (3a-0000003820a6)
        sensors = [f for f in listdir(self._path_to_1W_sensors) \
            if re.match(r"28-[0-9a-f]{12}", f) ]
        
        return sensors  

    def show_all_devices(self) -> None:
        """Ausgabe aller gefunden 1-Wire Sensoren in der Konsole
        """
        
        # Ausgabe der Sensoren
        print("Folgende 1-Wire Sensoren wurden gefunden:")
        for i in self.list_all_devices():
            print(i)
 

    def read_1w_sensor_ds18s20(self,id: str) -> list[str, float]:
        """Auslesen eines spezifischen DS18S20 Sensors
        
        Die Methode gibt die aktuelle Temperatur des angewählten Sensors
        aus. Dazu wird das File  :mod:`~driver.one_wire.OneWire._temp_sensor_1w_filename` ausgelesen und anschließend der Wert berechnet.
        
        .. note::
        
            Beispiel eines w1_slave Files:
            
            63 01 4b 46 7f ff 0c 10 d1 : crc=d1 YES \n
            63 01 4b 46 7f ff 0c 10 d1 t=22187
        
        Sollte das File nicht lesbar sein, so wird eine Exception ausgegeben.
        

        :param id: Die ID des auszulesenden DS18S20 Sensors
        :type id: string
        :return: eine Liste mit der SensorID und des dazugehörigen Messwertes
        :rtype: list[str, float]
        """
        
        value = None
        path = join(self._path_to_1W_sensors,id,self._temp_sensor_1w_filename)
        
        # Versuchen den Sensor auszulesen
        try:
            with open(path,'r') as sensorfile:
                # Wenn die Auslesung korrekt erfolgt ist
                line1 = sensorfile.readline()
                if re.match(r"([0-9a-f]{2} ){9}: crc=[0-9a-f]{2} YES", line1):
                    # Extrahiere den Messwert
                    line2 = sensorfile.readline()
                    m = re.match(r"([0-9a-f]{2} ){9}t=([+-]?[0-9]+)", line2)
                    if m:
                        # Berechne das Ergebnis
                        value = str(float(m.group(2)) / 1000.0)            
                                                          
        # Fehlermeldung sollte 1-Wire Sensor nicht lesbar sein
        except(OSError):
                
            # Logging Info
            msg = f'DS1820 mit ID: {id} nicht auslesbar. File {path} konnte nicht gelesen werden'
            self.logger.warning(msg)
            
            value = None
            
        except Exception as e:
            
            # Logging Info
            self.logger.exception(e)
            
            value = None
                        
        if value == None:                             
            # Ausgabe eines Info das Messung fehlgeschlagen
            self.logger.warning('measure_1wire_ds18s20 hat für Kanal %s keinen Wert auslesen können.',id)
        
        return [id,value]

