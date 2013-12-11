#!/usr/bin/env python

import sys
import logging
from threading import Thread
from time import sleep

try:
    import RPi.GPIO as gpio
    gpio_missing = 0
except ImportError, e:
    if e.message != 'No module named RPi.GPIO':
        raise
    gpio_missing = 1

log = logging.getLogger('bartendro')

class TriggerSwitch(Thread):

    # pin definitions
    switch = 26

    def __init__(self, mixer, software_only):
        Thread.__init__(self)
        self.mixer = mixer
        self.software_only = software_only
        if self.software_only: return

        if gpio_missing:
            loglogerror("You must install the RPi.GPIO module")
            sys.exit(-1)

        # select the method by which we want to identify GPIO pins
        gpio.setmode(gpio.BOARD)
        gpio.setwarnings(False)

        # set our gpio pins to OUTPUT
        gpio.setup(self.switch, gpio.IN)

    def run(self):
        recipe = { "booze61" : 19, "booze62": 19 }
        while True:
            if not gpio.input(self.switch):
                print "make drink"
                self.mixer.make_drink(85, recipe)
                sleep(3)
            sleep(.1)
