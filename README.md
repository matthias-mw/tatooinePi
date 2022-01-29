# tatooinePi
Raspberry Pi on SV Tatooine
---------------------------
Ziel des Projektes ist es einen Überwachung einer Segelyacht aus der Ferne zu gewährleisten.

Dazu sollen folgende Features implemetiert werden:

1. Aufzeichnung wichtiger Yachtdaten

* Messen von Spannungen (ServiceBat, BowthrusterBat, StarterBat)
  - I2C ADS1115

* Messen der Stromaufnahme (IT-System)
  - I2C INA219

* Messen von Temperaturen (Batterie)
  - 1Wire DS18S20

* Messen der Beschleunigungen und Lagewinkel
  - I2C MPU6050

* Messen der Luftfeuchte und des Luftdrucks (Kabine)
  - I2C BMP280
  
2. Speichern dieser Daten in einer InfluxDB


3. Ermöglichen des externen Zugriffes auf diese Daten

4. Installation einer Überwachungskamera
