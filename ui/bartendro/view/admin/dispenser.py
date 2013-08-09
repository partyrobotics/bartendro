# -*- coding: utf-8 -*-
from sqlalchemy import func, asc
import memcache
from bartendro import app, db
from flask import Flask, request, redirect, render_template
from flask.ext.login import login_required
from wtforms import Form, SelectField, IntegerField, validators
from bartendro.model.drink import Drink
from bartendro.model.booze import Booze
from bartendro.model.dispenser import Dispenser
from bartendro.form.dispenser import DispenserForm
from bartendro.mixer import CALIBRATE_ML
from operator import itemgetter

@app.route('/admin')
@login_required
def dispenser():
    driver = app.driver
    count = driver.count()

    saved = int(request.args.get('saved', "0"))

    class F(DispenserForm):
        pass

    dispensers = db.session.query(Dispenser).order_by(Dispenser.id).all()
    boozes = db.session.query(Booze).order_by(Booze.id).all()
    booze_list = [(b.id, b.name) for b in boozes]
    sorted_booze_list = sorted(booze_list, key=itemgetter(1))

    if app.options.use_liquid_level_sensors:
        states = [dispenser.out for dispenser in dispensers]
    else:
        states = [0 for dispenser in dispensers]

    kwargs = {}
    fields = []
    for i in xrange(1, 17):
        dis = "dispenser%d" % i
        actual = "actual%d" % i
        setattr(F, dis, SelectField("%d" % i, choices=sorted_booze_list)) 
        setattr(F, actual, IntegerField(actual, [validators.NumberRange(min=1, max=100)]))
        kwargs[dis] = "1" # string of selected booze
        fields.append((dis, actual))

    form = F(**kwargs)
    for i, dispenser in enumerate(dispensers):
        form["dispenser%d" % (i + 1)].data = "%d" % booze_list[dispenser.booze_id - 1][0]
        form["actual%d" % (i + 1)].data = dispenser.actual

    return render_template("admin/dispenser", 
                           title="Dispensers",
                           calibrate_ml=CALIBRATE_ML, 
                           form=form, count=count, 
                           fields=fields, 
                           saved=saved,
                           options=app.options,
                           states=states)

@app.route('/admin/save', methods=['POST'])
@login_required
def save():
    cancel = request.form.get("cancel")
    if cancel: return redirect('/admin/dispenser')

    form = DispenserForm(request.form)
    if request.method == 'POST' and form.validate():
        dispensers = db.session.query(Dispenser).order_by(Dispenser.id).all()
        for dispenser in dispensers:
            try:
                dispenser.booze_id = request.form['dispenser%d' % dispenser.id]
                #dispenser.actual = request.form['actual%d' % dispenser.id]
            except KeyError:
                continue
        db.session.commit()

    mc = app.mc
    mc.delete("top_drinks")
    mc.delete("other_drinks")
    mc.delete("available_drink_list")
    return redirect('/admin?saved=1')
