Architektur und Datenfluss
===========================

Aufbau des Repositories
-----------------------

.. code-block:: text

   tatooinePi/
   ├── requirements.txt                 # Python-Abhängigkeiten (nur Pi)
   ├── tatooine_monitor.service         # systemd-Unit
   └── tatooine_monitor/
       ├── tatooine_monitor.py          # Hauptprogramm: Argumentparser, Config, Main Loop
       ├── monitor_live.conf            # Konfiguration LIVE-System
       ├── monitor_simu.conf            # Konfiguration Simu-System
       ├── config_channels.csv          # Definition der Messkanäle
       ├── config_alerts.csv            # Definition der Alarme
       ├── .env                         # Secrets (gitignored)
       ├── tatooine_data/               # Package: Erfassung, Speicherung, Alarmierung
       │   ├── aquire_data.py           #   AquireData: zentrale Datenerfassung
       │   ├── datapoint.py             #   DataPoint: Messwert, Historie, Filter, Statistik
       │   ├── store_data.py            #   StoreDataToInflux: Schreibzugriff InfluxDB V2
       │   ├── alert_service.py         #   Alerting: Alarmberechnung und E-Mail-Versand
       │   ├── alert_chn.py             #   AlertChn: Konfigurations- und Statusobjekt eines Alarms
       │   ├── gpio_service.py          #   GpioService: Auslesen der GPIO-Eingänge
       │   └── helper.py                #   Helper: CSV-Config, .env, Conf-Zugriff, Anzeige
       └── driver/                      # Treiber für die Sensoren
           ├── i2c_ads1115.py           #   ADS1115: 4 analoge Spannungskanäle
           ├── i2c_ina219.py            #   INA219: Spannung/Strom/Leistung (gemeinsamer smbus2-Bus)
           ├── i2c_mpu6050.py           #   MPU6050: Beschleunigung/Gyroskop (gemeinsamer smbus2-Bus)
           └── one_wire.py              #   1-Wire: DS18S20-Temperatursensoren

Datenfluss
----------

