Konfiguration der Messkan�le
==================================

Alle Messkan�le werden mittels der Datei :file:`config_channels.csv` konfiguriert. Diese dDatei wird eingelesen und mittels der Funktion :func:`~tatooine_data.helper.config_channels` und die Metadateen der Messkan�le im Array :mod:`~tatooine_data.aquire_data.AquireData.data_last_measured` gespeichert. Damit k�nnen alle Eigenschaften f�r jeden einzelnen Kanal wie folgt definiert werden.


Spalten des Konfigurationsfiles
--------------------------------

.. bibliographic fields (which also require a transform)::

:ID:                eindeutige ID mit der der Messkanal im python code identifiziert wird
:Name:              Name des Messkanals
:Description:       Beschreibung des Messkanals
:Unit:              Einheit des Messkanals
:Filter:            Anzahl der Werte aus der Historie, die zur Filterung (gleitender Mittelwert) herangezogen werden
:TickMax:           Anzahl der Schleifen (:mod:`~tatooine_data.aquire_data.AquireData._MAX_DATA_POINTS_HISTORY`) die standardm�ßig durchlaufen werden, bevor dieser Kanal abgespeichert wird
:TickFast:          Anzahl der Schleifen (:mod:`~tatooine_data.aquire_data.AquireData._MAX_DATA_POINTS_HISTORY`) die im hochaufl�senden  Modus durchlaufen werden, bevor dieser Kanal abgespeicher wird.
:Threshold_Abs:     Wenn der aktuelle Messwert mehr als dieser absolute Schwellwert vom Mittelwert der Historie abweicht, dann mir unabh�ngig vom Tick der Messwert und der vorherige Messwert abgespeichert.
:Threshold_Perc:    noch nicht implementiert




Aktive Messkan�le des TatooineMonitors
--------------------------------------


.. csv-table:: 
   :file:   /home/pi/TatooineMonitor/tatooine_monitor/config_channels.csv
   :widths: 20, 10, 10, 10, 10, 10, 10, 10, 10
   :header-rows: 1