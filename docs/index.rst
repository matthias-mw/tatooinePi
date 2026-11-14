
Welcome to Tatooine Monitor's documentation!
============================================

Tatooine Monitor ist ein Projekt zur Überwachung der Segelyacht Tatooine. folgende Funktionalitäten sind umgesetzt:

**1. Aufzeichnen von relevanten Messdaten**
   Messdaten werden mit speziellen Sensoren (I2C, 1-Wire, GPIO) erfasst, gefiltert und in einer InfluxDB (V2 API) gespeichert. Der externe Zugriff erfolgt über die InfluxDB.

**2. Alarmierung basierend auf Messdaten**
   Grenzwertverletzungen (konfigurierbar in :file:`config_alerts.csv`, inkl. Hysterese) lösen Alarm-E-Mails über SMTP aus (Debouncing, Tageslimit).

**3. Zwei Systeme (Live / Simu)**
   Über ``-c/--config`` wählbar: ``monitor_live.conf`` (Bucket ``sensors``) und ``monitor_simu.conf`` (Bucket ``sensors_simu``). Zugangsdaten liegen in einer ``.env`` neben der jeweiligen conf.

**Geplant:** Integration in SignalK/OpenPlotter, Überwachung des Speicherplatzes der Überwachungskamera inkl. Warnung.


Inhalt
============================================

:doc:`config_channels` 
   Konfiguration aller gemessen Kanäle.

:doc:`tatooine_data`
    In diesem Package sind alle Module zu Erfassung, Berechnung und Speicherung von den Messdaten des TatooineMonitor enthalten.

:doc:`tatooine_notify`
    In diesem Package sind alle Module zum Benachrichtigungs- und Alarmsystem von den Messdaten des TatooineMonitor enthalten.

:doc:`driver`
    In diesem Package sind alle Module (Treiber) integriert, welche zur Gewinnung von Messdaten des TatooineMonitors benötigt werden.




.. toctree::
   :maxdepth: 3
   :hidden:

   config_channels
   tatooine_data
   tatooine_notify
   driver




Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
