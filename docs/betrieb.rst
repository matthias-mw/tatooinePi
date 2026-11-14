Programmstart und Betrieb
=========================

Start des Programms
-------------------

.. code-block:: console

   $ cd /opt/tatooinePi/tatooine_monitor
   $ ./venv-monitor/bin/python tatooine_monitor.py [Optionen]

Kommandozeilenoptionen
----------------------

.. list-table::
   :header-rows: 1

   * - Option
     - Wirkung
   * - ``-c``, ``--config <datei>``
     - Konfigurationsdatei auswählen (Default: ``/opt/tatooinePi/tatooine_monitor/monitor_live.conf``)
   * - ``-t``, ``--testemail``
     - Test-Alarm-E-Mail über den SMTP-Pfad versenden und das Programm beenden
   * - ``-v``, ``--version``
     - Programmversion anzeigen und beenden
   * - ``-d``, ``--debug``
     - Debug-Logging aktivieren (überschreibt ``LOG_LEVEL`` der conf)
   * - ``-s``, ``--show``
     - Live-Ausgabe der aktuellen Messwerte auf stdout (Tabelle mit Wert, Mittelwert und Abweichung)

Wird eine angegebene conf-Datei nicht gefunden oder kann nicht geparst werden,
bricht das Programm mit einer Fehlermeldung und Exit-Code 1 ab. Gleiches gilt,
wenn ein Secret (z. B. ``INFLUXDB_TOKEN``) weder in der Umgebung/``.env`` noch
in der conf steht.

Live- und Simu-System
---------------------

Über ``-c/--config`` werden zwei unabhängige Konfigurationen betrieben:

.. list-table::
   :header-rows: 1

   * - conf-Datei
     - System
     - InfluxDB-Bucket
     - Location-Tag
     - Developer Mode
   * - :file:`monitor_live.conf`
     - LIVE (Default, systemd)
     - ``sensors``
     - ``tatooine``
     - ``false``
   * - :file:`monitor_simu.conf`
     - Simu / Weiterentwicklung (manueller Start)
     - ``sensors_simu``
     - ``tatooine-simu``
     - ``true``

.. code-block:: console

   $ # LIVE-System (Default, Argument kann weggelassen werden)
   $ ./venv-monitor/bin/python tatooine_monitor.py
   $ # Simu-System
   $ ./venv-monitor/bin/python tatooine_monitor.py -c monitor_simu.conf -s

Die CSV-Konfigurationen (:file:`config_channels.csv`, :file:`config_alerts.csv`)
und die :file:`.env` werden aus dem Verzeichnis der gewählten conf gelesen —
beide Systeme können also eigene Dateien in ihrem Verzeichnis liegen haben.

Ablauf der Hauptschleife
------------------------

Die Main Loop in :func:`tatooine_monitor.main` läuft mit einer Zykluszeit von
**250 ms** (:data:`tatooine_monitor.MAIN_LOOP_LENGHT_MS`):

1. I2C-Sensoren messen (jeder Zyklus, :func:`~tatooine_data.aquire_data.AquireData.aquire_data_i2c`:
   INA219, ADS1115, MPU6050, GPIO)
2. Langsame I2C-Sensoren messen (alle 10 Zyklen = 2,5 s,
   :func:`~tatooine_data.aquire_data.AquireData.aquire_data_i2c_slow`: BMP280)
3. 1-Wire-Sensoren messen (alle 10 Zyklen,
   :func:`~tatooine_data.aquire_data.AquireData.aquire_data_1wire`: DS18S20)
4. Messdaten in die InfluxDB schreiben
   (:func:`~tatooine_data.store_data.StoreDataToInflux.store_data`)
5. Alarme berechnen und verarbeiten
   (:func:`~tatooine_data.alert_service.Alerting.calc_alerts` und
   :func:`~tatooine_data.alert_service.Alerting.process_alerts`) — erst nach
   einer Startup-Verzögerung von 20 Zyklen (5 s), damit keine Fehlalarme
   direkt nach dem Start verschickt werden

Die Messungen laufen in eigenen Threads (``ThreadPoolExecutor``), damit ein
langsamer Sensor (z. B. 1-Wire) die Hauptschleife nicht aufhält. Exceptions in
den Threads werden protokolliert und beenden das Programm nicht. Details siehe
:doc:`architektur`.

Datenablage in der InfluxDB
---------------------------

* Alle Messwerte werden als Points im konfigurierten **Bucket** unter dem
  **Measurement** (``TatooineRemote``, ``[InfluxDB] MEASUREMENT``) mit dem Tag
  ``location=<TAG_LOCATION>`` geschrieben (V2 API, synchroner Schreibzugriff).
* Pro Messkanal ist das Field der Kanalname (z. B. ``U_Service``), der Wert
  ist der gefilterte Messwert.
* **Developer Mode** (``[InfluxDB] DEVELOPER_MODE: true``, im Simu-System
  aktiv): zusätzlich werden die Debug-Felder ``<Name>_raw`` (ungefilterter
  Rohwert), ``<Name>_dev_abs``, ``<Name>_dev_perc`` und ``<Name>_value_mean``
  gespeichert. Im Live-System ist der Mode deaktiviert (spart Speicherplatz).
* Beim Sprung eines Messwertes (Abweichung größer ``Threshold_Abs``) werden
  der aktuelle **und** der vorletzte Wert geschrieben, damit die Änderung in
  der Datenbank zeitlich aufgelöst werden kann.
* LIVE- und Simu-System schreiben in getrennte Buckets, die Daten vermischen
  sich nicht.
* Das Bucket muss in der InfluxDB bereits existieren, das Token braucht
  Schreibrechte darauf. Beim Start wird die Verbindung per ``ping`` geprüft;
  ist die Datenbank nicht erreichbar, beendet sich das Programm mit Exit-Code 1
  (systemd startet es neu).

Logging
-------

Log-Datei und -Verzeichnis sind in der ``[Logging]``-Sektion der conf
konfiguriert (:file:`monitor_live.log` bzw. :file:`monitor_simu.log` unter
``/opt/tatooinePi/tatooine_monitor``). Das Log-Level ist einer der Werte
``DEBUG``, ``INFO``, ``WARNING``, ``ERROR`` (``-d`` erzwingt ``DEBUG``).

Beim Start werden außerdem die Datenbankgrößen der InfluxDB
(``[COMMON] INFLUX_DB_PATH``) und der Videos (``[COMMON] VIDEO_PATH``) ausgegeben.

Beenden
-------

``Strg+C`` (KeyboardInterrupt) wird abgefangen, protokolliert und beendet das
Programm sauber mit Exit-Code 0. Über systemd übernimmt das der Service
(``Restart=always`` startet nur bei einem harten Abbruch neu).
