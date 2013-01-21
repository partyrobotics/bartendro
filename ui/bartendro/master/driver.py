#!/usr/bin/env python

import sys
import os
from subprocess import call
from time import sleep, localtime, time
import smbus
import serial
import random
from struct import pack, unpack
import pack7

BAUD_RATE = 9600

MAX_DISPENSERS = 15
SHOT_TICKS     = 20

RAW_PACKET_SIZE      = 10
PACKET_SIZE          =  8

PACKET_ACK_OK      = 0
PACKET_CRC_FAIL    = 1
PACKET_ACK_TIMEOUT = 2
PACKET_ACK_INVALID = 3
PACKET_ACK_INVALID_HEADER = 4
PACKET_ACK_HEADER_IN_PACKET = 5

PACKET_PING            = 3
PACKET_SET_MOTOR_SPEED = 4
PACKET_TICK_DISPENSE   = 5
PACKET_TIME_DISPENSE   = 6
PACKET_LED_OFF         = 7
PACKET_LED_IDLE        = 8
PACKET_LED_DISPENSE    = 9
PACKET_LED_DRINK_DONE  = 10
PACKET_IS_DISPENSING   = 11
PACKET_LIQUID_LEVEL    = 12
PACKET_COMM_TEST       = 0xFE

DEST_BROADCAST         = 0xFF

ROUTER_BUS              = 1
ROUTER_ADDRESS          = 4
ROUTER_SELECT_CMD_BEGIN = 0
ROUTER_SELECT_CMD_END   = MAX_DISPENSERS
ROUTER_CMD_SYNC_ON      = 251
ROUTER_CMD_SYNC_OFF     = 252
ROUTER_CMD_PING         = 253
ROUTER_CMD_COUNT        = 254
ROUTER_CMD_RESET        = 255

