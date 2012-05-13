# -*- coding: utf-8 -*-
from werkzeug.utils import redirect
from bartendro.utils import session, render_template, render_json, expose, validate_url, url_for, local
from bartendro.model.drink import Drink
from bartendro.model.booze import Booze
from bartendro.model.booze_group import BoozeGroup
from bartendro.form.booze import BoozeForm

@expose('/admin/booze')
def view(request):
    form = BoozeForm(request.form)
    boozes = Booze.query.order_by(Booze.name)
    return render_template("admin/booze", boozes=boozes, form=form, title="Booze")

@expose('/admin/booze/edit/<id>')
def edit(request, id):

    saved = int(request.args.get('saved', "0"))
    booze = Booze.query.filter_by(id=int(id)).first()
    form = BoozeForm(obj=booze)
    boozes = Booze.query.order_by(Booze.name)
    return render_template("admin/booze", booze=booze, boozes=boozes, form=form, title="Booze", saved=saved)

@expose('/admin/booze/save')
def save(request):

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
            session.add(booze)

        session.commit()
        mc = local.application.mc
        mc.delete("top_drinks")
        mc.delete("other_drinks")
        mc.delete("available_drink_list")
        return redirect('/admin/booze/edit/%d?saved=1' % booze.id)

    boozes = Booze.query.order_by(Booze.name)
    return render_template("admin/booze", boozes=boozes, form=form, title="")
