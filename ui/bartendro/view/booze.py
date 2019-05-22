# -*- coding: utf-8 -*-
from bartendro import app, db
from sqlalchemy import func, asc, text
from flask import Flask, request, redirect, render_template
from flask.ext.login import login_required
from bartendro.model.drink import Drink, DrinkName
from bartendro.model.drink_booze import DrinkBooze
from bartendro.model.booze import Booze, booze_types
from bartendro.model.booze_group import BoozeGroup
from bartendro.form.booze import BoozeForm
from bartendro.model.dispenser import Dispenser
from bartendro.view.root import filter_drink_list

def load_loaded_boozes():
    loaded = db.session.query("id", "name", "abv", "type","dispenser")\
                 .from_statement(text("""SELECT booze.id, 
                                           booze.name,
                                           booze.abv,
                                           booze.type,
					   booze.image
                                           dispenser.id as dispenser
                                      FROM booze, dispenser
                                     WHERE booze.id = dispenser.booze_id
                                  ORDER BY booze.name ;"""))\
                 .params(foo='', bar='').all()
    return loaded

def load_drink_list(booze_id):
    """ load drinks that can be made with booze_id. We have both
        all the possible drinks and the drinks we can make with the 
        booze we have """
    drink_list = []
    all_drink_list = db.session.query(Drink) \
                        .join(DrinkName) \
                        .join(DrinkBooze) \
                        .filter(Drink.name_id == DrinkName.id)  \
                        .filter(Drink.popular == 0)  \
                        .filter(Drink.available == 1)  \
                        .filter(DrinkBooze.booze_id == booze_id)  \
                        .order_by(asc(func.lower(DrinkName.name))).all()
     
    can_make = app.mixer.get_available_drink_list()
    can_make_dict = {}
    for drink in can_make:
        can_make_dict[drink] = 1

    can_make_drink_list = filter_drink_list(can_make_dict, all_drink_list)
    return (all_drink_list, can_make_drink_list)

@app.route('/booze')
@login_required
def booze():
    all_boozes = Booze.query.order_by(asc(func.lower(Booze.name)))
    loaded_boozes = load_loaded_boozes()
    (all_drink_list, can_make_drink_list) = load_drink_list(0)
    
    return render_template("booze", options=app.options, all_drink_list=all_drink_list, all_boozes=all_boozes, loaded_boozes=loaded_boozes, can_make_drink_list=can_make_drink_list, title="Explore Booze")

@app.route('/booze/<id>')
@login_required
def booze_detail(id):
    booze = Booze.query.filter_by(id=int(id)).first()
    # what is your booze_types
    #import pdb
    #pdb.set_trace()
    booze.type = booze_types[booze.type][1]
    all_boozes = Booze.query.order_by(asc(func.lower(Booze.name)))
    loaded_boozes = load_loaded_boozes()
    drink_list = load_drink_list(booze.id)
    (all_drink_list, can_make_drink_list) = load_drink_list(booze.id)
    return render_template("booze", options=app.options, all_drink_list=all_drink_list, all_boozes=all_boozes, loaded_boozes=loaded_boozes, can_make_drink_list=can_make_drink_list, title="Explore Booze", booze=booze )
