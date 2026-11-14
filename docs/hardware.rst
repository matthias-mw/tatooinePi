Hardware
========

Dieser Abschnitt beschreibt die Hardware des Tatooine Monitor: den Raspberry Pi,
die verwendeten Busse und die angeschlossenen Sensoren.

Schaltplan und Hardware-Dokumentation als PDF:
:download:`TatooineMonitor.pdf herunterladen <TatooineMonitor.pdf>`

.. note::
   Die PDF-Dokumentation liegt im :file:`docs/`-Verzeichnis des Repos und wird
   beim Doku-Build über ``html_extra_path`` 1:1 in das HTML-Ausgabeverzeichnis
   kopiert, sodass der Download-Link funktioniert.

Raspberry Pi und Busse
----------------------

Der Tatooine Monitor läuft auf einem **Raspberry Pi** (GPIO-Nummerierung BCM).
Folgende Schnittstellen müssen aktiviert sein (``sudo raspi-config`` →
*Interface Options*) und sind in :doc:`installation` beschrieben:

.. list-table::
   :header-rows: 1
   :widths: 18 24 58

   * - Bus / Schnittstelle
     - Systempfad
     - Pins & Aktivierung (BCM)
   * - I2C (Bus 1)
     - ``/dev/i2c-1``
     - SDA = GPIO2, SCL = GPIO3 (3,3 V); raspi-config → I2C
   * - 1-Wire
     - ``/sys/bus/w1/devices``
     - Datenpin [#w1]_; raspi-config → 1-Wire
   * - GPIO (digitale Eingänge)
     - —
     - BCM 14, 15, 17, 18, 27 (als Eingänge); keine Aktivierung nötig

.. [#w1] 1-Wire-Datenpin über Device-Tree-Overlay ``w1-gpio``
   (``dtoverlay=w1-gpio`` in der :file:`config.txt`, Pin über
   ``w1-gpio,pins=<BCM>`` wählbar), externer Pull-up 4,7 kΩ gegen 3,3 V.
   **LIVE-System (tatooinePi): GPIO4** (raspi-config-Default) —
   **Simu-System (tatooinePiSimu): GPIO22** (z. B. ``dtoverlay=w1-gpio,pins=22``).

Angeschlossene Sensoren
-----------------------

.. list-table::
   :header-rows: 1
   :widths: 20 10 24 30 16

   * - Sensor
     - Bus
     - Adresse / Anschluss
     - Funktion
     - Kanäle (ID in :file:`config_channels.csv`)
   * - ADS1115 (TI, 16-Bit-ADC)
     - I2C
     - ``0x48``
     - 4 analoge Spannungsmessungen (PGA 4,096 V, Spannungsteiler ×10, Kalibrierfaktor 1,087 je Kanal)
     - ``__U_ADC1`` … ``__U_ADC4``
   * - INA219 (TI, Strom/Leistung)
     - I2C
     - ``0x40``, Shunt 0,1 Ω (max. 3 A erwartet)
     - Spannung, Strom und Leistung des IT-Systems (P = U × I)
     - ``__U_POWER_IT``, ``__I_POWER_IT``, ``__P_POWER_IT``
   * - MPU6050 (Gyroskop/Beschleunigung)
     - I2C
     - ``0x68``
     - Beschleunigung X/Y/Z (g), Drehrate X/Y/Z (dps), Chip-Temperatur (°C)
     - ``__ACC_X/Y/Z``, ``__GYRO_X/Y/Z``, ``__GYRO_TEMP``
   * - BMP280 (Luftdruck/Temperatur)
     - I2C
     - Default-Adresse der ``bmp280``-Bibliothek
     - Lufttemperatur (°C) und Luftdruck (hPa)
     - ``__T_Baro``, ``__Baro``
   * - DS18S20 (Temperatur)
     - 1-Wire
     - Jeder Sensor über seine eigene 1-Wire-ID (``28-...``)
     - Temperatur (°C); die Sensor-ID ist zugleich die Kanal-ID in der CSV
     - z. B. ``28-0121131907b3`` (Live), in der Simu andere IDs
   * - GPIO-Eingänge
     - GPIO
     - BCM 14, 15, 17, 18, 27
     - Digitale Zustände (0/1)
     - ``GPIO14``, ``GPIO15``, ``GPIO17``, ``GPIO18``, ``GPIO27``

Details zur Software-Anbindung (Treiber, Kanäle, Main Loop) siehe
:doc:`architektur`; die konkrete Kanalbelegung steht in der
:file:`config_channels.csv` des jeweiligen Systems (:doc:`konfiguration`).
