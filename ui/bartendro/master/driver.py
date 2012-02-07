#!/usr/bin/env python

import os
from subprocess import call
from gpio import GPIO
from time import sleep
import serial

# stty -F /dev/ttyACM0 ispeed 9600 ospeed 9600 cs8 -parenb

#define OK                        0
#define BAD_DISPENSER_INDEX_ERROR 1
#define TRANSMISSION_ERROR        2
#define DISPENSER_FAULT_ERROR     3
#define INVALID_COMMAND_ERROR     4
#define INVALID_SPEED_ERROR       5

BAUD_RATE = 38400

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

    def __init__(self, device, logfile):
        self.device = device
        self.logfile = logfile
        self.ser = None
        self.msg = ""
        self.ret = 0
        self.ss = GPIO(135)
        self.ss.setup()
        self.num_dispensers = 0

    def open(self):
        '''Open the serial connection to the master'''

        try: 
            self.software_only = int(os.environ['BARTENDRO_SOFTWARE_ONLY'])
        except KeyError:
            self.software_only = 0

        if self.software_only:
            print "Running SOFTWARE ONLY VERSION. No communication between software and hardware chain will happen!"
            return

        try:
            self.ser = serial.Serial(self.device, 
                                     BAUD_RATE, 
                                     bytesize=serial.EIGHTBITS, 
                                     parity=serial.PARITY_NONE, 
                                     stopbits=serial.STOPBITS_ONE, 
                                     timeout=2)
            self.l = open(self.logfile, "a")
        except serial.serialutil.SerialException:
            raise SerialIOError;

        print "Opened %s for %d baud N81" % (self.device, BAUD_RATE)

    def chain_init(self):

        if self.software_only: return

        # reset the chain
        print "send reset"
        self.ss.low()
        sleep(1)

        self.ss.high()
        sleep(.2)
        self.ss.low()
        sleep(.2)

        print "address assignment"
        while True:
            self.ser.write(chr(0))
            r = self.ser.read(1)
            if len(r) == 0:
                continue
            break

        if len(r) > 0:
            self.num_dispensers = ord(r)
        else:
            print "Cannot communicate with dispenser chain!"

    def close(self):
        if self.software_only: return
        self.ser.close()
        self.ser = None

    def send(self, cmd):
        if self.software_only: return
        self.ser.write(cmd)
        return self.ser.readline()

    def count(self):
        return self.num_dispensers

    def start(self, dispenser):
        self.ret, self.msg = self.send("%d on\n" % dispenser)
        return self.ret

    def stop(self, dispenser):
        self.ret, self.msg = self.send("%d off\n" % dispenser)
        return self.ret

    def dispense(self, dispenser, duration):
        self.ret, self.msg = self.send("%d disp %d" % (dispenser, duration))
        return self.ret

    def led(self, dispenser, r, g, b):
        self.ret, self.msg = self.send("%d led %d %d %d" % (dispenser, r, g, b))
        return self.ret

if __name__ == "__main__":
    md = MasterDriver("/dev/ttyACM0", "log");
#    md = MasterDriver("/dev/ttyS1", "log");
    md.open()
    md.chain_init()
    sleep(2)
    while True:
        md.send("7 disp 3000\n")
        md.send("6 disp 3000\n")
        sleep(15)
