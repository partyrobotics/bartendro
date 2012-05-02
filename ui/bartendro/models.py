# -*- coding: utf-8 -*-
from sqlalchemy.orm import mapper, relationship, backref

from bartendro.model.drink import Drink
from bartendro.model.custom_drink import CustomDrink
from bartendro.model.custom_drink_booze import CustomDrinkBooze
from bartendro.model.drink_name import DrinkName
from bartendro.model.drink_booze import DrinkBooze

from bartendro.model.booze import Booze
from bartendro.model.booze_group import BoozeGroup
from bartendro.model.booze_group_booze import BoozeGroupBooze

from bartendro.model.dispenser import Dispenser

Drink.name = relationship(DrinkName, backref=backref("drink"))

# TODO: This relationship should really be on Drinkbooze
Drink.drink_boozes = relationship(DrinkBooze, backref=backref("drink"))
DrinkBooze.booze = relationship(Booze, backref=backref("drink_booze"))

# This is the proper relationship from above.
#DrinkBooze.drink= relationship(Drink, backref=backref("drink_booze"))

Dispenser.booze = relationship(Booze, backref=backref("dispenser"))
BoozeGroup.abstract_booze = relationship(Booze, backref=backref("booze_group"))
BoozeGroupBooze.booze_group = relationship(BoozeGroup, backref=backref("booze_group_booze"))
BoozeGroupBooze.booze = relationship(Booze, backref=backref("booze_group_booze"))
CustomDrink.drink = relationship(Drink, backref=backref("custom_drink"))
CustomDrinkBooze.booze = relationship(Booze, backref=backref("custom_drink_booze"))
CustomDrinkBooze.custom_drink = relationship(Drink, backref=backref("custom_drink_booze"),
                                      primaryjoin="CustomDrinkBooze.custom_drink_id==Drink.id",
                                      foreign_keys=[CustomDrinkBooze.custom_drink_id])
