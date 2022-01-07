# tatooinePi
Raspberry Pi on SV Tatooine
---------------------------
Ziel des Projektes ist es einen �berwachung einer Segelyyacht aus der Ferne zu gew�hrleisten.

Dazu sollen folgende Features implemetiert werden:

1. Aufzeichnung wichtiger Yachtdaten

* Messen von Spannungen (ServiceBat, BowthrusterBat, StarterBat)
  - I2C ADS1115

* Messen der Stromaufnahme (IT-System)
  - I2C INA219

* Messen von Temperaturen (Batterie)
  - 1Wire DS18S20


* Messer der Luftfeuchte (Kabine)
  
  
2. Speichern dieser Daten in einer InluxDB


3. Erm�glichen des externen Zugriffes auf diese Daten

4. Installation einer �berwachungskamera
