# -*- coding: utf-8 -*-
import time
from bartendro import app, db
from flask import Flask, request, render_template
from bartendro.model.drink import Drink
from bartendro.model.booze import Booze
from bartendro.model.booze_group import BoozeGroup
from bartendro.form.booze import BoozeForm

@app.route('/admin/report')
def report_index():
    return render_template("admin/report", title="Top drinks report")

@app.route('/admin/report/<begin>/<end>')
def report_view(begin, end):
    begindate = int(time.mktime(time.strptime(begin, "%Y-%m-%d %H:%M")))
    enddate = int(time.mktime(time.strptime(end, "%Y-%m-%d %H:%M")))

    total_number = session.query("number")\
                 .from_statement("""SELECT count(*) as number
                                      FROM drink_log 
                                     WHERE drink_log.time >= :begin 
                                       AND drink_log.time <= :end""")\
                 .params(begin=begindate, end=enddate).first()

    total_volume = session.query("volume")\
                 .from_statement("""SELECT sum(drink_log.size) as volume 
                                      FROM drink_log 
                                     WHERE drink_log.time >= :begin 
                                       AND drink_log.time <= :end""")\
                 .params(begin=begindate, end=enddate).first()

    top_drinks = session.query("name", "number", "volume")\
                 .from_statement("""SELECT drink_name.name,
                                           count(drink_log.drink_id) AS number, 
                                           sum(drink_log.size) AS volume 
                                      FROM drink_log, drink_name 
                                     WHERE drink_log.drink_id = drink_name.id 
                                       AND drink_log.time >= :begin AND drink_log.time <= :end 
                                  GROUP BY drink_name.name 
                                  ORDER BY count(drink_log.drink_id) desc;""")\
                 .params(begin=begindate, end=enddate).all()

    return render_template("admin/report", top_drinks = top_drinks, 
                                           title="Top drinks report",
                                           total_number=total_number[0],
                                           total_volume=total_volume[0],
                                           begin=begin, 
                                           end=end)
