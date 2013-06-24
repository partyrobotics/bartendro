# -*- coding: utf-8 -*-
import json
from time import sleep
from operator import itemgetter
from bartendro import app, db, mixer
from flask import Flask, request
from flask.ext.login import login_required, current_user
from werkzeug.exceptions import ServiceUnavailable, BadRequest, InternalServerError
from bartendro.model.blender_log import BlenderLog

@app.route('/ws/blender-log')
#@login_required
def blender_log_load():
    log = BlenderLog.query.all()
    blends = []
    for blend in log:
        blends.append((blend.id, blend.blend))
    return json.dumps({ 'log' : blends})

@app.route('/ws/blender-log/assign')
#@login_required
def blender_log_assign():

    arg_blend = []
    for arg in request.args:
        n = int(arg[5:])
        v = int(request.args.get(arg))
        arg_blend.append((n, v))
    arg_set = set(arg_blend)

    log = BlenderLog.query.all()
    for entry in log:
        blend = []
        data = json.loads(entry.blend)
        for k, v in data:
            blend.append((int(k), int(v)))
        this_set = set(blend)
        if this_set == arg_set:
            return json.dumps({ 'id' : entry.id })

    # save new blend to disk
    blend = BlenderLog(json.dumps(arg_blend))
    db.session.add(blend)
    db.session.commit()

    return json.dumps({ 'id' : blend.id})
