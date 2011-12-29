# -*- coding: utf-8 -*-
from sqlalchemy.orm import mapper, relationship, backref

from bartendro.model.drink import Drink
from bartendro.model.dispenser import Dispenser
from bartendro.model import drink_booze
from bartendro.model import booze

class Mixer(object):
    '''This is where the magic happens!'''

    def __init__(self, driver):
        self.driver = driver
        self.err = ""

    def get_error(self):
        #self.driver.get_error()
        return self.err

    def make_drink(self, id, size, strength):
        drink = Drink.query.filter_by(id=int(id)).first()
        dispensers = Dispenser.query.order_by(Dispenser.id).all()
        print "make ", drink
        print "dispensers ", dispensers

        disp_count = self.driver.count()
        print "%d dispensers\n" % disp_count

        recipe = []
        for db in drink.drink_boozes:
            r = None
            for i in xrange(disp_count):
                disp = dispensers[i]
                print "db: %d disp: %d" % (db.booze_id, disp.booze_id)
                if db.booze_id == disp.booze_id:
                    print "drink_booze %d is in dispenser %d" % (db.booze_id, disp.id)
                    r = {}
                    r['dispenser'] = disp.id
                    r['booze'] = db.booze_id
                    r['part'] = db.value
                    break
            if not r:
                print "Fail to make drink"
                self.err = "Cannot make drink. I don't have the required booze: %s" % db.booze.name
                return 1

        return 0 
