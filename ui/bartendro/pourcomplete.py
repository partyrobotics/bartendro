# -*- coding: utf-8 -*-
from time import sleep, time
from threading import Thread

class PourCompleteDelay(Thread):
    def __init__(self, mixer):
        Thread.__init__(self)
        self.mixer = mixer

    def run(self):
        sleep(5);
        self.mixer.driver.led_idle()
