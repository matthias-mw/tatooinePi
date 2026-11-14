#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#Schnittstelle zur InfluxDB
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS

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
    _measurement_name = 'Signal'
    """Name des Measurements in der InfluxDB"""
    _tag_location = 'tatooine'
    """Wert des Tags 'location' in der InfluxDB"""
    
    client = None
    """Object des InfluxDB Clients"""
    
    def __init__(self, host = str("127.0.0.1"), port = int(8086), \
        token = str(""), org = str(""), bucket = str("sensors"), \
        _measurement_name = 'Signal', _tag_location = 'tatooine', \
        developer_mode = False) -> None:
        """Initialisierung der Verbindung zu InfluxDB
        
        Es wird ein Client zur InfluxDB angelegt. Die Verbindung erfolgt über
        die InfluxDB V2 API (Token-basiert).

        :param host:        Hostname der InfluxDB, defaults to "127.0.0.1"
        :type host:         str, optional
        :param port:        Port der InfluxDB, defaults to 8086
        :type port:         int, optional
        :param token:       InfluxDB V2 API Token, defaults to ""
        :type token:        str, optional
        :param org:         InfluxDB V2 Organisation, defaults to ""
        :type org:          str, optional
        :param bucket:      InfluxDB V2 Bucket, defaults to "sensors"
        :type bucket:       str, optional
        :param _measurement_name: Name des Measurements, defaults to 'Signal'
        :type _measurement_name:  str, optional
        :param _tag_location:     Wert des Location Tags, defaults to 'tatooine'
        :type _tag_location:      str, optional
        :param developer_mode:    Wenn True, werden zusatzliche Debug-Felder
                                  (_raw, _dev_abs, _dev_perc, _value_mean)
                                  in InfluxDB gespeichert. Defaults to False.
        :type developer_mode:     bool, optional
        
        """
        
        # Konfiguration der InfluxDB
        self._db_host = host        # IP der Datenbank
        self._db_port = port        # Port
        self._measurement_name = _measurement_name
        self._tag_location = _tag_location
        self._db_token = token      # InfluxDB V2 API Token
        self._db_org = org          # InfluxDB V2 Organisation
        self._bucket = bucket      # InfluxDB V2 Bucket
        self._developer_mode = developer_mode  # Debug-Felder speichern?

        # InfluxDB Client mit V2 API (Token-basiert)
        url = f"http://{self._db_host}:{self._db_port}"
        self.client = InfluxDBClient(url=url, token=self._db_token, org=self._db_org)
        # write_api einmalig anlegen (SYNCHRONOUS) und wiederverwenden
        self.write_api = self.client.write_api(write_options=SYNCHRONOUS)

        # ============================================
        # Konfiguration des Logging
        # ============================================
        self.logger = logging.getLogger(__name__)
        self.logger.addHandler(logging.NullHandler())
    
    def check_db_connection(self) -> bool:
        """Prüft die Verbindung zur InfluxDB per ping

        :return: True wenn die Datenbank erreichbar ist, sonst False
        :rtype: bool
        """
        try:
            ok = bool(self.client.ping())
        except Exception as e:
            self.logger.error(f"InfluxDB nicht erreichbar ({self._db_host}:{self._db_port}): {e}")
            return False

        if ok:
            self.logger.info(f"InfluxDB {self._db_host}:{self._db_port} erreichbar (ping OK)")
        else:
            self.logger.error(f"InfluxDB {self._db_host}:{self._db_port} antwortet nicht auf ping")
        return ok
    
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
                    self._measurement_name, self._tag_location, 2, \
                    self._developer_mode)
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
                    self._measurement_name, self._tag_location, 1, \
                    self._developer_mode)
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
            # self.client.write_points(json_list) 

        
            # Schreibzugriff abgesichert: ein Fehler (z.B. DB im laufenden
            # Betrieb ausgefallen) darf die Hauptschleife nicht killen
            try:
                self.write_api.write(bucket=self._bucket, record=json_list)
                self.logger.debug(f"{len(json_list)} Datenpunkte in InfluxDB geschrieben")
            except Exception as e:
                self.logger.error(f"Fehler beim Schreiben in die InfluxDB: {e}")
    
    
