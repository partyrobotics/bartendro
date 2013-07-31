# -*- coding: utf-8 -*-
from time import sleep
from bartendro import app, db, mixer
from flask import Flask, request
from flask.ext.login import login_required, current_user
from werkzeug.exceptions import ServiceUnavailable, BadRequest
from bartendro.model.drink import Drink
from bartendro.model.booze import Booze
from bartendro.form.booze import BoozeForm
from bartendro import constant

@app.route('/ws/drink/<int:drink>')
def ws_drink(drink):
    drink_mixer = app.mixer
    if app.options.must_login_to_dispense and not current_user.is_authenticated():
        return "login required"

    recipe = {}
    for arg in request.args:
        recipe[arg] = int(request.args.get(arg))

    try:
        err = drink_mixer.make_drink(drink, recipe)
        if not err:
            return "ok\n"
        else:
            raise BadRequest(err)
    except mixer.BartendroBusyError:
        raise ServiceUnavailable("busy")

@app.route('/ws/drink/<int:drink>/available/<int:state>')
def ws_drink_available(drink, state):

    if not drink:
        db.session.query(Drink).update({'available' : state})
    else:
        db.session.query(Drink).filter(Drink.id==drink).update({'available' : state})
    db.session.flush()
    db.session.commit()
    return "ok\n"
