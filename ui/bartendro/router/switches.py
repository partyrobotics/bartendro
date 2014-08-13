#!/usr/bin/env python

import sys
import logging
from threading import Thread
from time import sleep

DRINKS = [
   [ 100, 60, 40 ],
   [ 100, 50, 0  ],
   [ 100, 100, 0 ]
]

try:
    import RPi.GPIO as gpio
    gpio_missing = 0
except ImportError, e:
    if e.message != 'No module named RPi.GPIO':
        raise
    gpio_missing = 1

log = logging.getLogger('bartendro')

class Switches(Thread):

    # pin definitions
    switch0 = 11
    switch1 = 13
    switch2 = 15

    def __init__(self, driver, software_only):
        Thread.__init__(self)
        self.driver = driver
        self.software_only = software_only
        if self.software_only: return

        if gpio_missing:
            log.error("You must install the RPi.GPIO module")
            sys.exit(-1)

        # select the method by which we want to identify GPIO pins
        gpio.setmode(gpio.BOARD)
#        gpio.setwarnings(False)

        # set our gpio pins to OUTPUT
        gpio.setup(self.switch0, gpio.IN)
        gpio.setup(self.switch1, gpio.IN)
        gpio.setup(self.switch2, gpio.IN)

        log.info("switches module initialized")

    def check_switch(self, switch, percents):
        # If switch is not pressed, bail
        if gpio.input(switch):
            return

        log.info("switch on pin %d pressed" % switch)

        sleep(.05)

        # If switch is still pressed, wait for possible bounces
        if gpio.input(switch):
            return

        log.info("switch on pin %d debounced. Starting cocktails!" % switch)

        # Switch is still pressed, it must be cocktail time!
        # Turn on the motors
        for i, p, in enumerate(percents):
            log.info("Turn on dispenser %d to %d", dispenser, p * 255 // 100)
            self.driver.start(i, p * 255 // 100)

        # Wait for the switch to be released
        while not gpio.input(switch):
            pass

        log.info("switch released")

        # Turn the motors off
        for i in xrange(len(percents)):
            log.info("turn off dispenser %d" % dispenser)
            self.driver.stop(i)

        # Sleep for a second to get things to calm down again
        sleep(1)

        log.sleep("Cocktail donw. bottoms up")

    def run(self):
        while True:
            self.check_switch(self.switch0, DRINKS[0])
            self.check_switch(self.switch1, DRINKS[1])
            self.check_switch(self.switch2, DRINKS[2])
            sleep(.05)
