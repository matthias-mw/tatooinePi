#!/usr/bin/env python3

import logging
import smbus
import time

from aquireData.aquire_data import AquireData

from aquireData.store_data import StoreDataToInflux


# Get I2C bus
bus = smbus.SMBus(1)

if __name__ == '__main__':



        
        
    inflDB = StoreDataToInflux()

    

    Data = AquireData(bus)

    cnt = 0
    while True:
        cnt +=1
        
        Data.aquire_data()
        
        inflDB.check_db_connection()
        inflDB.store_data(Data.data_last_measured,cnt)
        

        
        
        
        time.sleep(0.25)
