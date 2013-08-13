# -*- coding: utf-8 -*-
import json
from sqlalchemy import asc, func
from bartendro import app, db, mixer
from flask import Flask, request
from flask.ext.login import login_required, logout_user
from werkzeug.exceptions import InternalServerError, BadRequest
from bartendro.model.option import Option
from bartendro.options import bartendro_options

@app.route('/ws/options', methods=["POST", "GET"])
@login_required
def ws_options():
    if request.method == 'GET':
        options = Option.query.order_by(asc(func.lower(Option.key)))
        data = {}
        for o in options:
            if isinstance(bartendro_options[o.key], int):
               value = int(o.value)
            elif isinstance(bartendro_options[o.key], unicode):
               value = unicode(o.value)
            elif isinstance(bartendro_options[o.key], boolean):
               value = boolean(o.value)
            else:
                raise InternalServerError
            data[o.key] = value

        return json.dumps({ 'options' : data });

    if request.method == 'POST':
        try:
            data = request.json['options']
            logout = request.json['logout']
        except KeyError:
            raise BadRequest

        if logout: logout_user()

        Option.query.delete()

        for key in data:
            option = Option(key, data[key])
            db.session.add(option)

        db.session.commit()
        try:
            import uwsgi
            uwsgi.reload()
            reload = True
        except ImportError:
            reload = False
        return json.dumps({ 'reload' : reload });

    raise BadRequest
