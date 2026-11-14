Tatooine Monitor
================

Der **Tatooine Monitor** überwacht die Segelyacht *SV Tatooine* aus der Ferne.
Ein Raspberry Pi auf dem Boot erfasst laufend Messdaten, speichert sie in einer
lokalen InfluxDB und versendet bei Grenzwertverletzungen Alarm-E-Mails.

Funktionsumfang
---------------

**1. Messdatenerfassung**
   Die Messdaten werden mit verschiedenen Sensoren über I2C, 1-Wire und GPIO
   erfasst, gefiltert (gleitender Mittelwert) und in einer InfluxDB (V2 API)
   gespeichert. Der externe Zugriff auf die Daten erfolgt über die InfluxDB
   (z. B. Grafana).

**2. Alarmierung basierend auf den Messdaten**
   Grenzwertverletzungen — konfigurierbar in :file:`config_alerts.csv` inklusive
   Hysterese — lösen Alarm-E-Mails über SMTP aus. Debouncing und ein Tageslimit
   verhindern Mail-Fluten bei Störungen.

**3. Zwei Systeme (Live / Simu) in getrennten conf-Verzeichnissen**
   Über das Argument ``-c/--config`` ist wählbar: :file:`monitor_live.conf`
   (Bucket ``sensors``, Location-Tag ``tatooine``) und
   :file:`simu/monitor_simu.conf` (Bucket ``sensors_simu``, Location-Tag
   ``tatooine-simu``, Developer Mode aktiv). Jedes System hat sein eigenes
   Verzeichnis mit eigenen :file:`config_channels.csv`, :file:`config_alerts.csv`
   und :file:`.env` — das Simu-System kann also z. B. andere DS18S20-Sensoren
   konfigurieren. Details in :doc:`konfiguration`.

Gemessene Größen
----------------

.. list-table::
   :header-rows: 1

   * - Messgröße
     - Sensor
     - Bus
   * - Batteriespannungen (Service 12 V, Bugstrahlruder 24 V, Starter 12 V, Aux 1/2)
     - ADS1115 (16-Bit-ADC, 4 Kanäle)
     - I2C (Adresse ``0x48``)
   * - Stromaufnahme und Leistung des IT-Systems
     - INA219 (Shunt 0,1 Ohm)
     - I2C (Adresse ``0x40``)
   * - Beschleunigung (X/Y/Z), Drehraten (X/Y/Z), Chip-Temperatur
     - MPU6050
     - I2C (Adresse ``0x68``)
   * - Lufttemperatur und Luftdruck
     - BMP280
     - I2C
   * - Temperaturen (z. B. Batterien), je Sensor über die 1-Wire-ID als Kanal
     - DS18S20
     - 1-Wire (``/sys/bus/w1/devices``)
   * - Digitale Eingänge (BCM 14, 15, 17, 18, 27)
     - GPIO
     - GPIO

**Geplant:** Integration in SignalK/OpenPlotter, Überwachung des Speicherplatzes
der Überwachungskamera inklusive Warnung bei Knappheit.

Inhalt
------

.. toctree::
   :maxdepth: 2

   installation
   betrieb
   konfiguration
   architektur
   hardware
   tatooine_data
   alerting
   driver


Indices und Tabellen
====================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
