# -*- coding: utf-8 -*-
import logging
from time import sleep, time
from threading import Thread
from flask import Flask, current_app
from flask.ext.sqlalchemy import SQLAlchemy
import memcache
from sqlalchemy.orm import mapper, relationship, backref
from bartendro import db, app
from bartendro.global_lock import STATE_INIT, STATE_READY, STATE_LOW, STATE_OUT, STATE_ERROR
from bartendro.model.drink import Drink
from bartendro.model.dispenser import Dispenser
from bartendro.model.drink_log import DrinkLog
from bartendro.model.shot_log import ShotLog

TICKS_PER_ML = 2.78
CALIBRATE_ML = 60 
CALIBRATION_TICKS = TICKS_PER_ML * CALIBRATE_ML

FULL_SPEED = 255
HALF_SPEED = 128
SLOW_DISPENSE_THRESHOLD = 20 # ml
MAX_DISPENSE = 1000 # ml max dispense per call. Just for sanity. :)

CLEAN_DURATION = 10 # seconds

LIQUID_OUT_THRESHOLD       = 75
LIQUID_WARNING_THRESHOLD   = 120 

DISPENSER_OUT     = 1
DISPENSER_OK      = 0
DISPENSER_WARNING = 2

log = logging.getLogger('bartendro')

class BartendroBusyError(Exception):
    pass

def log_and_return(text):
    ''' helper function to make code less cluttered '''
    log.error(text)
    return text

