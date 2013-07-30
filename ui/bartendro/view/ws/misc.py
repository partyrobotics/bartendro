# -*- coding: utf-8 -*-
from werkzeug.exceptions import ServiceUnavailable
from flask.ext.login import login_required
from bartendro import app, db
from flask import Flask, request
from bartendro.model.drink import Drink
from bartendro.model.booze import Booze
from bartendro.form.booze import BoozeForm
import dropbox
from dropbox import rest as dbrest

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
	    raise ServiceUnavailable("Dispenser %d failed ping." % disp + 1)

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

@app.route('/ws/dropbox-finish/<auth_code>')
@login_required
def admin_options_dropbox_finish(auth_code):
    mc = app.mc
    flow = dropbox.client.DropboxOAuth2FlowNoRedirect(app.options.app_key, app.options.app_secret)
    try:
        access_token, user_id = flow.finish(auth_code)
        mc.set("dropbox_access_token", access_token)
        mc.set("dropbox_user_id", user_id)
    except dbrest.ErrorResponse, e:
        print('Error: %s' % (e,))
        return 'Error: %s' % (e,)

    return "ok\n"
