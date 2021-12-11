#Modul zur Bearbeitung der Zeitstempel
from datetime import datetime

# Klasse für die Abspeicherung der Datenpinkte
from aquireData.datapoint import DataPoint


#i2c Treiber - AD-Wandler ADS1115
from driver.i2c_ads1115  import ADS1115
#i2c Treiber - Powerüberwachung INA219
from driver.i2c_ina219 import INA219
from driver.i2c_ina219 import DeviceRangeError
#i2c Treiber - Gyroscope
from driver.i2c_mpu6050 import mpu6050




class AquireData:
    """Klasse zur zentralen Datenerfassung
    
    Mit dieser Klasse werde alle Messwerte von den verschiedenen Sensoren
    erfasst und entsprechend aufbereitet, um sie dann in einem Datenpunkt
    der Klasse XXXX abzuspeichern.
    
    """    
    __U_POWER_IT = "U_IT"
    __I_POWER_IT = "I_IT"
    __P_POWER_IT = "P_IT"
    __U_ADC1 = "U_BAT1"
    __U_ADC2 = "P_BAT2"
    __U_ADC3 = "P_BAT3"
    __ACC_X = "ACC_X"
    __ACC_Y = "ACC_Y"
    __ACC_Z = "ACC_Z"
    __GYRO_X = "GYRO_X"
    __GYRO_Y = "GYRO_Y"
    __GYRO_Z = "GYRO_Z"
    __GYRO_TEMP = "GYRO_TEMP"
    
    CHANNELS = [__U_POWER_IT,__I_POWER_IT,__P_POWER_IT,__U_ADC1,__U_ADC2,__U_ADC3,__ACC_X,__ACC_Y,__ACC_Z,__GYRO_X,__GYRO_Y,__GYRO_Z,__GYRO_TEMP]
    
    SHUNT_OHMS = 0.1
    
    _MAX_DATA_POINTS_HISTORY = 5
    """Anzahl der Werte die in der Datenhistorie betrachtet werden"""     
  
    data_last_measured = []
    """Array von Datapoint, welcher den aktuellen Messwert jedes verfügbaren Kanals bereit hält.
    """  
    
    
    def __init__(self, bus = None):
        """Initialisierung des Datenaquisition Klasse

        Bei der Initialisierung werden alles Objekte für den Zugriff auf die diversen Sensorchips (siehe ToDo ) erstellt und entsprechend konfiguriert.

        :param bus: Object das den Datenbus repräsentiert, defaults to None
        :type bus: Objekt(smbus), optional
        """        
        self.i2c_bus = bus
        
        self.Adc1 = ADS1115(bus,ADS1115.MUX_AIN0_GND,4.096)
        self.Adc2 = ADS1115(bus,ADS1115.MUX_AIN1_GND,4.096)
        self.Adc3 = ADS1115(bus,ADS1115.MUX_AIN2_GND,4.096)

        # Objekt für die Powerüberwachung anlegen
        self.Ina = INA219(self.SHUNT_OHMS,3,1,0x40)

        #Objekt für den MPU6050 anlegen
        self.mpu = mpu6050(0x68)
        isoTime = datetime.now()
        
        #initialisierung der aktuellen Messdaten
        self.data_last_measured =[DataPoint(x,"-",isoTime,0) for x in self.CHANNELS]
   
    def _store_data(self, data_point, value=0.0, unit = "-", 
                    time = datetime.now()):
        """Abspeichern eines Wertes in einen Datenpunkt

        Mit dieser internen Hilfsfunktion wird ein Messwert samt Einheit und Zeitstempel in den entsprechenden Datenpunkt abgespeichert.
        
        
        :param data_point: Datenpunktobjekt
        :type data_point: class DataPoint
        :param value: abzuspeichernder Messwert, defaults to 0.0
        :type value: float, optional
        :param unit: Einheit des Messwertes, defaults to "-"
        :type unit: str, optional
        :param time: Zeitstempel des Messwertes, defaults to datetime.now()
        :type time: datetime objekt, optional
        """        

        data_point.unit = unit
        data_point.update_value(value,time.timestamp())

    
    def measure_power(self):
        """Messung der Leistungsaufnahme des INA219
        
        Mittels des INA219 Sensors wird über I2C die aktuelle Spannung, die Stromaufnahme und die Leistungsaufnahme gemessen.
        """        
        
        
        #--------------------------------------------------------------------
        # Erfassung der Messwerte des INA219 und anschließendes Abspeichern 
        #--------------------------------------------------------------------
        self.Ina.configure()
        isoTime = datetime.now()
                
        for x in self.data_last_measured:
            if x.name == self.__U_POWER_IT:
                self._store_data(x,self.Ina.voltage(),"V",isoTime)
            if x.name == self.__I_POWER_IT:
                self._store_data(x,self.Ina.current(),"mA",isoTime)
            if x.name == self.__P_POWER_IT:
                self._store_data(x,self.Ina.power(),"mW",isoTime)


    def measure_adc(self):
        """Messung von analogen Spannungen am ADS1115
        
            Es können bis zu 4 Spannungen an den ADC Eingängen des ADS1115 über den I2C Bus gemessen werden.
            
            TODO
            Schaltungsaufbau beschreiben
            
        """        
               
        #--------------------------------------------------------------------
        # Erfassung der Messwerte des ADS1115 und anschließendes Abspeichern 
        #--------------------------------------------------------------------
        isoTime = datetime.now()
                
        for x in self.data_last_measured:        
            if x.name == self.__U_ADC1:
                self._store_data(x,self.Adc1.getVoltage(),"V",isoTime)
            if x.name == self.__U_ADC2:
                self._store_data(x,self.Adc2.getVoltage(),"V",isoTime)
            if x.name == self.__U_ADC3:
                self._store_data(x,self.Adc3.getVoltage(),"V",isoTime)
    
    def measure_gyro(self):
        """Messung der Gyro Werte des MPU6050
        
        Mit dieser Funktion werden alle Messwert des MPU6050 über den I2C Bus ausgelesen. So können Beschleunigungen und Gierwinkel über die Achsen X,Y,Z erfasst werden.
        
        """        
        
        #--------------------------------------------------------------------
        # Erfassung der Messwerte des MPU6050 und anschließendes Abspeichern 
        #--------------------------------------------------------------------
        isoTime = datetime.now()
        accel_data = self.mpu.get_accel_data(True)
        gyro_data =self.mpu.get_gyro_data()
        
        for x in self.data_last_measured:        
            if x.name == self.__ACC_X:
                self._store_data(x,accel_data['x'],"g",isoTime)
            if x.name == self.__ACC_Y:
                self._store_data(x,accel_data['y'],"g",isoTime)
            if x.name == self.__ACC_Z:
                self._store_data(x,accel_data['z'],"g",isoTime)
            if x.name == self.__GYRO_X:
                self._store_data(x,gyro_data['x'],"dps",isoTime)
            if x.name == self.__GYRO_Y:
                self._store_data(x,gyro_data['y'],"dps",isoTime)
            if x.name == self.__GYRO_Z:
                self._store_data(x,gyro_data['z'],"dps",isoTime)
            if x.name == self.__GYRO_TEMP:
                self._store_data(x,self.mpu.get_temp(), 'grdC',isoTime)          
            
    
    def aquire_data(self, print_out = False):
        """Zentrale Funktion zum Messen und anzeigen aller Daten
        
        Die Funktion fragt nach einander alle verbauten Sensoren ab und speichert damit die werte in den Array[Datapoint] data_last_measured ab. Anschließend erfolgt eine Ausgabe in der Console.
                
        """        

        #----------------------------------------------------------------------------
        # Erfassung der Messwerte und anschließendes Abspeichern in der Historie
        #----------------------------------------------------------------------------
        self.measure_power()
        self.measure_adc()
        self.measure_gyro()
       
        #----------------------------------------------------------------------------
        # Erfassung der Messwerte und anschließendes Abspeichern in der Historie
        #----------------------------------------------------------------------------
        
        if print_out:
            DataPoint.print_header()
            for x in self.data_last_measured:
                DataPoint.print_data_line(x)
            
  
                     
                
        
 