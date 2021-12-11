
#Schnittstelle zur InfluxDB
from influxdb import InfluxDBClient
# Klasse für die Abspeicherung der Datenpinkte
from aquireData.datapoint import DataPoint


class StoreDataToInflux:
    
    
    _db_host = "127.0.0.1"
    _db_port = 8086
    _db_user = "admin"
    _db_password = "admin"
    _db_name = "database"
    
    client = None
    
    def __init__(self) -> None:
        
        
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
        
        print(self.client.ping())
    
        return False
    
    def store_data (self, current_data_list: list[DataPoint], tick):
        
        
        for chn in current_data_list:
        
            if (chn.storage_tick_counter >= chn.storage_tick_max or \
                chn.value_dev_abs > chn.thd_deviation_abs or \
                chn.value_dev_perc > chn.thd_deviation_per):
                
                tmp = chn.create_json_lastvalue('Signal3','tatooine')
        
                # Schreibe die Daten in die Datenbank
                self.client.write_points(tmp)        
                
                
                chn.storage_tick_counter = 0
            else:
                chn.storage_tick_counter += 1
        
        
        
        
        
    
    