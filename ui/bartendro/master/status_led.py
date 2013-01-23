#!/usr/bin/env python

import RPi.GPIO as gpio


class StatusLED(object):

    # pin definitions
    red = 18
    green = 22
    blue = 16

    def __init__(self, software_only):
        self.software_only = software_only
        if self.software_only: return

        # select the method by which we want to identify GPIO pins
        gpio.setmode(gpio.BOARD)
        gpio.setwarnings(False)

        # set our gpio pins to OUTPUT
        gpio.setup(self.red, gpio.OUT)
        gpio.setup(self.green, gpio.OUT)
        gpio.setup(self.blue, gpio.OUT)

    def set_color(self, red, green, blue):
        if self.software_only: return
        if red:
            gpio.output(self.red, gpio.HIGH)
        else:
            gpio.output(self.red, gpio.LOW)
            
        if green:
            gpio.output(self.green, gpio.HIGH)
        else:
            gpio.output(self.green, gpio.LOW)

        if blue:
            gpio.output(self.blue, gpio.HIGH)
        else:
            gpio.output(self.blue, gpio.LOW)
