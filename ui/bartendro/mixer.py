# -*- coding: utf-8 -*-
from sqlalchemy.orm import mapper, relationship, backref

from bartendro.model import drink
from bartendro.model import drink_booze
from bartendro.model import booze

class DrinkMixer(object):
    '''This is where the magic happens!'''

    def __init__(self):
        pass

    def make_drink(self, id):
        drink = Drink.query.filter_by(id=int(id)).first()
