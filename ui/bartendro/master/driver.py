#!/usr/bin/env python

import os
from bartendro.utils import log, error, local
from subprocess import call
from gpio import GPIO
from time import sleep, localtime
import serial
import random

BAUD_RATE = 38400

MAX_DISPENSERS = 15

class SttyNotFoundException:
    pass

class SerialPortException:
    pass

class SerialIOError:
    pass

class LogFileException:
    pass

class MasterDriver(object):
    '''This object interacts with the bartendro master controller.'''

    def __init__(self, device, software_only):
        self.device = device
        self.ser = None
        self.msg = ""
        self.ret = 0
        self.ss = GPIO(134)
        self.ss.setup()
        self.num_dispensers = 0
        self.cl = open("logs/comm.log", "a")
        self.software_only = software_only

    def log(self, msg):
        if self.software_only: return
        try:
            t = localtime()
            self.cl.write("%d-%d-%d %d:%02d %s" % (t.tm_year, t.tm_mon, t.tm_mday, t.tm_hour, t.tm_min, msg))
            self.cl.flush()
        except IOError:
            pass

    def open(self):
        '''Open the serial connection to the master'''

        if self.software_only: return

        try:
            self.ser = serial.Serial(self.device, 
                                     BAUD_RATE, 
                                     bytesize=serial.EIGHTBITS, 
                                     parity=serial.PARITY_NONE, 
                                     stopbits=serial.STOPBITS_ONE, 
                                     timeout=2)
        except serial.serialutil.SerialException:
            raise SerialIOError;

        self.log("Opened %s for %d baud N81" % (self.device, BAUD_RATE))
        log("Opened %s for %d baud N81" % (self.device, BAUD_RATE))

    def close(self):
        if self.software_only: return
        self.ser.close()
        self.ser = None

    def chain_init(self):
        return True

    def make_shot(self):
        return True

    def count(self):
        return 1

    def start(self, dispenser):
        return True

    def stop(self, dispenser):
        return True

    def dispense_time(self, dispenser, duration):
        return True

    def dispense_ticks(self, dispenser, ticks):
        return True

    def led(self, dispenser, r, g, b):
        return True

    def is_dispensing(self, dispenser):
        return False

    def get_liquid_level(self, dispenser):
        return 50

    def ping(self, dispenser):
        return True

    def get_dispense_stats(self, dispenser):
        return (0, 0)

if __name__ == "__main__":
    md = MasterDriver("/dev/ttyAMA0");
    md.open()
    md.chain_init()
    sleep(1)
    md.dispense(0, 3000);
    while md.is_dispensing(0):
        sleep(.1)
