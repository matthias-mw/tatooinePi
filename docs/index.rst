
Welcome to Tatooine Monitor's documentation!
============================================

Tatooine Monitor ist ein Projekt zur Überwachung der Segelyacht Tatooine. Dazu sind folgende grundlegenden Funktionalitäten angedacht:

**1. Aufzeichen von relevanten Messdaten**
   Relevante Messdaten sollen mit speziellen Sensoren erfasst, aufbereitet und aufgezeichnet werden. Die Speicherung erfolgt in einer InfluxDB auf die dann über das Netz zugegriffen werden kann.

**2. Auslösen von Events basierend auf Messdaten**
   .. todo::
      Auf der Basis der Messdaten sollen Berichte und alarme versendet werden

**Folgende weitere Funktionen können in der Zukunft folgen.**
   Integration in SignalK, Open Plotter, tbd...


Inhalt
============================================

:doc:`config_channels` 
   Konfiguration aller gemessen Kanäle.

:doc:`tatooine_data`
    In diesem Package sind alle Module zu Erfassung, Berechnung und Speicherung von den Messdaten  des TatooineMonitor enthalten.
:doc:`driver`
    In diesem Package sind alle Module (Treiber) integriert, welche zur Gewinnung von Messdaten des TatooineMonitors benötigt werden.




.. toctree::
   :maxdepth: 3
   :hidden:

   config_channels
   tatooine_data
   driver




Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
