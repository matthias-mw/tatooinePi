# tatooinePi

Überwachung der Segelyacht **SV Tatooine** aus der Ferne — auf Basis eines
Raspberry Pi, der wichtige Yachtdaten misst, in einer InfluxDB speichert und
bei Grenzwertverletzungen Alarm-E-Mails versendet.

## Funktionsumfang

1. Aufzeichnung wichtiger Yachtdaten
2. Speicherung der Daten in einer InfluxDB (V2 API)
3. Externer Zugriff auf die Daten über die InfluxDB
4. Alarmierung per E-Mail bei Grenzwertverletzungen

### Geplante Features

- Überwachung der Speicherplatzverfügbarkeit der Überwachungskamera inkl. Warnung bei Knappheit

### Messgrößen und Sensoren

| Messgröße | Sensor | Bus |
|---|---|---|
| Spannungen (ServiceBat, BowthrusterBat, StarterBat, Aux) | ADS1115 (ADC) | I2C |
| Stromaufnahme / Leistung IT-System | INA219 | I2C |
| Temperaturen (Batterien) | DS18S20 | 1-Wire |
| Beschleunigung und Lagewinkel | MPU6050 | I2C |
| Lufttemperatur, Luftfeuchte, Luftdruck (Kabine) | BMP280 | I2C |

## Aufbau des Repositories

```
tatooinePi/
├── README.md
├── requirements.txt                 # Python-Abhängigkeiten
├── tatooine_monitor.service        # systemd-Unit (nach /etc/systemd/system/ kopieren)
└── tatooine_monitor/
    ├── tatooine_monitor.py          # Hauptprogramm (Main Loop)
    ├── monitor_live.conf            # Konfiguration LIVE-System (Default ohne -c)
    ├── config_channels.csv          # LIVE: Definition der Messkanäle (Filter, Schwellen, ...)
    ├── config_alerts.csv            # LIVE: Definition der Alarme (Grenzwerte, Hysterese, ...)
    ├── .env                         # LIVE: Secrets (gitignored)
    ├── tatooine_data/               # Datenerfassung, InfluxDB-Schreibzugriff, Alerting, Helper
    ├── driver/                      # Treiber für die einzelnen Sensoren (I2C, 1-Wire)
    └── simu/                        # Simu-System: eigenes conf-Verzeichnis
        ├── monitor_simu.conf        # Konfiguration Simu (Bucket sensors_simu, DEVELOPER_MODE)
        ├── config_channels.csv      # Simu: eigene Messkanäle (z. B. andere DS18S20-IDs)
        ├── config_alerts.csv        # Simu: eigene Alarme
        └── .env                     # Simu: Secrets (gitignored)
```

## Installation

Voraussetzungen auf dem Raspberry Pi: Python 3, aktivierte I2C- und
1-Wire-Schnittstellen (`raspi-config`), InfluxDB 2.x lokal erreichbar.

Deployment auf dem Live-System nach `/opt/tatooinePi/` (die Programme
erwarten die Konfigurationsdateien unter diesem Pfad). Das venv liegt
**auf dem Pi neben dem Code** unter `/opt/tatooinePi/tatooine_monitor/venv-monitor`
(Name bewusst nicht `.venv`/`venv`, damit es nicht mit anderen venvs kollidiert;
über `.gitignore` nicht in git). Im Repo liegt nur die `requirements.txt`:

```bash
# direkt auf dem Raspberry Pi ausführen (RPi.GPIO ist nur dort installierbar):
cd /opt/tatooinePi/tatooine_monitor
python3 -m venv venv-monitor
./venv-monitor/bin/pip install -r ../requirements.txt

# Test: Version ausgeben / Test-Alarm-Mail senden
./venv-monitor/bin/python tatooine_monitor.py -v
./venv-monitor/bin/python tatooine_monitor.py -t
```

Aktivieren zum manuellen Arbeiten: `source /opt/tatooinePi/tatooine_monitor/venv-monitor/bin/activate`.

## Dokumentation (Sphinx)

Die API-Doku liegt in `docs/` und wird aus den Docstrings per Sphinx gebaut
(nicht auf dem Pi nötig, eigene Abhängigkeiten in `docs/requirements.txt`).
Doku-Build auf dem Entwicklungsrechner (z.B. barbuda) in eigener venv
`venv-docs` im Repo-Root (gitignored, nicht zu verwechseln mit `.venv`
oder der Pi-venv `tatooine_monitor/venv-monitor`):

```bash
python3 -m venv venv-docs
source venv-docs/bin/activate
pip install -r docs/requirements.txt
cd docs
make html        # Ausgabe: docs/_build/html/index.html
```

## Konfiguration

Die zentrale Konfiguration liegt in einer INI-Datei. Es gibt zwei Varianten,
jede in ihrem eigenen Verzeichnis (damit liegen auch die CSVs und die `.env`
getrennt):

