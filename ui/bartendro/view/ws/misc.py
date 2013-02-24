# -*- coding: utf-8 -*-
from bartendro import app, db
from flask import Flask, request, render_text
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
    return render_text("ok\n")

@app.route('/ws/test')
def ws_test_chain():
    driver = app.driver
    for disp in xrange(driver.count()):
        print "test %d" % disp
	if not driver.ping(disp):
	    raise ServiceUnavailable("Error: Dispenser %d failed ping." % disp)
    return render_text("ok\n")

@app.route('/ws/checklevels')
def ws_check_levels(request):
    mixer = app.mixer
    if not mixer.check_liquid_levels():
        raise ServiceUnavailable("Error: Checking dispenser levels failed.")
    mc = app.mc
    mc.delete("top_drinks")
    mc.delete("other_drinks")
    mc.delete("available_drink_list")
    return render_text("ok\n")
