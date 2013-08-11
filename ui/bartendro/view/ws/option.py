# -*- coding: utf-8 -*-
import json
from operator import itemgetter
from bartendro import app, db, mixer
from flask import Flask, request
from flask.ext.login import login_required
from werkzeug.exceptions import ServiceUnavailable, BadRequest
from bartendro.model.option import Option

@app.route('/ws/option/save', methods=["POST"])
def ws_option_save(drink):
    data = request.json['options']

    # TODO: Lookup how to remove all the options in the DB
    Option.query.remove.all()

    # json: { options : [(key, value), (..), ..] }
    for key, value in data:
        option = Option(key, value)
        db.session.add(option)

    db.session.commit()

    # TODO: figure out how to restart Bartendro

    return json.dumps({});
