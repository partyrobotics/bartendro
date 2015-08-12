# -*- coding: utf-8 -*-
import logging
import sys
import traceback
from time import sleep, time
from threading import Thread
from flask import Flask, current_app
from flask.ext.sqlalchemy import SQLAlchemy
import memcache
from sqlalchemy.orm import mapper, relationship, backref
from bartendro import db, app
from bartendro import fsm
from bartendro.clean import CleanCycle
from bartendro.pourcomplete import PourCompleteDelay
from bartendro.router.driver import MOTOR_DIRECTION_FORWARD
from bartendro.model.drink import Drink
from bartendro.model.booze import BOOZE_TYPE_EXTERNAL
from bartendro.model.dispenser import Dispenser
from bartendro.model.drink_log import DrinkLog
from bartendro.model.shot_log import ShotLog
from bartendro.global_lock import BartendroLock
from bartendro.error import BartendroBusyError, BartendroBrokenError, BartendroCantPourError, BartendroCurrentSenseError

TICKS_PER_ML = 2.78
CALIBRATE_ML = 60 
CALIBRATION_TICKS = TICKS_PER_ML * CALIBRATE_ML

FULL_SPEED = 255
HALF_SPEED = 166
SLOW_DISPENSE_THRESHOLD = 20 # ml
MAX_DISPENSE = 1000 # ml max dispense per call. Just for sanity. :)

LIQUID_OUT_THRESHOLD   = 75
LIQUID_LOW_THRESHOLD   = 120 

LL_OUT     = 0
LL_OK      = 1
LL_LOW     = 2

log = logging.getLogger('bartendro')

class BartendroLiquidLevelReadError(Exception):
    pass

class Recipe(object):
    ''' Define everything related to dispensing one or more liquids at the same time '''
    def __init__(self):
        self.data = {}
        self.drink = None   # Use for dispensing drinks
        self.booze  = None  # Use for dispensing single shots of one booze

