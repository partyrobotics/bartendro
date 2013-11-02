# -*- coding: utf-8 -*-
import json
import os
from sqlalchemy import asc, func
from bartendro import app, db, mixer
from flask import Flask, request
from flask.ext.login import login_required, logout_user
from werkzeug.exceptions import InternalServerError, BadRequest, ServiceUnavailable

@app.route('/ws/planner/start', methods=["POST"])
@login_required
def ws_planner_start():
    if request.method != 'POST':
        raise BadRequest

    require_booze = request.json['require_booze']
    exclude_booze = request.json['exclude_booze']
    num_generations = request.json['num_generations']

    planner = app.planner
    if not planner.is_done(): raise ServiceUnavailable
    planner.evolve(require_booze, exclude_booze, num_generations)

    return json.dumps({ });

@app.route('/ws/planner/update')
@login_required
def ws_planner_update():
    planner = app.planner
    print json.dumps(planner.get_best_set());
    return json.dumps(planner.get_best_set());
