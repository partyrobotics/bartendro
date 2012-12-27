# -*- coding: utf-8 -*-
import memcache
from bartendro.utils import session, render_template, render_json, expose, validate_url, url_for, local
from bartendro.model.drink import Drink
from bartendro.model.drink_name import DrinkName

def process_ingredients(drinks):
    for drink in drinks:
        drink.process_ingredients()

def filter_drink_list(can_make_dict, drinks):
    filtered = []
    for drink in drinks:
        try:
            foo =can_make_dict[drink.id]
            filtered.append(drink)
        except KeyError:
            pass
    return filtered

@expose('/bartendro')
def index(request):
    mixer = local.application.mixer

    can_make = mixer.get_available_drink_list()
    can_make_dict = {}
    for drink in can_make:
        can_make_dict[drink] = 1

    top_drinks = session.query(Drink) \
                        .join(DrinkName) \
                        .filter(Drink.name_id == DrinkName.id)  \
                        .filter(Drink.popular == 1)  \
                        .filter(Drink.available == 1)  \
                        .order_by(DrinkName.name).all() 
    top_drinks = filter_drink_list(can_make_dict, top_drinks)
    process_ingredients(top_drinks)

    other_drinks = session.query(Drink) \
                        .join(DrinkName) \
                        .filter(Drink.name_id == DrinkName.id)  \
                        .filter(Drink.popular == 0)  \
                        .filter(Drink.available == 1)  \
                        .order_by(DrinkName.name).all() 
    other_drinks = filter_drink_list(can_make_dict, other_drinks)
    process_ingredients(other_drinks)
            
    return render_template("index", 
                           top_drinks=top_drinks, 
                           other_drinks=other_drinks,
                           title="Bartendro")
