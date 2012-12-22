#!/usr/bin/env python

import smbus
import time
bus = smbus.SMBus(0)
address = 4 

while True:
    bus.write_byte(address, 34)
    time.sleep(.1)
    bus.write_byte(address, 75)
    time.sleep(.1)
