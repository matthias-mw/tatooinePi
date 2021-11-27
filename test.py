import smbus
import time
import i2c_ads1115 as ADS1115


# Get I2C bus
bus = smbus.SMBus(1)

ADC1 = ADS1115.AnalogIn(bus,ADS1115.MUX_AIN0_GND,4.096)
ADC2 = ADS1115.AnalogIn(bus,ADS1115.MUX_AIN1_GND,4.096)
ADC3 = ADS1115.AnalogIn(bus,ADS1115.MUX_AIN2_GND,4.096)


while True:
    
    ADC1.measure_analogIn()
    ADC2.measure_analogIn()
    ADC3.measure_analogIn()

    #print(ADC1.voltage)
    print(ADC1.__dict__)
    #print(ADC2.voltage)
    print(ADC2.__dict__)
    #print(ADC3.voltage)
    print(ADC3.__dict__)
    
    print("...")
    # Output data to screen

    ADC1.print_config()
    #Verzögerung
    time.sleep(10)