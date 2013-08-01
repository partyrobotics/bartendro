#!/usr/bin/env python

import sys
from time import sleep

class GPIO(object):
    def __init__(self, pin):
        self.pin = pin

    def setup(self):
        try:
            f = open("/sys/class/gpio/gpio%d/direction" % self.pin, "w")
        except IOError:
            return False
        f.write("high\n")
        f.close()

    def low(self):
        try:
            f = open("/sys/class/gpio/gpio%d/value" % self.pin, "w")
        except IOError:
            return False
        f.write("0\n")
        f.close()
        return True

    def high(self):
        try:
            f = open("/sys/class/gpio/gpio%d/value" % self.pin, "w")
        except IOError:
            return False
        f.write("1\n")
        f.close()
        return True
