#!/usr/bin/python
# -*- coding: utf-8 -*-

import re
import time
import concurrent.futures
from os import listdir, path
from os.path import isfile, join



class OneWire:
    '''
    
    '''

    # Festlegen des Systempfades für die 1-Wire Sensoren
    _path_to_1W_sensors = "/sys/bus/w1/devices"
    # Filename mit den Sensorwerten
    _temp_sensor_1w_filename = "w1_slave"

    def __init__(self):
        self._temp_sensor_1w_filename = "w1_slave"
    
    
    def list_all_devices(self):

        # Alle Files der 1Wire Sensoren extrahieren
        # typischer Aufbau des Filenamens (3a-0000003820a6)
        sensors = [f for f in listdir(self._path_to_1W_sensors) \
            if re.match(r"[0-9a-f]{2}-[0-9a-f]{12}", f)]
        
        return sensors    

    def show_all_devices(self):
        
        # Ausgabe der Sensoren
        print("Folgende 1-Wire Sensoren wurden gefunden:")
        for i in self.list_all_devices():
            print(i)

        

    def read_1w_sensor_ds18s20(self,id = str):
        
        value = 0.0
        path = join(self._path_to_1W_sensors,id,self._temp_sensor_1w_filename)
        
        # Versuchen den Sensor auszulesen
        try:
            with open(path,'r') as sensorfile:
                # Wenn die Auslesung korrekt erfolgt ist
                line = sensorfile.readline()
                if re.match(r"([0-9a-f]{2} ){9}: crc=[0-9a-f]{2} YES", line):
                    # Extrahiere den Messwert
                    line = sensorfile.readline()
                    m = re.match(r"([0-9a-f]{2} ){9}t=([+-]?[0-9]+)", line)
                    if m:
                        # Berechne das Ergebnis
                        value = str(float(m.group(2)) / 1000.0)            
                        
                        print(f'{id} hat aktuell den Wert: {value} GrdC')
                        
        # Fehlermeldung sollte 1-Wire Sensor nicht lesbar sein
        except(IOError):
                print ("Error reading ", path)
                value = None
        
        return value



start = time.perf_counter()

sensor = OneWire()

print(sensor)

sensor.show_all_devices()


with concurrent.futures.ThreadPoolExecutor() as executor:
    
    results = [executor.submit(sensor.read_1w_sensor_ds18s20,i) for i in sensor.list_all_devices()]

    for f in concurrent.futures.as_completed(results):
        print(f.result())

  

finish = time.perf_counter()


print(f'Finished in {round(finish-start,2)} s')

# Bespiel für DS18S20 Sensor Filename
# 28-0121131907b3

# Beispiel aus dem w1_slave file
# 63 01 4b 46 7f ff 0c 10 d1 : crc=d1 YES
# 63 01 4b 46 7f ff 0c 10 d1 t=22187