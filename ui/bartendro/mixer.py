# -*- coding: utf-8 -*-
from time import sleep, localtime
from threading import Thread
import memcache
from sqlalchemy.orm import mapper, relationship, backref
from bartendro.utils import session, local, log, error
from bartendro.model.drink import Drink
from bartendro.model.dispenser import Dispenser
from bartendro.model import drink_booze
from bartendro.model import booze

TICKS_PER_ML = 671
CALIBRATE_ML = 60 
CALIBRATION_TICKS = TICKS_PER_ML * CALIBRATE_ML

class Mixer(object):
    '''This is where the magic happens!'''

    def __init__(self, driver, led_driver):
        self.driver = driver
        self.led_driver = led_driver
        self.err = ""
        self.disp_count = self.driver.count()
        self.mc = local.application.mc
        self.led_driver.idle()

    def get_error(self):
        return self.err

    def can_make_drink(self, boozes, booze_dict):
        ok = True
        for booze in boozes:
            try:
                foo = booze_dict[booze]
            except KeyError:
                ok = False
        return ok

    def liquid_level_test(self, dispenser, threshold):

        print "Start liquid level test:"
        self.driver.start(dispenser)
        last = -1
        level = 255;
        while level > threshold:
            level = self.driver.get_liquid_level(dispenser)
            if level != last:
                print "  %d" % level
                last = level

        self.driver.stop(dispenser)
        print "Stopped at level: %d" % level
        sleep(.1);
        level = self.driver.get_liquid_level(dispenser)
        print "motor stopped at level: %d" % level

    def get_available_drink_list(self):
        can_make = self.mc.get("available_drink_list")
        if can_make: 
            return can_make

        add_boozes = session.query("abstract_booze_id") \
                            .from_statement("""SELECT bg.abstract_booze_id 
                                                 FROM booze_group bg 
                                                WHERE id 
                                                   IN (SELECT distinct(bgb.booze_group_id) 
                                                         FROM booze_group_booze bgb, dispenser 
                                                        WHERE bgb.booze_id = dispenser.booze_id)""")

        boozes = session.query("booze_id") \
                        .from_statement("SELECT booze_id FROM dispenser ORDER BY id LIMIT :d") \
                        .params(d=self.disp_count).all()
        boozes.extend(add_boozes)

        booze_dict = {}
        for booze_id in boozes:
            booze_dict[booze_id[0]] = 1

        drinks = session.query("drink_id", "booze_id") \
                        .from_statement("SELECT d.id AS drink_id, db.booze_id AS booze_id FROM drink d, drink_booze db WHERE db.drink_id = d.id ORDER BY d.id, db.booze_id") \
                        .all()
        last_drink = -1
        boozes = []
        can_make = []
        for drink_id, booze_id in drinks:
            if last_drink < 0: last_drink = drink_id
            if drink_id != last_drink:
                if self.can_make_drink(boozes, booze_dict): 
                    can_make.append(last_drink)
                boozes = []
            boozes.append(booze_id)
            last_drink = drink_id

        if self.can_make_drink(boozes, booze_dict): 
            can_make.append(last_drink)

        self.mc.set("available_drink_list", can_make)
        return can_make

    def make_drink(self, id, recipe_arg):

        drink = Drink.query.filter_by(id=int(id)).first()
        dispensers = Dispenser.query.order_by(Dispenser.id).all()

        recipe = []
        size = 0
        for booze in recipe_arg:
            r = None
            booze_id = int(booze[5:])
            for i in xrange(self.disp_count):
                disp = dispensers[i]
                if booze_id == disp.booze_id:
                    r = {}
                    r['dispenser'] = disp.id
                    r['dispenser_actual'] = disp.actual
                    r['booze'] = booze_id
                    r['ml'] = recipe_arg[booze]
                    size += r['ml']
                    break
            if not r:
                self.err = "Cannot make drink. I don't have the required booze: %d" % booze_id
                error(self.err)
                return False
            recipe.append(r)
        
        log("Making drink: '%s' size %.2f ml" % (drink.name.name, size))
        self.led_driver.make_drink()
        dur = 0
        active_disp = []
        for r in recipe:
            if r['dispenser_actual'] == 0:
                r['ms'] = int(r['ml'] * TICKS_PER_ML)
            else:
                r['ms'] = int(r['ml'] * TICKS_PER_ML * (CALIBRATE_ML / float(r['dispenser_actual'])))
            self.driver.dispense_ticks(r['dispenser'] - 1, int(r['ms']))
            log("..dispense %d for %d ticks" % (r['dispenser'] - 1, int(r['ms'])))
            active_disp.append(r['dispenser'])
            sleep(.01)

            if r['ms'] > dur: dur = r['ms']

        while True:
            sleep(.1)
            done = True
            for disp in active_disp:
                if self.driver.is_dispensing(disp - 1): 
                    done = False
                    break
            if done: break

        self.led_driver.drink_complete()
        log("drink complete")

        try:
            t = localtime()
            drinklog = open(local.application.drinks_log_file, "a")
            drinklog.write("%d-%d-%d %d:%02d,%s,%d ml\n" % (t.tm_year, t.tm_mon, t.tm_mday, t.tm_hour, t.tm_min, drink.name.name, size))
            drinklog.close()
        except IOError:
            pass

#        trouble = False
#        for disp in xrange(self.disp_count):
#            if not self.driver.ping(disp):
#                error("dispenser %d failed to respond to ping" % disp)
#                trouble = True
#
#        if trouble:
#            self.driver.chain_init()
#            log("resetting the chain!")

        FlashGreenLeds(self).start()

        return True 

class FlashGreenLeds(Thread):
    def __init__(self, mixer):
        Thread.__init__(self)
        self.mixer = mixer

    def run(self):
        sleep(5);
        self.mixer.led_driver.idle()
