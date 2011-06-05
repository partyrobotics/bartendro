# -*- coding: utf-8 -*-
from werkzeug.utils import redirect
from bartendro.utils import session, render_template, render_json, expose, validate_url, url_for
from bartendro.model.drink import Drink
from bartendro.model.booze import Booze
from bartendro.form.booze import BoozeForm

@expose('/admin/booze')
def view(request):
    # TODO: Show saved text
    form = BoozeForm(request.form)
    boozes = Booze.query.order_by(Booze.name)
    return render_template("admin/booze", boozes=boozes, form=form)

@expose('/admin/booze/edit')
def edit(request):

    id = request.form.get("edit")
    if id:
        booze = Booze.query.filter_by(id=int(id)).first()
        form = BoozeForm(obj=booze)
    else:
        form = BoozeForm(request.form)

    boozes = Booze.query.order_by(Booze.name)
    return render_template("admin/booze", boozes=boozes, form=form)

@expose('/admin/booze/save')
def save(request):

    form = BoozeForm(request.form)
    if request.method == 'POST' and form.validate():
        id = request.form.get("id")
        booze = Booze.query.filter_by(id=int(id)).first()
        booze.update(form.data)
        if not booze.id:
            session.add(booze)
        session.commit()
        return redirect('/admin/booze')

    boozes = Booze.query.order_by(Booze.name)
    return render_template("admin/booze", boozes=boozes, form=form)
