# -*- coding: utf-8 -*-
from operator import attrgetter
from bartendro.utils import session, render_template, render_json, expose, validate_url, url_for
from bartendro.model.drink import Drink
from bartendro.model.drink_name import DrinkName

def process_ingredients(drinks):
    for drink in drinks:
        ing = []

        drink.drink_boozes = sorted(drink.drink_boozes, key=attrgetter('booze.abv', 'booze.name'), reverse=True)
        for db in drink.drink_boozes:
            ing.append(db.booze.name)
        drink.ingredients = ing

@expose('/')
def index(request):
    top_drinks = session.query(Drink) \
                        .join(DrinkName) \
                        .filter(Drink.name_id == DrinkName.id)  \
                        .filter(Drink.popular == 1)  \
                        .order_by(DrinkName.name).all() 
    process_ingredients(top_drinks)
    other_drinks = session.query(Drink) \
                        .join(DrinkName) \
                        .filter(Drink.name_id == DrinkName.id)  \
                        .filter(Drink.popular == 0)  \
                        .order_by(DrinkName.name).all() 
    process_ingredients(other_drinks)
            
    return render_template("index", top_drinks=top_drinks, other_drinks=other_drinks)
