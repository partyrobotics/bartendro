#!/usr/bin/env python

import os
from bartendro.utils import log, error, local
from time import sleep, localtime
import serial

BAUD_RATE = 38400

class SttyNotFoundException:
    pass

class SerialPortException:
    pass

class SerialIOError:
    pass

class LogFileException:
    pass

class LEDDriver(object):
    '''This object interacts with the bartendro master controller.'''

    def __init__(self, device):
        self.device = device
        self.ser = None
        self.cl = open("logs/comm.log", "a")

    def log(self, msg):
        try:
            t = localtime()
            self.cl.write("%d-%d-%d %d:%02d %s" % (t.tm_year, t.tm_mon, t.tm_mday, t.tm_hour, t.tm_min, msg))
            self.cl.flush()
        except IOError:
            pass

    def open(self):
        '''Open the serial connection to the leds'''

        try: 
            self.software_only = int(os.environ['BARTENDRO_SOFTWARE_ONLY'])
        except KeyError:
            self.software_only = 0

        if self.software_only:
            return

        try:
            self.ser = serial.Serial(self.device, 
                                     BAUD_RATE, 
                                     bytesize=serial.EIGHTBITS, 
                                     parity=serial.PARITY_NONE, 
                                     stopbits=serial.STOPBITS_ONE, 
                                     timeout=2)
        except serial.serialutil.SerialException:
            raise SerialIOError;

        self.log("Opened leds %s for %d baud N81" % (self.device, BAUD_RATE))
        log("Opened leds %s for %d baud N81" % (self.device, BAUD_RATE))

    def close(self):
        if self.software_only: return
        self.ser.close()
        self.ser = None

    def idle(self):
        if self.software_only: return
        self.ser.write("i")

    def make_drink(self):
        if self.software_only: return
        self.ser.write("p")

    def drink_complete(self):
        if self.software_only: return
        self.ser.write("d")

    def panic(self):
        if self.software_only: return
        self.ser.write("e")

    def warning(self):
        print "state: WARNING!"
        if self.software_only: return
        self.ser.write("w")

    def out_of_booze(self):
        print "state: OUT OF BOOZE!"
        if self.software_only: return
        self.ser.write("o")

    def all_good(self):
        print "state: ALL GOOD!"
        if self.software_only: return
        self.ser.write("g")
