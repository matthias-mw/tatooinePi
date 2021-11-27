import logging
import smbus
import time
import i2c_ads1115 as ADS1115

from i2c_ina219 import INA219

from i2c_ina219 import DeviceRangeError

from i2c_mpu6050 import mpu6050


# Get I2C bus
bus = smbus.SMBus(1)

ADC1 = ADS1115.AnalogIn(bus,ADS1115.MUX_AIN0_GND,4.096)
ADC2 = ADS1115.AnalogIn(bus,ADS1115.MUX_AIN1_GND,4.096)
ADC3 = ADS1115.AnalogIn(bus,ADS1115.MUX_AIN2_GND,4.096)


SHUNT_OHMS = 0.1


def read():
    ina = INA219(SHUNT_OHMS,3,1,0x40)
    ina.configure()

    print("Bus Voltage: %.3f V" % ina.voltage())
    try:
        print("Bus Current: %.3f mA" % ina.current())
        print("Power: %.3f mW" % ina.power())
        print("Shunt voltage: %.3f mV" % ina.shunt_voltage())
    except DeviceRangeError as e:
        # Current out of device range with specified shunt resistor
        print(e)


mpu = mpu6050(0x68)
    

while True:
    
    ADC1.measure_analogIn()
    ADC2.measure_analogIn()
    # ADC3.measure_analogIn()

    read()

    # #print(ADC1.voltage)
    print(ADC1.__dict__)
    # #print(ADC2.voltage)
    print(ADC2.__dict__)
    # #print(ADC3.voltage)
    # print(ADC3.__dict__)
    
    # print("...")
    # # Output data to screen

    # ADC1.print_config()
    
    
    print(mpu.get_temp())
    accel_data = mpu.get_accel_data(True)
    print("ax: ",accel_data['x'])
    print("ay: ",accel_data['y'])
    print("az: ",accel_data['z'])
    gyro_data = mpu.get_gyro_data()
    print("gyroX:", gyro_data['x'])
    print("gyroY:",gyro_data['y'])
    print("gyroZ:",gyro_data['z'])
    
    #Verzögerung
    time.sleep(1)