# -*- coding: utf-8 -*-
from bartendro import app, db
from flask import Flask, request, session, g, redirect, url_for, abort, render_template
from bartendro.model.drink import Drink
from bartendro.model.booze import Booze
from bartendro.form.booze import BoozeForm

@app.route('/ws/booze/match/<str>')
def ws_booze(request, str):
    str = str + "%%"
    boozes = session.query("id", "name").from_statement("SELECT id, name FROM booze WHERE name LIKE :s").params(s=str).all()
    return render_json(boozes)
