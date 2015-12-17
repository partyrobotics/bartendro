# -*- coding: utf-8 -*-
import time
from bartendro import app, db
from sqlalchemy import desc
from flask import Flask, request, render_template
from flask.ext.login import login_required
from bartendro.model.drink import Drink
from bartendro.model.drink_log import DrinkLog
from bartendro.model.booze import Booze
from bartendro.model.booze_group import BoozeGroup
from bartendro.form.booze import BoozeForm

DEFAULT_TIME = 12
display_info = {
    12 : 'Drinks poured in the last 12 hours.',
    72 : 'Drinks poured in the last 3 days.',
    168 : 'Drinks poured in the last week.',
    0 : 'All drinks ever poured'
}

@app.route('/trending')
def trending_drinks():
    return trending_drinks_detail(DEFAULT_TIME)

@app.route('/trending/<int:hours>')
def trending_drinks_detail(hours):

    title = "Trending drinks"
    log = db.session.query(DrinkLog).order_by(desc(DrinkLog.time)).first() or 0
    if log:
        if not log.time:
            enddate = int(time.time())
        else:
            enddate = log.time
    
        try:
            txt = display_info[hours]
        except IndexError:
            txt = "Drinks poured in the last %d hours" % hours

        # if a number of hours is 0, then show for "all time"
        if hours:
            begindate = enddate - (hours * 60 * 60)
        else:
            begindate = 0
    else:
	begindate = 0
        enddate = 0
        txt = ""

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

    top_drinks = db.session.query("id", "name", "number", "volume")\
                 .from_statement("""SELECT drink.id, 
                                           drink_name.name,
                                           count(drink_log.drink_id) AS number, 
                                           sum(drink_log.size) AS volume 
                                      FROM drink_log, drink_name, drink 
                                     WHERE drink_log.drink_id = drink_name.id 
                                       AND drink_name.id = drink.id
                                       AND drink_log.time >= :begin AND drink_log.time <= :end 
                                  GROUP BY drink_name.name 
                                  ORDER BY count(drink_log.drink_id) desc;""")\
                 .params(begin=begindate, end=enddate).all()

    return render_template("trending", top_drinks = top_drinks, options=app.options,
                                       title="Trending drinks",
                                       txt=txt,
                                       total_number=total_number[0],
                                       total_volume=total_volume[0],
                                       hours=hours)
