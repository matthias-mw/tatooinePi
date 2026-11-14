Konfiguration
=============

Die Konfiguration verteilt sich auf vier Dateien im Verzeichnis der gewählten
conf (Default: ``/opt/tatooinePi/tatooine_monitor``):

.. list-table::
   :header-rows: 1

   * - Datei
     - Inhalt
   * - :file:`monitor_live.conf` / :file:`monitor_simu.conf`
     - Zentrale INI-Konfiguration (InfluxDB, Logging, Alarmierung, Pfade); Auswahl über ``-c/--config``
   * - :file:`.env`
     - Secrets (InfluxDB-Token, SMTP-Zugangsdaten) — nicht in git
   * - :file:`config_channels.csv`
     - Definition aller Messkanäle
   * - :file:`config_alerts.csv`
     - Definition aller Alarme

Zentrale conf-Datei
-------------------

Die INI-Datei hat vier Sektionen:

``[InfluxDB]`` — Verbindung zur InfluxDB (V2 API, token-basiert)

.. list-table::
   :header-rows: 1

   * - Schlüssel
     - Bedeutung
   * - ``HOST`` / ``PORT``
     - Adresse der InfluxDB (Default ``127.0.0.1:8086``, lokal auf dem Pi)
   * - ``ORG``
     - InfluxDB V2 Organisation
   * - ``BUCKET``
     - InfluxDB V2 Bucket, muss bereits existieren (``sensors`` bzw. ``sensors_simu``)
   * - ``MEASUREMENT``
     - Name des Measurements (``TatooineRemote``)
   * - ``TAG_LOCATION``
     - Wert des Tags ``location`` (``tatooine`` bzw. ``tatooine-simu``)
   * - ``DEVELOPER_MODE``
     - ``true``: zusätzliche Debug-Felder in der InfluxDB speichern (``_raw``, ``_dev_abs``, ``_dev_perc``, ``_value_mean``); ``false``: nur der gefilterte Hauptwert
   * - Token
     - kommt **nicht** aus der conf, sondern aus der Umgebungsvariable ``INFLUXDB_TOKEN`` (geladen aus der :file:`.env`); nur als Legacy-Fallback wird ``[InfluxDB] TOKEN`` gelesen

``[Logging]``

.. list-table::
   :header-rows: 1

   * - Schlüssel
     - Bedeutung
   * - ``LOG_FILE`` / ``LOG_DIR``
     - Log-Datei und -Verzeichnis (z. B. ``monitor_live.log`` unter ``/opt/tatooinePi/tatooine_monitor``)
   * - ``LOG_LEVEL``
     - ``DEBUG``, ``INFO``, ``WARNING`` oder ``ERROR``

``[ALERTING]`` — Alarmierung per E-Mail

.. list-table::
   :header-rows: 1

   * - Schlüssel
     - Bedeutung
   * - ``SMTP_SERVER`` / ``SMTP_PORT``
     - Postausgangsserver (Port 587, STARTTLS)
   * - ``EMAIL_SENDER`` / ``EMAIL_RECIEVER``
     - Absender- und Empfängeradresse der Alarm-E-Mails
   * - ``DEBOUNCE_EMAIL_ALARM_S``
     - Verzögerung in Sekunden zwischen Alarmeintritt und E-Mail-Versand (Default 5 s); ermöglicht das Sammeln mehrerer Alarme in einer Mail
   * - ``DEBOUNCE_EMAIL_BETWEEN_ALARM_S``
     - Mindestabstand in Sekunden zwischen zwei Alarm-E-Mails (Default 120 s)
   * - ``EMAIL_LIMIT_PER_DAY``
     - Maximale Anzahl Alarm-E-Mails pro Tag (Default 10); schützt vor Mail-Flut bei Fehlfunktion
   * - SMTP-Zugangsdaten
     - kommen **nicht** aus der conf, sondern aus den Umgebungsvariablen ``SMTP_USERNAME`` / ``SMTP_PASSWORD`` (geladen aus der :file:`.env`)

``[COMMON]``

.. list-table::
   :header-rows: 1

   * - Schlüssel
     - Bedeutung
   * - ``INFLUX_DB_PATH``
     - Verzeichnis der InfluxDB-Daten (für die Größenanzeige beim Start)
   * - ``VIDEO_PATH``
     - Verzeichnis der Kamera-Videos (für die Größenanzeige beim Start)

Zugangsdaten (.env)
-------------------

.. code-block:: ini

   INFLUXDB_TOKEN=<InfluxDB V2 API Token>
   SMTP_USERNAME=<SMTP Benutzername>
   SMTP_PASSWORD=<SMTP Passwort>

* Vorlage siehe :file:`.env_example` im conf-Verzeichnis; :file:`.env` ist über
  ``.gitignore`` nicht in git.
* Format pro Zeile ``KEY=VALUE``; ``#``-Kommentare und leere Zeilen werden
  ignoriert.
* Bereits gesetzte Umgebungsvariablen haben Vorrang vor der :file:`.env`.
* Fehlt ein Secret, beendet sich das Programm mit Fehlermeldung und Exit-Code 1.
* Test des SMTP-Pfads ohne Hauptprogramm: ``tatooine_monitor.py -t``
  (sendet eine Test-Alarm-E-Mail und beendet sich).

