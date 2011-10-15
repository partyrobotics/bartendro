#!/usr/bin/env python

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

    def open(self):
        '''Open the serial connection to the master'''

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

    def send_test(self):
        while True:
            self.ser.write('A\r\n')

    def receive_test(self):
        while True:
            print self.ser.read()

    def chain_test(self):

        # reset the chain
        print "set SS low"
        self.ss.low()
        sleep(1)

        print "set SS high"
        self.ss.high()
        sleep(.2)
        print "set SS low"
        self.ss.low()
        sleep(.2)

        print "Transmit address character"
        while True:
            self.ser.write(chr(0))
	    r = self.ser.read(1)
            if len(r) == 0:
                continue
            break

	print "received %d chars:" % len(r)
	for ch in r:
	    print "  %d" % ord(r),
        print
        print

    def addr_test(self):
        self.ser.write(0);

    def close(self):
        self.ser.close()
        self.ser = None

    def send(self, cmd):
        self.ser.write(cmd)
        ret = self.ser.readline()
        print ret

if __name__ == "__main__":
    md = MasterDriver("/dev/ttyS1", "log");
    md.open()
    md.chain_test()
    sleep(2)
    while True:
        md.send("7 disp 3000\n")
        md.send("6 disp 3000\n")
        sleep(15)
