import time
import sys

from influxdb import InfluxDBClient
from datetime import datetime

# Konfiguration der InfluxDatenbank
host = "192.168.1.45"   # IP der Datenbank
port = 8086             # default port
user = "admin"          # the user/password created for influxdb
password = "tatooinedb" 
dbname = "sensors"      # name der Datenbank



interval = 0.1  # Festlegen des Schreibintervall

# Create the InfluxDB client object
client = InfluxDBClient(host, port, user, password, dbname)

# Abfrage der Databases in influxdb
# client.get_list_database()


# Beispielsignal
measurement = "test_Signal"
test=0

# Endlosschleife
try:
    while True:
        # Messwert erfassen
        test = test+5
        isoTime = datetime.now()
        
        # Erzeuge JSON Datenstruktur passend zu InfluxDB
        data = [
        {
          "measurement": measurement,
              "tags": {
                  "location": "tatooine",
              },
              "time": isoTime,
              "fields": {
                  "test1" : test,
                  "test2" : test*test
              }
          }
        ]
        # Schreibe die Daten in die Datenbank
        client.write_points(data)
        
        # Print for debugging
        print("[%s] Test1: %s, Test2: %s" % (isoTime, test, 2*test)) 
        
        
        # Warte auf den Intervall....
        time.sleep(interval)
 
except KeyboardInterrupt:
    pass