.. code-block:: text

   Sensoren ──► driver/* ──► AquireData.measure_*() ──► DataPoint.update_value()
                                                              │  Filter (gleitender MW), Historie, Statistik
                                                              ▼
   Alarm-E-Mail ◄── Alerting.process_alerts() ◄── Alerting.calc_alerts() ◄──┤
                                                              ▼
                                              StoreDataToInflux.store_data() ──► InfluxDB (Bucket, Measurement, Tag location)

1. **Erfassung:** Die Methoden :meth:`~tatooine_data.aquire_data.AquireData.measure_power`,
   :meth:`~tatooine_data.aquire_data.AquireData.measure_adc`,
   :meth:`~tatooine_data.aquire_data.AquireData.measure_gyro`,
   :meth:`~tatooine_data.aquire_data.AquireData.measure_baro`,
   :meth:`~tatooine_data.aquire_data.AquireData.measure_gpio` und
   :meth:`~tatooine_data.aquire_data.AquireData.measure_1wire_ds18s20` lesen die
   Sensoren über die Treiber aus und speichern die Rohwerte per
   :meth:`~tatooine_data.aquire_data.AquireData._store_data` in den passenden
   :class:`~tatooine_data.datapoint.DataPoint` der Liste ``data_last_measured``.

2. **Aufbereitung (DataPoint):** :meth:`~tatooine_data.datapoint.DataPoint.update_value`
   hängt den neuen Wert an die Historie (max. 10 Werte), bildet den gleitenden
   Mittelwert über die letzten ``Filter`` Werte und berechnet Mittelwert sowie
   absolute/prozentuale Abweichung des aktuellen Wertes vom Historie-Mittelwert.

3. **Speicherung (InfluxDB):** :meth:`~tatooine_data.store_data.StoreDataToInflux.store_data`
   entscheidet pro Kanal, ob geschrieben wird: spätestens nach ``TickMax`` Zyklen
   oder sofort bei einer Abweichung größer ``Threshold_Abs`` (dann inklusive
   vorletztem Wert, siehe :doc:`konfiguration`). Das Schreiben erfolgt synchron
   über die InfluxDB V2 API; Schreibfehler werden geloggt, ohne die Hauptschleife
   zu beenden.

4. **Alarmierung:** :meth:`~tatooine_data.alert_service.Alerting.calc_alerts`
   und :meth:`~tatooine_data.alert_service.Alerting.process_alerts` überwachen
   die Messwerte gegen :file:`config_alerts.csv` und versenden bei Bedarf eine
   HTML-Alarm-E-Mail über SMTP (Details in :doc:`konfiguration`).

Hauptschleife und Threads
-------------------------

Die Main Loop (:func:`tatooine_monitor.main`) läuft alle **250 ms**. Die
Messungen werden über einen ``ThreadPoolExecutor`` in eigenen Threads
ausgeführt, jeweils nur, wenn der vorherige Lauf des Sensors beendet ist:

.. list-table::
   :header-rows: 1

   * - Thread
     - Intervall
     - Sensoren
   * - ``aquire_data_i2c``
     - jeder Zyklus (250 ms)
     - INA219, ADS1115, MPU6050, GPIO
   * - ``aquire_data_i2c_slow``
     - alle 10 Zyklen (2,5 s)
     - BMP280
   * - ``aquire_data_1wire``
     - alle 10 Zyklen (2,5 s)
     - alle DS18S20 (pro Sensor ein eigener Thread)

Synchronisation über Locks:

* ``AquireData._i2c_lock`` — exklusiver Zugriff auf den gemeinsamen I2C-Bus
  (smbus2), damit die I2C-Threads sich nicht ins Gehege kommen.
* ``DataPoint._lock`` — thread-sicheres Update der Messwerte, während der
  Main-Thread die Felder liest (z. B. für die Anzeige und die InfluxDB).

Ein Sensorfehler (Exception in einem Mess-Thread) wird geloggt und beendet das
Programm nicht; der betroffene Kanal behält seinen letzten Wert.

Angeschlossene Sensoren
-----------------------

.. list-table::
   :header-rows: 1

   * - Chip
     - Bus / Adresse
     - Kanäle (ID)
     - Treiber
   * - INA219 (Strom/Leistung)
     - I2C ``0x40``, Shunt 0,1 Ohm, max. 3 A
     - ``__U_POWER_IT`` (V), ``__I_POWER_IT`` (mA), ``__P_POWER_IT`` (mW = U × I)
     - :mod:`driver.i2c_ina219`
   * - ADS1115 (ADC)
     - I2C ``0x48``, 4 Kanäle, 4,096 V Skala, Spannungsteiler ×10, Kalibrierfaktor 1,087
     - ``__U_ADC1`` … ``__U_ADC4`` (V)
     - :mod:`driver.i2c_ads1115`
   * - MPU6050 (Gyroskop/Beschleunigung)
     - I2C ``0x68``
     - ``__ACC_X/Y/Z`` (g), ``__GYRO_X/Y/Z`` (dps), ``__GYRO_TEMP`` (°C)
     - :mod:`driver.i2c_mpu6050`
   * - BMP280 (Luftdruck/Temperatur)
     - I2C (über Bibliothek ``bmp280``)
     - ``__T_Baro`` (°C), ``__Baro`` (hPa)
     - Bibliothek ``bmp280``
   * - DS18S20 (Temperatur)
     - 1-Wire ``/sys/bus/w1/devices``, Kanal-ID = Sensor-ID ``28-...``
     - z. B. ``28-0121131907b3``
     - :mod:`driver.one_wire`
   * - GPIO-Eingänge
     - BCM 14, 15, 17, 18, 27
     - ``GPIO14``, ``GPIO15``, ``GPIO17``, ``GPIO18``, ``GPIO27``
     - :mod:`tatooine_data.gpio_service`

Alle I2C-Treiber teilen sich ein gemeinsames ``smbus2.SMBus(1)``-Objekt, das
erst in :func:`tatooine_monitor.main` geöffnet wird — dadurch bleibt das Modul
auch ohne ``/dev/i2c-1`` importierbar (z. B. für ``-t/--testemail`` oder Tests).
