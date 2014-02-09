# -*- coding: utf-8 -*-
from sqlalchemy import func, asc
import memcache
from bartendro import app, db
from flask import Flask, request, redirect, render_template
from flask.ext.login import login_required
from bartendro.model.drink import Drink
from bartendro.model.booze import Booze
from bartendro.model.dispenser import Dispenser

@app.route('/blender')
def dispenser():
    driver = app.driver
    count = driver.count()

    dispensers = db.session.query(Dispenser).order_by(Dispenser.id).all()
    boozes = db.session.query(Booze).order_by(Booze.id).all()

    return render_template("blender", 
                           title="Bartendro Blender",
                           dispensers=dispensers,
                           boozes=boozes,
                           options=app.options)
