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
from bartendro.model.blend_log import BlendLog

@app.route('/blend')
def blend():
    driver = app.driver
    count = driver.count()

    recipe = {}
    for arg in request.args:
        n = int(arg[5:])
        recipe[n] = int(request.args.get(arg))

    dispensers = db.session.query(Dispenser).order_by(Dispenser.id).all()
    boozes = db.session.query(Booze).order_by(Booze.id).all()

    return render_template("blend", 
                           title="Blend designer",
                           dispensers=dispensers,
                           boozes=boozes,
                           count=count,
                           recipe=recipe,
                           options=app.options)

@app.route('/blend/log')
#@login_required
def blend_log():
    boozes = db.session.query(Booze).order_by(Booze.id).all()
    booze_index = {}
    for booze in boozes:
        booze_index[booze.id] = booze.name    

    print booze_index

    log = BlendLog.query.all()
    blends = []
    args = []
    for entry in log:
        blend = []
        data = json.loads(entry.blend)
        for id, v in data:
            blend.append({ 'name' : booze_index[id], 'value' : v})
            args.append("booze%d=%d" % (id, v))
        url = "/blend?" + "&".join(args)
        blends.append({ 'number' : entry.id, 'blend' : blend, 'url' : url })

    return render_template("blend-log",
                           title="Previous blends",
                           blends=blends,
                           options=app.options)
