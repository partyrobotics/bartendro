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
from bartendro import fsm

@app.route('/admin')
@login_required
def dispenser():
    driver = app.driver
    count = driver.count()

    saved = int(request.args.get('saved', "0"))
    updated = int(request.args.get('updated', "0"))

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

    bstate = app.globals.get_state()
    error = False
    if bstate == fsm.STATE_START:
        state = "Bartendro is starting up."
    elif bstate == fsm.STATE_READY:
        state = "Bartendro is ready!"
    elif bstate == fsm.STATE_LOW:
        state = "Bartendro is ready, but one or more boozes is low!"
    elif bstate == fsm.STATE_OUT:
        state = "Bartendro is ready, but one or more boozes is out!"
    elif bstate == fsm.STATE_HARD_OUT:
        state = "Bartendro cannot make any drinks from the available booze!"
    elif bstate == fsm.STATE_ERROR:
        state = "Bartendro is out of commission. Please reset Bartendro!"
        error = True
    else:
        state = "Bartendro is in bad state: %d" % bstate

    avail_drinks = app.mixer.get_available_drink_list()
    return render_template("admin/dispenser", 
                           title="Dispensers",
                           calibrate_ml=CALIBRATE_ML, 
                           form=form, count=count, 
                           fields=fields, 
                           saved=saved,
                           state=state,
                           error=error,
                           updated=updated,
                           num_drinks=len(avail_drinks),
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

    app.mixer.check_levels()
    return redirect('/admin?saved=1')
