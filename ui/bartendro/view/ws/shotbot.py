# -*- coding: utf-8 -*-
from bartendro import app, db
from flask import Flask, request, render_text
from bartendro.model.drink import Drink
from bartendro.model.booze import Booze
from bartendro.form.booze import BoozeForm

@app.route('/ws/shotbot')
def ws_reset():
    driver = app.driver
    driver.make_shot()
    return render_text("ok\n")
