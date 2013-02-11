#!/usr/bin/env python

import sys
import os
from time import sleep

ROUTER_BUS              = 0
ROUTER_ADDRESS          = 4
ROUTER_SELECT_CMD_BEGIN = 0
ROUTER_CMD_SYNC_ON      = 251
ROUTER_CMD_SYNC_OFF     = 252
ROUTER_CMD_PING         = 253
ROUTER_CMD_COUNT        = 254
ROUTER_CMD_RESET        = 255


try:
    import smbus
    smbus_missing = 0
except ImportError, e:
    if e.message != 'No module named smbus':
        raise
    smbus_missing = 1

class DispenserSelect(object):
    '''This object interacts with the bartendro router controller to select dispensers'''

    def __init__(self, max_dispensers, software_only):
        self.software_only = software_only
        self.max_dispensers = max_dispensers
        self.router = None
        self.num_dispensers = 3
        self.selected = 0

    def reset(self):
        if self.software_only: return
        self.router.write_byte(ROUTER_ADDRESS, ROUTER_CMD_RESET)
        sleep(6)

    def select(self, dispenser):
        if self.software_only: return
        if dispenser < self.num_dispensers and self.selected != dispenser:
            self.selected = dispenser
            self.router.write_byte(ROUTER_ADDRESS, dispenser)
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
        '''Open the i2c connection to the router'''

        if self.software_only: return

        if smbus_missing:
            print "You must install the smbus module!"
            sys.exit(-1)

        try:
            self.router = smbus.SMBus(ROUTER_BUS)
        except IOError:
            raise I2CIOError


if __name__ == "__main__":
    ds = DispenserSelect(15, 0)
    ds.open()
    ds.reset()
