# -*- coding: utf-8 -*-
from bartendro import app, db
from flask import Flask, request, render_template
from flask.ext.login import login_required
from bartendro.model.drink import Drink
from bartendro.model.booze import Booze
from bartendro.model.booze_group import BoozeGroup
from bartendro.form.liquidout import LiquidOutTestForm

@app.route('/admin/liquidout')
@login_required
def admin_liquidout():
    form = LiquidOutTestForm(request.form)
    return render_template("admin/liquidout", form=form, title="Liquid out test")

@app.route('/admin/liquidout/test', methods=['POST'])
@login_required
def admin_liquidout_save():

    form = LiquidOutTestForm(request.form)
    #if request.method == 'POST' and form.validate():
    dispenser = int(request.form.get("dispenser") or '1') - 1
    threshold = int(request.form.get("threshold") or '0')
    app.mixer.liquid_level_test(dispenser, threshold)

    return render_template("admin/liquidout", form=form, title="Liquid out test")
