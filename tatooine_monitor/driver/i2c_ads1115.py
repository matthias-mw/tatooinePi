#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Bibliothek zur Ansteuerung des ADS1115 

Der ADS1115 ist ein Baustein von Texas Instruments zur Messung mehrerer Spannungen oder Spannungsdifferenzen, welcher über den i2c Bus ausgelesen werden kann. 
*ADS111x Ultra-Small, Low-Power, I2C-Compatible, 860-SPS, 16-Bit ADCsWith Internal Reference, Oscillator, and Programmable Comparator*

"""

class ADS1115():
    """Die Klasse zur Ansteuerung des ADS1115
    
    In der Klasse werden alle Methoden und Attribute bereit gestellt, die
    benötigt werden einen ADS1115 anzusteuern, zu konfigurieren und 
    auszulesen. Die übergebenen Parameter dienen der Basiskonfiguration für die Auslesung des jeweiligen Kanals
    
    Im Rahmen der Initialisierung wird der Sensor durch mit Standardeinstellungen konfiguriert und die Messung erfolgt anschließend mit der Methode **getVoltage()**.
    
    .. code-block:: python

         # Objekte für die Spannungsmessung anlegen
        Adc1 = ADS1115(bus,ADS1115.MUX_AIN0_GND,4.096)
        v = Adc1.getVoltage()
    


    :param bus: obj übergeben von der Funktion smbus
    :type bus: object
    :param mux: Einstellung fär den Multiplexer im ADS1115
    :type mux: int
    :param scale: Skalierung des AD-Wandlers in Volt
    :type scale: float
    :param address: i2c Adresse des Chip, defaults to 0x48
    :type address: byte [optional]
    
    :return:    Das Objekt repräsentiert einen AD Kanal des ADS1115
    :rtype:     object
        
    """

    #=================================================================
    # Register Selector
    #=================================================================
    #Select Conversation Register
    CMD_SEL_REG_CONV    = 0x00
    #Select Config Register
    CMD_SEL_REG_CONFIG  = 0x01
    #Select Lo_Threshold Register
    CMD_SEL_REG_LOW_THD  = 0x02
    #Select Hi_Threshold Register
    CMD_SEL_REG_HIGH_THD  = 0x03


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
    
    #=======================================================================
    # Klassenattribute
    #=======================================================================
    
    #Adresse des I2C Devices 
    i2c_addr    = 0x48
    #Gemessene Spannung 
    __voltage     = 0
    #16bit Wert des AD Wandlers
    __raw_adc     = 0
    #Config für den Multiplexer
    mux         = MUX_AIN0_GND
    #MSB für das Configregister
    configMSB   = OS_BEGIN_SINGLE_CONV | MUX_AIN0_GND | PGA_4V096 | MODE_SINGLE_SHOT_CONV
    #LSB für das Configregister
    configLSB   = DR_128SPS | COMP_MODE_TRADITIONAL | COMP_DISABLE

        
    def __init__(self,bus,mux,scale, address = 0x48):
        """Initialisierung des AnalogChannel vom ADS1115

        :param bus: obj übergeben von der Funktion smbus
        :type bus: object
        :param mux: Einstellung fär den Multiplexer im ADS1115
        :type mux: int
        :param scale: Skalierung des AD-Wandlers in Volt
        :type scale: float
        :param address: i2c Adresse des Chip, defaults to 0x48
        :type address: byte [optional]
        """
        
        self.bus = bus
        self.mux = mux
        self.scale = scale
        self.i2c_addr = address
        # Übernahme der Mux Einstellung
        self.configMSB = self.configMSB & 0b10001111
        self.configMSB = self.configMSB | mux
        
        #Config Schreiben
        self.write_config()
        
    def read_conversation(self) -> int:
        """Auslesen des Conversation Registers des ADS1115
        
        Mit der Funktion wird eine Liste von 2 Byte [MSB,LSB] ausgelesen, welche
        den 16Bit Inhalt des Conversation Registers enthält.
        
        :return: Inhalt des Conversation Registers
        :rtype: int
        """
        #Auslesen des Conversation Registers im ADS1115
        return self.bus.read_i2c_block_data(self.i2c_addr, self.CMD_SEL_REG_CONV, 2)
     
    def set_config(self, msb,lsb) -> None:
        """Erstellen der Config Bytes für das Register im ADS1115

        :param msb: Most Significant Byte
        :type msb:  byte
        :param lsb: Least Significant Byte
        :type lsb:  byte
        """
     
        #Abspeichern des Config
        self.configMSB = msb
        self.configLSB = lsb
        
    def write_config(self) -> None:
        """Schreiben des Configregisters vom ADS1115
        """
         #Schreiben der Konfiguration in des ads1115
        self.bus.write_i2c_block_data(self.i2c_addr, self.CMD_SEL_REG_CONFIG, [self.configMSB,self.configLSB])       
        
    def read_config(self) -> int:
        """Lesen des Configregisters vom ADS1115
        
        :return: Inhalt des Config Registers
        :rtype: int
        """
        #Auslesen der Konfiguration in des ads1115
        return self.bus.read_i2c_block_data(self.i2c_addr, self.CMD_SEL_REG_CONFIG, 2)
    
    def print_config(self) -> None:
        """Ausgabe der aktuellen Connfig dieses AD Objektes in der Konsole
        """
        print ("MSB:" + "{0:010b}".format(self.configMSB) + " --- LSB:" + "{0:010b}".format(self.configLSB))
        
    
    def __measure_analogIn(self) -> None:
        """ Ausführen einer SingleShot Messung am entsprechendem AD-Eingang
        
        Messung der Spannung am AD-Wandler mittels Single Shot. Dazu wird
        zuerst das Config register geschrieben und damit Single Shot getriggert.
        Anschließend wird Config gepollt, um sicherzustellen, dass die Messung 
        abgeschlossen wurde. Anschließend wird der Messwert ausgelesen und skaliert.

        Returns:
            [float]: Gemessen Spannung am AD-Wandler
        """
        
        #Schreiben der Konfiguration in des ads1114
        self.write_config()

        #Warten bis die SingleShot Messung abgeschlossen ist
        while 1:
            conf = self.read_config()
            #print ("{0:b}".format(conf[0]), "{0:b}".format(conf[1]))
            if conf[0] & self.OS_DEV_CONV_NOT_ACTIV:
                break
            
        #Auslesen der 16bit aus der letzten Messung
        data = self.read_conversation()
        
        # Convert the data
        self.__raw_adc = data[0] * 256 + data[1]

        # Umwandlung Rohwert in +/- FullScale
        # The ADS115 provides a 16bit Signal 
        # -FullScale     <<        0        >>        +FullScale
        # 0x8000         0xFFFF    0    0x0001            0x7FFF
        if self.__raw_adc > 32767:
            self.__raw_adc -= 65535

        #Skalierung des ADC auf Volt
        self.__voltage = self.scale / 0x7FFF * self.__raw_adc 
        
    def getVoltage(self):
        """Ausgabe der Spannung am konfiguriertem Eingang

        Die Funktion lässt eine Messung aus und übergibt dann den fertig 
        umgerechneten Wert der Spannung in Volt. Der Eingang wurde über 
        die MUX Stellung bei der Config gewählt.

        :return:    Spannung[V]
        :rtype:     float
        """        
        
        #Messen der Analogen Spannung am ADS1115
        self.__measure_analogIn()
        
        return self.__voltage
        


