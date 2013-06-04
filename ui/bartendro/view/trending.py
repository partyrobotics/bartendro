# -*- coding: utf-8 -*-
import time
from bartendro import app, db
from flask import Flask, request, render_template
from flask.ext.login import login_required
from bartendro.model.drink import Drink
from bartendro.model.booze import Booze
from bartendro.model.booze_group import BoozeGroup
from bartendro.form.booze import BoozeForm

TREND_WINDOW = 12 # in hours

@app.route('/trending')
def trending_drinks():
    return trending_drinks_detail(TREND_WINDOW)

@app.route('/trending/<int:hours>')
def trending_drinks_detail(hours):
    enddate = int(time.time())
    begindate = enddate - (hours * 60 * 60)

    total_number = db.session.query("number")\
                 .from_statement("""SELECT count(*) as number
                                      FROM drink_log 
                                     WHERE drink_log.time >= :begin 
                                       AND drink_log.time <= :end""")\
                 .params(begin=begindate, end=enddate).first()

    total_volume = db.session.query("volume")\
                 .from_statement("""SELECT sum(drink_log.size) as volume 
                                      FROM drink_log 
                                     WHERE drink_log.time >= :begin 
                                       AND drink_log.time <= :end""")\
                 .params(begin=begindate, end=enddate).first()

    top_drinks = db.session.query("name", "number", "volume")\
                 .from_statement("""SELECT drink_name.name,
                                           count(drink_log.drink_id) AS number, 
                                           sum(drink_log.size) AS volume 
                                      FROM drink_log, drink_name 
                                     WHERE drink_log.drink_id = drink_name.id 
                                       AND drink_log.time >= :begin AND drink_log.time <= :end 
                                  GROUP BY drink_name.name 
                                  ORDER BY count(drink_log.drink_id) desc;""")\
                 .params(begin=begindate, end=enddate).all()

    return render_template("trending", top_drinks = top_drinks, options=app.options,
                                       title="Trending drinks in the last %s hours" % hours,
                                       total_number=total_number[0],
                                       total_volume=total_volume[0],
                                       hours=hours)