# TODO 
# NameError: global name 'I2CIOError' is not defined
# CHeck timeout ACK that comes in less than timeout time
# Improve error handling and repeating requests that failed
# Hook up more LED algs & drive during drink making

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
        self.num_dispensers = 7 
        self.selected = 0
        self.cl = None #open("logs/comm.log", "a")
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
        sleep(6)
        self.led_idle()

    def select(self, dispenser):
        if self.software_only: return
        if dispenser < self.num_dispensers and self.selected != dispenser:
            self.selected = dispenser
            self.router.write_byte(ROUTER_ADDRESS, dispenser)
            print "Selected dispenser %d" % dispenser
            sleep(.01)

    def sync(self, state):
        if self.software_only: return
        if (state):
            self.router.write_byte(ROUTER_ADDRESS, ROUTER_CMD_SYNC_ON)
        else:
            self.router.write_byte(ROUTER_ADDRESS, ROUTER_CMD_SYNC_OFF)

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

        self.reset()

    def close(self):
        if self.software_only: return
        self.ser.close()
        self.bus.close()
        self.ser = None
        self.bus = None

    def crc16_update(self, crc, a):
        crc ^= a
        for i in xrange(0, 8):
            if crc & 1:
                crc = (crc >> 1) ^ 0xA001
            else:
                crc = (crc >> 1)

        return crc

    def send_packet(self, dest, packet):
        if self.software_only: return True

        self.select(dest);

        for attempt in xrange(3):
            self.ser.flushInput()
            self.ser.flushOutput()

            crc = 0
            for ch in packet:
                crc = self.crc16_update(crc, ord(ch))

            encoded = pack7.pack_7bit(packet + pack("<H", crc))
            if len(encoded) != RAW_PACKET_SIZE:
                print "ERROR: Encoded packet size is wrong: %d vs %s" % (len(encoded), RAW_PACKET_SIZE)
                return False

            t0 = time()
            written = self.ser.write(chr(0xFF) + chr(0xFF) + encoded)
            if written != RAW_PACKET_SIZE + 2:
                print "ERROR: Send timeout"
                continue

            if dest == DEST_BROADCAST:
                return True

            ch = self.ser.read(1)
            t1 = time()
            print "packet time: %f" % (t1 - t0)
            if len(ch) < 1:
                print "  * read timeout"
                continue

            ack = ord(ch)
            if ack == PACKET_ACK_OK: return True
            if ack == PACKET_CRC_FAIL: 
                print "  * crc fail"
                continue
            if ack == PACKET_ACK_TIMEOUT: 
                print "  * ack timeout"
                continue
            if ack == PACKET_ACK_INVALID: 
                print "  * dispenser received invalid packet"
                continue
            if ack == PACKET_ACK_INVALID_HEADER: 
                print "  * dispenser received invalid header"
                continue
            if ack == PACKET_ACK_HEADER_IN_PACKET:
                print "  * header in packet error"
                continue


            # if we get an invalid ack code, it might be ok. 
            print "  * Invalid ACK code %d" % ord(ch)
        return False

    def send_packet8(self, dest, type, val):
        return self.send_packet(dest, pack("BBBBBB", dest, type, val, 0, 0, 0))

    def send_packet16(self, dest, type, val):
        return self.send_packet(dest, pack("<BBHH", dest, type, val, 0))

    def send_packet32(self, dest, type, val):
        return self.send_packet(dest, pack("<BBI", dest, type, val))

    def receive_packet(self):
        if self.software_only: return True

        header = 0
        while True:
            ch = self.ser.read(1)
            if len(ch) < 1:
                print "receive packet response timeout"
                return (PACKET_ACK_TIMEOUT, "")
            else:
                print "header received: %02X" % ord(ch)

            if (ord(ch) == 0xFF):
                header += 1
            else:
                header = 0

            if header == 2:
                break

        print "received header"

        ack = PACKET_ACK_OK
        raw_packet = self.ser.read(RAW_PACKET_SIZE)
        if len(raw_packet) != RAW_PACKET_SIZE:
            print "receive packet timeout"
            ack = PACKET_ACK_TIMEOUT

        if ack == PACKET_ACK_OK:
            packet = pack7.unpack_7bit(raw_packet)
            if len(packet) != PACKET_SIZE:
                ack = PACKET_ACK_INVALID
                print "ERROR: Unpacked length incorrect"

            if ack == PACKET_ACK_OK:
                received_crc = unpack("<H", packet[6:8])[0]
                packet = packet[0:6]

                crc = 0
                for ch in packet:
                    crc = self.crc16_update(crc, ord(ch))

                if received_crc != crc:
                    print "CRC fail"
                    ack = PACKET_ACK_CRC_FAIL

        # Send the response back to the dispenser
        if self.ser.write(chr(ack)) != 1:
            print "Send ack timeout!"
            ack = PACKET_ACK_TIMEOUT

        if ack == PACKET_ACK_OK:
            return (ack, packet)
        else:
            return (ack, "")

    def receive_packet8(self):
        ack, packet = self.receive_packet()
        if ack == PACKET_ACK_OK:
            data = unpack("BBBBBB", packet)
            return (ack, data[2])
        else:
            return (ack, 0)

    def receive_packet16(self):
        ack, packet = self.receive_packet()
        if ack == PACKET_ACK_OK:
            data = unpack("<BBHH", packet)
            return (ack, data[2])
        else:
            return (ack, 0)

    def make_shot(self):
        self.send_packet32(0, PACKET_TICK_DISPENSE, 80)
        return True

    def ping(self, dispenser):
        return self.send_packet32(dispenser, PACKET_PING, 0)

    def start(self, dispenser):
        return self.send_packet8(dispenser, PACKET_SET_MOTOR_SPEED, 255)

    def stop(self, dispenser):
        return self.send_packet8(dispenser, PACKET_SET_MOTOR_SPEED, 0)

    def dispense_time(self, dispenser, duration):
        return True

    def dispense_ticks(self, dispenser, ticks):
        return self.send_packet32(dispenser, PACKET_TICK_DISPENSE, ticks)

    def led_off(self):
        self.sync(0)
        self.send_packet8(DEST_BROADCAST, PACKET_LED_OFF, 0)
        return True

    def led_idle(self):
        self.sync(0)
        self.send_packet8(DEST_BROADCAST, PACKET_LED_IDLE, 0)
        sleep(.01)
        self.sync(1)
        return True

    def led_dispense(self):
        self.sync(0)
        self.send_packet8(DEST_BROADCAST, PACKET_LED_DISPENSE, 0)
        sleep(.01)
        self.sync(1)
        return True

    def led_complete(self):
        self.sync(0)
        self.send_packet8(DEST_BROADCAST, PACKET_LED_DRINK_DONE, 0)
        sleep(.01)
        self.sync(1)
        return True

    def comm_test(self):
        self.sync(0)
        return self.send_packet8(0, PACKET_COMM_TEST, 0)

    def is_dispensing(self, dispenser):
        while True:
            if self.send_packet8(dispenser, PACKET_IS_DISPENSING, 0):
                ack, value = self.receive_packet8()
                if ack == PACKET_ACK_OK:
                    return value

    def get_liquid_level(self, dispenser):
        return 100
        while True:
            if self.send_packet8(dispenser, PACKET_LIQUID_LEVEL, 0):
                ack, value = self.receive_packet16()
                if ack == PACKET_ACK_OK:
                    print "received packet ok"
                    return value

    def get_dispense_stats(self, dispenser):
        return (0, 0)

def ping_test(md):
    while True:
        disp = 0
        print "ping %d:" % disp
        md.ping(disp)
        sleep(1)

def led_test(md):
    while True:
        print "idle"
        md.led_idle()
        sleep(5)
        print "dispense"
        md.led_dispense()
        sleep(5)
        print "complete"
        md.led_complete()
        sleep(5)

def comm_test(md):
    print "put disp 0 into comm test"
    md.select(0)
    while not md.comm_test():
        sleep(1)

    print "put disp 1 into comm test"
    md.select(1)
    while not md.comm_test():
        sleep(1)

if __name__ == "__main__":
    md = MasterDriver("/dev/ttyAMA0", 0)
    md.open()
    sleep(3)
    print "Ping:"
    while not md.ping(0):
        pass

#    comm_test(md)
    val = md.is_dispensing(0)
    print "is dispensing: %d\n" % val

    sleep(2)

    print "Ping:"
    md.ping(0)
    print

#    val = md.get_liquid_level(1)
#    print "liquid level: %d\n" % val
    val = md.is_dispensing(0)
    print "is dispensing: %d\n" % val

    sleep(2)

    md.ping(0);

#    led_test(md)
#    dispense_test()
