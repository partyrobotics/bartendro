# -*- coding: utf-8 -*-
from bartendro import app, db
from flask import Flask, request, render_template
from bartendro.model.drink import Drink
from bartendro.model.drink_booze import DrinkBooze
from bartendro.model.custom_drink import CustomDrink
from bartendro.model.booze import Booze, booze_types
from bartendro.model.booze import BOOZE_TYPE_UNKNOWN, BOOZE_TYPE_ALCOHOL, BOOZE_TYPE_TART, BOOZE_TYPE_SWEET
from bartendro.model.booze_group import BoozeGroup
from bartendro.model.booze_group_booze import BoozeGroupBooze
from bartendro.model.drink_name import DrinkName
from bartendro.model.dispenser import Dispenser
from bartendro import constant 

@app.route('/drink/<id>')
def drink(id):
    drink = db.session.query(Drink) \
                          .filter(Drink.id == id) \
                          .first() 

    boozes = db.session.query(Booze) \
                          .join(DrinkBooze.booze) \
                          .filter(DrinkBooze.drink_id == drink.id)

    custom_drink = db.session.query(CustomDrink) \
                          .filter(drink.id == CustomDrink.drink_id) \
                          .first()
    drink.process_ingredients()

    has_non_alcohol = False
    has_alcohol = False
    has_sweet = False
    has_tart = False
    show_sobriety = 0 #drink.id == 46
    for booze in boozes:
        if booze.type == BOOZE_TYPE_ALCOHOL: 
            has_alcohol = True
        else:
            has_non_alcohol = True
        if booze.type == BOOZE_TYPE_SWEET: has_sweet = True
        if booze.type == BOOZE_TYPE_TART: has_tart = True

    show_sweet_tart = has_sweet and has_tart
    show_strength = has_alcohol and has_non_alcohol
    show_size = 1
    show_taster = 0 #not show_sobriety

    if not custom_drink:
        return render_template("drink/index", 
                               drink=drink, 
                               title=drink.name.name,
                               metric=1,
                               is_custom=0,
                               show_sweet_tart=show_sweet_tart,
                               show_strength=show_strength,
                               show_size=show_size,
                               show_taster=show_taster,
                               show_sobriety=show_sobriety)

    dispensers = db.session.query(Dispenser).all()
    disp_boozes = {}
    for dispenser in dispensers:
        disp_boozes[dispenser.booze_id] = 1

    print disp_boozes

    booze_group = db.session.query(BoozeGroup) \
                          .join(DrinkBooze, DrinkBooze.booze_id == BoozeGroup.abstract_booze_id) \
                          .join(BoozeGroupBooze) \
                          .filter(Drink.id == id) \
                          .first()

    filtered = []
    for bgb in booze_group.booze_group_boozes:
        print booze
        try:
            dummy = disp_boozes[bgb.booze_id]
            filtered.append(bgb)
        except KeyError:
            pass

    booze_group.booze_group_boozes = sorted(filtered, key=lambda booze: booze.sequence ) 
    return render_template("drink/index", 
                           drink=drink, 
                           title=drink.name.name,
                           is_custom=1,
                           metric=1,
                           custom_drink=drink.custom_drink[0],
                           booze_group=booze_group,
                           show_sweet_tart=show_sweet_tart,
                           show_strength=show_strength,
                           show_size=show_size,
                           show_taster=show_taster,
                           show_sobriety=show_sobriety)

@app.route('/drink/sobriety')
def drink_sobriety():
    return render_template("drink/sobriety")
