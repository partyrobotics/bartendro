# -*- coding: utf-8 -*-
from sqlalchemy import func, asc
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
                                 .order_by(asc(func.lower(DrinkName.name))).all()

    boozes = db.session.query(Booze).order_by(asc(func.lower(Booze.name))).all()
    booze_list = [(b.id, b.name) for b in boozes] 
    return render_template("admin/drink", options=app.options, 
                                          title="Drinks",
                                          booze_list=booze_list,
                                          drinks=drinks)
