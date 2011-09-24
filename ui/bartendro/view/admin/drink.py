# -*- coding: utf-8 -*-
from werkzeug.utils import redirect
from bartendro.utils import session, render_template, render_json, expose, validate_url, url_for
from bartendro.model.drink import Drink
from bartendro.model.booze import Booze
from bartendro.model.drink_booze import DrinkBooze
from bartendro.model.drink_name import DrinkName
from bartendro.form.booze import BoozeForm
from bartendro.form.drink import DrinkForm

@expose('/admin/drink')
def view(request):
    form = DrinkForm(request.form)
    drinks = session.query(Drink).join(DrinkName).filter(Drink.name_id == DrinkName.id) \
                                 .order_by(DrinkName.name).all()
    return render_template("admin/drink", drinks=drinks, form=form, title="Enter new drink")

@expose('/admin/drink/edit/<id>')
def edit(request, id):

    drink = Drink.query.filter_by(id=int(id)).first()
    form = DrinkForm(obj=drink, drink_name=drink.name.name)
    drinks = session.query(Drink).join(DrinkName).filter(Drink.name_id == DrinkName.id) \
                                 .order_by(DrinkName.name).all()
    return render_template("admin/drink", drinks=drinks, form=form, title="Edit drink")

@expose('/admin/drink/save')
def save(request):

    cancel = request.form.get("cancel")
    if cancel: return redirect('/admin/drink')

    form = DrinkForm(request.form)
    if request.method == 'POST' and form.validate():
        id = int(request.form.get("id") or '0')
        if id:
            drink = Drink.query.filter_by(id=int(id)).first()
            drink.update(form.data)
        else:
            drink = Drink(data=form.data)
            session.add(drink)

        session.commit()
        return redirect('/admin/drink')

    drinks = session.query(Drink).join(DrinkName).filter(Drink.name_id == DrinkName.id) \
                                 .order_by(DrinkName.name).all()
    return render_template("admin/drink", drinks=drinks, form=form, title="")
