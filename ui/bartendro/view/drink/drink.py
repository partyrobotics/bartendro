# -*- coding: utf-8 -*-
from werkzeug.utils import redirect
from bartendro.utils import session, render_template, render_json, expose, validate_url, url_for
from bartendro.model.drink import Drink
from bartendro.model.drink_booze import DrinkBooze
from bartendro.model.custom_drink import CustomDrink
from bartendro.model.custom_drink_booze import CustomDrinkBooze
from bartendro.model.booze import Booze
from bartendro.model.booze_group import BoozeGroup
from bartendro.model.booze_group_booze import BoozeGroupBooze
from bartendro.model.drink_name import DrinkName
from bartendro import constant 

@expose('/drink/<id>')
def view(request, id):
    drink = session.query(Drink).join(DrinkName).filter(Drink.id == id).first()
    drink.process_ingredients()
    # convert size to fl oz
    drink.sugg_size = drink.sugg_size / constant.ML_PER_FL_OZ

    custom_drink = session.query(CustomDrink) \
                          .join(CustomDrinkBooze) \
                          .filter(drink.id == CustomDrink.drink_id) \
                          .first()

    if not custom_drink:
        return render_template("drink/index", drink=drink, title="Make a %s" % drink.name, is_custom=0)

    booze_group = session.query(BoozeGroup) \
                          .join(DrinkBooze, DrinkBooze.booze_id == BoozeGroup.abstract_booze_id) \
                          .join(BoozeGroupBooze) \
                          .filter(Drink.id == id) \
                          .first()

    booze_group.booze_group_boozes = sorted(booze_group.booze_group_boozes, 
                                            key=lambda booze: booze.sequence )

    return render_template("drink/index", 
                           drink=drink, 
                           title="Make a %s" % drink.name,
                           is_custom=1,
                           custom_drink_name=drink.custom_drink[0].name,
                           booze_group=booze_group)
