
#Schnittstelle zur InfluxDB
from influxdb import InfluxDBClient
# Klasse für die Abspeicherung der Datenpinkte
from aquireData.datapoint import DataPoint


class StoreDataToInflux:
    
    
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
    
    _MEASUREMENT_NAME = 'Signal3'
    """Name des Mesurements in der InfluxDB"""
    _TAG_LOCATION = 'tatooine'
    """Wert des Tags 'location' in der InfluxDB"""
    
    
    client = None
    """Object des InfluxDB Clients"""
    
    def __init__(self) -> None:
        
        
        #TODO Initialisierung
        
        # Konfiguration der InfluxDatenbank
        self._db_host = "192.168.1.45"   # IP der Datenbank
        self._db_port = 8086             # default port
        self._db_user = "admin"          # the user/password created for
                                         # influxdb
        self._db_password = "tatooinedb" 
        self._db_name = "sensors"      # name der Datenbank
    

        # Create the InfluxDB client object
        self.client = InfluxDBClient(self._db_host, self._db_port,
                                      self._db_user, self._db_password, 
                                      self._db_name)   
    
    def check_db_connection(self):
        """Checken der Connection zur Datenbank

        Die Datenbank wird angesprochen. Im Falle einer ertablierten Verbindung wird die Versionnummer der DatenBank ausgegeben.
        
        ToDo: Handle Fehlverhalten wenn DB nicht erreichbar!
        
        :return: Datenbank erfolgreich verbunden
        :rtype: bool
        """
        
        print("Host: {0:s}:{1:d}  -> InfluxDB Version: {2:s}  erfolgreich "\
            "verbunden".format(self._db_host,self._db_port,self.client.ping()))
    
        return True
    
    def store_data (self, current_data_list: list[DataPoint]):
        """Abspeicherung der Messdaten in der InfluxDB Datenbank
        
        Es werden alle Datenunkte, welche in der Liste 'current_data_list' 
        enthalten sind, in die InfluxDB gespeichert. Die Speicherung erfolgt 
        wenn:
        
        - die Anzahl Schleifen größer dem "TickMax" des Messkanals ist
        - die Abweichung des letzten Messwertes größer "Threshold_Abs" ist
        - ....

        Im Falle der Speicherung wird zunächst durch 
        :func: 'datapoint.create_json_lastvalue' eine JSON Objekt erzeugt und
        dann Kanal für Kanal in einen Liste von JSON Objekten überführt. Anschließend wird diese Liste an die InfluxDB gesendet.

        :param current_data_list: [description]
        :type current_data_list: list[DataPoint]
        :param tick: [description]
        :type tick: [type]
        """
        
        #Liste von JSON Dictonaries die in InfluxDB geschrieben wir
        json_list = []
        
        #Für jeden Kanal überprüfen, ob er geschrieben werden muss
        for chn in current_data_list:
        
            #Wenn der Wert sich stark geändert hat
            if (chn.value_dev_abs > chn.thd_deviation_abs):

                #das JSON des aktuellen Kanals anhängen        
                json_list  += chn.create_json_lastvalue( \
                    self._MEASUREMENT_NAME,self._TAG_LOCATION)
                #den Counter für das Abspeichern zurücksetzen
                chn.storage_tick_counter = 0            
            
            elif (chn.storage_tick_counter >= chn.storage_tick_max):
                
                #das JSON des aktuellen Kanals anhängen        
                json_list  += chn.create_json_lastvalue( \
                    self._MEASUREMENT_NAME, self._TAG_LOCATION)
                #den Counter für das Abspeichern zurücksetzen
                chn.storage_tick_counter = 0
                
            else:
                chn.storage_tick_counter += 1
        
        # Schreibe die Daten in die Datenbank
        self.client.write_points(json_list)    
        
        
        
    
    