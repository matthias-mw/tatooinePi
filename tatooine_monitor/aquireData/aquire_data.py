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
    
    data_last_measured = []

    
    
    def __init__(self, bus = None):
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
   
    def _store_data(self, data_point, value=0.0, unit = "-", time = datetime.now()):

        data_point.unit = unit
        data_point.update_value(value,time.timestamp())

    
    def measure_power(self):
        
        
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
            
    
    def aquire_data(self):
        

        #----------------------------------------------------------------------------
        # Erfassung der Messwerte und anschließendes Abspeichern in der Historie
        #----------------------------------------------------------------------------
        self.measure_power()
        self.measure_adc()
        self.measure_gyro()
       
        #----------------------------------------------------------------------------
        # Erfassung der Messwerte und anschließendes Abspeichern in der Historie
        #----------------------------------------------------------------------------
        DataPoint.print_header()
        for x in self.data_last_measured:
            DataPoint.print_data_line(x)
        
  
                     
                
        
 