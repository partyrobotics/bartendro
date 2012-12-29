#!/usr/bin/env python

import os
from subprocess import call
from time import sleep, localtime
import smbus
import serial
import random
from struct import pack

BAUD_RATE = 38400

MAX_DISPENSERS = 15
SHOT_TICKS     = 20

PACKET_ACK_OK      = 0
PACKET_CRC_FAIL    = 1
PACKET_ACK_TIMEOUT = 2

PACKET_PING            = 3
PACKET_SET_MOTOR_SPEED = 4
PACKET_TICK_DISPENSE   = 5
PACKET_TIME_DISPENSE   = 6
PACKET_BROADCAST       = 0xFF

ROUTER_BUS              = 0
ROUTER_ADDRESS          = 4
ROUTER_SELECT_CMD_BEGIN = 0
ROUTER_SELECT_CMD_END   = MAX_DISPENSERS
ROUTER_CMD_PING  = 253
ROUTER_CMD_COUNT = 254
ROUTER_CMD_RESET = 255

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
        self.num_dispensers = 2
        self.selected = 0
        self.cl = None; #open("logs/comm.log", "a")
        self.software_only = software_only
        self.router = None

    def log(self, msg):
        return
        if self.software_only: return
        try:
            t = localtime()
            self.cl.write("%d-%d-%d %d:%02d %s" % (t.tm_year, t.tm_mon, t.tm_mday, t.tm_hour, t.tm_min, msg))
            self.cl.flush()
        except IOError:
            pass

    def reset(self):
        if self.software_only: return
        self.router.write_byte(ROUTER_ADDRESS, ROUTER_CMD_RESET)

    def select(self, dispenser):
        if self.software_only: return
        if dispenser < self.num_dispensers:
            self.selected = dispenser
            print "select dispenser %d" % self.selected
            self.router.write_byte(ROUTER_ADDRESS, dispenser)

    def count(self):
        return self.num_dispensers

    def open(self):
        '''Open the serial connection to the master'''

        if self.software_only: return

        try:
            print "Opening %s" % self.device
            self.ser = serial.Serial(self.device, 
                                     BAUD_RATE, 
                                     bytesize=serial.EIGHTBITS, 
                                     parity=serial.PARITY_NONE, 
                                     stopbits=serial.STOPBITS_ONE, 
                                     timeout=2)
        except serial.serialutil.SerialException:
            raise SerialIOError

        self.log("Opened %s for %d baud N81" % (self.device, BAUD_RATE))

        try:
            self.router = smbus.SMBus(ROUTER_BUS)
        except IOError:
            raise I2CIOError

        self.reset();

    def close(self):
        if self.software_only: return
        self.ser.close()
        self.bus.close()
        self.ser = None
        self.bus = None

    def crc16_update(self, crc, a):
        crc ^= a;
        for i in xrange(0, 8):
            if crc & 1:
                crc = (crc >> 1) ^ 0xA001;
            else:
                crc = (crc >> 1);

        return crc;

    def send_packet(self, packet):
        if self.software_only: return True
        print "Send packet to %d" % self.selected
        self.ser.write(packet)
        crc = 0
        for ch in packet:
            crc = self.crc16_update(crc, ord(ch))
        self.ser.write(pack("<H", crc))

        ch = self.ser.read(1)
        if len(ch) < 1:
            print "timeout"
            return False
        return True

    def send_packet8(self, dest, type, val):
        return self.send_packet(pack("BBBBBB", dest, type, val, 0, 0, 0))

    def send_packet16(self, dest, type, val):
        return self.send_packet(pack("<BBHH", dest, type, val, 0))

    def send_packet32(self, dest, type, val):
        return self.send_packet(pack("<BBI", dest, type, val))

    def make_shot(self):
        self.send_packet32(0, 5, 80)
        return True

    def ping(self):
        self.send_packet32(self.selected, PACKET_PING, 0)
        return True

    def start(self, dispenser):
        self.select(dispenser)
        return self.send_packet8(dispenser, PACKET_SET_MOTOR_SPEED, 255)

    def stop(self, dispenser):
        self.select(dispenser)
        return self.send_packet8(dispenser, PACKET_SET_MOTOR_SPEED, 0)

    def dispense_time(self, dispenser, duration):
        return True

    def dispense_ticks(self, dispenser, ticks):
        print "dispense %d ticks" % ticks
        self.select(dispenser)
        return self.send_packet32(dispenser, PACKET_TICK_DISPENSE, ticks)
        return True

    def led(self, dispenser, r, g, b):
        return True

    def is_dispensing(self, dispenser):
        return False

    def get_liquid_level(self, dispenser):
        return 80

    def get_dispense_stats(self, dispenser):
        return (0, 0)

if __name__ == "__main__":
    md = MasterDriver("/dev/ttyAMA0", 0);
    md.open()
    sleep(6)
    while True:
        print "ping 0"
        md.select(0)
        sleep(.1)
        md.ping()
        sleep(1)
        print "ping 1"
        md.select(1)
        md.ping()
        sleep(1)
