# -*- coding: utf-8 -*-
import os
from time import sleep
from werkzeug.exceptions import BadRequest
from bartendro import app, db
from flask import Flask, request, Response
from flask.ext.login import login_required

@app.route('/ws/liquidlevel/test/<int:disp>')
@login_required
def ws_liquidlevel_test(disp):
    low, out = app.driver.get_liquid_level_thresholds(disp)
    app.mixer.liquid_level_test(disp, out)
    return "ok"

@app.route('/ws/liquidlevel/out/<int:disp>/set')
@login_required
def ws_liquidlevel_out_set(disp):
    driver = app.driver
    if disp < 0 or disp >= driver.count():
        raise BadRequest
    driver.update_liquid_levels()
    sleep(.01)
    out = driver.get_liquid_level(disp)
    low, dummy = driver.get_liquid_level_thresholds(disp)
    driver.set_liquid_level_thresholds(disp, low, out)
    return "%d\n" % out

@app.route('/ws/liquidlevel/low/<int:disp>/set')
@login_required
def ws_liquidlevel_low_set(disp):
    driver = app.driver
    driver.update_liquid_levels()
    sleep(.01)
    low = driver.get_liquid_level(disp)
    dummy, out = driver.get_liquid_level_thresholds(disp)
    driver.set_liquid_level_thresholds(disp, low, out)
    return "%d\n" % low

@app.route('/ws/liquidlevel/out/all/set')
@login_required
def ws_liquidlevel_out_all_set():
    driver = app.driver
    driver.update_liquid_levels()
    sleep(.01)

    for disp in xrange(driver.count()):
        out = driver.get_liquid_level(disp)
        low, dummy = driver.get_liquid_level_thresholds(disp)
        driver.set_liquid_level_thresholds(disp, low, out)

    return "ok\n"

@app.route('/ws/liquidlevel/low/all/set')
@login_required
def ws_liquidlevel_low_all_set():
    driver = app.driver
    driver.update_liquid_levels()
    sleep(.01)

    for disp in xrange(driver.count()):
        low = driver.get_liquid_level(disp)
        dummy, out = driver.get_liquid_level_thresholds(disp)
        driver.set_liquid_level_thresholds(disp, low, out)

    return "ok\n"
