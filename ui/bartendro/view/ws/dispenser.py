# -*- coding: utf-8 -*-
import logging
from time import sleep
from werkzeug.exceptions import ServiceUnavailable
from bartendro import app, db, mixer
from flask import Flask, request
from flask.ext.login import current_user
from bartendro.model.drink import Drink
from bartendro.model.booze import Booze
from bartendro.form.booze import BoozeForm
from bartendro import fsm

log = logging.getLogger('bartendro')

@app.route('/ws/dispenser/<int:disp>/on')
def ws_dispenser_on(disp):
    if app.options.must_login_to_dispense and not current_user.is_authenticated():
        return "login required"

    if app.globals.get_state() == fsm.STATE_ERROR:
        return "error state"

    is_disp, is_cs = app.driver.is_dispensing(disp - 1)
    if is_cs:
        app.mixer.set_state(fsm.STATE_ERROR)
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

    if app.globals.get_state() == fsm.STATE_ERROR:
        return "error state"

    is_disp, is_cs = app.driver.is_dispensing(disp - 1)
    if is_cs:
        app.mixer.set_state(fsm.STATE_ERROR)
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

    if app.globals.get_state() == fsm.STATE_ERROR:
        return "error state"

    dispenser = db.session.query(Dispenser).filter_by(id=disp).first()
    if not dispenser:
        return "Cannot test dispenser. Incorrect dispenser."

    try:
        is_cs, err = app.mixer.dispense_ml(dispenser, app.options.test_dispense_ml)
        if is_cs:
            app.mixer.set_state(fsm.STATE_ERROR)
            return "error state"
        if err:
            err = "Failed to test dispense on dispenser %d: %s" % (disp, err)
            log.error(err)
            return err
    except mixer.BartendroBusyError:
        return "busy"

    return ""

@app.route('/ws/clean')
def ws_dispenser_clean():
    if app.options.must_login_to_dispense and not current_user.is_authenticated():
        return "login required"

    if app.globals.get_state() == fsm.STATE_ERROR:
        return "error state"

    try:
        app.mixer.clean()
    except mixer.BartendroCantPourError, err:
        raise BadRequest(err)
    except mixer.BartendroBrokenError, err:
        raise InternalServerError(err)
    except mixer.BartendroBusyError, err:
        raise ServiceUnavailable(err)

    return ""

@app.route('/ws/clean/right')
def ws_dispenser_clean_right():
    if app.options.must_login_to_dispense and not current_user.is_authenticated():
        return "login required"

    if app.globals.get_state() == fsm.STATE_ERROR:
        return "error state"

    try:
        app.mixer.clean_right()
    except mixer.BartendroCantPourError, err:
        raise BadRequest(err)
    except mixer.BartendroBrokenError, err:
        raise InternalServerError(err)
    except mixer.BartendroBusyError, err:
        raise ServiceUnavailable(err)
    return ""

@app.route('/ws/clean/left')
def ws_dispenser_clean_left():
    if app.options.must_login_to_dispense and not current_user.is_authenticated():
        return "login required"

    if app.globals.get_state() == fsm.STATE_ERROR:
        return "error state"

    try:
        app.mixer.clean_left()
    except mixer.BartendroCantPourError, err:
        raise BadRequest(err)
    except mixer.BartendroBrokenError, err:
        raise InternalServerError(err)
    except mixer.BartendroBusyError, err:
        raise ServiceUnavailable(err)

    return ""
