# -*- coding: utf-8 -*-
from operator import itemgetter
from bartendro import app, db
from flask import Flask, request, redirect, render_template
from flask.ext.login import login_required
from bartendro.model.drink import Drink
from bartendro.model.booze import Booze
from bartendro.model.drink_booze import DrinkBooze
from bartendro.model.drink_name import DrinkName

@app.route('/admin/drink')
@login_required
def admin_drink_new():
    drinks = db.session.query(Drink).join(DrinkName).filter(Drink.name_id == DrinkName.id) \
                                 .order_by(DrinkName.name).all()

    boozes = db.session.query(Booze).order_by(Booze.id).all()
    booze_list = [(b.id, b.name) for b in boozes] 
    sorted_booze_list = sorted(booze_list, key=itemgetter(1))
    return render_template("admin/drink", options=app.options, 
                                          title="Drinks",
                                          booze_list=sorted_booze_list,
                                          drinks=drinks)
