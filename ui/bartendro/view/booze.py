# -*- coding: utf-8 -*-
from bartendro import app, db
from sqlalchemy import func, asc
from flask import Flask, request, redirect, render_template
from flask.ext.login import login_required
from bartendro.model.drink import Drink
from bartendro.model.booze import Booze
from bartendro.model.booze_group import BoozeGroup
from bartendro.form.booze import BoozeForm
from bartendro.model.dispenser import Dispenser

def load_loaded_boozes():
    loaded = db.session.query("id", "name", "abv", "type","dispenser")\
                 .from_statement("""SELECT booze.id, 
                                           booze.name,
                                           booze.abv,
                                           booze.type,
                                           dispenser.id as dispenser
                                      FROM booze, dispenser
                                     WHERE booze.id = dispenser.booze_id
                                  ORDER BY abv desc;""")\
                 .params(foo='', bar='').all()
    return loaded

@app.route('/booze')
@login_required
def booze():
    #form = BoozeForm(request.form)
    all_boozes = Booze.query.order_by(asc(func.lower(Booze.name)))
    loaded_boozes = load_loaded_boozes()
    return render_template("booze", options=app.options, all_boozes=all_boozes,loaded_boozes=loaded_boozes, title="Booze")

@app.route('/booze/<id>')
@login_required
def booze_detail(id):
    booze = Booze.query.filter_by(id=int(id)).first()
    all_boozes = Booze.query.order_by(asc(func.lower(Booze.name)))
    loaded_boozes = load_loaded_boozes()
    return render_template("booze", options=app.options, booze=booze, all_boozes=all_boozes,loaded_boozes=loaded_boozes, title="Booze" )
