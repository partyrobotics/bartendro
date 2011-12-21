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
        self.msg = ""
        self.ret = 0

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

    def get_error(self):
        return self.msg

    def send_command(self, cmd):

        self.ser.write("%s\r" % cmd)
#        print "w: '%s'" % cmd

        while True:
            line = self.ser.readline()
            if not line: 
                return (-1, "Communication timeout")
            if line: line = line.strip()
#            print "r: '%s'" % line
            if not line.startswith("#"): break

        try:
            ret, msg = line.split(" ", 1)
        except ValueError:
            return (-1, "Invalid response: '%s'" % line)

        return int(ret), msg

    def check(self):
        self.ret, self.msg = self.send_command("check")
        return not self.ret

    def count(self):
        self.ret, self.msg = self.send_command("count")
        if self.ret: return -1
        try:
            num, rest = self.msg.split(" ", 1)
        except ValueError:
            return -1
        return num

    def start(self, dispenser, speed):
        self.ret, self.msg = self.send_command("on %d %d" % (dispenser, speed))
        return not self.ret

    def stop(self, dispenser):
        self.ret, self.msg = self.send_command("off %d" % dispenser)
        return not self.ret

if __name__ == "__main__":
    md = MasterDriver("/dev/ttyACM0", "log");
    md.open()
    print "Check: ", md.check()
    print "Count: ", md.count()
    while True:
        r = md.start(1, 128)
        if r: 
            print "motor on"
        else:
            print md.get_error()
        sleep(1)

        r = md.start(2, 128)
        if r: 
            print "motor on"
        else:
            print md.get_error()
        sleep(1)

        r = md.stop(1);
        if r: 
            print "motor off"
        else:
            print md.get_error()
        sleep(1)

        r = md.stop(2);
        if r: 
            print "motor off"
        else:
            print md.get_error()
        sleep(1)
    sleep(1)
