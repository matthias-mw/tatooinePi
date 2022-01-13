Python Treiber für die Messmodule
=================================

In diesem Package sind alle Treiber integriert, welche zur Gewinnung von Messdaten des TatooineMonitors benötigt werden. Es gibt einen Treiber pro verwendetem Chip. Es können sich mehrere Chips den gleichen Datenbus teilen. 


Module angeschlossen am i2c Bus
--------------------------------

ADS111x
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. automodule:: driver.i2c_ads1115
   :members:

**Für die detailierte Konfiguration müssen 2 Byte (MSB,LSB) in des Config Register geschrieben werden. Diese Bytes ergeben sich durch das "bitweise Oder" der folgenden Konstanten**

.. literalinclude:: ../tatooine_monitor/driver/i2c_ads1115.py
   :language: python
   :lines: 53 - 142

INA219
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. automodule:: driver.i2c_ina219
   :members:

MPU 6050
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. automodule:: driver.i2c_mpu6050
   :members:

Module für den 1-Wire Bus
--------------------------------
.. automodule:: driver.one_wire
   :members:
   :private-members: _path_to_1W_sensors, _temp_sensor_1w_filename