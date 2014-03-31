# -*- coding: utf-8 -*-
import logging
from time import sleep, time
from threading import Thread
from bartendro import db, app
from bartendro.error import BartendroBrokenError

CLEAN_DURATION = 10 # seconds

log = logging.getLogger('bartendro')

class CleanCycle(Thread):
    left_set = [4, 5, 6, 7, 8, 9, 10]
    right_set = [0, 1, 2, 3, 11, 12, 13, 14]
    STAGGER_DELAY = .150 # ms

    def __init__(self, mixer, mode):
        Thread.__init__(self)
        self.mixer = mixer
        self.mode = mode

    def run(self):

        disp_list = []

        if self.mixer.disp_count == 15:
            if self.mode == "all":
                disp_list.extend(self.left_set)
                disp_list.extend(self.right_set)
            elif self.mode == "right":
                disp_list.extend(self.right_set)
            else:
                disp_list.extend(self.left_set)
        else:
            for d in xrange(self.mixer.disp_count):
                disp_list.append(d)

        self.mixer.driver.led_clean()
        for disp in disp_list:
            self.mixer.driver.start(disp)
            sleep(self.STAGGER_DELAY)

        sleep(CLEAN_DURATION)
        for disp in disp_list:
            self.mixer.driver.stop(disp)
            sleep(self.STAGGER_DELAY)

        # Give bartendro a moment to collect himself
        sleep(.1)

        try:
            self.mixer.check_levels()
        except BartendroBrokenError, msg:
            log.error("Post clean: %s" % msg) 