class Mixer(object):
    '''The mixer object is the heart of Bartendro. This is where the state of the bot
       is managed, checked if drinks can be made, and actually make drinks. Everything
       else in Bartendro lives for *this* *code*. :) '''

    def __init__(self, driver, mc):
        self.driver = driver
        self.mc = mc
        self.err = ""
        self.disp_count = self.driver.count()
        self.check_liquid_levels()

    def reset(self):
        self.set_state(STATE_INIT)
        self.check_liquid_levels()

    def get_state(self):
        return app.globals.get_state()

    def set_state(self, state):
        return app.globals.set_state(state)

    def led_idle(self):
        self.driver.led_idle()

    def led_dispense(self):
        self.driver.led_dispense()

    def led_complete(self):
        self.driver.led_complete()

    def led_clean(self):
        self.driver.led_clean()

    def clean(self):
        CleanCycle(self, "all").start()

    def clean_right(self):
        CleanCycle(self, "right").start()

    def clean_left(self):
        CleanCycle(self, "left").start()

    def check_liquid_levels(self):
        """ Ask the dispense to update their own liquid levels and then fetch the levels
            and set the machine state accordingly. """
        if self.get_state() == STATE_ERROR:
            return STATE_ERROR

        if not app.options.use_liquid_level_sensors: 
            self.driver.set_status_color(0, 1, 0)
            self.set_state(STATE_READY)
            return STATE_READY

        new_state = STATE_READY

        log.info("mixer.check_liquid_levels: check levels");
        # step 1: ask the dispensers to update their liquid levels
        if not self.driver.update_liquid_levels():
            log.error("Failed to update liquid levels")
            self.set_state(STATE_ERROR)
            return STATE_ERROR

        # wait for the dispensers to determine the levels
        sleep(.01)

        # Now ask each dispenser for the actual level
        dispensers = db.session.query(Dispenser).order_by(Dispenser.id).all()
        for i, dispenser in enumerate(dispensers):
            if i >= self.disp_count: break

            dispenser.out = DISPENSER_OK
            level = self.driver.get_liquid_level(i)
            if level < 0:
                log.error("Failed to read liquid levels from dispenser %d" % (i+1))
                return STATE_ERROR

            log.info("dispenser %d level: %d" % (i, level))

            if level <= LIQUID_WARNING_THRESHOLD:
                if new_state == STATE_READY:
                    new_state = STATE_LOW
                if dispenser.out != DISPENSER_WARNING:
                    dispenser.out = DISPENSER_WARNING

            if level <= LIQUID_OUT_THRESHOLD:
                if new_state == STATE_READY or new_state == STATE_LOW:
                    new_state = STATE_OUT
                if dispenser.out != DISPENSER_OUT:
                    dispenser.out = DISPENSER_OUT

        db.session.commit()

        self.set_state(new_state)
        self._update_status_led()
        log.info("Checking levels done. New state: %d" % new_state)

        return new_state

    def liquid_level_test(self, dispenser, threshold):
        if self.get_state() == STATE_ERROR:
            return 
        if not app.options.use_liquid_level_sensors: return

        log.info("Start liquid level test: (disp %s thres: %d)" % (dispenser, threshold))

        if not self.driver.update_liquid_levels():
            log.error("Failed to update liquid levels")
            return
        sleep(.01)

        level = self.driver.get_liquid_level(dispenser)
	log.info("initial reading: %d" % level)
        if level <= threshold:
	    log.info("liquid is out before starting: %d" % level)
	    return

        last = -1
        self.driver.start(dispenser)
        while level > threshold:
            if not self.driver.update_liquid_levels():
                log.error("Failed to update liquid levels")
                return
            sleep(.01)
            level = self.driver.get_liquid_level(dispenser)
            if level != last:
                 log.info("  %d" % level)
            last = level

        self.driver.stop(dispenser)
        log.info("Stopped at level: %d" % level)
        sleep(.1);
        level = self.driver.get_liquid_level(dispenser)
        log.info("motor stopped at level: %d" % level)

    def get_available_drink_list(self):
        if self.get_state() == STATE_ERROR:
            return []

        can_make = self.mc.get("available_drink_list")
        if can_make: 
            return can_make

        add_boozes = db.session.query("abstract_booze_id") \
                            .from_statement("""SELECT bg.abstract_booze_id 
                                                 FROM booze_group bg 
                                                WHERE id 
                                                   IN (SELECT distinct(bgb.booze_group_id) 
                                                         FROM booze_group_booze bgb, dispenser 
                                                        WHERE bgb.booze_id = dispenser.booze_id)""")

        if app.options.use_liquid_level_sensors: 
            sql = "SELECT booze_id FROM dispenser WHERE out == 0 ORDER BY id LIMIT :d"
        else:
            sql = "SELECT booze_id FROM dispenser ORDER BY id LIMIT :d"

        boozes = db.session.query("booze_id") \
                        .from_statement(sql) \
                        .params(d=self.disp_count).all()
        boozes.extend(add_boozes)

        booze_dict = {}
        for booze_id in boozes:
            booze_dict[booze_id[0]] = 1

        drinks = db.session.query("drink_id", "booze_id") \
                        .from_statement("SELECT d.id AS drink_id, db.booze_id AS booze_id FROM drink d, drink_booze db WHERE db.drink_id = d.id ORDER BY d.id, db.booze_id") \
                        .all()
        last_drink = -1
        boozes = []
        can_make = []
        for drink_id, booze_id in drinks:
            if last_drink < 0: last_drink = drink_id
            if drink_id != last_drink:
                if self._can_make_drink(boozes, booze_dict): 
                    can_make.append(last_drink)
                boozes = []
            boozes.append(booze_id)
            last_drink = drink_id

        if self._can_make_drink(boozes, booze_dict): 
            can_make.append(last_drink)

        self.mc.set("available_drink_list", can_make)
        return can_make

    def dispense_ml(self, disp, ml, booze_id = -1):
        if disp < 0 or disp >= self.driver.count():
            return (0, "invalid dispenser")

        if self.get_state() == STATE_ERROR:
            return (0, "Bartendro is in error state")

        locked = self._lock_bartendro()
        if not locked: raise BartendroBusyError

        self.led_dispense()
        self.driver.dispense_ticks(disp, ml * TICKS_PER_ML)
        if not self._wait_til_finished_dispensing(disp):
            self.set_state(STATE_ERROR)
            self._update_status_led()
            self._unlock_bartendro()
            return (1, "Dispenser is current limited")
        self.led_idle()

        # If we're given a booze_id, log this shot
        if booze_id >= 0:
            t = int(time())
            slog = ShotLog(booze_id, t, ml)
            db.session.add(slog)
            db.session.commit()

        self._unlock_bartendro()
        return (0, "")

    def make_drink(self, id, recipe_arg, speed = 255):
        '''Make a drink! is is the drink id and its optional to make a "custom" drink that isn't in the drink
           table. If no id is given, the drink will not be logged to the drink log.'''

        log.debug("Make drink state: %d" % self.get_state())
        if self.get_state() == STATE_ERROR:
            return log_and_return("Cannot make a drink. Bartendro has encountered some error and is stopped. :(")

        # start by updating liqid levels to make sure we have the right fluids
        state = self.check_liquid_levels()
        if state != STATE_READY and state != STATE_LOW:
            return log_and_return("Cannot make drink. State is not low or out. :(")

        if id:
            drink = Drink.query.filter_by(id=int(id)).first()
        else:
            drink = None

        dispensers = Dispenser.query.order_by(Dispenser.id).all()

        recipe = {}
        size = 0
        log_lines = {}
        for booze_id in sorted(recipe_arg.keys()):
            found = False
            for i in xrange(self.disp_count):
                disp = dispensers[i]

                # if we're out of booze, don't consider this drink
                if app.options.use_liquid_level_sensors and disp.out == DISPENSER_OUT:
                    return log_and_return("Cannot make drink: Dispenser %d is out of booze." % (i+1))

                if booze_id == disp.booze_id:
                    found = True
                    ml = recipe_arg[booze_id]
                    if ml <= 0:
                        log_lines[i] = "  %-2d %-32s %d ml (not dispensed)" % (i, "%s (%d)" % (disp.booze.name, disp.booze.id), ml)
                        continue

                    if ml > MAX_DISPENSE:
                        return log_and_return("Cannot make drink. Invalid dispense quantity: %d ml. (Max %d ml)" % (ml, MAX_DISPENSE))

                    recipe[i] =  ml
                    size += ml
                    log_lines[i] = "  %-2d %-32s %d ml" % (i, "%s (%d)" % (disp.booze.name, disp.booze.id), ml)
                    continue

            if not found:
                return log_and_return("Cannot make drink. I don't have the required booze: %d" % booze_id)

        ret = self.dispense_recipe(recipe, speed)
        if ret:
            return log_and_return(ret)

        if drink:
            log.info("Made cocktail: %s" % drink.name.name)
        else:
            log.info("Made custom drink:")
        for line in sorted(log_lines.keys()):
            log.info(log_lines[line])
        log.info("%s ml dispensed. done." % size)

        if drink:
            t = int(time())
            dlog = DrinkLog(drink.id, t, size)
            db.session.add(dlog)
            db.session.commit()

        return ""

    def dispense_recipe(self, recipe, speed):

        locked = self._lock_bartendro()
        if not locked: raise BartendroBusyError
   
        self.led_dispense()
        active_disp = []
        for disp in recipe:
            if not recipe[disp]:
                continue
            ticks = int(recipe[disp] * TICKS_PER_ML)
            if recipe[disp] < SLOW_DISPENSE_THRESHOLD and speed > HALF_SPEED: 
                actual_speed = HALF_SPEED 
            else:
                actual_speed = speed 
            if not self.driver.dispense_ticks(disp, ticks, actual_speed):
                log.error("Dispense error. Dispense %d ticks, speed %d on dispenser %d failed." % (ticks, actual_speed, disp + 1))
            active_disp.append(disp)
            sleep(.01)

        current_sense = False
        for disp in active_disp:
            if not self._wait_til_finished_dispensing(disp):
                current_sense = True
                break

        if current_sense: 
            self.set_state(STATE_ERROR)
            self._update_status_led()
            self._unlock_bartendro()
            log.error("Current sense triggered on dispenser %d" % disp + 1)
            return "One of the pumps did not operate properly. Your drink is broken. Sorry. :("

        self.led_complete()

        if app.options.use_liquid_level_sensors:
            state = self.check_liquid_levels()
            log.info("Post make drink. State is: %d" % state)

        FlashGreenLeds(self).start()
        self._unlock_bartendro()

        return "" 

    # ----------------------------------------
    # Private methods
    # ----------------------------------------

    def _lock_bartendro(self):
        return app.globals.lock_bartendro()

    def _unlock_bartendro(self):
        return app.globals.unlock_bartendro()

    def _can_make_drink(self, boozes, booze_dict):
        ok = True
        for booze in boozes:
            try:
                foo = booze_dict[booze]
            except KeyError:
                ok = False
        return ok

    def _update_status_led(self):
        state = self.get_state()
        if state == STATE_OUT:
            self.driver.set_status_color(1, 0, 0)
        elif state == STATE_LOW:
            self.driver.set_status_color(1, 1, 0)
        elif state == STATE_READY:
            self.driver.set_status_color(0, 1, 0)
        else:
            self.driver.set_status_color(1, 1, 1)

    def _wait_til_finished_dispensing(self, disp):
        """Check to see if the given dispenser is still dispensing. Returns True when finished. False if over current"""
        timeout_count = 0
        while True:
            (is_dispensing, over_current) = app.driver.is_dispensing(disp)
            if is_dispensing < 0 or over_current < 0:
                continue

            log.debug("is_disp %d, over_cur %d" % (is_dispensing, over_current))
            if over_current: return False
            if is_dispensing == 0: return True

            # This timeout count is here to counteract Issue #64 -- this can be removed once #64 is fixed
            if is_dispensing == -1:
                timeout_count += 1
                if timeout_count == 3:
                    break

            sleep(.1)

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

class FlashGreenLeds(Thread):
    def __init__(self, mixer):
        Thread.__init__(self)
        self.mixer = mixer

    def run(self):
        sleep(5);
        self.mixer.led_idle()
