from typing import ClassVar
import smbus
import time
from datetime import datetime
from dataclasses import dataclass
from dataclasses import field


#i2c - AD-Wandler INA219
import i2c_ads1115 as ADS1115
#i2c - Powerüberwachung INA219
from i2c_ina219 import INA219
from i2c_ina219 import DeviceRangeError
#i2c - Gyroscope
from i2c_mpu6050 import mpu6050


# Get I2C bus
bus = smbus.SMBus(1)



@dataclass
class   DataPoint():
    
    name: str = '-'
    unit: str = '-'
    timestamp: float = 0
    value: float = 0
    interval_std: float = 10
    interval_fast: float   = 0.1
    thd_deviation_abs: float = 10
    thd_deviation_per: float = 5
    value_mean: float = 0
    value_dev_perc: float = 0
    value_dev_abs: float = 0
    history_length: int = 10
    timestamp_history: list[float] = field(default_factory=list)
    value_history: list[float] = field(default_factory=list)
    
    
    
    def update_value(self, new_value, new_timestamp):
        
        
        #----------------------------------------------------------------------------
        # Ältesten Wert aus der Historie entfernen
        #----------------------------------------------------------------------------        
        if len(self.value_history) >= self.history_length:
            del self.value_history[0]
            
        if len(self.timestamp_history) >= self.history_length:
            del self.timestamp_history[0]
        
        #----------------------------------------------------------------------------
        # Updaten der Werte und Historie
        #----------------------------------------------------------------------------        
        self.value_history.append(new_value)
        self.value = new_value
        self.timestamp_history.append(new_timestamp)
        self.timestamp = new_timestamp
        
        #----------------------------------------------------------------------------
        # Berechnung der Mittelwerte und aktuellen Abweichung für die gesamte Historie
        #----------------------------------------------------------------------------        
        mean = 0
        
        for x in self.value_history:
            mean += x
               
        #Berechne die Statistikdaten
        self.value_mean = mean / len(self.value_history)
        self.value_dev_abs = abs(self.value_mean - self.value)
        if self.value_mean == 0:
            self.value_dev_perc = 0
        else:
            self.value_dev_perc = self.value_dev_abs / self.value_mean *100        
        
    def print_data_line(self):
        
        print('{0:15s}  {1:10.2f}{5:>5s} {2:10.3f}{5:>5s} {3:10.3f}{5:>5s} {4:9.4f} %'.format(self.name,self.value, self.value_mean, self.value_dev_abs, self.value_dev_perc, self.unit))             
    
    def print_header():
        
        print(chr(27) + "[2J")
        print('Channel               Value            Mean                  Deviation  ')     
        print('================================================================================')




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
        
        self.Adc1 = ADS1115.AnalogIn(bus,ADS1115.MUX_AIN0_GND,4.096)
        self.Adc2 = ADS1115.AnalogIn(bus,ADS1115.MUX_AIN1_GND,4.096)
        self.Adc3 = ADS1115.AnalogIn(bus,ADS1115.MUX_AIN2_GND,4.096)

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
        self.Adc1.measure_analogIn()
        self.Adc2.measure_analogIn()
        self.Adc3.measure_analogIn()
                
        for x in self.data_last_measured:        
            if x.name == self.__U_ADC1:
                self._store_data(x,self.Adc1.voltage,"V",isoTime)
            if x.name == self.__U_ADC2:
                self._store_data(x,self.Adc2.voltage,"V",isoTime)
            if x.name == self.__U_ADC3:
                self._store_data(x,self.Adc3.voltage,"V",isoTime)
    
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
        
  
                     
                
        
        
             

        
        
 
Data = AquireData(bus)

cnt = 0
while cnt < 10:
    cnt =1
    Data.aquire_data()
    #Data.measure_gyro()
    time.sleep(0.3)
