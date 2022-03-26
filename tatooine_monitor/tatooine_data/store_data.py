#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#Schnittstelle zur InfluxDB
from influxdb import InfluxDBClient
# Klasse für die Abspeicherung der Datenpinkte
from .datapoint import DataPoint

# Import Logging Modul
import logging

class StoreDataToInflux:
    """Klasse zur Abspeicherung der Messdaten in einer InfluxDB
    
    In dieser Klasse sind alle HighLevel Methoden angelegt, welche
    zur Speicherung von Messdaten in der InfluxDB benötigt werden.
    
    """
    
    _db_host = "127.0.0.1"
    """Hostadresse der InfluxDB"""
    _db_port = 8086
    """Port der InfluxDB auf dem Host '_db_host' """
    _db_user = "admin"
    """Username zum einloggen an der InfluxDB"""
    _db_password = "admin"
    """Passwort zum einloggen an der InfluxDB"""
    _db_name = "database"
    """Name der Datenbank die verwendet werden soll"""
    
    _measurement_name = 'Signal'
    """Name des Mesurements in der InfluxDB"""
    _tag_location = 'tatooine'
    """Wert des Tags 'location' in der InfluxDB"""
    
    client = None
    """Object des InfluxDB Clients"""
    
    def __init__(self,host = str ("127.0.0.1"), port = int (8086), user = \
        str("admin"), password = str("admin"), db_name = "sensors" , \
            _measurement_name = 'Signal', _tag_location = 'tatooine') -> None:
        """Initialisierung des Verbindung zu InfluxDB
        
        Es wird ein Client zur InfluxDB angelegt.

        :param host:    Hostname der InfluxDB, defaults to str("127.0.0.1")
        :type host:     str, optional
        :param port:    Port der InfluxDB, defaults to int(8086)
        :type port:     int, optional
        :param user:    user der angemeldet werden soll, defaults to "admin"
        :type user:     str, optional
        :param password:    Passwort, defaults to "admin"
        :type password:     str, optional
        :param db_name:     Name der Datenbank, defaults to "sensors"
        :type db_name:      str, optional
        
        """
        
        # Konfiguration der InfluxDatenbank
        self._db_host = host        # IP der Datenbank
        self._db_port = port        # default port
        self._db_user = user        # the user/password created for influxdb
        self._db_password = password 
        self._db_name = db_name     # name der Datenbank
        self._measurement_name = _measurement_name
        self._tag_location = _tag_location

        # Create the InfluxDB client object
        self.client = InfluxDBClient(self._db_host, self._db_port,
                                      self._db_user, self._db_password, 
                                      self._db_name)   
        
        # ============================================
        # Konfiguration des Logging
        # ============================================
        self.logger = logging.getLogger(__name__)
        self.logger.addHandler(logging.NullHandler())
    
    def check_db_connection(self):
        """Checken der Connection zur Datenbank

        Die Datenbank wird angesprochen. Im Falle einer ertablierten Verbindung wird die Versionnummer der DatenBank ausgegeben.
        
        ToDo: Handle Fehlverhalten wenn DB nicht erreichbar!
        
        :return: Datenbank erfolgreich verbunden
        :rtype: bool
        """
        
        print("Host: {0:s}:{1:s}  -> InfluxDB Version: {2:s}  erfolgreich "\
            "verbunden".format(self._db_host,self._db_port,self.client.ping()))
    
        return True
    
    def store_data (self, current_data_list: list[DataPoint]) -> None:
        """Abspeicherung der Messdaten in der InfluxDB Datenbank
        
        Es werden alle Datenunkte, welche in der Liste 'current_data_list' 
        enthalten sind, in die InfluxDB gespeichert. Die Speicherung erfolgt 
        wenn:
        
        - die Anzahl Schleifen größer dem :mod:`~tatooine_data.datapoint.DataPoint.storage_tick_max` des Messkanals ist
        - die Abweichung des letzten Messwertes größer :mod:`~tatooine_data.datapoint.DataPoint.thd_deviation_abs` ist
  

        Im Falle der Speicherung wird zunächst durch 
        :func:`~tatooine_data.datapoint.DataPoint.create_json_for_influxDB` ein JSON Objekt erzeugt und dann Kanal für Kanal in eine Liste von JSON Objekten überführt. Anschließend wird diese Liste an die InfluxDB gesendet.

        :param current_data_list: Liste mit den aktuellen Messwerten
        :type current_data_list: list[DataPoint]
        """
        
        #Liste von JSON Dictonaries die in InfluxDB geschrieben wir
        json_list = []
        
        #für jeden Kanal überprüfen, ob er geschrieben werden muss
        for chn in current_data_list:
            
            # Wenn der Wert sich erstmalig stark geändert hat
            if (chn.value_dev_abs > chn.thd_deviation_abs) and \
                not(chn.storage_prelim_hysterese):

                # das JSON des aktuellen Kanals inkl. vorletztem Wert anhängen 
                json_list  += chn.create_json_for_influxDB( \
                    self._measurement_name,self._tag_location, 2)
                # den Counter für das Abspeichern zurücksetzen
                chn.storage_tick_counter = 0  
                
                # die Sprungerkennung abspeichern
                self.logger.debug(f"Sprung erkannt auf {chn.name} -> aktueller Wert: {chn.value:3.2f} {chn.unit}")
                
                chn.storage_prelim_hysterese = True
                chn.act_val_stored_to_db = True

            # Wenn der die max Anzahl von Zyklen ohne Speicherung abgelaufen ist
            elif (chn.storage_tick_counter >= chn.storage_tick_max) or \
                (chn.value_dev_abs > chn.thd_deviation_abs):
                
                # das JSON des aktuellen Kanals anhängen        
                json_list  += chn.create_json_for_influxDB( \
                    self._measurement_name, self._tag_location, 1)
                # den Counter für das Abspeichern zurücksetzen
                chn.storage_tick_counter = 0
                chn.act_val_stored_to_db = True
            

            # keine Speicherung in diesem Zyklus und Zykluscounter hochzählen
            else:
                chn.storage_tick_counter += 1
            
            if (chn.storage_prelim_hysterese and (chn.value_dev_abs < chn.thd_deviation_abs)):
                # die Sprungerkennung zurücksetzen
                chn.storage_prelim_hysterese = False

        if len(json_list) > 0:      
            # Schreibe die Daten in die Datenbank
            self.client.write_points(json_list) 

        
        
        
    
    
