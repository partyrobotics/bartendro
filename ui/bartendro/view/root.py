# -*- coding: utf-8 -*-
import memcache
import random
from sqlalchemy import func, asc
from sqlalchemy.exc import OperationalError
from bartendro import app, db
from flask import Flask, request, render_template, redirect
from bartendro.model.dispenser import Dispenser
from bartendro.model.drink import Drink
from bartendro.model.drink_name import DrinkName
from bartendro import fsm
from bartendro.mixer import LL_LOW, LL_OK

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

@app.route('/')
def index():
    if app.globals.get_state() == fsm.STATE_ERROR:
        return render_template("index", 
                               options=app.options, 
                               top_drinks=[], 
                               other_drinks=[],
                               error_message="Bartendro is in trouble!<br/><br/>I need some attention! Please find my master, so they can make me feel better.",
                               title="Bartendro error")

    try:
        can_make = app.mixer.get_available_drink_list()
    except OperationalError:
        return render_template("index", 
                               options=app.options, 
                               top_drinks=[], 
                               other_drinks=[],
                               error_message="Bartendro database errror.<br/><br/>There doesn't seem to be a valid database installed.",
                               title="Bartendro error")

    can_make_dict = {}
    for drink in can_make:
        can_make_dict[drink] = 1

    top_drinks = db.session.query(Drink) \
                        .join(DrinkName) \
                        .filter(Drink.name_id == DrinkName.id)  \
                        .filter(Drink.popular == 1)  \
                        .filter(Drink.available == 1)  \
                        .order_by(asc(func.lower(DrinkName.name))).all() 

    top_drinks = filter_drink_list(can_make_dict, top_drinks)
    process_ingredients(top_drinks)

    other_drinks = db.session.query(Drink) \
                        .join(DrinkName) \
                        .filter(Drink.name_id == DrinkName.id)  \
                        .filter(Drink.popular == 0)  \
                        .filter(Drink.available == 1)  \
                        .order_by(asc(func.lower(DrinkName.name))).all() 
    other_drinks = filter_drink_list(can_make_dict, other_drinks)
    process_ingredients(other_drinks)


    if (not len(top_drinks) and not len(other_drinks)) or app.globals.get_state() == fsm.STATE_HARD_OUT:
        return render_template("index", 
                               options=app.options, 
                               top_drinks=[], 
                               other_drinks=[],
                               error_message="Drinks can't be made with the available boozes.<br/><br/>I need some attention! Please find my master, so they can make me feel better.",
                               title="Bartendro error")
            
    return render_template("index", 
                           options=app.options, 
                           top_drinks=top_drinks, 
                           other_drinks=other_drinks,
                           lucky_drink_id = can_make[int(random.randint(0, len(can_make) - 1))],
                           title="Bartendro")

@app.route('/shots')
def shots():

    if not app.options.use_shotbot_ui:
        return redirect("/")

    if app.globals.get_state() == fsm.STATE_ERROR:
        return render_template("shots", 
                               num_shots_ready=0,
                               options=app.options, 
                               error_message="Bartendro is in trouble!<br/><br/>I need some attention! Please find my master, so they can make me feel better.",
                               title="Bartendro error")

    dispensers = db.session.query(Dispenser).all()
    dispensers = dispensers[:app.driver.count()]

    shots = []
    for disp in dispensers:
        if disp.out == LL_OK or disp.out == LL_LOW or not app.options.use_liquid_level_sensors:
            shots.append(disp.booze)

    if len(shots) == 0:
        return render_template("shots", 
                               num_shots_ready=0,
                               options=app.options, 
                               error_message="Bartendro is out of all boozes. Oh no!<br/><br/>I need some attention! Please find my master, so they can make me feel better.",
                               title="Bartendro error")

    return render_template("shots", 
                           num_shots_ready= len(shots),
                           options=app.options, 
                           shots=shots, 
                           title="Shots")
