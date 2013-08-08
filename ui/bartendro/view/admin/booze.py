# -*- coding: utf-8 -*-
from bartendro import app, db
from sqlalchemy import func, asc
from flask import Flask, request, redirect, render_template
from flask.ext.login import login_required
from bartendro.model.drink import Drink
from bartendro.model.booze import Booze
from bartendro.model.booze_group import BoozeGroup
from bartendro.form.booze import BoozeForm

@app.route('/admin/booze')
@login_required
def admin_booze():
    form = BoozeForm(request.form)
    boozes = Booze.query.order_by(asc(func.lower(Booze.name)))
    return render_template("admin/booze", options=app.options, boozes=boozes, form=form, title="Booze")

@app.route('/admin/booze/edit/<id>')
@login_required
def admin_booze_edit(id):
    saved = int(request.args.get('saved', "0"))
    booze = Booze.query.filter_by(id=int(id)).first()
    form = BoozeForm(obj=booze)
    boozes = Booze.query.order_by(asc(func.lower(Booze.name)))
    return render_template("admin/booze", options=app.options, booze=booze, boozes=boozes, form=form, title="Booze", saved=saved)

@app.route('/admin/booze/save', methods=['POST'])
@login_required
def admin_booze_save():

    cancel = request.form.get("cancel")
    if cancel: return redirect('/admin/booze')

    form = BoozeForm(request.form)
    if request.method == 'POST' and form.validate():
        id = int(request.form.get("id") or '0')
        if id:
            booze = Booze.query.filter_by(id=int(id)).first()
            booze.update(form.data)
        else:
            booze = Booze(data=form.data)
            db.session.add(booze)

        db.session.commit()
        mc = app.mc
        mc.delete("top_drinks")
        mc.delete("other_drinks")
        mc.delete("available_drink_list")
        return redirect('/admin/booze/edit/%d?saved=1' % booze.id)

    boozes = Booze.query.order_by(asc(func.lower(Booze.name)))
    return render_template("admin/booze", options=app.options, boozes=boozes, form=form, title="")
