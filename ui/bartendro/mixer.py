# -*- coding: utf-8 -*-
from time import sleep
from sqlalchemy.orm import mapper, relationship, backref
from bartendro.model.drink import Drink
from bartendro.model.dispenser import Dispenser
from bartendro.model import drink_booze
from bartendro.model import booze

ML_PER_FL_OZ = 29.57
MS_PER_ML = 86 

class Mixer(object):
    '''This is where the magic happens!'''

    def __init__(self, driver):
        self.driver = driver
        self.err = ""
        self.disp_count = self.driver.count()
        self.leds_idle()

    def get_error(self):
        #self.driver.get_error()
        return self.err

    def leds_idle(self):
        for i in xrange(self.disp_count):
            self.driver.led(i, 0, 0, 255);

    def leds_make_drink(self):
        for i in xrange(self.disp_count):
            self.driver.led(i, 255, 0, 0);

    def leds_drink_complete(self):
        for i in xrange(self.disp_count):
            self.driver.led(i, 0, 0, 255);

    def make_drink(self, id, size, strength):
        drink = Drink.query.filter_by(id=int(id)).first()
        dispensers = Dispenser.query.order_by(Dispenser.id).all()
        print "make ", drink
        print "dispensers ", dispensers

        recipe = []
        for db in drink.drink_boozes:
            r = None
            for i in xrange(self.disp_count):
                disp = dispensers[i]
                if db.booze_id == disp.booze_id:
                    print "drink_booze %d is in dispenser %d" % (db.booze_id, disp.id)
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

        print "start making drink!"
        self.leds_make_drink()
        dur = 0
        for r in recipe:
            r['ml'] = r['part'] * size * ML_PER_FL_OZ / total_parts
            r['ms'] = r['ml'] * MS_PER_ML
            self.driver.dispense(r['dispenser'] - 1, int(r['ms']))
            sleep(.01)

            if r['ms'] > dur: dur = r['ms']

        print "commands sent"

        dur = dur * 2
        sleep(dur / 1000)
        print "drink kinda done"
        leds_drink_complete()
        sleep(3)
        leds_idle()

        return 0 
