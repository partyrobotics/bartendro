# -*- coding: utf-8 -*-
import os
from werkzeug.exceptions import ServiceUnavailable
from bartendro import app, db, STATIC_FOLDER
from flask import Flask, request, Response
from flask.ext.login import login_required
from bartendro.model.drink import Drink
from bartendro.model.booze import Booze
from bartendro.form.booze import BoozeForm

@app.route('/ws/reset')
@login_required
def ws_reset():
    driver = app.driver
    mc = app.mc
    mc.delete("top_drinks")
    mc.delete("other_drinks")
    mc.delete("available_drink_list")
    driver.reset()
    return "ok\n"

@app.route('/ws/test')
@login_required
def ws_test_chain():
    driver = app.driver
    for disp in xrange(driver.count()):
	if not driver.ping(disp):
	    raise ServiceUnavailable("Dispenser %d failed ping." % (disp + 1))

    return "ok"

@app.route('/ws/checklevels')
@login_required
def ws_check_levels():
    mixer = app.mixer
    if not mixer.check_liquid_levels():
        raise ServiceUnavailable("Error: Checking dispenser levels failed.")
    mc = app.mc
    mc.delete("top_drinks")
    mc.delete("other_drinks")
    mc.delete("available_drink_list")
    return "ok\n"

@app.route('/ws/download/bartendro.db')
@login_required
def ws_download_db():

    # close the connection to the database to flush anything that might still be in a cache somewhere
    db.session.bind.dispose()

    # Now read the database into memory
    try:
        fh = open("bartendro.db", "r")
        db_data = fh.read()
        fh.close()
    except IOError, e:
        raise ServiceUnavailable("Error: downloading database failed: %s" % e)

    r = Response(db_data, mimetype='application/x-sqlite')
    r.set_cookie("fileDownload", "true")
    return r
