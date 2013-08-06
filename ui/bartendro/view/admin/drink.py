# -*- coding: utf-8 -*-
import json
from operator import itemgetter
from bartendro import app, db
from flask import Flask, request, redirect, render_template
from flask.ext.login import login_required
from wtforms import Form, TextField, SelectField, DecimalField, validators, HiddenField
from bartendro.model.drink import Drink
from bartendro.model.booze import Booze
from bartendro.model.drink_booze import DrinkBooze
from bartendro.model.drink_name import DrinkName
from bartendro.form.booze import BoozeForm
from bartendro.form.drink import DrinkForm
from bartendro import constant

MAX_BOOZES_PER_DRINK = 25

@app.route('/admin/drink')
@login_required
def admin_drink_new():
    drinks = db.session.query(Drink).join(DrinkName).filter(Drink.name_id == DrinkName.id) \
                                 .order_by(DrinkName.name).all()

    boozes = db.session.query(Booze).order_by(Booze.id).all()
    booze_list = [(b.id, b.name) for b in boozes] 
    sorted_booze_list = sorted(booze_list, key=itemgetter(1))

    print sorted_booze_list
    drink = { 
        'id'         : 0,
        'name'       : "",
        'desc'       : "",
        'popular'    : 'n',
        'available'  : 'n',
        'boozes'     : [],
        'booze_list' : sorted_booze_list,
        'max_boozes' : MAX_BOOZES_PER_DRINK,
        'num_boozes' : 0
    }
    return render_template("admin/drink", options=app.options, 
                                          title="Drinks",
                                          drinks=drinks,
                                          drink=drink)

@app.route('/admin/drink/<int:id>/edit', methods=['GET'])
@login_required
def admin_drink_edit(id):

    if request.method == 'GET':
        drinks = db.session.query(Drink).join(DrinkName).filter(Drink.name_id == DrinkName.id) \
                                     .order_by(DrinkName.name).all()
        drink = Drink.query.filter_by(id=int(id)).first()

        boozes = db.session.query(Booze).order_by(Booze.id).all()
        booze_list = [(b.id, b.name) for b in boozes] 
        sorted_booze_list = sorted(booze_list, key=itemgetter(1))

        boozes = []
        for booze in drink.drink_boozes:
            boozes.append((booze.booze_id, booze.booze.name, booze.value))
        drink = { 
            'id'         : id,
            'name'       : drink.name.name,
            'desc'       : drink.desc,
            'popular'    : drink.popular,
            'available'  : drink.available,
            'boozes'     : boozes,
            'booze_list' : sorted_booze_list,
            'max_boozes' : MAX_BOOZES_PER_DRINK,
            'num_boozes' : len(boozes)
        }
        return render_template("admin/drink", options=app.options, 
                                              title="Drinks",
                                              drinks=drinks,
                                              drink=drink)

