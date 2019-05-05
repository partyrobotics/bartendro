# -*- coding: utf-8 -*-
import time, datetime
from bartendro import app, db
from sqlalchemy import desc, text
from flask import Flask, request, render_template
from flask.ext.login import login_required
from bartendro.model.drink import Drink
from bartendro.model.drink_log import DrinkLog
from bartendro.model.booze import Booze
from bartendro.model.booze_group import BoozeGroup
from bartendro.form.booze import BoozeForm

BARTENDRO_DAY_START_TIME = 10 * 60 * 60
DEFAULT_TIME = 12
display_info = {
    12 : 'Drinks poured in the last 12 hours.',
    72 : 'Drinks poured in the last 3 days.',
    168 : 'Drinks poured in the last week.',
    0 : 'All drinks ever poured'
}

@app.route('/trending')
def trending_drinks():
    return trending_drinks_detail(DEFAULT_TIME,'')

# figure out begindate and enddate
# begindate exists, but no enddate = assume it is one day
# enddate exists but no beginndate = assume begindate=first day
# need some text for this.
# begin and enddate need to be in timestamp format.

@app.route('/trending/date/')
def trending_drinks_date():
    """ this assumes ?begindate=yyyy-mm-dd&enddate=yyyy-mm-dd
        or ?begindate=yyyy-mm-dd (with no enddate)
    """

    title = "Drinks by date"

    begindate = request.args.get("begindate", "") 
    if (len(begindate) > 0) :
        begin_ts = time.mktime(datetime.datetime.strptime(begindate, "%Y-%m-%d").timetuple())
        begin_ts = begin_ts + BARTENDRO_DAY_START_TIME 
        begindate = datetime.datetime.fromtimestamp(begin_ts).strftime('%c')
    else:
        begin_ts = 0 
        begindate = 'The beginning of time'

    enddate = request.args.get("enddate", "") 
    if (len(enddate) == 0):
        end_ts = begin_ts + (24 * 60 * 60) - 1
        #end_ts = end_ts + BARTENDRO_DAY_START_TIME - 1 
        enddate = datetime.datetime.fromtimestamp(end_ts).strftime('%c')
    else:
        end_ts = time.mktime(datetime.datetime.strptime(enddate, "%Y-%m-%d").timetuple())
        end_ts = end_ts + 24*60*60+BARTENDRO_DAY_START_TIME  - 1
        enddate = datetime.datetime.fromtimestamp(end_ts).strftime('%c')

    try:
        txt = "Drinks poured from %s to %s " % (begindate, enddate)
    except IndexError:
        txt = "Drinks poured by date"

    hours = 0
    return trending_drinks_detail(begin_ts, end_ts, txt, hours)

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

    return trending_drinks_detail(begindate, enddate, txt, hours)


def trending_drinks_detail(begindate, enddate, txt='', hours=''):

    title = "Trending drinks"

    #import pdb
    #pdb.set_trace()
    total_number = db.session.query("number")\
                 .from_statement(text("""SELECT count(*) as number
                                      FROM drink_log 
                                     WHERE drink_log.time >= :begin 
                                       AND drink_log.time <= :end"""))\
                 .params(begin=begindate, end=enddate).first()

    total_volume = db.session.query("volume")\
                 .from_statement(text("""SELECT sum(drink_log.size) as volume 
                                      FROM drink_log 
                                     WHERE drink_log.time >= :begin 
                                       AND drink_log.time <= :end"""))\
                 .params(begin=begindate, end=enddate).first()

    top_drinks = db.session.query("id", "name", "number", "volume")\
                 .from_statement(text("""SELECT drink.id, 
                                           drink_name.name,
                                           count(drink_log.drink_id) AS number, 
                                           sum(drink_log.size) AS volume 
                                      FROM drink_log, drink_name, drink 
                                     WHERE drink_log.drink_id = drink_name.id 
                                       AND drink_name.id = drink.id
                                       AND drink_log.time >= :begin AND drink_log.time <= :end 
                                  GROUP BY drink_name.name 
                                  ORDER BY count(drink_log.drink_id) desc;"""))\
                 .params(begin=begindate, end=enddate).all()

    drinks_by_date = db.session.query("date",  "number", "volume")\
                 .from_statement(text("""SELECT date(time- :BARTENDRO_DAY_START_TIME,'unixepoch') as date, 
                                           count(drink_log.drink_id) AS number, 
                                           sum(drink_log.size) AS volume 
                                      FROM drink_log, drink_name, drink 
                                     WHERE drink_log.drink_id = drink_name.id 
                                       AND drink_name.id = drink.id
                                  GROUP BY date 
                                  ORDER BY date desc;"""))\
                 .params(BARTENDRO_DAY_START_TIME=BARTENDRO_DAY_START_TIME).all()

    return render_template("trending", top_drinks = top_drinks, 
                                       drinks_by_date = drinks_by_date,
                                       options=app.options,
                                       title="Trending drinks",
                                       txt=txt,
                                       total_number=total_number[0],
                                       total_volume=total_volume[0],
                                       hours=hours)


