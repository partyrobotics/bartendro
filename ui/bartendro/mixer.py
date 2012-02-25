# -*- coding: utf-8 -*-
from time import sleep
import memcache
from sqlalchemy.orm import mapper, relationship, backref
from bartendro.utils import session, local
from bartendro.model.drink import Drink
from bartendro.model.dispenser import Dispenser
from bartendro.model import drink_booze
from bartendro.model import booze

MS_PER_ML = 86 

class Mixer(object):
    '''This is where the magic happens!'''

    def __init__(self, driver):
        self.driver = driver
        self.err = ""
        self.disp_count = self.driver.count()
        self.leds_color(0, 0, 255)
        self.mc = local.application.mc

    def get_error(self):
        #self.driver.get_error()
        return self.err

    def leds_color(self, r, g, b):
        for i in xrange(self.disp_count):
            self.driver.led(i, r, g, b)

    def can_make_drink(self, boozes, booze_dict):
        ok = True
        for booze in boozes:
            try:
                foo = booze_dict[booze]
            except KeyError:
                ok = False
        return ok

    def get_available_drink_list(self):
        can_make = self.mc.get("available_drink_list")
        if can_make: 
            return can_make

        boozes = session.query("booze_id") \
                        .from_statement("SELECT booze_id FROM dispenser ORDER BY id LIMIT :d") \
                        .params(d=self.disp_count).all()

        booze_dict = {}
        for booze_id in boozes:
            booze_dict[booze_id[0]] = 1

        drinks = session.query("drink_id", "booze_id") \
                        .from_statement("SELECT d.id AS drink_id, db.booze_id AS booze_id FROM drink d, drink_booze db WHERE db.drink_id = d.id ORDER BY d.id, db.booze_id") \
                        .all()
        print drinks
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

    def make_drink(self, id, size, strength):
        self.get_available_drink_list()

        drink = Drink.query.filter_by(id=int(id)).first()
        dispensers = Dispenser.query.order_by(Dispenser.id).all()

        recipe = []
        for db in drink.drink_boozes:
            r = None
            for i in xrange(self.disp_count):
                disp = dispensers[i]
                if db.booze_id == disp.booze_id:
                    r = {}
                    r['dispenser'] = disp.id
                    r['booze'] = db.booze_id
                    r['booze_name'] = db.booze.name
                    r['part'] = db.value
                    break
            if not r:
                self.err = "Cannot make drink. I don't have the required booze: %s" % db.booze.name
                print self.err
                return 1
            recipe.append(r)

        total_parts = 0
        for r in recipe:
            total_parts += r['part']

        self.leds_color(255, 0, 255)
        dur = 0
        active_disp = []
        for r in recipe:
            r['ml'] = r['part'] * size / total_parts
            print "%s: %d ml" % (r['dispenser']-1, r['ml'])
            r['ms'] = r['ml'] * MS_PER_ML
            self.driver.dispense(r['dispenser'] - 1, int(r['ms']))
            active_disp.append(r['dispenser'])
            sleep(.01)

            if r['ms'] > dur: dur = r['ms']

        self.leds_color(255, 0, 0)
        while True:
            done = True
	    for disp in active_disp:
		if self.driver.is_dispensing(disp - 1): 
                    done = False
                    break
            if done: break

        self.leds_color(0, 255, 0)
        sleep(1)
#        for i in xrange(10):
#            self.leds_color(0, 255, 0)
#            sleep(.25)
#            self.leds_color(0, 0, 0)
#            sleep(.25)

        self.leds_color(0, 0, 255)

        return 0 
