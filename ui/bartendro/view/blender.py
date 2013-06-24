# -*- coding: utf-8 -*-
from sqlalchemy import func, asc
import memcache
import json
from bartendro import app, db
from flask import Flask, request, redirect, render_template
from flask.ext.login import login_required
from bartendro.model.drink import Drink
from bartendro.model.booze import Booze
from bartendro.model.dispenser import Dispenser
from bartendro.model.blender_log import BlenderLog

@app.route('/blender')
def blender():
    driver = app.driver
    count = driver.count()

    recipe = {}
    for arg in request.args:
        n = int(arg[5:])
        recipe[n] = int(request.args.get(arg))

    dispensers = db.session.query(Dispenser).order_by(Dispenser.id).all()
    boozes = db.session.query(Booze).order_by(Booze.id).all()

    return render_template("blender", 
                           title="Blender",
                           dispensers=dispensers,
                           boozes=boozes,
                           count=count,
                           recipe=recipe,
                           options=app.options)

@app.route('/blender/log')
#@login_required
def blender_log():
    boozes = db.session.query(Booze).order_by(Booze.id).all()
    log = BlenderLog.query.all()
    blends = []
    args = []
    for entry in log:
        blend = []
        data = json.loads(entry.blend)
        for k, v in data:
            blend.append({ 'name' : boozes[k].name, 'value' : v})
            args.append("booze%d=%d" % (boozes[k].id, v))
        url = "/blender?" + "&".join(args)
        blends.append({ 'number' : entry.id, 'blend' : blend, 'url' : url })

    return render_template("blender-log",
                           title="Previous blends",
                           blends=blends,
                           options=app.options)
