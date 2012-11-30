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

    def chain_init(self):
        if self.software_only: 
            self.num_dispensers = 15
            return

        log("initialize communication chain")
        self.log("initialize communication chain")

        # reset the chain
        print "send reset"
        self.ss.low()
        sleep(1)

        self.ss.high()
        sleep(.1)
        self.ss.low()
        sleep(.1)

        print "address assignment"
        while True:
            self.ser.write("0\n")
            r = self.ser.readline()
            if len(r) == 0:
                continue
            break

        if len(r) > 0:
            r= r[0:-1]
	    print "received '%s'" % r
            num = int(r)
            if num < 1 or num > MAX_DISPENSERS:
		msg = "Found an invalid number of dispensers. Communication chain busted!"
                self.log(msg)
		error(msg)
                self.num_dispensers = -1;
            else: 
		msg = "found %d dispensers" % int(r)
                self.log(msg)
		error(msg)
		self.num_dispensers = int(r)
                sleep(1)
        else:
            error("Cannot communicate with dispenser chain!")
            self.log("Cannot communicate with dispenser chain!")

    def close(self):
        if self.software_only: return
        self.ser.close()
        self.ser = None

    def send(self, cmd):
        if self.software_only: return
        self.ser.write(cmd)
        self.log("w: '%s'\n" % cmd.replace("\n", ""))
        ret = self.ser.readline()
        if ret == "": 
            msg = "Serial comms timeout after cmd '%s'." % cmd[0:len(cmd)-1]
            error(msg)
            self.log(msg)
        else:
            self.log("r: '%s'\n" % ret.replace("\n", ""))
        return ret

    def count(self):
        return self.num_dispensers

    def start(self, dispenser):
        return self.send("%d on\n" % dispenser)

    def stop(self, dispenser):
        return self.send("%d off\n" % dispenser)

    def dispense_time(self, dispenser, duration):
        return self.send("%d timedisp %d\n" % (dispenser, duration))

    def dispense_ticks(self, dispenser, ticks):
        return self.send("%d tickdisp %d\n" % (dispenser, ticks))

    def led(self, dispenser, r, g, b):
        return self.send("%d led %d %d %d\n" % (dispenser, r, g, b))

    def is_dispensing(self, dispenser):
        '''expects "!3 isdisp 1" '''

        if self.software_only: return False

        self.send("%d isdisp\n" % dispenser)
        ret = self.ser.readline()
        if not ret: 
            msg = "is_dispensing timeout!"
            self.log(msg)
            error(msg)
	    return False
        try:
            self.log("r: '%s'\n" % ret.replace("\n", ""))
            disp, cmd, value = ret.split(" ")
	    if value[0] == '1': 
	        return True
	    else:
	        return False
        except ValueError:
            self.log("parse error")
	    return False

    def get_liquid_level(self, dispenser):
        '''expects "!3 level 69" '''

        if self.software_only: return 100 #int(random.random() * 26)

        self.send("%d level\n" % dispenser)
        ret = self.ser.readline()
        if not ret: 
            msg = "get level timeout!"
            self.log(msg)
            error(msg)
	    return -1
        try:
            self.log("r: '%s'\n" % ret.replace("\n", ""))
            disp, cmd, value = ret.split(" ")
            return int(value)
        except ValueError:
            self.log("parse error")
	    return -1

    def ping(self, dispenser):
        '''expects "!3 pong" '''
        if self.software_only: return True

        self.send("%d ping\n" % dispenser)
        ret = self.ser.readline()
        if not ret: 
            msg = "ping response timeout"
            self.log(msg)
            error(msg)
	    return False

 	ret = ret[:-1]
        try:
            ret = ret[1:] # strip off the !
            disp, cmd = ret.split(" ")
 	    disp = int(disp)
	    if disp == dispenser: 
	        return True
	    else:
                msg = "wrong dispenser number in pong"
                self.log("wrong dispenser number in pong")
                error(msg)
	        return False
        except ValueError:
            msg = "error parsing pong data. response: '%s'" % ret
            self.log(msg)
            error(msg)
	    return False

    def get_dispense_stats(self, dispenser):
        '''expects "!3 dispstats <time> <ticks>" '''
        if self.software_only: return True

        self.send("%d dispstat\n" % dispenser)
        ret = self.ser.readline()
        print "'%s'\n" % ret
        if not ret: 
            msg = "dispstat response timeout"
            self.log(msg)
            error(msg)
            return (-1, -1)

 	ret = ret[:-1]
        try:
            ret = ret[1:] # strip off the !
            disp, cmd, t, ticks = ret.split(" ")
 	    disp = int(disp)
	    if disp == dispenser: 
	        return (-1, -1)
	    else:
                msg = "wrong dispenser number in pong"
                self.log("wrong dispenser number in pong")
                error(msg)
	        return False
            t = int(t)
            ticks = int(ticks)
            return (t, ticks)
        except ValueError:
            msg = "error parsing pong data. response: '%s'" % ret
            self.log(msg)
            error(msg)
	    return (-1, -1)

if __name__ == "__main__":
    md = MasterDriver("/dev/ttyS1");
    md.open()
    md.chain_init()
    sleep(1)
    md.dispense(0, 3000);
    while md.is_dispensing(0):
        sleep(.1)
