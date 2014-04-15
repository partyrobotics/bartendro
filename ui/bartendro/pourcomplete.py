# -*- coding: utf-8 -*-
from time import sleep, time
from threading import Thread
import logging 

log = logging.getLogger('bartendro')

class PourCompleteDelay(Thread):
    def __init__(self, mixer):
        Thread.__init__(self)
        self.mixer = mixer

    def run(self):
        log.info("Pour complete LED thread started")
        sleep(5);
        log.info("Setting LEDs to idle")
        self.mixer.driver.led_idle()
