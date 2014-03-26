# -*- coding: utf-8 -*-
from time import sleep, time
from threading import Thread
from bartendro import db, app

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
        if self.mode == "all":
            disp_list.extend(self.left_set)
            disp_list.extend(self.right_set)
        elif self.mode == "right":
            disp_list.extend(self.right_set)
        else:
            disp_list.extend(self.left_set)

        self.mixer.led_clean()
        for disp in disp_list:
            self.mixer.driver.start(disp)
            sleep(self.STAGGER_DELAY)

        sleep(CLEAN_DURATION)
        for disp in disp_list:
            self.mixer.driver.stop(disp)
            sleep(self.STAGGER_DELAY)

        self.mixer.led_idle()

        for i in xrange(self.mixer.disp_count):
            (is_dispensing, over_current) = app.driver.is_dispensing(i)
            if over_current:
                app.mixer.set_state(STATE_ERROR)
                app.mixer._update_status_led()
                break
