# -*- coding: utf-8 -*-
from bartendro import app, db
from sqlalchemy import func, asc, text
from flask import Flask, request, redirect, render_template
from flask import Response
import json
from flask.ext.login import login_required
from bartendro.model.drink import Drink, DrinkName
from bartendro.model.drink_booze import DrinkBooze
from bartendro.model.booze import Booze, booze_types
from bartendro.model.booze_group import BoozeGroup
from bartendro.form.booze import BoozeForm
from bartendro.model.dispenser import Dispenser
from bartendro.view.root import filter_drink_list

def load_loaded_boozes():
    # this assumes we have 16 dispensers, or, this doesn't care what max dispensers is
    loaded = db.session.query("id", "name", "abv", "type","dispenser")\
                 .from_statement(text("""SELECT booze.id, 
                                           booze.name,
                                           booze.abv,
                                           booze.type,
					   booze.image,
                                           dispenser.id as dispenser
                                      FROM booze, dispenser
                                     WHERE booze.id = dispenser.booze_id
                                     AND dispenser.id < 9
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
    ''' Page showing all booze, and all loaded booze '''

    all_boozes = Booze.query.order_by(asc(func.lower(Booze.name)))
    loaded_boozes = load_loaded_boozes()
    (all_drink_list, can_make_drink_list) = load_drink_list(0)
    
    return render_template("booze", options=app.options, all_drink_list=all_drink_list, all_boozes=all_boozes, loaded_boozes=loaded_boozes, can_make_drink_list=can_make_drink_list, title="Explore Booze")

@app.route('/booze/<int:id>')
@login_required
def booze_detail(id):
    ''' Page showing the selected booze, and drinks that can be made with that booze.'''

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

@app.route('/booze/all')
def booze_all():
    ''' Returns json of all booze in our database. '''

    data = Booze.query.order_by(asc(func.lower(Booze.name)))
    lst = [{'id':b.id, 'name':b.name} for b in data]
    js = json.dumps(lst)
    resp = Response(js, status=200, mimetype="application/json")
    return resp

@app.route('/booze/loaded')
def booze_loaded():
    ''' Returns json of all loaded booze. But does not show the dispenser where it is loaded.'''
    data = Booze.query.order_by(asc(func.lower(Booze.name)))
    data = load_loaded_boozes()
    lst = [{'id':b.id, 'name':b.name} for b in data]
    js = json.dumps(lst)
    resp = Response(js, status=200, mimetype="application/json")
    return resp
