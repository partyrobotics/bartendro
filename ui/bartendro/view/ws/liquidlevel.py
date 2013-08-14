# -*- coding: utf-8 -*-
import os
import json
import logging
from time import sleep
from werkzeug.exceptions import BadRequest, InternalServerError
from bartendro import app, db
from flask import Flask, request, Response
from flask.ext.login import login_required

log = logging.getLogger('bartendro')

@app.route('/ws/liquidlevel/test/<int:disp>')
@login_required
def ws_liquidlevel_test(disp):
    low, out = app.driver.get_liquid_level_thresholds(disp)
    if low < 0 or out < 0: 
        log.error("Failed to read liquid level threshold from dispenser %d" % (disp + 1))
        raise InternalServerError
    app.mixer.liquid_level_test(disp, out)
    return "ok"

@app.route('/ws/liquidlevel/out/<int:disp>/set')
@login_required
def ws_liquidlevel_out_set(disp):
    driver = app.driver
    if disp < 0 or disp >= driver.count():
        raise BadRequest

    if not driver.update_liquid_levels():
        log.error("Failed to update liquid level thresholds")
        raise InternalServerError
    sleep(.01)

    out = driver.get_liquid_level(disp)
    if out < 0: 
        log.error("Failed to read liquid level threshold from dispenser %d" % (disp + 1))
        raise InternalServerError

    low, dummy = driver.get_liquid_level_thresholds(disp)
    if low < 0 or dummy < 0: 
        log.error("Failed to read liquid level threshold from dispenser %d" % (disp + 1))
        raise InternalServerError

    driver.set_liquid_level_thresholds(disp, low, out)
    return "%d\n" % out

@app.route('/ws/liquidlevel/low/<int:disp>/set')
@login_required
def ws_liquidlevel_low_set(disp):
    driver = app.driver
    if not driver.update_liquid_levels():
        log.error("Failed to update liquid level thresholds")
        raise InternalServerError
    sleep(.01)

    low = driver.get_liquid_level(disp)
    if low < 0: 
        log.error("Failed to read liquid level threshold from dispenser %d" % (disp + 1))
        raise InternalServerError

    dummy, out = driver.get_liquid_level_thresholds(disp)
    if dummy < 0 or out < 0: 
        log.error("Failed to read liquid level threshold from dispenser %d" % (disp + 1))
        raise InternalServerError

    driver.set_liquid_level_thresholds(disp, low, out)
    return "%d\n" % low


from random import randint

@app.route('/ws/liquidlevel/out/all/set')
@login_required
def ws_liquidlevel_out_all_set():
    driver = app.driver

    data = []
    for disp in xrange(driver.count()):
        out = driver.get_liquid_level(disp)
        if out < 0: 
            log.error("Failed to read liquid level threshold from dispenser %d" % (disp + 1))
            raise InternalServerError

        low, dummy = driver.get_liquid_level_thresholds(disp)
        if low < 0 or dummy < 0: 
            log.error("Failed to read liquid level threshold from dispenser %d" % (disp + 1))
            raise InternalServerError

        driver.set_liquid_level_thresholds(disp, low, out)
        data.append(out)

    if not driver.update_liquid_levels():
        log.error("Failed to update liquid level thresholds")
        raise InternalServerError
    sleep(.01)

    return json.dumps({ 'levels' : data })

@app.route('/ws/liquidlevel/low/all/set')
@login_required
def ws_liquidlevel_low_all_set():
    driver = app.driver

    data = []
    for disp in xrange(driver.count()):
        low = driver.get_liquid_level(disp)
        if low < 0: 
            log.error("Failed to read liquid level threshold from dispenser %d" % (disp + 1))
            raise InternalServerError

        dummy, out = driver.get_liquid_level_thresholds(disp)
        if dummy < 0 or out < 0: 
            log.error("Failed to read liquid level threshold from dispenser %d" % (disp + 1))
            raise InternalServerError

        driver.set_liquid_level_thresholds(disp, low, out)
        data.append(low)

    if not driver.update_liquid_levels():
        log.error("Failed to update liquid level thresholds")
        raise InternalServerError
    sleep(.01)

    return json.dumps({ 'levels' : data })