Messkanäle (:file:`config_channels.csv`)
----------------------------------------

Jede Zeile definiert einen Messkanal. Die Datei wird beim Start über
:func:`tatooine_data.helper.config_channels` eingelesen; pro Kanal wird ein
:class:`~tatooine_data.datapoint.DataPoint` angelegt.

.. list-table::
   :header-rows: 1

   * - Spalte
     - Bedeutung
   * - ``ID``
     - eindeutige ID des Kanals; identifiziert den Kanal im Code (z. B. ``__U_POWER_IT``, ``__U_ADC1``, ``GPIO14``) bzw. ist bei 1-Wire-Sensoren die Sensor-ID (``28-...``)
   * - ``Name``
     - Anzeigename des Kanals; zugleich Field-Name in der InfluxDB und Matching-Key für Alarme
   * - ``Description``
     - Freitext-Beschreibung
   * - ``Unit``
     - Maßeinheit (z. B. ``V``, ``mA``, ``grdC``)
   * - ``Filter``
     - Breite des gleitenden Mittelwerts: der gespeicherte Wert ist der Mittelwert der letzten ``Filter`` Messwerte (``0``/``1`` = ungefiltert)
   * - ``TickMax``
     - maximale Anzahl Schleifenzyklen (à 250 ms), nach denen der Kanal spätestens in die InfluxDB geschrieben wird
   * - ``TickFast``
     - reserviert für einen schnelleren Speichertick — aktuell nicht ausgewertet
   * - ``Threshold_Abs``
     - absolute Abweichung vom Mittelwert der Historie, ab der der Wert unabhängig vom Tick gespeichert wird (Sprungerkennung; dabei wird auch der vorletzte Wert mitgespeichert)
   * - ``Threshold_Perc``
     - prozentuale Abweichung — reserviert, aktuell nicht ausgewertet

Aktuell konfigurierte Kanäle:

.. csv-table::
   :file: ../tatooine_monitor/config_channels.csv
   :widths: 20, 10, 25, 5, 5, 5, 5, 10, 10
   :header-rows: 1

Alarme (:file:`config_alerts.csv`)
----------------------------------

Jede Zeile definiert einen Alarm auf einem Messkanal (Matching über ``Name``).
Die Datei wird über :func:`tatooine_data.alert_service.Alerting.conf_alerts`
eingelesen.

.. list-table::
   :header-rows: 1

   * - Spalte
     - Bedeutung
   * - ``Name``
     - Name des Messkanals, der überwacht wird (muss dem ``Name`` in :file:`config_channels.csv` entsprechen)
   * - ``Unit``
     - Maßeinheit (nur informativ, für die E-Mail-Ausgabe)
   * - ``Description``
     - Freitext-Beschreibung des Alarms
   * - ``Level``
     - Schwellwert, bei dessen Über-/Unterschreitung der Alarm auslöst
   * - ``Hysterese``
     - Hysterese in der Einheit des Kanals: der Alarm wird erst zurückgesetzt, wenn der Wert die Schwelle um mindestens die Hysterese wieder unter-/überschritten hat (entprellt die Schwelle)
   * - ``Condition``
     - ``gt`` = Alarm wenn Wert **größer** Level; ``st`` = Alarm wenn Wert **kleiner** Level
   * - ``Type``
     - ``email`` = Alarm-E-Mail; ``sms`` ist als Typ vorgesehen, aktuell wird nur E-Mail versendet

Aktuell konfigurierte Alarme:

.. csv-table::
   :file: ../tatooine_monitor/config_alerts.csv
   :widths: 20, 5, 25, 10, 10, 10, 10
   :header-rows: 1

Alarmablauf im Detail
~~~~~~~~~~~~~~~~~~~~~

1. :func:`~tatooine_data.alert_service.Alerting.calc_alerts` vergleicht in jedem
   Zyklus die aktuellen Messwerte mit den Alarmkonfigurationen. Bei Verletzung
   der Schwelle wird der Alarm aktiv (Status ``ALERT_PENDING_EMAIL``) und die
   Uhrzeit gespeichert.
2. :func:`~tatooine_data.alert_service.Alerting.process_alerts` versendet die
   E-Mail, sobald seit dem Alarmeintritt ``DEBOUNCE_EMAIL_ALARM_S`` vergangen
   sind **und** seit der letzten Alarm-Mail mindestens
   ``DEBOUNCE_EMAIL_BETWEEN_ALARM_S`` liegen. Anliegende Alarme werden in der
   Mail gesammelt (:func:`~tatooine_data.alert_service.Alerting.msg_html`).
3. Das Tageslimit ``EMAIL_LIMIT_PER_DAY`` wird über
   :func:`~tatooine_data.alert_service.Alerting.email_limit` überwacht; ist es
   erreicht, werden keine weiteren Mails versendet (Log-Warnung).
4. Die Alarm-E-Mail enthält die ausgelösten Alarme (Kanal, Schwelle, Uhrzeit)
   und eine Tabelle aller aktuellen Messwerte.
