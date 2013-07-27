# -*- coding: utf-8 -*-
from time import sleep
from werkzeug.exceptions import ServiceUnavailable
from bartendro import app, db, mixer
from flask import Flask, request
from flask.ext.login import current_user
from bartendro.model.drink import Drink
from bartendro.model.booze import Booze
from bartendro.form.booze import BoozeForm

@app.route('/ws/dispenser/<int:disp>/on')
def ws_dispenser_on(disp):
    if app.options.must_login_to_dispense and not current_user.is_authenticated():
        return "login required"

    app.driver.start(disp - 1)
    return "ok\n"

@app.route('/ws/dispenser/<int:disp>/off')
def ws_dispenser_off(disp):
    if app.options.must_login_to_dispense and not current_user.is_authenticated():
        return "login required"

    app.driver.stop(disp - 1)
    return "ok\n"

@app.route('/ws/dispenser/<int:disp>/test')
def ws_dispenser_test(disp):
    try:
        app.mixer.test_dispense(disp - 1)
    except mixer.BartendroBusyError:
        raise ServiceUnavailable("busy")
    return "ok\n"

@app.route('/ws/clean')
def ws_dispenser_clean():
    if app.options.must_login_to_dispense and not current_user.is_authenticated():
        return "login required"

    app.mixer.clean()
    return "ok\n"
