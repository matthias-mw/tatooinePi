from datetime import datetime
from pytz import timezone
from dataclasses import dataclass
from dataclasses import field

tz_berlin = timezone('Europe/Berlin')


@dataclass
class   DataPoint():
    """Datenpunkt Objekt welches alle Informationen eines Messpunktes enthält

    Das Objekt :class 'DataPoint' hält alle Informationen und Methoden die 
    notwendig sind einzelne Datenpunkte zu verwalten. Folgende features sind beinhaltet:
    
    * Speichern des Messwertes und des Zeitstempels
    * Abspeichern einer Historie von x Werten
    * Filterung
    * Berechnung Mittelwert der Historie und Abweichung dazu
    
    
    :return:    DatenpunktObjekt
    :rtype:     Object
    """    
    
    name: str = '-'
    unit: str = '-'
    timestamp: float = 0
    value: float = 0
    interval_std: float = 10
    interval_fast: float   = 0.1
    thd_deviation_abs: float = 10
    thd_deviation_per: float = 5
    value_mean: float = 0
    value_dev_perc: float = 0
    value_dev_abs: float = 0
    history_length: int = 10
    timestamp_history: list[float] = field(default_factory=list)
    value_history: list[float] = field(default_factory=list)
    
    
    
    def update_value(self, new_value, new_timestamp):
        """Updaten des Messwertes in der Dataclass
        
        Es wird der neue Messwert und dessen Zeitstempel in der Klasse 
        abgespeichert, sowie anschließend alle neuen Statistikberechnungen
        durchgeführt.

        :param new_value        neuer Messwert zum abspeichern
        :type:                  float
        :param new_timestamp    Zeitstempel des neuen Messwertes 
        :type:                  datetime
        """        
        
        #----------------------------------------------------------------------------
        # Ältesten Wert aus der Historie entfernen
        #----------------------------------------------------------------------------        
        if len(self.value_history) >= self.history_length:
            del self.value_history[0]
            
        if len(self.timestamp_history) >= self.history_length:
            del self.timestamp_history[0]
        
        #----------------------------------------------------------------------------
        # Updaten der Werte und Historie
        #----------------------------------------------------------------------------        
        self.value_history.append(new_value)
        self.value = new_value
        self.timestamp_history.append(new_timestamp)
        self.timestamp = new_timestamp
        
        #----------------------------------------------------------------------------
        # Berechnung der Mittelwerte und aktuellen Abweichung für die gesamte Historie
        #----------------------------------------------------------------------------        
        mean = 0        
        for x in self.value_history:
            mean += x
               
        #Berechne die Statistikdaten
        self.value_mean = mean / len(self.value_history)
        self.value_dev_abs = abs(self.value_mean - self.value)
        if self.value_mean == 0:
            self.value_dev_perc = float(0)
        else:
            self.value_dev_perc = float(self.value_dev_abs / self.value_mean *100)
        
        
    def print_data_line(self):
        """ Print Funktion zur Darstellung des Messwertes und der Statistik in
            einer Linie.
            
            Bsp: 
            GYRO_X                 4.44  dps      4.474  dps      0.039  dps    0.8702 %
        """        
        print('{0:15s}  {1:10.2f}{5:>5s} {2:10.3f}{5:>5s} {3:10.3f}{5:>5s} {4:9.4f} %'.format(self.name,self.value, self.value_mean, self.value_dev_abs, self.value_dev_perc, self.unit))             
    
    def print_header():
        """ Print Funktion zur Darstellung eines Headers für die Zeilendarstellung 
            der MEsswerte
        """        
        
        print(chr(27) + "[2J")
        print('Channel               Value            Mean                  Deviation  ')     
        print('================================================================================')


    def create_json_lastvalue(self,measurement = 'signal', location = 'tag'):
        """Erstellen eines JSON Strings zur Abspeicherung der Daten in influxDB
        
        Mit der Funktion werden alle relevanten Werte so in einen JSON Objekt
        zusammengestellt, das sie direkt in InfluxDB geschrieben werden können.

        :param measurement: Name des Measurement, defaults to 'Signal'
        :type measurement:  str, optional
        :param location:    Name das Location Tags, defaults to 'tag'
        :type location:     str, optional
        :return:    Ein JSON Eintrag der direkt in InfluxDB 
                    geschrieben werden kann
        :rtype: List[JSON]]
        """        
        # Erzeuge JSON Datenstruktur passend zu InfluxDB
        json_data = [
        {
          "measurement": measurement,
              "tags": {
                  "location": location,
              },
              "time": datetime.fromtimestamp(self.timestamp,tz_berlin),
              "fields": {
                  self.name:      self.value,
                  self.name + "_dev_abs":    self.value_dev_abs,
                  self.name + "_dev_perc":   self.value_dev_perc,
                  self.name + "_value_mean": self.value_mean
              }
          }
        ]
        
        return json_data

