# -*- coding: utf-8 -*-
from bartendro import app, db
from flask import Flask, request, jsonify
from flask import Response
from sqlalchemy.sql import text
from bartendro.model.drink import Drink
from bartendro.model.booze import Booze
from bartendro.form.booze import BoozeForm
import json

@app.route('/ws/booze/match/<str>')
def ws_booze(str):
    ''' Does a case insensitive search on booze for the partial string.
    entering 'equ' will find all of the tequillas. '''
    str = "%%%s%%" % str 
    boozes = db.session.query("id", "name").from_statement(text("SELECT id, name FROM booze WHERE name LIKE :s")).params(s=str).all()
    js = json.dumps(boozes)
    resp=Response(js, status=200, mimetype="application/json")
    return resp
