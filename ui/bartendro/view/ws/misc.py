# -*- coding: utf-8 -*-
from werkzeug.exceptions import ServiceUnavailable
from bartendro import app, db
from flask import Flask, request
from bartendro.model.drink import Drink
from bartendro.model.booze import Booze
from bartendro.form.booze import BoozeForm

@app.route('/ws/reset')
def ws_reset():
    driver = app.driver
    mc = app.mc
    mc.delete("top_drinks")
    mc.delete("other_drinks")
    mc.delete("available_drink_list")
    driver.reset()
    return "ok\n"

@app.route('/ws/test')
def ws_test_chain():
    driver = app.driver
    for disp in xrange(driver.count()):
	if not driver.ping(disp):
	    raise ServiceUnavailable("Dispenser %d failed ping." % disp + 1)

    return "ok"

@app.route('/ws/checklevels')
def ws_check_levels():
    mixer = app.mixer
    if not mixer.check_liquid_levels():
        raise ServiceUnavailable("Error: Checking dispenser levels failed.")
    mc = app.mc
    mc.delete("top_drinks")
    mc.delete("other_drinks")
    mc.delete("available_drink_list")
    return "ok\n"
