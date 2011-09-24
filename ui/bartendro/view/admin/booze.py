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
    return render_template("admin/booze", boozes=boozes, form=form, title="Enter new booze")

@expose('/admin/booze/edit/<id>')
def edit(request, id):

    booze = Booze.query.filter_by(id=int(id)).first()
    form = BoozeForm(obj=booze)
    boozes = Booze.query.order_by(Booze.name)
    return render_template("admin/booze", boozes=boozes, form=form, title="Edit booze")

@expose('/admin/booze/save')
def save(request):

    cancel = request.form.get("cancel")
    if cancel: return redirect('/admin/booze')

    form = BoozeForm(request.form)
    if request.method == 'POST' and form.validate():
        id = int(request.form.get("id") or '0')
        print "save to id: %d" % id
        if id:
            print "save existing entry"
            booze = Booze.query.filter_by(id=int(id)).first()
            booze.update(form.data)
        else:
            print "save new entry"
            booze = Booze(data=form.data)
            session.add(booze)

        session.commit()
        return redirect('/admin/booze')

    boozes = Booze.query.order_by(Booze.name)
    return render_template("admin/booze", boozes=boozes, form=form, title="")
