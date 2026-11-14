API: Treiber für die Messmodule (``driver``)
=============================================

In diesem Package sind alle Treiber integriert, die zur Gewinnung der Messdaten
benötigt werden — ein Treiber pro Chip. Mehrere Chips teilen sich den I2C-Bus
(gemeinsames ``smbus2``-Busobjekt, exklusiver Zugriff über Lock in
:class:`~tatooine_data.aquire_data.AquireData`). Siehe auch :doc:`architektur`.

Module am I2C-Bus
-----------------

ADS1115 (4 analoge Spannungskanäle, Adresse ``0x48``)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. automodule:: driver.i2c_ads1115
   :members:

Die Konfiguration des ADS1115 erfolgt über zwei Bytes (MSB/LSB) im
Config-Register, die sich durch bitweises Oder der Klassenkonstanten ergeben
(MUX, PGA, MODE, Data-Rate, Komparator). Die Messung läuft als Single-Shot:
Config schreiben, pollen bis die Conversion abgeschlossen ist, dann das
Conversion-Register lesen und auf Volt skalieren.

INA219 (Spannung/Strom/Leistung, Adresse ``0x40``)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. automodule:: driver.i2c_ina219
   :members:

MPU6050 (Gyroskop/Beschleunigung, Adresse ``0x68``)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. automodule:: driver.i2c_mpu6050
   :members:

Modul für den 1-Wire-Bus
------------------------

.. automodule:: driver.one_wire
   :members:
