# -*- coding: utf-8 -*-
from time import sleep
from sqlalchemy.orm import mapper, relationship, backref
from bartendro.model.drink import Drink
from bartendro.model.dispenser import Dispenser
from bartendro.model import drink_booze
from bartendro.model import booze

# We have a more accurate version here in the mixer. The UI doesn't need to be so accurate, but
# while dispensing, its better to be accurate.
ML_PER_FL_OZ = 29.57
MS_PER_ML = 86 

class Mixer(object):
    '''This is where the magic happens!'''

    def __init__(self, driver):
        self.driver = driver
        self.err = ""
        self.disp_count = self.driver.count()
        self.leds_color(0, 0, 255)

    def get_error(self):
        #self.driver.get_error()
        return self.err

    def leds_color(self, r, g, b):
        for i in xrange(self.disp_count):
            self.driver.led(i, r, g, b)

    def make_drink(self, id, size, strength):
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
                print "Fail to make drink"
                self.err = "Cannot make drink. I don't have the required booze: %s" % db.booze.name
                return 1
            recipe.append(r)

        total_parts = 0
        for r in recipe:
            total_parts += r['part']

        self.leds_color(255, 0, 255)
        dur = 0
        active_disp = []
        for r in recipe:
            r['ml'] = r['part'] * size * ML_PER_FL_OZ / total_parts
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
