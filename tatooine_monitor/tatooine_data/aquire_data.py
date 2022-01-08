#!/usr/bin/env python3
# -*- coding: utf-8 -*- 

# Modul zur Bearbeitung der Zeitstempel
from datetime import datetime

# Modul zum Multithreading
import concurrent.futures

# Klasse für die Abspeicherung der Datenpunkte
from .datapoint import DataPoint

# Helper Modul stell Kanalkonfiguration zur Verfügung
from .helper import *

#i2c Treiber - AD-Wandler ADS1115
from driver.i2c_ads1115  import ADS1115
#i2c Treiber - Powerüberwachung INA219
from driver.i2c_ina219 import INA219
from driver.i2c_ina219 import DeviceRangeError
#i2c Treiber - Gyroscope
from driver.i2c_mpu6050 import mpu6050
# 1Wire Treiber
from driver.one_wire import OneWire


class AquireData:
    """Klasse zur zentralen Datenerfassung
    
    Mit dieser Klasse werden alle Messwerte von den verschiedenen Sensoren
    erfasst und entsprechend aufbereitet, um sie dann in einem Datenpunkt
    der Klasse :class:`~tatooine_data.datapoint.DataPoint` abzuspeichern.
    
    """    
    
    SHUNT_OHMS = 0.1
    """Widerstandswert (Ohm) des Shunt am INA219"""
    
    _MAX_DATA_POINTS_HISTORY = 8
    """Anzahl der Werte die in der Datenhistorie betrachtet werden"""     
  
    data_last_measured = []
    """Array von :class:`~tatooine_data.datapoint.DataPoint`, welcher den aktuellen Messwert jedes verfügbaren Kanals bereit hält.
    """  
    
    
    def __init__(self, bus = None):
        """Initialisierung des Datenaquisition Klasse

        Bei der Initialisierung werden alles Objekte für den Zugriff auf die diversen Sensorchips (siehe ToDo ) erstellt und entsprechend konfiguriert.

        :param bus: Object das den Datenbus repräsentiert, defaults to None
        :type bus: Objekt(smbus), optional
        """        
        self.i2c_bus = bus
        
        # Objekte für die Spannungsmessung anlegen
        self.Adc1 = ADS1115(bus,ADS1115.MUX_AIN0_GND,4.096)
        self.Adc2 = ADS1115(bus,ADS1115.MUX_AIN1_GND,4.096)
        self.Adc3 = ADS1115(bus,ADS1115.MUX_AIN2_GND,4.096)

        # Objekt für die Powerüberwachung anlegen
        self.Ina = INA219(self.SHUNT_OHMS,3,1,0x40)

        # Objekt für den MPU6050 anlegen
        self.mpu = mpu6050(0x68)

        # Objekt für den 1-Wire Bus anlegen
        self.one_wire = OneWire()
        
        #initialisierung der aktuellen Messdaten
        self.data_last_measured =[DataPoint(x['ID'],x['Name'],x["Unit"], \
            int(x['Filter']),int(x['TickMax']), int(x['TickFast']), \
            float(x['Threshold_Abs']), float(x['Threshold_Perc'])) for x in CHANNEL_CONFIG_LIST]

   
    def _store_data(self, data_point, value=0.0, 
                    time = datetime.now()):
        """Abspeichern eines Wertes in einen Datenpunkt

        Mit dieser internen Hilfsfunktion wird ein Messwert samt Einheit und Zeitstempel in den entsprechenden Datenpunkt abgespeichert.
        
        
        :param data_point: Datenpunktobjekt
        :type data_point: class DataPoint
        :param value: abzuspeichernder Messwert, defaults to 0.0
        :type value: float, optional
        :param time: Zeitstempel des Messwertes, defaults to datetime.now()
        :type time: datetime objekt, optional
        """        

        data_point.update_value(value,time.timestamp())

    
    def measure_power(self) -> None:
        """Messung der Leistungsaufnahme des INA219
        
        Mittels des INA219 Sensors wird über I2C die aktuelle Spannung, die Stromaufnahme und die Leistungsaufnahme gemessen. Anschließend speichert die Methode die Werte in den Array[:class:`~tatooine_data.datapoint.DataPoint.data_last_measured`] ab.
        """        
        
        #--------------------------------------------------------------------
        # Erfassung der Messwerte des INA219 und anschließendes Abspeichern 
        #--------------------------------------------------------------------
        self.Ina.configure()
        isoTime = datetime.now()
                
        for x in self.data_last_measured:
            if x.id == "__U_POWER_IT":
                self._store_data(x,self.Ina.voltage(),isoTime)
            if x.id == "__I_POWER_IT":
                self._store_data(x,self.Ina.current(),isoTime)
            if x.id == "__P_POWER_IT":
                self._store_data(x,self.Ina.power(),isoTime)


    def measure_adc(self) -> None:
        """Messung von analogen Spannungen am ADS1115
        
        Es können bis zu 4 Spannungen an den ADC Eingängen des ADS1115 über den I2C Bus gemessen werden.
        Anschließend speichert sie die Werte in den Array :class:`~tatooine_data.datapoint.DataPoint.data_last_measured`] ab.
            
        .. todo::
            Schaltungsaufbau beschreiben
            
        """        
               
        #--------------------------------------------------------------------
        # Erfassung der Messwerte des ADS1115 und anschließendes Abspeichern 
        #--------------------------------------------------------------------
        isoTime = datetime.now()
                
        for x in self.data_last_measured:        
            if x.id == "__U_ADC1":
                self._store_data(x,self.Adc1.getVoltage(),isoTime)
            if x.id == "__U_ADC2":
                self._store_data(x,self.Adc2.getVoltage(),isoTime)
            if x.id == "__U_ADC3":
                self._store_data(x,self.Adc3.getVoltage(),isoTime)
    
    def measure_gyro(self) -> None:
        """Messung der Gyro Werte des MPU6050
        
        Mit dieser Funktion werden alle Messwert des MPU6050 über den I2C Bus ausgelesen. So können Beschleunigungen und Gierwinkel über die Achsen X, Y,Z erfasst werden. Anschließend speichert sie die Werte in den Array[:class:`~tatooine_data.datapoint.DataPoint.data_last_measured`] ab. 
        
        """        
        
        #--------------------------------------------------------------------
        # Erfassung der Messwerte des MPU6050 und anschließendes Abspeichern 
        #--------------------------------------------------------------------
        isoTime = datetime.now()
        accel_data = self.mpu.get_accel_data(True)
        gyro_data =self.mpu.get_gyro_data()
        
        for x in self.data_last_measured:        
            if x.id == "__ACC_X":
                self._store_data(x,accel_data['x'],isoTime)
            if x.id == "__ACC_Y":
                self._store_data(x,accel_data['y'],isoTime)
            if x.id == "__ACC_Z":
                self._store_data(x,accel_data['z'],isoTime)
            if x.id == "__GYRO_X":
                self._store_data(x,gyro_data['x'],isoTime)
            if x.id == "__GYRO_Y":
                self._store_data(x,gyro_data['y'],isoTime)
            if x.id == "__GYRO_Z":
                self._store_data(x,gyro_data['z'],isoTime)
            if x.id == "__GYRO_TEMP":
                self._store_data(x,self.mpu.get_temp(), isoTime)          
            
    
    def measure_1wire_ds18s20(self) -> None:
        """Auslesen aller DS18S20 Sensoren im 1-Wire Bus
        
        Die Methode fragt nach einander alle verbauten DS18S20 Sensoren ab und speichert die Werte in den Array[:class:`~tatooine_data.datapoint.DataPoint.data_last_measured`] ab. 
        
        """
        isoTime = datetime.now()

        # Starten der Multithreading Abfrage des 1-Wire Devices
        with concurrent.futures.ThreadPoolExecutor() as executor:
            # Einen Thread pro DS18s20 starten
            results = [executor.submit(self.one_wire.read_1w_sensor_ds18s20,i) 
                       for i in self.one_wire.list_ds18s20_devices()]
            
            # Wenn die Sensoren geantwortet haben
            for f in concurrent.futures.as_completed(results):
                # Abspeichern des entsprechenden Ergebnisses im Speicher der 
                # aktuellen Werte
                for x in self.data_last_measured:        
                    if x.id == f.result()[0]:
                        self._store_data(x,float(f.result()[1]),isoTime)


    def aquire_data_i2c(self) -> None:
        """Zentrale Methode zum Messen aller i2c Sensoren
        
        Die Methode aktualisiert alle Messwerte der verbauten i2c Sensoren.
        
        """        

        #-----------------------------------------------------------------------
        # Erfassung der Messwerte und anschließendes Abspeichern in der Historie
        #-----------------------------------------------------------------------
        self.measure_power()
        self.measure_adc()
        self.measure_gyro()
        

    def aquire_data_1wire(self) -> None:
        """Zentrale Methode zum auslesen aller 1 Wire Sensoren
        
        Die Methode aktualisiert alle Messwerte der verbauten 1-Wire Sensoren.
        """        
        
        #-----------------------------------------------------------------------
        # Erfassung der Messwerte und anschließendes Abspeichern in der Historie
        #-----------------------------------------------------------------------
        self.measure_1wire_ds18s20()
                     

    # ToDo Ausgabefunktion für die Konsole erstellen
    #-----------------------------------------------------------------------
    # # Erfassung der Messwerte und anschließendes Abspeichern in der Historie
    # #-----------------------------------------------------------------------
    
    # if print_out:
    #     DataPoint.print_header()
    #     for x in self.data_last_measured:
    #         DataPoint.print_data_line(x)                
    
 