#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Module zur Bearbeitung der Zeitstempel
from datetime import datetime
from pytz import timezone

# Modul für Datenklassen
from dataclasses import dataclass
from dataclasses import field

# Import Logging Modul
import logging

# Festlegen der Zeitzone für die Aufnahme der Messwerte und deren Zeitstempel
tz_berlin = timezone('Europe/Berlin')


@dataclass
class   DataPoint():
    """Datenpunkt Objekt welches alle Informationen eines Messpunktes enthält

    Das Objekt hält alle Informationen und Methoden die 
    notwendig sind einzelne Datenpunkte zu verwalten. Folgende features sind beinhaltet:
    
    * Speichern des Messwertes und des Zeitstempels
    * Abspeichern einer Historie von :mod:`~tatooine_data.aquire_data.AquireData._MAX_DATA_POINTS_HISTORY` Werten
    * Filterung
    * Berechnung Mittelwert der Historie und Abweichung dazu
    
    
    :return:    DatenpunktObjekt
    :rtype:     Object
    """    
    
    id: str='-'
    """ID des Messkanals zur Auswahl in den Measure-Methoden"""
    
    name: str = '-'
    """Name des Messkanals"""
    
    unit: str = '-'
    """Masseinheit des Messwertes"""
   
    filter_cnt: int = 4
    """der Wert gibt die Breite des gleitenden Mittelwertes an"""
    
    storage_tick_max: int = 20
    """Ticker Wert bei dem der Kanal gespeichert wird"""

    storage_tick_fast: int = 20
    """Ticker Wert bei dem der Kanal gespeichert wird"""
    
    thd_deviation_abs: float = 10
    """Absolute Abweichung des Messwertes, bei dem eine Speicherung unabhängig vom Tickerwert ausgelöst wird """
    
    thd_deviation_per: float = 5
    """Prozentuale Abweichung des Messwertes, bei dem eine Speicherung unabhängig vom Tickerwert ausgelöst wird """
        
    timestamp: float = 0
    """Zeitstempel des aktuellen Wertes"""
    
    value: float = 0
    """aktueller Wert inklusive aller Nachbearbeitungen"""

    value_raw: float = 0
    """aktuell erfasster Messwert Wert ohne Nachbearbeitungen"""
    
    value_mean: float = 0
    """Mittelwert der Historie"""
    
    value_dev_perc: float = 0
    """prozentuale Abweichung des Lestzen Messwertes vom Mittelwert der Historie"""
    
    value_dev_abs: float = 0
    """absolute Abweichung des letzten Messwertes vom Mittelwert der Historie"""

    storage_tick_counter: int = 0
    """Ticker der in jeder ZEitschleife hochgezählt und erst bei Speichern resetiert wird"""
    
    storage_prelim_hysterese: bool = True
    """Bei einer großen Abweichung wird auch der vorangegangene Wert mit abgespeichert, um das sprungevent Zeitlich auflösen zu können. Dies erfolgt aber nur einmalig zu Beginn, dazu wird dieses Bit dan auf True gesetzt und erst nach der nächsten Unterschreitung der Sprungerkennung resetiert"""
    
    act_val_stored_to_db: bool = False
    """Mit diesem Flag wird gekennzeichnet, dass der aktuell vorhandene Wert schon in der InfluxDB abgelegt wurde. So werden mehrfache unbenötigte Schreibzugriffe unterbunden."""
    
    history_length: int = 10
    """Anzahl der Werte die in der Historie gespeichert werden"""
        
    timestamp_history: list[float] = field(default_factory=list)
    """Historie am Zeitstempeln mit der Länge :mod:`~tatooine_data.aquire_data.AquireData._MAX_DATA_POINTS_HISTORY` """ 
    
    value_history: list[float] = field(default_factory=list)
    """Historie am Messwerten mit der Länge :mod:`~tatooine_data.aquire_data.AquireData._MAX_DATA_POINTS_HISTORY` """    
    
    # ============================================
    # Konfiguration des Logging
    # ============================================
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    logger.addHandler(logging.NullHandler())
    
    
    def update_value(self, new_value = float , new_timestamp = datetime):
        """Updaten des Messwertes in der Dataclass
        
        Es wird der neue Messwert und dessen Zeitstempel in der Klasse 
        abgespeichert, sowie anschließend alle neuen Statistikberechnungen
        durchgeführt.
        
        Folgende Schritte werden ausgeführt:
        
        1. Löschen des ältesten Wertes der Historie
        2. Filtern des aktuellen Wertes durch Mittelwertbildung mit den letzten :mod:`~tatooine_data.datapoint.DataPoint.filter_cnt` Werten der Historie.
        3. Speichern in der neuen Werte in der Historie :mod:`~tatooine_data.aquire_data.AquireData._MAX_DATA_POINTS_HISTORY`
        4. Berechnung des neuen Mittelwertes der Historie und der Abweichung des letzten Wertes von diesem Mittelwert

        :param new_value: neuer Messwert zum abspeichern
        :type new_value:  float
        :param new_timestamp:    Zeitstempel des neuen Messwertes 
        :type new_timestamp:  datetime
        """        
        
        #-----------------------------------------------------------------------
        # Ältesten Wert aus der Historie entfernen
        #-----------------------------------------------------------------------
        if len(self.value_history) >= self.history_length:
            del self.value_history[0]
            
        if len(self.timestamp_history) >= self.history_length:
            del self.timestamp_history[0]
                        
        #-----------------------------------------------------------------------
        # Nachbearbeitung (filtern) des aktuellen Messwertes
        #-----------------------------------------------------------------------
        self.value_raw = new_value
        if (len(self.value_history) >= self.filter_cnt) and \
            (self.filter_cnt > 1):
            # Berechnung des gleitenden Mittelwertes über lie letzten Messwerte
            self.value = (sum(self.value_history[(len(self.value_history) - \
                         self.filter_cnt + 1):]) + self.value_raw) / self.filter_cnt
            
        else:
            # Wenn noch keinen Historie vorhanden, dann wird der Rohwert 
            # übernommen
            self.value = new_value

        #-----------------------------------------------------------------------
        # Updaten der Werte und Historie
        #-----------------------------------------------------------------------
        self.value_history.append(self.value)
        self.timestamp_history.append(new_timestamp)
        self.timestamp = new_timestamp

        #-----------------------------------------------------------------------
        # Berechnung der Mittelwerte und aktuellen Abweichung für die gesamte
        # Historie
        #-----------------------------------------------------------------------
        if (len(self.value_history)>= (self.history_length)):
            mean = 0        
            for x in self.value_history:
                mean += x
                
            #Berechne die Statistikdaten
            self.value_mean = mean / len(self.value_history)
            self.value_dev_abs = abs(self.value_mean - self.value)
            if self.value_mean == 0:
                self.value_dev_perc = float(0)
            else:
                self.value_dev_perc = float(self.value_dev_abs / self.value_mean 
                                            *100)
        else:
            # Sonderfall nach Einschalten der Messung
            self.value_mean = self.value
            self.value_dev_abs = float(0)
            self.value_dev_perc = float(0)
            
        # Vermerken, das ein neuer Wert vorliegt    
        self.act_val_stored_to_db = False
        
        
    def print_data_line(self):
        """ Print Funktion zur Darstellung des Messwertes und der Statistik in
            einer Linie.
            
            Bsp: 
            GYRO_X                 4.44  dps               4.474  dps               0.039  dps            0.8702 %
        """        
        print('{0:15s}  {1:10.2f}{5:>5s} {2:10.3f}{5:>5s} {3:10.3f}{5:>5s} {4:9.4f} %'.format(\
            self.name, self.value, self.value_mean, self.value_dev_abs, self.value_dev_perc, self.unit))
    
    def print_header():
        """ Print Funktion zur Darstellung eines Headers für die Zeilendarstellung 
            der Messwerte
        """        
        
        print(chr(27) + "[2J")
        print('Channel               Value            Mean                  Deviation  ')     
        print('================================================================================')


    def create_json_for_influxDB(self,measurement = 'signal', location = 'tag',\
        number_of_points = int(1) ):
        """Erstellen eines JSON Strings zur Abspeicherung der Daten in influxDB
        
        Mit der Funktion werden alle relevanten Werte so in einen JSON Objekt
        zusammengestellt, dass sie direkt in InfluxDB geschrieben werden können. Über den Parameter 'number_of_points' kann die Anzahl der ausgegeben Datensätze bestimmt werden.
        
        - number_of_points = 1 ... nur der aktuelle, letzte Wert wird ausgegeben
        - number_of_points = 2 ... es wird zusätzlich der vorletzte Wert aus der Historie ausgegeben
                
        :param measurement: Name des Measurement, defaults to 'Signal'
        :type measurement:  str, optional
        :param location:    Name das Location Tags, defaults to 'tag'
        :type location:     str, optional
        :param number_of_points:    Anzahl der Datenpunkte in der JSON Liste,   
                                    defaults to 1
        :type number_of_points:     int, optional 
        
        :return:    Ein JSON Eintrag der direkt in InfluxDB 
                    geschrieben werden kann
        :rtype: List[JSON]]
        """        
        
        #Liste mit JSON Objekten
        json_data = []        
        
        # Erzeuge JSON Datenstruktur passend zu InfluxDB für den vorletzten
        # Messwert
        if ((number_of_points == 2) and (len(self.value_history) > 1)):
            
            #Berechnung aller Werte des vorletzten Messpunktes aus der Historie
            timestamp = self.timestamp_history[len(self.timestamp_history)-2]
            penultimate_val = self.value_history[len(self.value_history)-2]
            
            #Berechnung der Statistik des vorletzten Messpunktes 
            penultimate_dev_abs = abs(self.value_mean - penultimate_val)
            if self.value_mean == 0:
                penultimate_dev_perc = float(0)
            else:
                penultimate_dev_perc = float(penultimate_dev_abs / \
                    self.value_mean * 100)
            
            #Erstellung des JSON
            json_data += [
            {
                "measurement": measurement,
                    "tags": {
                        "location": location,
                    },
                    "time": datetime.fromtimestamp(timestamp,tz_berlin),
                    "fields": {
                        self.name:      float(penultimate_val),
                        self.name + "_raw":    float(penultimate_val),
                        self.name + "_dev_abs":    float(penultimate_dev_abs),
                        self.name + "_dev_perc":   float(penultimate_dev_perc),
                        self.name + "_value_mean": float(self.value_mean)
                    }
                }
            ]
            
            self.logger.debug(f"Doppelabspeicherung von {self.name}")
       
        # Erzeuge JSON Datenstruktur passend zu InfluxDB für den aktuellen 
        # Messwert
        json_data += [
        {
          "measurement": measurement,
              "tags": {
                  "location": location,
              },
              "time": datetime.fromtimestamp(self.timestamp,tz_berlin),
              "fields": {
                  self.name:      float(self.value),
                  self.name + "_raw":       float(self.value_raw),
                  self.name + "_dev_abs":    float(self.value_dev_abs),
                  self.name + "_dev_perc":   float(self.value_dev_perc),
                  self.name + "_value_mean": float(self.value_mean)
              }
          }
        ]
        
        
        return json_data

