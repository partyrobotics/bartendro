# -*- coding: utf-8 -*-
from sqlalchemy.orm import mapper, relationship, backref

from bartendro.model import drink
from bartendro.model import drink_name
from bartendro.model import drink_liquid
from bartendro.model import liquid
#from bartendro.model import config

drink.Drink.name = relationship(drink_name.DrinkName, backref=backref("drink"))
