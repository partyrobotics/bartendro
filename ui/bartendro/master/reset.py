#!/usr/bin/env python

from gpio import GPIO
from time import sleep

ss = GPIO(134)
ss.setup()

ss.high()
sleep(.2)
ss.low()
