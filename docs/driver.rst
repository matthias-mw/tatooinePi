Python Treiber für die Messmodule
=================================

In diesem Package sind alle Treiber integriert, welche zur Gewinnung von Messdaten des TatooineMonitors benötigt werden. Es gibt einen Treiber pro verwendetem Chip. Es können sich mehrere Chips den gleichen Datenbus teilen. 


Module angeschlossen am i2c Bus
--------------------------------

.. automodule:: driver.i2c_ads1115
   :members:

.. automodule:: driver.i2c_ina219
   :members:

.. automodule:: driver.i2c_mpu6050
   :members:

Module für den 1-Wire Bus
--------------------------------
.. automodule:: driver.one_wire
   :members:
   :private-members: _path_to_1W_sensors, _temp_sensor_1w_filename