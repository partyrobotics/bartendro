# -*- coding: utf-8 -*-
import logging
from time import sleep
from werkzeug.exceptions import ServiceUnavailable
from bartendro import app, db, mixer
from flask import Flask, request
from flask.ext.login import current_user
from bartendro.model.drink import Drink
from bartendro.model.booze import Booze
from bartendro.model.dispenser import Dispenser
from bartendro.form.booze import BoozeForm
from bartendro import fsm
from bartendro.error import BartendroBusyError, BartendroBrokenError, BartendroCantPourError, BartendroCurrentSenseError
from bartendro.router.driver import MOTOR_DIRECTION_FORWARD, MOTOR_DIRECTION_BACKWARD

log = logging.getLogger('bartendro')


@app.route('/ws/dispenser/<int:disp>/on')
def ws_dispenser_on(disp):
    if app.options.must_login_to_dispense and not current_user.is_authenticated():
        return "login required"

    return run_dispenser(disp, True)

@app.route('/ws/dispenser/<int:disp>/on/reverse')
def ws_dispenser_reverse(disp):
    if app.options.must_login_to_dispense and not current_user.is_authenticated():
        return "login required"

    return run_dispenser(disp, False)

def run_dispenser(disp, forward):
    if app.globals.get_state() == fsm.STATE_ERROR:
        return "error state"

    is_disp, is_cs = app.driver.is_dispensing(disp - 1)
    if is_cs:
        app.mixer.set_state(fsm.STATE_ERROR)
        return "error state"

    if forward:
        app.driver.set_motor_direction(disp, MOTOR_DIRECTION_FORWARD)
    else:
        app.driver.set_motor_direction(disp, MOTOR_DIRECTION_BACKWARD)

    err = ""
    if not app.driver.start(disp - 1):
        err = "Failed to start dispenser %d" % disp
        log.error(err)

    return err

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

    err = ""
    if not app.driver.stop(disp - 1):
        err = "Failed to stop dispenser %d" % disp
        log.error(err)

    app.driver.set_motor_direction(disp, MOTOR_DIRECTION_FORWARD) 
        
    return err

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
        app.mixer.dispense_ml(dispenser, app.options.test_dispense_ml)
    except BartendroBrokenError:
        raise InternalServerError

    return ""

@app.route('/ws/clean')
def ws_dispenser_clean():
    if app.options.must_login_to_dispense and not current_user.is_authenticated():
        return "login required"

    if app.globals.get_state() == fsm.STATE_ERROR:
        return "error state"

    try:
        app.mixer.clean()
    except BartendroCantPourError, err:
        raise BadRequest(err)
    except BartendroBrokenError, err:
        raise InternalServerError(err)
    except BartendroBusyError, err:
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
    except BartendroCantPourError, err:
        raise BadRequest(err)
    except BartendroBrokenError, err:
        raise InternalServerError(err)
    except BartendroBusyError, err:
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
    except BartendroCantPourError, err:
        raise BadRequest(err)
    except BartendroBrokenError, err:
        raise InternalServerError(err)
    except BartendroBusyError, err:
        raise ServiceUnavailable(err)

    return ""
