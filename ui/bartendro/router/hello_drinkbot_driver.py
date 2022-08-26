import sys
import pdb
import os
import collections
import logging
from subprocess import call
from time import sleep, localtime, time
import serial
from struct import pack, unpack
import bartendro.router.pack7
#import pack7
#import dispenser_select
#from bartendro.error import SerialIOError
import random

import threading

#try:
#    from Adafruit_MotorHAT import Adafruit_MotorHAT, Adafruit_DCMotor
#except:
#    pass

# import atext

DISPENSER_DEFAULT_VERSION = 2
DISPENSER_DEFAULT_VERSION_SOFTWARE_ONLY = 3

BAUD_RATE = 9600
DEFAULT_TIMEOUT = 2  # in seconds

MAX_DISPENSERS = 8
# MAX_DISPENSERS = 15
SHOT_TICKS = 20

RAW_PACKET_SIZE = 10
PACKET_SIZE = 8

PACKET_ACK_OK = 0
PACKET_CRC_FAIL = 1
PACKET_ACK_TIMEOUT = 2
PACKET_ACK_INVALID = 3
PACKET_ACK_INVALID_HEADER = 4
PACKET_ACK_HEADER_IN_PACKET = 5
PACKET_ACK_CRC_FAIL = 6

PACKET_PING = 3
PACKET_SET_MOTOR_SPEED = 4
PACKET_TICK_DISPENSE = 5
PACKET_TIME_DISPENSE = 6
PACKET_LED_OFF = 7
PACKET_LED_IDLE = 8
PACKET_LED_DISPENSE = 9
PACKET_LED_DRINK_DONE = 10
PACKET_IS_DISPENSING = 11
PACKET_LIQUID_LEVEL = 12
PACKET_UPDATE_LIQUID_LEVEL = 13
PACKET_ID_CONFLICT = 14
PACKET_LED_CLEAN = 15
PACKET_SET_CS_THRESHOLD = 16
PACKET_SAVED_TICK_COUNT = 17
PACKET_RESET_SAVED_TICK_COUNT = 18
PACKET_GET_LIQUID_THRESHOLDS = 19
PACKET_SET_LIQUID_THRESHOLDS = 20
PACKET_FLUSH_SAVED_TICK_COUNT = 21
PACKET_TICK_SPEED_DISPENSE = 22
PACKET_PATTERN_DEFINE = 23
PACKET_PATTERN_ADD_SEGMENT = 24
PACKET_PATTERN_FINISH = 25
PACKET_SET_MOTOR_DIRECTION = 26
PACKET_GET_VERSION = 27
PACKET_COMM_TEST = 0xFE

DEST_BROADCAST = 0xFF

MOTOR_DIRECTION_FORWARD = 1
MOTOR_DIRECTION_BACKWARD = 0

LED_PATTERN_IDLE = 0
LED_PATTERN_DISPENSE = 1
LED_PATTERN_DRINK_DONE = 2
LED_PATTERN_CLEAN = 3
LED_PATTERN_CURRENT_SENSE = 4

MOTOR_DIRECTION_FORWARD = 1
MOTOR_DIRECTION_BACKWARD = 0

# logging.basicConfig(level=logging.INFO)
log = logging.getLogger('bartendro')

# todo: put this in a start() method
try:
    from Adafruit_MotorHAT import Adafruit_MotorHAT, Adafruit_DCMotor
    pass

except:

    class Adafruit_MotorHAT:
        FORWARD = 1
        BACKWARD = 2
        BRAKE = 3
        RELEASE = 4

    log.info('no motor hat')


def crc16_update(crc, a):
    crc ^= a
    for i in range(0, 8):
        if crc & 1:
            crc = (crc >> 1) ^ 0xA001
        else:
            crc = (crc >> 1)
    return crc

class Fake_Motor():
    def __init__(self, num):
        self.num = num

    def setSpeed(self, speed):
        self.speed = speed

    def run(self, command=None):
        log.info('run fake motor %s' % self.num)

class Fake_MotorHAT():

    def __init__(self):
        self.port = 0x60
        self.motors = [Fake_Motor(i) for i in range(9)]

    def getMotor(self, num):

        return self.motors[num]



