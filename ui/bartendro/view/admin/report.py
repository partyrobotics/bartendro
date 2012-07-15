# -*- coding: utf-8 -*-
import time
from werkzeug.utils import redirect
from bartendro.utils import session, render_template, render_json, expose, validate_url, url_for, local
from bartendro.model.drink import Drink
from bartendro.model.booze import Booze
from bartendro.model.booze_group import BoozeGroup
from bartendro.form.booze import BoozeForm

@expose('/admin/report/<begin>/<end>')
def view_report(request, begin, end):
    begindate = int(time.mktime(time.strptime(begin, "%Y-%m-%d")))
    enddate = int(time.mktime(time.strptime(end, "%Y-%m-%d")))
    top_drinks = session.query("name", "cnt", "total").from_statement("""select drink_name.name, count(drink_log.drink_id) as cnt, 
                      sum(drink_log.size) as total from drink_log, drink_name where drink_log.drink_id = drink_name.id and 
                      drink_log.time >= :begin and drink_log.time <= :end group by drink_name.name order 
                      by count(drink_log.drink_id) desc;""").params(begin=begindate, end=enddate).all()
    return render_template("admin/report", top_drinks = top_drinks, title="Top Drinks", begin=begin, end=end)
