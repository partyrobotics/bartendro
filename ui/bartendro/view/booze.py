# -*- coding: utf-8 -*-
from bartendro import app, db
from sqlalchemy import func, asc
from flask import Flask, request, redirect, render_template
from flask.ext.login import login_required
from bartendro.model.drink import Drink, DrinkName
from bartendro.model.drink_booze import DrinkBooze
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

def load_drink_list(booze_id):
    """ load drinks that can be made with booze_id """
    drink_list = []
    drink_list = db.session.query(Drink) \
                        .join(DrinkName) \
                        .join(DrinkBooze) \
                        .filter(Drink.name_id == DrinkName.id)  \
                        .filter(Drink.popular == 0)  \
                        .filter(Drink.available == 1)  \
                        .filter(DrinkBooze.booze_id == booze_id)  \
                        .order_by(asc(func.lower(DrinkName.name))).all()
  
     

    return drink_list
    # query saved as an example
    all_boozes = DrinkBooze.query.filter_by(booze_id=booze_id)

@app.route('/booze')
@login_required
def booze():
    #form = BoozeForm(request.form)
    all_boozes = Booze.query.order_by(asc(func.lower(Booze.name)))
    loaded_boozes = load_loaded_boozes()
    drink_list = ""
    
    return render_template("booze", options=app.options, drink_list=drink_list, all_boozes=all_boozes,loaded_boozes=loaded_boozes, title="Booze")

@app.route('/booze/<id>')
@login_required
def booze_detail(id):
    booze = Booze.query.filter_by(id=int(id)).first()
    all_boozes = Booze.query.order_by(asc(func.lower(Booze.name)))
    loaded_boozes = load_loaded_boozes()
    drink_list = load_drink_list(booze.id)
    return render_template("booze", options=app.options, booze=booze, drink_list=drink_list, all_boozes=all_boozes,loaded_boozes=loaded_boozes, title="Booze" )
