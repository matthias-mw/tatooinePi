Installation und Inbetriebnahme
===============================

Dieses Kapitel beschreibt die Erstinstallation des Tatooine Monitor auf dem
Raspberry Pi an Bord der SV Tatooine (Live-System). Für die Entwicklung steht
ein zweites System (Simu) zur Verfügung, siehe :doc:`betrieb`.

Voraussetzungen
---------------

* Raspberry Pi mit Raspberry Pi OS und Python 3
* Aktivierte Schnittstellen (einmalig über ``sudo raspi-config``):

  * *Interface Options → I2C* aktivieren (ergibt ``/dev/i2c-1``)
  * *Interface Options → 1-Wire* aktivieren (ergibt ``/sys/bus/w1/devices``)

* InfluxDB 2.x, lokal auf dem Pi erreichbar (``127.0.0.1:8086``)
* SMTP-Postfach für den Alarm-Mail-Versand (z. B. beim Webhoster)
* Angeschlossene Sensoren gemäß :doc:`architektur`

Schritt 1: Schnittstellen prüfen
--------------------------------

Nach dem Aktivieren und einem Reboot müssen folgende Pfade existieren:

.. code-block:: console

   $ ls -l /dev/i2c-1
   crw-rw---- 1 root i2c 89, 1 ... /dev/i2c-1
   $ ls /sys/bus/w1/devices
   28-012113124839  28-0121131907b3  ...  w1_bus_master1

Die ``28-...``-Verzeichnisse sind die angeschlossenen DS18S20-Sensoren.

Schritt 2: InfluxDB vorbereiten
--------------------------------

In der InfluxDB 2.x (lokale Installation auf dem Pi):

1. Organisation anlegen (in der conf unter ``[InfluxDB] ORG``, z. B.
   ``sv-tatooine``).
2. Bucket anlegen (z. B. ``sensors`` für Live, ``sensors_simu`` für Simu).
3. API-Token mit **Schreibrecht auf das Bucket** anlegen. Das Token wird
   später in der :file:`.env` hinterlegt (siehe Schritt 5).

Schritt 3: Repository nach ``/opt/tatooinePi`` deployen
-------------------------------------------------------

Die Programme erwarten die Konfigurationsdateien unter
``/opt/tatooinePi/tatooine_monitor``:

.. code-block:: console

   $ sudo mkdir -p /opt/tatooinePi
   $ sudo chown tatooine:tatooine /opt/tatooinePi
   $ git clone <repo-url> /opt/tatooinePi

Schritt 4: Virtuelle Umgebung anlegen und Abhängigkeiten installieren
----------------------------------------------------------------------

Die Installation der Abhängigkeiten muss **direkt auf dem Pi** erfolgen,
da ``RPi.GPIO`` nur auf einem Raspberry Pi installierbar ist. Die venv liegt
bewusst neben dem Code unter
``/opt/tatooinePi/tatooine_monitor/venv-monitor`` (Name nicht ``venv`` oder
``.venv``, damit es nicht mit anderen venvs kollidiert; über ``.gitignore``
nicht in git):

.. code-block:: console

   $ cd /opt/tatooinePi/tatooine_monitor
   $ python3 -m venv venv-monitor
   $ ./venv-monitor/bin/pip install -r ../requirements.txt

Installiert werden: ``influxdb-client``, ``pytz``, ``bmp280``, ``smbus2``,
``RPi.GPIO`` (siehe :file:`requirements.txt` im Repo-Root).

Schritt 5: Zugangsdaten in der .env hinterlegen
------------------------------------------------

Secrets stehen nicht im Code und nicht in den conf-Dateien, sondern in einer
:file:`.env`-Datei **im selben Verzeichnis wie die verwendete conf**:

.. code-block:: console

   $ cd /opt/tatooinePi/tatooine_monitor
   $ cp .env_example .env
   $ chmod 600 .env
   $ # .env bearbeiten und echte Werte eintragen:

.. code-block:: ini

   INFLUXDB_TOKEN=<InfluxDB V2 API Token>
   SMTP_USERNAME=<SMTP Benutzername>
   SMTP_PASSWORD=<SMTP Passwort>

Beim Start werden die Variablen aus der :file:`.env` geladen; eine bereits
gesetzte Umgebungsvariable hat Vorrang vor der :file:`.env`. Fehlt ein Secret,
bricht das Programm mit einer Fehlermeldung ab. Die :file:`.env` ist über
``.gitignore`` nicht in git eingecheckt.

Schritt 6: Funktionstest (noch ohne systemd)
--------------------------------------------

.. code-block:: console

   $ cd /opt/tatooinePi/tatooine_monitor
   $ # Version ausgeben
   $ ./venv-monitor/bin/python tatooine_monitor.py -v
   $ # Test-Alarm-E-Mail über den SMTP-Pfad senden (Prüft .env + SMTP-Konfig)
   $ ./venv-monitor/bin/python tatooine_monitor.py -t
   $ # Kurzer Probelauf auf dem Simu-System mit Live-Ausgabe der Messwerte
   $ ./venv-monitor/bin/python tatooine_monitor.py -c simu/monitor_simu.conf -s

Das Programm bricht beim Start hart ab (Exit-Code 1), wenn die InfluxDB nicht
erreichbar ist — systemd startet es in diesem Fall automatisch neu.

Schritt 7: systemd-Service einrichten (Live-System)
---------------------------------------------------

.. code-block:: console

   $ sudo cp /opt/tatooinePi/tatooine_monitor.service /etc/systemd/system/
   $ sudo systemctl daemon-reload
   $ sudo systemctl enable --now tatooine_monitor.service
   $ systemctl status tatooine_monitor.service
   $ journalctl -u tatooine_monitor.service -f

Die Unit startet das Programm **ohne** ``-c``, verwendet also die
:file:`monitor_live.conf` und das venv-Python
(``/opt/tatooinePi/tatooine_monitor/venv-monitor/bin/python``). ``Restart=always``
sorgt dafür, dass das Programm nach einem Abbruch (z. B. InfluxDB-Neustart)
neu gestartet wird.

Das Simu-System wird nicht über systemd betrieben, sondern manuell mit
``-c simu/monitor_simu.conf`` gestartet (eigenes conf-Verzeichnis
:file:`simu/` mit eigenen CSVs und eigener :file:`.env`), siehe :doc:`betrieb`
und :doc:`konfiguration`.

Weiteres
--------

* Konfiguration der conf-Dateien, Messkanäle und Alarme: :doc:`konfiguration`
* Programmstart, Optionen und Betrieb: :doc:`betrieb`
* Aufbau und Datenfluss des Programms: :doc:`architektur`
* API-Dokumentation (autodoc aus den Docstrings): :doc:`tatooine_data`,
  :doc:`alerting`, :doc:`driver`

Dokumentation bauen
-------------------

Die Sphinx-Doku wird **nicht auf dem Pi**, sondern auf dem Entwicklungsrechner
(z. B. barbuda) gebaut — in einer eigenen venv ``venv-docs`` im Repo-Root:

.. code-block:: console

   $ cd /mnt/tatooinePi/tatooinePi        # Repo-Root auf dem Entwicklungsrechner
   $ python3 -m venv venv-docs
   $ source venv-docs/bin/activate
   $ pip install -r docs/requirements.txt
   $ cd docs && make html                  # Ausgabe: docs/_build/html/index.html
