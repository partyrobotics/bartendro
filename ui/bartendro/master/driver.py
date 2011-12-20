#!/usr/bin/env python

from subprocess import call
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
        self._get_line_saved = ""

    def open(self):
        '''Open the serial connection to the master'''

        print "open serial port, waiting for arduino reset.\n"
        call(["stty", "-F", self.device, "ispeed", "%d" % BAUD_RATE, "ospeed", "%d" % BAUD_RATE, "cs8", "-parenb"])
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

        sleep(2.5)
        self.ser.read(self.ser.inWaiting())

    def close(self):
        self.ser.close()
        self.ser = None

    def get_line(self):
        while True:
            line = self.ser.readline()
            if not line: continue
            if line: line = line.strip()
            print "r: '%s'" % line
            if not line.startswith("#"): return line

    def send_command(self, cmd):

        self.ser.write("%s\r" % cmd)
        print "w: '%s'" % cmd
#        line = self.get_line()
#        if line[0] == '!':
#            print "== Master rebooted!"

        while True:
            line = self.ser.readline()
            if not line: continue
            if line: line = line.strip()
            print "r: '%s'" % line
            if not line.startswith("#"): break

        print "result: '%s'" % line

#code, msg = line.split(' ')
#print "%s %s\n" % (code, msg)
        return line

    def check(self):
        self.send_command("check")

    def count(self):
        self.send_command("count")

    def start(self, dispenser, speed):
        self.send_command("on %d %d" % (dispenser, speed))

    def stop(self, dispenser):
        self.send_command("off %d" % dispenser)


md = MasterDriver("/dev/ttyACM0", "log");
md.open()
#md.start(1, 128)
#sleep(1)
#md.stop(1);
#sleep(1)

while True:
    md.start(1, 128);
    sleep(1)
#    md.start(2, 128);
#    sleep(1)
#    md.stop(1);
#    sleep(1)
    md.stop(1);
    sleep(1)
d.check()
d.count()
