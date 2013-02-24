# -*- coding: utf-8 -*-
from time import sleep
from bartendro import app, db
from flask import Flask, request, render_text
from bartendro.model.drink import Drink
from bartendro.model.booze import Booze
from bartendro.form.booze import BoozeForm
from bartendro.mixer import CALIBRATION_TICKS

@app.route('/ws/dispenser/<int:disp>/on')
def ws_dispenser_on(disp):
    app.driver.start(disp - 1)
    return render_text("ok\n")

@app.route('/ws/dispenser/<int:disp>/off')
def ws_dispenser_off(disp):
    app.driver.stop(disp - 1)
    return render_text("ok\n")

@app.route('/ws/dispenser/<int:disp>/test')
def ws_dispenser_test(disp):
    app.driver.dispense_ticks(disp - 1, CALIBRATION_TICKS)
    while driver.is_dispensing(disp - 1):
	sleep(.1)
    t, ticks = driver.get_dispense_stats(disp - 1)
    return render_text("ok\n")