| conf-Datei | System | InfluxDB-Bucket |
|---|---|---|
| `tatooine_monitor/monitor_live.conf` | LIVE (Default) | `sensors` |
| `tatooine_monitor/simu/monitor_simu.conf` | Simu / Weiterentwicklung | `sensors_simu` |

Die Auswahl erfolgt über das Kommandozeilenargument `-c` / `--config`:

```bash
# LIVE-System (Default, Argument kann weggelassen werden)
python3 tatooine_monitor.py

# Simu-System (eigenes conf-Verzeichnis mit eigenen CSVs und .env)
python3 tatooine_monitor.py -c /opt/tatooinePi/tatooine_monitor/simu/monitor_simu.conf
```

Wird eine angegebene Datei nicht gefunden oder kann nicht geparst werden,
bricht das Programm mit einer Fehlermeldung und Exit-Code 1 ab.

### Zugangsdaten (.env)

Secrets (InfluxDB-Token, SMTP-Zugangsdaten) stehen **nicht** mehr in den
conf-Dateien oder im Code, sondern in einer `.env`-Datei im selben
Verzeichnis wie die verwendete conf:

```
INFLUXDB_TOKEN=<InfluxDB V2 API Token>
SMTP_USERNAME=<SMTP Benutzername>
SMTP_PASSWORD=<SMTP Passwort>
```

Vorlage siehe `.env_example`. Die `.env` wird über `.gitignore` nicht in git
eingecheckt. Beim Start werden die Variablen aus der `.env` geladen; eine
bereits gesetzte Umgebungsvariable hat Vorrang. Fehlt ein Secret, bricht das
Programm mit Fehlermeldung ab.

`config_channels.csv` und `config_alerts.csv` werden ebenfalls aus dem
Verzeichnis der gewählten conf gelesen — Live- und Simu-System können also
jeweils eigene CSVs im eigenen Verzeichnis liegen haben.

### Sektionen der .conf-Datei

| Sektion | Inhalt |
|---|---|
| `[InfluxDB]` | HOST, PORT, TOKEN, ORG, BUCKET, MEASUREMENT, TAG_LOCATION, DEVELOPER_MODE |
| `[Logging]` | LOG_FILE, LOG_DIR, LOG_LEVEL (DEBUG, INFO, WARNING, ERROR) |
| `[ALERTING]` | SMTP-Server, Absender/Empfänger, Debounce-Zeiten, Tageslimit für E-Mails |
| `[COMMON]` | Pfade zur Ermittlung der Datenbankgrößen (InfluxDB, Videos) |

`DEVELOPER_MODE: true` speichert zusätzliche Debug-Felder (`_raw`,
`_dev_abs`, `_dev_perc`, `_value_mean`) in der InfluxDB — im Simu-System
aktiviert, im Live-System deaktiviert.

### Messkanäle und Alarme

- `config_channels.csv` — je Messkanal: ID, Name, Einheit, Filter, Messintervalle
  (TickMax/TickFast), absolute und prozentuale Abweichungsschwellen.
- `config_alerts.csv` — je Messgröße: Grenzwert (Level), Hysterese, Bedingung
  (`gt`/`st`) und Alarmkanal (z. B. `email`).

## Programmstart

```bash
python3 tatooine_monitor.py [Optionen]
```

| Option | Wirkung |
|---|---|
| `-c`, `--config <datei>` | Konfigurationsdatei auswählen (Default: `monitor_live.conf`) |
| `-t`, `--testemail` | Test-Alarm-E-Mail über den SMTP-Pfad versenden und Programm beenden |
| `-v`, `--version` | Programmversion anzeigen |
| `-d`, `--debug` | Debug-Logging aktivieren |
| `-s`, `--show` | Live-Ausgabe der aktuellen Messwerte auf stdout |

### systemd (LIVE-System)

`tatooine_monitor.service` nach `/etc/systemd/system/` kopieren und starten:

```bash
sudo systemctl enable --now tatooine_monitor.service
```

Die Unit startet das Programm ohne `-c`, es wird also `monitor_live.conf`
verwendet. Für das Simu-System genügt der manuelle Start mit `-c
simu/monitor_simu.conf` (relativ zu `/opt/tatooinePi/tatooine_monitor`).

## Datenablage (InfluxDB 2.x)

- Alle Messwerte werden als Points im konfigurierten **Bucket** unter dem
  **Measurement** (`TatooineRemote`) mit dem Tag `location=<TAG_LOCATION>`
  geschrieben.
- LIVE- und Simu-System schreiben in getrennte Buckets
  (`sensors` bzw. `sensors_simu`), die Daten vermischen sich nicht.
- Das Bucket muss in der InfluxDB bereits existieren und das Token muss
  Schreibrechte darauf haben.

## Logging

Log-Datei und -Verzeichnis sind in der `[Logging]`-Sektion konfiguriert
(`monitor_live.log` unter `/opt/tatooinePi/tatooine_monitor`,
`monitor_simu.log` unter `/opt/tatooinePi/tatooine_monitor/simu`).

---

Copyright 2021, TatooineMonitor Projekt — Matthias Werner <werner.matthias@web.de>
