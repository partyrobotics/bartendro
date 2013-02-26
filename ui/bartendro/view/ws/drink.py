# -*- coding: utf-8 -*-
from time import sleep
from bartendro import app, db
from flask import Flask, request
from werkzeug.exceptions import ServiceUnavailable
from bartendro.model.drink import Drink
from bartendro.model.booze import Booze
from bartendro.form.booze import BoozeForm
from bartendro import constant

@app.route('/ws/drink/<int:drink>')
def ws_drink(drink):
    mixer = app.mixer

    recipe = {}
    for arg in request.args:
        recipe[arg] = float(request.args.get(arg)) * constant.ML_PER_FL_OZ

    if mixer.make_drink(drink, recipe):
        return "ok\n"
    else:
        raise ServiceUnavailable("Error: %s (%d)" % (mixer.get_error(), ret))

@app.route('/ws/drink/<int:drink>/available/<int:state>')
def ws_drink_available(drink, state):

    if not drink:
        db.session.query(Drink).update({'available' : state})
    else:
        db.session.query(Drink).filter(Drink.id==drink).update({'available' : state})
    db.session.flush()
    db.session.commit()
    return "ok\n"
