# -*- coding: utf-8 -*-
import logging
from time import sleep
from werkzeug.exceptions import ServiceUnavailable
from bartendro import app, db, mixer
from bartendro.global_lock import STATE_ERROR
from flask import Flask, request
from flask.ext.login import current_user
from bartendro.model.drink import Drink
from bartendro.model.booze import Booze
from bartendro.form.booze import BoozeForm

log = logging.getLogger('bartendro')

@app.route('/ws/dispenser/<int:disp>/on')
def ws_dispenser_on(disp):
    if app.options.must_login_to_dispense and not current_user.is_authenticated():
        return "login required"

    if app.mixer.get_state() == STATE_ERROR:
        return "error state"

    is_disp, is_cs = app.driver.is_dispensing(disp - 1)
    if is_cs:
        app.mixer.set_state(STATE_ERROR)
        return "error state"

    if not app.driver.start(disp - 1):
        err = "Failed to start dispenser %d" % disp
        log.error(err)
        return err

    return ""

@app.route('/ws/dispenser/<int:disp>/off')
def ws_dispenser_off(disp):
    if app.options.must_login_to_dispense and not current_user.is_authenticated():
        return "login required"

    if app.mixer.get_state() == STATE_ERROR:
        return "error state"

    is_disp, is_cs = app.driver.is_dispensing(disp - 1)
    if is_cs:
        app.mixer.set_state(STATE_ERROR)
        return "error state"

    if not app.driver.stop(disp - 1):
        err = "Failed to stop dispenser %d" % disp
        log.error(err)
        return err
        
    return ""

@app.route('/ws/dispenser/<int:disp>/test')
def ws_dispenser_test(disp):
    if app.options.must_login_to_dispense and not current_user.is_authenticated():
        return "login required"

    if app.mixer.get_state() == STATE_ERROR:
        return "error state"

    try:
        is_cs, err = app.mixer.dispense_ml(disp - 1, app.options.test_dispense_ml)
        if is_cs:
            app.mixer.set_state(STATE_ERROR)
            return "error state"
        if err:
            err = "Failed to test dispense on dispenser %d: %s" % (disp, err)
            log.error(err)
            return err
    except mixer.BartendroBusyError:
        return "busy"

    return ""

@app.route('/ws/dispenser/<int:disp>/dispense')
def ws_dispenser_dispense(disp):
    if app.options.must_login_to_dispense and not current_user.is_authenticated():
        return "login required"

    if app.mixer.get_state() == STATE_ERROR:
        return "error state"

    quantityml = request.values.get('quantity', 0, type=int)

    if (quantityml < 0 && quantityml > 500) :
        err = "Invalid quantity %d" % (quantityml)
        log.error(err)
        return err
        
    try:
        is_cs, err = app.mixer.dispense_ml(disp - 1, quantityml)
        if is_cs:
            app.mixer.set_state(STATE_ERROR)
            return "error state"
        if err:
            err = "Failed to dispense on dispenser %d: %s" % (disp, err)
            log.error(err)
            return err
    except mixer.BartendroBusyError:
        return "busy"

    return ""

@app.route('/ws/clean')
def ws_dispenser_clean():
    if app.options.must_login_to_dispense and not current_user.is_authenticated():
        return "login required"

    if app.mixer.get_state() == STATE_ERROR:
        return "error state"

    app.mixer.clean()
    return ""
