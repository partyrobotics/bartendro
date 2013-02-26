# -*- coding: utf-8 -*-
import memcache
from bartendro import app, db
from flask import Flask, request, render_template
from bartendro.model.drink import Drink
from bartendro.model.drink_name import DrinkName

@app.route('/shotbot')
def index(request):
    return render_template("shotbot", title="ShotBot!")
