from typing import ClassVar
import smbus
import time
from datetime import datetime
import copy

#i2c - AD-Wandler INA219
import i2c_ads1115 as ADS1115
#i2c - Powerüberwachung INA219
from i2c_ina219 import INA219
from i2c_ina219 import DeviceRangeError
#i2c - Gyroscope
from i2c_mpu6050 import mpu6050


# Get I2C bus
bus = smbus.SMBus(1)








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
    
    data = []
    data_history = []
    
    
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
        
        for x in self.CHANNELS:
            self.data.append(DataPoint(x,"-",isoTime,0))
   
    def _store_data(self, data_point, value=0.0, unit = "-", time = datetime.now()):
        data_point.unit = unit
        data_point.time = time
        data_point.value = value      
        #print('gemessen ... -> {0:<15s} {1:s} {2:>10.2f} {3:s}'.format(data_point.name, time.strftime("%m/%d/%Y - %H:%M:%S"), value, unit))
    
    def measure_power(self):

        self.Ina.configure()
        isoTime = datetime.now()
                
        for x in self.data:
            if x.name == self.__U_POWER_IT:
                self._store_data(x,self.Ina.voltage(),"V",isoTime)
            if x.name == self.__I_POWER_IT:
                self._store_data(x,self.Ina.current(),"mA",isoTime)
            if x.name == self.__P_POWER_IT:
                self._store_data(x,self.Ina.power(),"mW",isoTime)

    def measure_adc(self):

        isoTime = datetime.now()
        self.Adc1.measure_analogIn()
        self.Adc2.measure_analogIn()
        self.Adc3.measure_analogIn()
                
        for x in self.data:        
            if x.name == self.__U_ADC1:
                self._store_data(x,self.Adc1.voltage,"V",isoTime)
            if x.name == self.__U_ADC2:
                self._store_data(x,self.Adc2.voltage,"V",isoTime)
            if x.name == self.__U_ADC3:
                self._store_data(x,self.Adc3.voltage,"V",isoTime)
    
    def measure_gyro(self):
        
        isoTime = datetime.now()
        accel_data = self.mpu.get_accel_data(True)
        gyro_data =self.mpu.get_gyro_data()
        
        for x in self.data:        
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
                self._store_data(x,self.mpu.get_temp(), chr(176)+'C',isoTime)          
            
    
    def aquire_data(self):
        

        #----------------------------------------------------------------------------
        # Erfassung der MEsswerte und anschließendes Abspeichern in der Historie
        #----------------------------------------------------------------------------    
        #self.measure_power()
        self.measure_adc()
        self.measure_gyro()
        tmp = copy.deepcopy(self.data)
        
        if len(self.data_history) > self._MAX_DATA_POINTS_HISTORY:
            del self.data_history[0]
        
        self.data_history.append(tmp)
       

       
        print(chr(27) + "[2J")
        print('Channel               Value          Deviation  ')     
        print('=============================================================')
        #----------------------------------------------------------------------------
        # Berechnung der Mittelwerte und aktuellen Abweichung für die gesamte Historie
        #----------------------------------------------------------------------------
        # #Auswahl des zu bearbeitenden Messkanals
        for chn in self.CHANNELS:
            #Init
            last = 0
            mean = 0
            dev = 0
            #Gehe durch jedes Datenpaket in der Historie
            for cur_data in self.data_history:
                #Gehe durch jeden Kanal des Datenpaketes
                for chn_sel in cur_data:  
                    #Führe die Berechnung für den Kanal durch  
                    if chn_sel.name == chn:
                        mean += chn_sel.value
                        last = chn_sel.value
                        break
                    
            #Berechne die Statistikdaten
            mean = mean / len(self.data_history)
            dev = abs(mean - last)
            if dev == 0:
                dev_per = 0
            else:
                dev_per = dev/ mean
        
            #ToDo DebugInfo
            print('{0:15s}  {1:10.3f}{2:<4s} {3:11.4f}{2:<4s}  {4:7.4f}%'.format(chn,mean,chn_sel.unit, dev, dev_per))     
            #self.show_history(chn)  
            
            
            
        
        
        
                  
        
        

        
        
    def show_history(self,chn = __U_POWER_IT):
        
        tmp = ""
        cnt = 0
        mean = 0
        
        for x in self.data_history:
            for y in x:    
                if y.name == chn:
                    tmp = tmp + '{0:>10.2f} {1:s}'.format(y.value, y.unit)
                    mean += y.value
                    
        mean = mean / len(self.data_history)
        print(tmp + '-> Mittelwert: {0:>10.2f}'.format(mean))
        
                     
                
        
        
             

class   DataPoint():
    
    interval_std    = 10
    interval_fast   = 0.1
    thd_deviation_abs = 10
    thd_deviation_per = 5
    value_mean = 0
    value_dev = 0
    
        
    def __init__(self, name, unit, time, value):
        
        self.name = name
        self.unit = unit
        self.time = time
        self.value = value
        
    
 
 
Data = AquireData(bus)

cnt = 0
while cnt < 10:
    cnt =1
    Data.aquire_data()
    #Data.measure_gyro()
    time.sleep(0.1)
