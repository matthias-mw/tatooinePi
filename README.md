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
    ├── monitor_live.conf            # Konfiguration LIVE-System
    ├── monitor_simu.conf            # Konfiguration Simu-System (eigenes InfluxDB-Bucket)
    ├── config_channels.csv          # Definition der Messkanäle (Filter, Schwellen, ...)
    ├── config_alerts.csv            # Definition der Alarme (Grenzwerte, Hysterese, ...)
    ├── tatooine_data/               # Datenerfassung, InfluxDB-Schreibzugriff, Alerting, Helper
    └── driver/                      # Treiber für die einzelnen Sensoren (I2C, 1-Wire)
```

## Installation

Voraussetzungen auf dem Raspberry Pi: Python 3, aktivierte I2C- und
1-Wire-Schnittstellen (`raspi-config`), InfluxDB 2.x lokal erreichbar.

```bash
# Abhängigkeiten installieren (im venv, direkt auf dem Raspberry Pi ausführen —
# RPi.GPIO ist nur auf dem Pi installierbar/verwendbar)
python3 -m venv tatooine_monitor/venv
tatooine_monitor/venv/bin/pip install -r requirements.txt
```

Deployment auf dem Live-System nach `/opt/tatooinePi/` (die Programme
erwarten die Konfigurationsdateien unter diesem Pfad).

## Konfiguration

Die zentrale Konfiguration liegt in einer INI-Datei. Es gibt zwei Varianten:

| Datei | System | InfluxDB-Bucket |
|---|---|---|
| `monitor_live.conf` | LIVE (Default) | `sensors` |
| `monitor_simu.conf` | Simu / Weiterentwicklung | `sensors_simu` |

Die Auswahl erfolgt über das Kommandozeilenargument `-c` / `--config`:

```bash
# LIVE-System (Default, Argument kann weggelassen werden)
python3 tatooine_monitor.py

# Simu-System
python3 tatooine_monitor.py -c /opt/tatooinePi/tatooine_monitor/monitor_simu.conf
```

Wird eine angegebene Datei nicht gefunden oder kann nicht geparst werden,
bricht das Programm mit einer Fehlermeldung und Exit-Code 1 ab.

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
monitor_simu.conf`.

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
(`monitor_live.log` bzw. `monitor_simu.log` unter `/opt/tatooinePi/tatooine_monitor`).

---

Copyright 2021, TatooineMonitor Projekt — Matthias Werner <werner.matthias@web.de>
