# -*- coding: utf-8 -*-
from operator import attrgetter
from bartendro.utils import session, render_template, render_json, expose, validate_url, url_for
from bartendro.model.drink import Drink
from bartendro.model.drink_name import DrinkName

@expose('/')
def index(request):
    drinks = session.query(Drink).join(DrinkName).filter(Drink.name_id == DrinkName.id) \
                                 .order_by(DrinkName.name).all()
    for drink in drinks:
        ing = []

        drink.drink_boozes = sorted(drink.drink_boozes, key=attrgetter('booze.abv', 'booze.name'), reverse=True)
        for db in drink.drink_boozes:
            ing.append(db.booze.name)
        drink.ingredients = ', '.join(ing)
            
    return render_template("index", drinks=drinks)
