# -*- coding: utf-8 -*-
from bartendro import app, db
from flask import Flask, request
from flask.ext.login import current_user
from bartendro.model.drink import Drink
from bartendro.model.booze import Booze
from bartendro.form.booze import BoozeForm

@app.route('/ws/shotbot')
def ws_shotbot():
    if app.options.must_login_to_dispense and not current_user.is_authenticated():
        return "login required"

    driver = app.driver
    driver.make_shot()
    return "ok\n"
