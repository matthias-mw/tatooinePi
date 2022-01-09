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

.. code-block:: Python

      #=================================================================
      # Register Config [HighByte]
      #=================================================================

      # OS: Operational status/single-shot conversion start
      # This bit determines the operational status of the device.
      # This bit can only be written when in power-down mode.
      # For a write status:
      # 0 : No effect
      # 1 : Begin a single conversion (when in power-down mode)
      # For a read status:
      # 0 : Device is currently performing a conversion
      # 1 : Device is not currently performing a conversion
      OS_BEGIN_SINGLE_CONV    = 0b10000000
      OS_DEV_CONV_ACTIV       = 0b00000000
      OS_DEV_CONV_NOT_ACTIV   = 0b10000000

      # MUX[2:0]: Input multiplexer configuration (ADS1115 only)
      # These bits configure the input multiplexer
      # MUX_(AINP)_(AINN)
      MUX_AIN0_AIN1           = 0b00000000    #default
      MUX_AIN0_AIN3           = 0b00010000
      MUX_AIN1_AIN3           = 0b00100000
      MUX_AIN2_AIN3           = 0b00110000
      MUX_AIN0_GND            = 0b01000000
      MUX_AIN1_GND            = 0b01010000
      MUX_AIN2_GND            = 0b01100000
      MUX_AIN3_GND            = 0b01110000

      # PGA[2:0]: Programmable gain amplifier configuration (ADS1114 and ADS1115 only)
      # These bits configure the programmable gain amplifier
      PGA_6V144               = 0b00000000
      PGA_4V096               = 0b00000010
      PGA_2V048               = 0b00000100    #default
      PGA_1V024               = 0b00000110
      PGA_0V512               = 0b00001000
      PGA_0V256               = 0b00001110

      # MODE: Device operating mode
      # This bit controls the current operational mode of the ADS1113/4/5.
      # 0 : Continuous conversion mode
      # 1 : Power-down single-shot mode (default)
      MODE_CONTINIUS_CONV     = 0x00000000
      MODE_SINGLE_SHOT_CONV   = 0b00000001    #default

      #=================================================================
      # Register Config [LowByte]
      #=================================================================

      #Data rate
      DR_8SPS                 = 0b00000000
      DR_16SPS                = 0b00100000
      DR_32SPS                = 0b01000000
      DR_64SPS                = 0b01100000
      DR_128SPS               = 0b10000000    #default
      DR_250SPS               = 0b10100000
      DR_475SPS               = 0b11000000
      DR_860SPS               = 0b11100000

      # COMP_MODE: Comparator mode (ADS1114 and ADS1115 only)
      # This bit controls the comparator mode of operation. It changes whether the comparator is implemented as a
      # traditional comparator (COMP_MODE = '0') or as a window comparator (COMP_MODE = '1'). 
      COMP_MODE_TRADITIONAL   = 0b00000000    #default
      COMP_MODE_WINDOW        = 0b00010000

      # COMP_POL: Comparator polarity (ADS1114 and ADS1115 only)
      # This bit controls the polarity of the ALERT/RDY pin. When COMP_POL = '0' the comparator output is active
      # low. When COMP_POL='1' the ALERT/RDY pin is active high. 
      COMP_POL_ACT_LOW        = 0b00000000    #default
      COMP_POL_ACT_HIGH       = 0b00001000

      # COMP_LAT: Latching comparator (ADS1114 and ADS1115 only)
      # This bit controls whether the ALERT/RDY pin latches once asserted or clears once conversions are within the
      # margin of the upper and lower threshold values. When COMP_LAT = '0', the ALERT/RDY pin does not latch
      # when asserted. When COMP_LAT = '1', the asserted ALERT/RDY pin remains latched until conversion data
      # are read by the master or an appropriate SMBus alert response is sent by the master, the device responds with
      # its address, and it is the lowest address currently asserting the ALERT/RDY bus line.
      COMP_LATCHING_ACT       = 0b00000100

      # COMP_QUE: Comparator queue and disable (ADS1114 and ADS1115 only)
      # These bits perform two functions. When set to '11', they disable the comparator function and put the
      # ALERT/RDY pin into a high state. When set to any other value, they control the number of successive
      # conversions exceeding the upper or lower thresholds required before asserting the ALERT/RDY pin.   
      COMP_ASSERT_1CONV       = 0b00000000
      COMP_ASSERT_2CONV       = 0b00000001
      COMP_ASSERT_4CONV       = 0b00000010
      COMP_DISABLE            = 0b00000011    #default


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