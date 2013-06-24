# -*- coding: utf-8 -*-
import json
from time import sleep
from operator import itemgetter
from bartendro import app, db, mixer
from flask import Flask, request
from flask.ext.login import login_required, current_user
from werkzeug.exceptions import ServiceUnavailable, BadRequest, InternalServerError
from bartendro.model.blender_log import BlenderLog

@app.route('/ws/blend-log/load')
#@login_required
def blend_log_load():
    log = BlenderLog.query.all()
    blends = []
    for blend in log:
        blends.append((blend.id, booze.blend))
    return json.dumps({ 'log' : blends})

@app.route('/ws/blend-log/assign')
#@login_required
def blend_log_assign():

    arg_blend = []
    arg_dict = {}
    for arg in request.args:
        n = int(arg[5:])
        v = int(request.args.get(arg))
        arg_blend.append((n, v))
        arg_dict[n] = v
    arg_set = set(arg_blend)

    log = BlenderLog.query.all()
    for entry in log:
        blend = []
        data = json.loads(entry.blend)
        for key in data:
            blend.append((int(key), data[key]))
        this_set = set(blend)
        print this_set
        print arg_set
        print
        if this_set == arg_set:
            return json.dumps({ 'id' : entry.id })

    # save new blend to disk
    blend = BlenderLog(json.dumps(arg_dict))
    db.session.add(blend)
    db.session.commit()

    return json.dumps({ 'id' : blend.id})
