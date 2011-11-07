# -*- coding: utf-8 -*-
from sqlalchemy.orm import mapper, relationship, backref

from bartendro.model import drink
from bartendro.model import drink_name
from bartendro.model import drink_booze
from bartendro.model import booze
#from bartendro.model import config

drink.Drink.name = relationship(drink_name.DrinkName, backref=backref("drink"))
drink.Drink.drink_boozes = relationship(drink_booze.DrinkBooze, backref=backref("drink"))
drink_booze.DrinkBooze.booze = relationship(booze.Booze, backref=backref("drink_booze"))