class RouterDriver(object):
    ''' plug in replacement for Bartendro RouterDriver to control the naive
    peristlatic pumps from Hello Drinkbot project. Provides a layer above
    the AdaFruit motor library which understands pumps. There is a lot of 
    code here which only applies to the real Bartendro pumps.'''

    def __init__(self, device,  software_only=False):
        ''' device is ignored, it is required for bartendro hardware'''
        self.device = device
        self.__doc__ = 'foo'
        self.dispenser_cnt = 8
        self.software_only = software_only

        self.dispenser_version = DISPENSER_DEFAULT_VERSION
        self.startup_log = ""

        # I need a hellodrinkbot switch
        #if not software_only:

        if 1:
            try:
                self.mh1 = Adafruit_MotorHAT(addr=0x60)
                #self.ports = [self.mh1.getMotor(foo+1) for foo in range(4)]
                #for motor in range(4):
                    #self.ports[motor].setSpeed(255)
            except:
                # no motor hat, but that might be fine if you are developing on another machine
                self.mh1 = Fake_MotorHAT()
                log.info("No Motor Hat?")

            self.ports = [self.mh1.getMotor(foo+1) for foo in range(4)]
            for motor in range(4):
                self.ports[motor].setSpeed(255)
            pass
            # Add a second motor hat, with a second  address. Comment the
            # above lines, replace with something like this:
            # self.mh1 = Adafruit_MotorHAT(addr=0x60)
            # self.mh2 = Adafruit_MotorHAT(addr=0xXX)
            # self.ports = [self.mh1.getMotor(range(1,9))]
            # for motor in range(8):
            #    self.ports[motor].setSpeed(255)

        else:
            #self.ports = [i for i in range(1, 5)]
            pass

        self.num_dispensers = MAX_DISPENSERS
        # The pumptest16.py does the right thing, but here dispensers 
        # 3 and 4, and 7 and 8 are reversed. But reversing them in this list 
        # of dispensers doesn't do what I need.
        self.dispensers = [
            #{'port': None, 'direction': MOTOR_DIRECTION_FORWARD}, 
            {'port': 0, 'direction': MOTOR_DIRECTION_FORWARD},
            {'port': 0, 'direction': MOTOR_DIRECTION_BACKWARD},
            {'port': 1, 'direction': MOTOR_DIRECTION_FORWARD},
            {'port': 1, 'direction': MOTOR_DIRECTION_BACKWARD},
            {'port': 2, 'direction': MOTOR_DIRECTION_FORWARD},
            {'port': 2, 'direction': MOTOR_DIRECTION_BACKWARD},
            {'port': 3, 'direction': MOTOR_DIRECTION_FORWARD},
            {'port': 3, 'direction': MOTOR_DIRECTION_BACKWARD},
        ]

     
    def get_startup_log(self):
        return self.startup_log

    def get_dispenser_version(self):
        return self.dispenser_version

    def reset(self):
        """Reset the hardware. Do this if there is shit going wrong. All motors will be stopped
           and reset."""
        if self.software_only:
            return

        self.close()
        self.open()

    def count(self):
        return self.num_dispensers

    def set_timeout(self, timeout):
        self.ser.timeout = timeout

    def open(self):
        '''Open the serial connection to the router'''
        if self.software_only:
            return

        self._clear_startup_log()

        try:
            log.info("Opening %s" % self.device)
            self.ser = serial.Serial(self.device,
                                     BAUD_RATE,
                                     bytesize=serial.EIGHTBITS,
                                     parity=serial.PARITY_NONE,
                                     stopbits=serial.STOPBITS_ONE,
                                     timeout=.01)
        except (serial.serialutil.SerialException, e):
            #raise SerialIOError(e)
            pass

        log.info("Done.\n")

        import status_led
        self.status = status_led.StatusLED(self.software_only)
        self.status.set_color(0, 0, 1)

        #self.dispenser_select = dispenser_select.DispenserSelect(
        #    MAX_DISPENSERS, self.software_only)
        #self.dispenser_select.open()
        #self.dispenser_select.reset()

        # This primes the communication line.
        self.ser.write(chr(170) + chr(170) + chr(170))
        sleep(.001)

        log.info("Discovering dispensers")
        self.num_dispensers = 0
        for port in range(MAX_DISPENSERS):
            self._log_startup("port %d:" % port)
            #self.dispenser_select.select(port)
            sleep(.01)
            while True:
                self.ser.flushInput()
                self.ser.write("???")
                data = self.ser.read(3)
                ll = ""
                for ch in data:
                    ll += "%02X " % ord(ch)
                if len(data) == 3:
                    if data[0] != data[1] or data[0] != data[2]:
                        self._log_startup("  %s -- inconsistent" % ll)
                        continue
                    id = ord(data[0])
                    self.dispenser_ids[self.num_dispensers] = id
                    self.dispenser_ports[self.num_dispensers] = port
                    self.num_dispensers += 1
                    self._log_startup(
                        "  %s -- Found dispenser with pump id %02X, index %d" % (ll, id, self.num_dispensers))
                    break
                elif len(data) > 1:
                    self._log_startup(
                        "  %s -- Did not receive 3 characters back. Trying again." % ll)
                    sleep(.5)
                else:
                    break

        self._select(0)
        self.set_timeout(DEFAULT_TIMEOUT)
        self.ser.write(chr(255))

        duplicate_ids = [x for x, y in collections.Counter(
            self.dispenser_ids).items() if y > 1]
        if len(duplicate_ids):
            for dup in duplicate_ids:
                if dup == 255:
                    continue
                self._log_startup("ERROR: Dispenser id conflict!\n")
                sent = False
                for i, d in enumerate(self.dispenser_ids):
                    if d == dup:
                        if not sent:
                            self._send_packet8(i, PACKET_ID_CONFLICT, 0)
                            sent = True
                        self._log_startup(
                            "  dispenser %d has id %d\n" % (i, d))
                        self.dispenser_ids[i] = 255
                        self.num_dispensers -= 1

        self.dispenser_version = self.get_dispenser_version(0)
        if self.dispenser_version < 0:
            self.dispenser_version = DISPENSER_DEFAULT_VERSION
        else:
            self.status.swap_blue_green()
        log.info("Detected dispensers version %d. (Only checked first dispenser)" %
                 self.dispenser_version)

        self.led_idle()

    def close(self):
        if self.software_only:
            return
        # change to adafruit all motors off off
        for port in self.ports:
            port.run(Adafruit_MotorHAT.RELEASE)
        self.status = None
        self.dispenser_select = None

    def log(self, msg):
        return
        if self.software_only:
            return
        try:
            t = localtime()
            self.cl.write("%d-%d-%d %d:%02d %s" % (t.tm_year,
                                                   t.tm_mon, t.tm_mday, t.tm_hour, t.tm_min, msg))
            self.cl.flush()
        except IOError:
            pass

    def make_shot(self):
        if self.software_only:
            return True
        # TODO: change to use dispense_ticks()
        self._send_packet32(0, PACKET_TICK_DISPENSE, 90)
        return True

    def ping(self, dispenser):
        if self.software_only:
            return True
        return self._send_packet32(dispenser, PACKET_PING, 0)

    def start(self, dispenser):
        if self.software_only:
            return True
        return self._send_packet8(dispenser, PACKET_SET_MOTOR_SPEED, 255, True)

    def set_motor_direction(self, dispenser, direction):
        if self.software_only:
            return True
        return self._send_packet8(dispenser, PACKET_SET_MOTOR_DIRECTION, direction)

    def dispenser_port(self, disp):
        """ Take a dispenser, return the port 
        """

        port = (disp)//2+1
        port = (disp)//2
        print('disp: %i port: %i' % (disp, port))
        #pdb.set_trace()
        return port

    def dispenser_sibling(self, disp):
        if (disp % 2):
            sibling = disp - 1
        else:
            sibling = disp + 1
        print('disp %i sibling %i ' % (disp, sibling))
    
        return sibling

    def stop(self, dispenser=None):
        """ turn one or all dispensers off """
        log.info('\tdispenser_off  %r ' %
                 ( dispenser))
        #if self.software_only:
            #return True
        # if dispenser==None turn them all off
        if not dispenser:
            log.info('\tstop no dispenser passed, turn off all')

            #for disp in (range(1, 4)):
            for disp in (range(9)):
                #self.ports[disp]['timer'] = None
                try:
                    self.ports[disp].run(Adafruit_MotorHAT.RELEASE)
                except:
                    pass
        else:
            log.info('\tstop dispenser %r' % dispenser)
            #self.ports[dispenser]['timer'] = None

            port = self.dispenser_port(dispenser)
            self.ports[port].run(Adafruit_MotorHAT.RELEASE)

    def dispense_time(self, dispenser, duration):
        log.info('dispense_time dispenser: %r port: %r ' % (
            dispenser, self.dispensers[dispenser]['port']))

        # can we dispense? Are we dispensing, or is our port-sibling dispensing?
        try:
            if self.dispensers[dispenser]['timer'].isAlive():
                log.info('Error: %r:%r dispenser in use. Not starting duplicate.' % (
                    self.dispensers[dispenser]['port'], dispenser))
                return False
        except:
            pass

        print('dispense_time')
        print('\tdispenser: %i ' % dispenser)
        port = self.dispenser_port(dispenser)
        print('\tport', port)
        print('\t',type(port))
        sibling = self.dispenser_sibling(dispenser)

        try:
            if self.dispensers[sibling]['timer'].isAlive():
                log.info('\tWarning: %r:%r port in use. Waiting to start.' % (
                    self.dispensers[dispenser]['port'], dispenser))
                self.dispensers[dispenser]['timerwait'] = threading.Timer(
                    1, self.dispense_time, [dispenser, duration])
                self.dispensers[dispenser]['timerwait'].start()
                return True
        except:
            pass

        # I feel too stupid to properly do software. 
        if dispenser == 0:
            self.ports[port].run(Adafruit_MotorHAT.FORWARD)
        if dispenser == 1:
            self.ports[port].run(Adafruit_MotorHAT.BACKWARD)
        if dispenser == 2:
            self.ports[port].run(Adafruit_MotorHAT.BACKWARD)
        if dispenser == 3:
            self.ports[port].run(Adafruit_MotorHAT.FORWARD)
        if dispenser == 4:
            self.ports[port].run(Adafruit_MotorHAT.FORWARD)
        if dispenser == 5:
            self.ports[port].run(Adafruit_MotorHAT.BACKWARD)
        if dispenser == 6:
            self.ports[port].run(Adafruit_MotorHAT.BACKWARD)
        if dispenser == 7:
            self.ports[port].run(Adafruit_MotorHAT.FORWARD)

        #if (dispenser % 2):
        #    self.ports[port].run(Adafruit_MotorHAT.BACKWARD)
        #    print('\t dispenser %i backward' % dispenser)
        #else:
        #    self.ports[port].run(Adafruit_MotorHAT.FORWARD)
        #    print('\t dispenser %i forward' % dispenser)

        #if not self.software_only:
        #    if (dispenser % 2):
        #        self.ports[dispenser].run(Adafruit_MotorHAT.FORWARD)
        #    else:
        #        self.ports[dispenser].run(Adafruit_MotorHAT.BACKWARD)

        log.info('setting stop callback to dispenser: %r ' % dispenser)
        self.dispensers[dispenser]['timer'] = threading.Timer(
            duration, self.stop, [dispenser])
        self.dispensers[dispenser]['timer'].start()
        return True

    # todo: Add dispense_ml, which calls dispense_time with a conversion factor
    def dispense_ml(self, dispenser, ml, speed=255):
        if self.software_only:
            pass
        SECONDS_PER_ML = 18/100. # huh? 
        time = ml*SECONDS_PER_ML
        ret = self.dispense_time(dispenser,time)
        return ret

    def dispense_ticks(self, dispenser, ticks, speed=255):
        if self.software_only:
            pass

        log.info('need to convert ticks to time')
        ret = self.dispense_time(dispenser, 5)

        # if it fails, do something?
        if not ret:
            log.error("*** dispense command failed. re-trying once.")

        return ret

    def led_off(self):
        if self.software_only:
            return True
        self._sync(0)
        self._send_packet8(DEST_BROADCAST, PACKET_LED_OFF, 0)
        return True

    def led_idle(self):
        if self.software_only:
            return True
        self._sync(0)
        self._send_packet8(DEST_BROADCAST, PACKET_LED_IDLE, 0)
        sleep(.01)
        self._sync(1)
        return True

    def led_dispense(self):
        if self.software_only:
            return True
        self._sync(0)
        self._send_packet8(DEST_BROADCAST, PACKET_LED_DISPENSE, 0)
        sleep(.01)
        self._sync(1)
        return True

    def led_complete(self):
        if self.software_only:
            return True
        self._sync(0)
        self._send_packet8(DEST_BROADCAST, PACKET_LED_DRINK_DONE, 0)
        sleep(.01)
        self._sync(1)
        return True

    def led_clean(self):
        if self.software_only:
            return True
        self._sync(0)
        self._send_packet8(DEST_BROADCAST, PACKET_LED_CLEAN, 0)
        sleep(.01)
        self._sync(1)
        return True

    def led_error(self):
        if self.software_only:
            return True
        self._sync(0)
        self._send_packet8(DEST_BROADCAST, PACKET_LED_CLEAN, 0)
        sleep(.01)
        self._sync(1)
        return True

    def comm_test(self):
        self._sync(0)
        return self._send_packet8(0, PACKET_COMM_TEST, 0)

    def is_dispensing(self, dispenser):
        """
        Returns a tuple of (dispensing, is_over_current) 
        """

        if self.software_only:
            return (False, False)

        # Sometimes the motors can interfere with communications.
        # In such cases, assume the motor is still running and
        # then assume the caller will again to see if it is still running
        self.set_timeout(.1)
        ret = self._send_packet8(dispenser, PACKET_IS_DISPENSING, 0)
        self.set_timeout(DEFAULT_TIMEOUT)
        if ret:
            ack, value0, value1 = self._receive_packet8_2()
            if ack == PACKET_ACK_OK:
                return (value0, value1)
            if ack == PACKET_ACK_TIMEOUT:
                return (-1, -1)
        return (True, False)

    def update_liquid_levels(self):
        if self.software_only:
            return True
        return self._send_packet8(DEST_BROADCAST, PACKET_UPDATE_LIQUID_LEVEL, 0)

    def get_liquid_level(self, dispenser):
        if self.software_only:
            return 100
        if self._send_packet8(dispenser, PACKET_LIQUID_LEVEL, 0):
            ack, value, dummy = self._receive_packet16()
            if ack == PACKET_ACK_OK:
                # Returning a random value as below is really useful for testing. :)
                # self.debug_levels[dispenser] = max(self.debug_levels[dispenser] - 20, 50)
                # return self.debug_levels[dispenser]
                # return random.randint(50, 200)
                return value
        return -1

    def get_liquid_level_thresholds(self, dispenser):
        if self.software_only:
            return True
        if self._send_packet8(dispenser, PACKET_GET_LIQUID_THRESHOLDS, 0):
            ack, low, out = self._receive_packet16()
            if ack == PACKET_ACK_OK:
                return (low, out)
        return (-1, -1)

    def set_liquid_level_thresholds(self, dispenser, low, out):
        if self.software_only:
            return True
        return self._send_packet16(dispenser, PACKET_SET_LIQUID_THRESHOLDS, low, out)

    def set_motor_direction(self, dispenser, dir):
        if self.software_only:
            return True
        return self._send_packet8(dispenser, PACKET_SET_MOTOR_DIRECTION, dir)

    def get_dispenser_version(self, dispenser):
        if self.software_only:
            return DISPENSER_DEFAULT_VERSION_SOFTWARE_ONLY
        if self._send_packet8(dispenser, PACKET_GET_VERSION, 0):
            # set a short timeout, in case its a v2 dispenser
            self.set_timeout(.1)
            ack, ver, dummy = self._receive_packet16(True)
            self.set_timeout(DEFAULT_TIMEOUT)
            if ack == PACKET_ACK_OK:
                return ver
        return -1

    def set_status_color(self, red, green, blue):
        if self.software_only:
            return
        if not self.status:
            return
        self.status.set_color(red, green, blue)

    def get_saved_tick_count(self, dispenser):
        if self.software_only:
            return True
        if self._send_packet8(dispenser, PACKET_SAVED_TICK_COUNT, 0):
            ack, ticks, dummy = self._receive_packet16()
            if ack == PACKET_ACK_OK:
                return ticks
        return -1

    def flush_saved_tick_count(self):
        if self.software_only:
            return True
        return self._send_packet8(DEST_BROADCAST, PACKET_FLUSH_SAVED_TICK_COUNT, 0)

    def pattern_define(self, dispenser, pattern):
        if self.software_only:
            return True
        return self._send_packet8(dispenser, PACKET_PATTERN_DEFINE, pattern)

    def pattern_add_segment(self, dispenser, red, green, blue, steps):
        if self.software_only:
            return True
        return self._send_packet8(dispenser, PACKET_PATTERN_ADD_SEGMENT, red, green, blue, steps)

    def pattern_finish(self, dispenser):
        if self.software_only:
            return True
        return self._send_packet8(dispenser, PACKET_PATTERN_FINISH, 0)

    # -----------------------------------------------
    # Past this point we only have private functions.
    # -----------------------------------------------

    def _sync(self, state):
        """Turn on/off the sync signal from the router. This signal is used to syncronize the LEDs"""

        if self.software_only:
            return
        self.dispenser_select.sync(state)

    def _select(self, dispenser):
        """Private function to select a dispenser."""

        if self.software_only:
            return True

        # If for broadcast, then ignore this select
        if dispenser == 255:
            return

        port = self.dispenser_ports[dispenser]
        self.dispenser_select.select(port)

    def _send_packet(self, dest, packet):
        if self.software_only:
            return True

        self._select(dest)
        self.ser.flushInput()
        self.ser.flushOutput()

        crc = 0
        for ch in packet:
            crc = crc16_update(crc, ord(ch))

        encoded = pack7.pack_7bit(packet + pack("<H", crc))
        if len(encoded) != RAW_PACKET_SIZE:
            log.error("send_packet: Encoded packet size is wrong: %d vs %s" % (
                len(encoded), RAW_PACKET_SIZE))
            return False

        try:
            t0 = time()
            written = self.ser.write(chr(0xFF) + chr(0xFF) + encoded)
            if written != RAW_PACKET_SIZE + 2:
                log.error("*** send timeout")
                log.error("*** dispenser: %d, type: %d" %
                          (dest + 1, ord(packet[1:2])))
                return False

            if dest == DEST_BROADCAST:
                return True

            ch = self.ser.read(1)
            t1 = time()
            log.debug("packet time: %f" % (t1 - t0))
            if len(ch) < 1:
                log.error("*** send packet: read timeout")
                log.error("*** dispenser: %d, type: %d" %
                          (dest + 1, ord(packet[1:2])))
                return False
        except (SerialException, err):
            log.error("SerialException: %s" % err)
            return False

        ack = ord(ch)
        if ack == PACKET_ACK_OK:
            return True
        if ack == PACKET_CRC_FAIL:
            log.error("*** send_packet: packet ack crc fail")
            log.error("*** dispenser: %d, type: %d" %
                      (dest + 1, ord(packet[1:2])))
            return False
        if ack == PACKET_ACK_TIMEOUT:
            log.error("*** send_packet: ack timeout")
            log.error("*** dispenser: %d, type: %d" %
                      (dest + 1, ord(packet[1:2])))
            return False
        if ack == PACKET_ACK_INVALID:
            log.error("*** send_packet: dispenser received invalid packet")
            log.error("*** dispenser: %d, type: %d" %
                      (dest + 1, ord(packet[1:2])))
            return False
        if ack == PACKET_ACK_INVALID_HEADER:
            log.error("*** send_packet: dispenser received invalid header")
            log.error("*** dispenser: %d, type: %d" %
                      (dest + 1, ord(packet[1:2])))
            return False
        if ack == PACKET_ACK_HEADER_IN_PACKET:
            log.error("*** send_packet: header in packet error")
            log.error("*** dispenser: %d, type: %d" %
                      (dest + 1, ord(packet[1:2])))
            return False

        # if we get an invalid ack code, it might be ok.
        log.error("send_packet: Invalid ACK code %d" % ord(ch))
        log.error("*** dispenser: %d, type: %d" % (dest + 1, ord(packet[1:2])))
        return False

    def _get_dispenser_id(self, dest):
        if dest != DEST_BROADCAST:
            try:
                return self.dispenser_ids[dest]
            except IndexError:
                log.error("*** send_packet to dispenser %d (of %d dispensers)" %
                          (dest + 1, len(self.dispenser_ids)))
                return 255
        else:
            return dest

    def _send_packet8(self, dest, type, val0, val1=0, val2=0, val3=0):
        dispenser_id = self._get_dispenser_id(dest)
        if dispenser_id == 255:
            return False

        return self._send_packet(dest, pack("BBBBBB", dispenser_id, type, val0, val1, val2, val3))

    def _send_packet16(self, dest, type, val0, val1):
        dispenser_id = self._get_dispenser_id(dest)
        if dispenser_id == 255:
            return False

        return self._send_packet(dest, pack("<BBHH", dispenser_id, type, val0, val1))

    def _send_packet32(self, dest, type, val):
        dispenser_id = self._get_dispenser_id(dest)
        if dispenser_id == 255:
            return False

        return self._send_packet(dest, pack("<BBI", dispenser_id, type, val))

    def _receive_packet(self, quiet=False):
        if self.software_only:
            return True

        header = 0
        while True:
            ch = self.ser.read(1)
            if len(ch) < 1:
                if not quiet:
                    log.error("receive packet: response timeout")
                return (PACKET_ACK_TIMEOUT, "")

            if (ord(ch) == 0xFF):
                header += 1
            else:
                header = 0

            if header == 2:
                break

        ack = PACKET_ACK_OK
        raw_packet = self.ser.read(RAW_PACKET_SIZE)
        if len(raw_packet) != RAW_PACKET_SIZE:
            if not quiet:
                log.error("receive packet: timeout")
            ack = PACKET_ACK_TIMEOUT

        if ack == PACKET_ACK_OK:
            packet = pack7.unpack_7bit(raw_packet)
            if len(packet) != PACKET_SIZE:
                ack = PACKET_ACK_INVALID
                if not quiet:
                    log.error("receive_packet: Unpacked length incorrect")

            if ack == PACKET_ACK_OK:
                received_crc = unpack("<H", packet[6:8])[0]
                packet = packet[0:6]

                crc = 0
                for ch in packet:
                    crc = crc16_update(crc, ord(ch))

                if received_crc != crc:
                    if not quiet:
                        log.error("receive_packet: CRC fail")
                    ack = PACKET_ACK_CRC_FAIL

        # Send the response back to the dispenser
        if self.ser.write(chr(ack)) != 1:
            if not quiet:
                log.error("receive_packet: Send ack timeout!")
            ack = PACKET_ACK_TIMEOUT

        if ack == PACKET_ACK_OK:
            return (ack, packet)
        else:
            return (ack, "")

    def _receive_packet8(self, quiet=False):
        ack, packet = self._receive_packet(quiet)
        if ack == PACKET_ACK_OK:
            data = unpack("BBBBBB", packet)
            return (ack, data[2])
        else:
            return (ack, 0)

    def _receive_packet8_2(self, quiet=False):
        ack, packet = self._receive_packet(quiet)
        if ack == PACKET_ACK_OK:
            data = unpack("BBBBBB", packet)
            return (ack, data[2], data[3])
        else:
            return (ack, 0, 0)

    def _receive_packet16(self, quiet=False):
        ack, packet = self._receive_packet(quiet)
        if ack == PACKET_ACK_OK:
            data = unpack("<BBHH", packet)
            return (ack, data[2], data[3])
        else:
            return (ack, 0, 0)

    def _clear_startup_log(self):
        self.startup_log = ""

    def _log_startup(self, txt):
        log.info(txt)
        self.startup_log += "%s\n" % txt


if __name__ == '__main__':

    # timer_test()
    log.info("in main")
    pump = RouterDriver('', True)
    print('Hello Drinkbot Driver now dispensing from pumps 1-8')

    # there are four ports, 0-3. 
    # Pump 1=Port 0 FORWARD
    # Pump 2=Port 0 BACKWARD
    # und so weiter
    # Pump 7=Port 3 FORWARD
    # Pump 8=Port 3 BACKWARD


    # pump.ports[3].run(Adafruit_MotorHAT.FORWARD)
    # pump.ports[3].run(Adafruit_MotorHAT.BACKWARD)
    # pump.ports[3].run(Adafruit_MotorHAT.RELEASE)


    # todo: why doesn't this work?
    pump.dispense_time(0, 1)
    pump.dispense_time(1, 1)
    pump.dispense_time(2, 1)
    pump.dispense_time(3, 1)
    pump.dispense_time(4, 1)
    pump.dispense_time(5, 1)
    pump.dispense_time(6, 1)
    pump.dispense_time(7, 1)

    # print("dir(pump.dispensers[1]['timer'])",  dir(pump.dispensers[1]['timer']))
    print('this is the end')