class Mixer(object):
    '''The mixer object is the heart of Bartendro. This is where the state of the bot
       is managed, checked if drinks can be made, and actually make drinks. Everything
       else in Bartendro lives for *this* *code*. :) '''

    def __init__(self, driver, mc):
        self.driver = driver
        self.mc = mc
        self.disp_count = self.driver.count()
        self.do_event(fsm.EVENT_START)
        self.err = ""

    def check_levels(self):
        with BartendroLock(app.globals):
            self.do_event(fsm.EVENT_CHECK_LEVELS)

    def dispense_shot(self, dispenser, ml):
        r = Recipe()
        r.data = { dispenser.booze.id : ml }
        r.booze = dispenser.booze
        self.recipe = r

        with BartendroLock(app.globals):
            self.do_event(fsm.EVENT_MAKE_SHOT)
            t = int(time())
            slog = ShotLog(dispenser.booze.id, t, ml)
            db.session.add(slog)
            db.session.commit()

    def dispense_ml(self, dispenser, ml):
        r = Recipe()
        r.data = { dispenser.booze.id : ml }
        r.booze = dispenser.booze
        self.recipe = r

        with BartendroLock(app.globals):
            self.do_event(fsm.EVENT_TEST_DISPENSE)

    def make_drink(self, drink, recipe):
        r = Recipe()
        r.data = recipe
        r.drink = drink
        self.recipe = r

        with BartendroLock(app.globals):
            self.do_event(fsm.EVENT_MAKE_DRINK)
            if drink and drink.id:
                size = 0
                for k in recipe.keys():
                    size += recipe[k] 
                t = int(time())
                dlog = DrinkLog(drink.id, t, size)
                db.session.add(dlog)
                db.session.commit()

    def do_event(self, event):
        cur_state = app.globals.get_state()
    
        while True:
            next_state = None
            for t_state, t_event, t_next_state in fsm.transition_table:
                if t_state == cur_state and event == t_event:
                    next_state = t_next_state
                    break
            
            if not next_state:
                log.error("Current state %d, event %d. No next state." % (cur_state, event))
                raise BartendroBrokenError("Bartendro is unable to pour drinks right now. Sorry.")
            #print "cur state: %d event: %d next state: %d" % (cur_state, event, next_state)

            try:
                if next_state == fsm.STATE_PRE_POUR:
                    event = self._state_pre_pour()
                elif next_state == fsm.STATE_CHECK:
                    event = self._state_check()
                elif next_state == fsm.STATE_PRE_SHOT:
                    event = self._state_pre_shot()
                elif next_state == fsm.STATE_READY:
                    event = self._state_ready()
                elif next_state == fsm.STATE_LOW:
                    event = self._state_low()
                elif next_state == fsm.STATE_OUT:
                    event = self._state_out()
                elif next_state == fsm.STATE_HARD_OUT:
                    event = self._state_hard_out()
                elif next_state == fsm.STATE_POURING or next_state == fsm.STATE_POUR_SHOT:
                    event = self._state_pouring()
                elif next_state == fsm.STATE_POUR_DONE:
                    event = self._state_pour_done()
                elif next_state == fsm.STATE_CURRENT_SENSE:
                    event = self._state_current_sense()
                elif next_state == fsm.STATE_ERROR:
                    event = self._state_error()
                elif next_state == fsm.STATE_TEST_DISPENSE:
                    event = self._state_test_dispense()
                else:
                    self._state_error()
                    app.globals.set_state(fsm.STATE_ERROR)
                    log.error("Current state: %d, event %d. Can't find next state." % (cur_state, event))
                    raise BartendroBrokenError("Internal error. Bartendro has had one too many.")

            except BartendroBrokenError, err:
                exc_type, exc_value, exc_traceback = sys.exc_info()
                #traceback.print_tb(exc_traceback)
                self._state_error()
                app.globals.set_state(fsm.STATE_ERROR)
                raise

            except BartendroCantPourError, err:
                exc_type, exc_value, exc_traceback = sys.exc_info()
                #traceback.print_tb(exc_traceback)
                raise
                
            except BartendroCurrentSenseError, err:
                exc_type, exc_value, exc_traceback = sys.exc_info()
                #traceback.print_tb(exc_traceback)
                raise BartendroBrokenError(err)

            cur_state = next_state
            if cur_state in fsm.end_states:
                break

        app.globals.set_state(cur_state)

    def _state_check(self):
        try:
            ll = self._check_liquid_levels()
        except BartendroLiquidLevelReadError:
            raise BartendroBrokenError("Failed to read liquid levels")

        # update the list of drinks we can make
        drinks = self.get_available_drink_list()
        if len(drinks) == 0:
            return fsm.EVENT_LL_HARD_OUT

        if ll == LL_OK:
            return fsm.EVENT_LL_OK

        if ll == LL_LOW:
            return fsm.EVENT_LL_LOW

        return fsm.EVENT_LL_OUT

    def _state_pre_pour(self):
        try:
            ll = self._check_liquid_levels()
        except BartendroLiquidLevelReadError:
            raise BartendroBrokenError("Failed to read liquid levels")

        # update the list of drinks we can make
        drinks = self.get_available_drink_list()
        if len(drinks) == 0:
            raise BartendroCantPourError("Cannot make this drink now.")

        if ll == LL_OK:
            return fsm.EVENT_LL_OK

        if ll == LL_LOW:
            return fsm.EVENT_LL_LOW

        return LL_OUT

    def _state_pre_shot(self):

        if not app.options.use_liquid_level_sensors:
            return fsm.EVENT_LL_OK

        try:
            ll = self._check_liquid_levels()
        except BartendroLiquidLevelReadError:
            raise BartendroBrokenError("Failed to read liquid levels")

        booze_id = self.recipe.data.keys()[0]
        dispensers = db.session.query(Dispenser).order_by(Dispenser.id).all()
        for i, disp in enumerate(dispensers):
            if disp.booze_id == booze_id:
                if disp.out == LL_OUT:
                    if ll == LL_OK:
                        app.globals.set_state(fsm.STATE_OK)
                    elif ll == LL_LOW:
                        app.globals.set_state(fsm.STATE_LOW)
                    elif ll == LL_OUT:
                        app.globals.set_state(fsm.STATE_OUT)
                    else:
                        app.globals.set_state(fsm.STATE_HARD_OUT)

                    raise BartendroCantPourError("Cannot make drink: Dispenser %d is out of booze." % (i+1))
                break

        return fsm.EVENT_LL_OK

    def _state_ready(self):
        self.driver.set_status_color(0, 1, 0)
        return fsm.EVENT_DONE

    def _state_low(self):
        self.driver.led_idle()
        self.driver.set_status_color(1, 1, 0)
        return fsm.EVENT_DONE

    def _state_out(self):
        self.driver.led_idle()
        self.driver.set_status_color(1, 0, 0)
        return fsm.EVENT_DONE

    # TODO: Make the hard out blink the status led
    def _state_hard_out(self):
        self.driver.led_idle()
        self.driver.set_status_color(1, 0, 0)
        return fsm.EVENT_DONE

    def _state_current_sense(self):
        return fsm.EVENT_DONE

    def _state_error(self):
        self.driver.led_idle()
        self.driver.set_status_color(1, 0, 0)
        return fsm.EVENT_DONE

    def _state_pouring(self):
        self.driver.led_dispense()

        recipe = {}
        size = 0
        log_lines = {}
        sql = "SELECT id FROM booze WHERE type = :d"
        ext_booze_list = db.session.query("id") \
                        .from_statement(sql) \
                        .params(d=BOOZE_TYPE_EXTERNAL).all()
        ext_boozes = {}
        for booze in ext_booze_list:
            ext_boozes[booze[0]] = 1

        dispensers = db.session.query(Dispenser).order_by(Dispenser.id).all()
        for booze_id in sorted(self.recipe.data.keys()):
            # Skip external boozes
            if booze_id in ext_boozes:
                continue

            found = False
            for i in xrange(self.disp_count):
                disp = dispensers[i]


                if booze_id == disp.booze_id:
                    # if we're out of booze, don't consider this drink
                    if app.options.use_liquid_level_sensors and disp.out == LL_OUT:
                        raise BartendroCantPourError("Cannot make drink: Dispenser %d is out of booze." % (i+1))

                    found = True
                    ml = self.recipe.data[booze_id]
                    if ml <= 0:
                        log_lines[i] = "  %-2d %-32s %d ml (not dispensed)" % (i, "%s (%d)" % (disp.booze.name, disp.booze.id), ml)
                        continue

                    if ml > MAX_DISPENSE:
                        raise BartendroCantPourError("Cannot make drink. Invalid dispense quantity: %d ml. (Max %d ml)" % (ml, MAX_DISPENSE))

                    recipe[i] =  ml
                    size += ml
                    log_lines[i] = "  %-2d %-32s %d ml" % (i, "%s (%d)" % (disp.booze.name, disp.booze.id), ml)
                    self.driver.set_motor_direction(i, MOTOR_DIRECTION_FORWARD);
                    continue

            if not found:
                raise BartendroCantPourError("Cannot make drink. I don't have the required booze: %d" % booze_id)

        self._dispense_recipe(recipe)

        if self.recipe.drink:
            log.info("Made cocktail: %s" % self.recipe.drink.name.name)
        else:
            log.info("Made custom drink:")
        for line in sorted(log_lines.keys()):
            log.info(log_lines[line])
        log.info("%s ml dispensed. done." % size)

        return fsm.EVENT_POUR_DONE

    def _state_test_dispense(self):

        booze_id = self.recipe.data.keys()[0]
        ml = self.recipe.data[booze_id]

        recipe = {}
        dispensers = db.session.query(Dispenser).order_by(Dispenser.id).all()
        for i in xrange(self.disp_count):
            if booze_id == dispensers[i].booze_id:
                recipe[i] =  ml
                self._dispense_recipe(recipe, True)
                break

        return fsm.EVENT_POUR_DONE

    def _state_pour_done(self):
        self.driver.led_complete()
        PourCompleteDelay(self).start()

        return fsm.EVENT_POST_POUR_DONE

    def reset(self):
        self.driver.led_idle()
        app.globals.set_state(fsm.STATE_START)
        self.do_event(fsm.EVENT_START)

    def clean(self):
        CleanCycle(self, "all").clean()

    def clean_right(self):
        CleanCycle(self, "right").clean()

    def clean_left(self):
        CleanCycle(self, "left").clean()

    def liquid_level_test(self, dispenser, threshold):
        if app.globals.get_state() == fsm.STATE_ERROR:
            return 
        if not app.options.use_liquid_level_sensors: return

        log.info("Start liquid level test: (disp %s thres: %d)" % (dispenser, threshold))

        if not self.driver.update_liquid_levels():
            raise BartendroBrokenError("Failed to update liquid levels")
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
                raise BartendroBrokenError("Failed to update liquid levels")
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
        if app.globals.get_state() == fsm.STATE_ERROR:
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
            sql = "SELECT booze_id FROM dispenser WHERE out == 1 or out == 2 ORDER BY id LIMIT :d"
        else:
            sql = "SELECT booze_id FROM dispenser ORDER BY id LIMIT :d"

        boozes = db.session.query("booze_id") \
                        .from_statement(sql) \
                        .params(d=self.disp_count).all()
        boozes.extend(add_boozes)

        # Load whatever external boozes we have and add them to this list
        sql = "SELECT id FROM booze WHERE type = :d"
        ext_boozes = db.session.query("id") \
                        .from_statement(sql) \
                        .params(d=BOOZE_TYPE_EXTERNAL).all()
        boozes.extend(ext_boozes)

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

    # ----------------------------------------
    # Private methods
    # ----------------------------------------

    def _check_liquid_levels(self):
        """ Ask the dispense to update their own liquid levels and then fetch the levels
            and set the machine state accordingly. """

        if not app.options.use_liquid_level_sensors: 
            return LL_OK

        ll_state = LL_OK

        log.info("mixer.check_liquid_levels: check levels");
        # step 1: ask the dispensers to update their liquid levels
        if not self.driver.update_liquid_levels():
            raise BartendroLiquidLevelReadError("Failed to update liquid levels")

        # wait for the dispensers to determine the levels
        sleep(.01)

        # Now ask each dispenser for the actual level
        dispensers = db.session.query(Dispenser).order_by(Dispenser.id).all()

        clear_cache = False
        for i, dispenser in enumerate(dispensers):
            if i >= self.disp_count:
                break

            level = self.driver.get_liquid_level(i)
            if level < 0:
                raise BartendroLiquidLevelReadError("Failed to read liquid levels from dispenser %d" % (i+1))

            log.info("dispenser %d level: %d (stored: %d)" % (i, level, dispenser.out))

            if level <= LIQUID_OUT_THRESHOLD:
                ll_state = LL_OUT
                if dispenser.out != LL_OUT:
                    clear_cache = True
                dispenser.out = LL_OUT

            elif level <= LIQUID_LOW_THRESHOLD:
                if ll_state == LL_OK:
                    ll_state = LL_LOW

                if dispenser.out == LL_OUT:
                    clear_cache = True
                dispenser.out = LL_LOW

            else:
                if dispenser.out == LL_OUT:
                    clear_cache = True

                dispenser.out = LL_OK

        db.session.commit()

        if clear_cache:
            self.mc.delete("top_drinks")
            self.mc.delete("other_drinks")
            self.mc.delete("available_drink_list")

        log.info("Checking levels done. New state: %d" % ll_state)

        return ll_state

    def _dispense_recipe(self, recipe, always_fast = False):

        active_disp = []
        for disp in recipe:
            if not recipe[disp]:
                continue
            ticks = int(recipe[disp] * TICKS_PER_ML)
            if recipe[disp] < SLOW_DISPENSE_THRESHOLD and not always_fast:
                speed = HALF_SPEED 
            else:
                speed = FULL_SPEED 

            self.driver.set_motor_direction(disp, MOTOR_DIRECTION_FORWARD);
            if not self.driver.dispense_ticks(disp, ticks, speed):
                raise BartendroBrokenError("Dispense error. Dispense %d ticks, speed %d on dispenser %d failed." % (ticks, speed, disp + 1))

            active_disp.append(disp)
            sleep(.01)

        for disp in active_disp:
            while True:
                (is_dispensing, over_current) = app.driver.is_dispensing(disp)
                log.debug("is_disp %d, over_cur %d" % (is_dispensing, over_current))

                # If we get errors here, try again. Running motors can cause noisy comm lines
                if is_dispensing < 0 or over_current < 0:
                    log.error("Is dispensing test on dispenser %d failed. Ignoring." % (disp + 1))
                    sleep(.2)
                    continue

                if over_current:
                    raise BartendroCurrentSenseError("One of the pumps did not operate properly. Your drink is broken. Sorry. :(")

                if is_dispensing == 0: 
                    break 

                sleep(.1)

    def _can_make_drink(self, boozes, booze_dict):
        ok = True
        for booze in boozes:
            try:
                foo = booze_dict[booze]
            except KeyError:
                ok = False
        return ok

