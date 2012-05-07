# -*- coding: utf-8 -*-
from operator import itemgetter
from werkzeug.utils import redirect
from wtforms import Form, TextField, SelectField, DecimalField, validators, HiddenField
from bartendro.utils import session, render_template, render_json, expose, validate_url, url_for, local
from bartendro.model.drink import Drink
from bartendro.model.booze import Booze
from bartendro.model.drink_booze import DrinkBooze
from bartendro.model.drink_name import DrinkName
from bartendro.form.booze import BoozeForm
from bartendro.form.drink import DrinkForm
from bartendro import constant

MAX_BOOZES_PER_DRINK = 8

@expose('/admin/drink')
def view(request):
    drinks = session.query(Drink).join(DrinkName).filter(Drink.name_id == DrinkName.id) \
                                 .order_by(DrinkName.name).all()
    class F(DrinkForm):
        pass

    boozes = session.query(Booze).order_by(Booze.id).all()
    booze_list = [(b.id, b.name) for b in boozes] 
    sorted_booze_list = sorted(booze_list, key=itemgetter(1))
    fields = []
    kwargs = {}
    null_drink_booze = DrinkBooze(Drink("dummy"), boozes[0], 0, 0)
    for i in xrange(MAX_BOOZES_PER_DRINK):
        booze = null_drink_booze
        show = 0

        bf = "booze_name_%d" % i
        bp = "booze_parts_%d" % i
        dbi = "drink_booze_id_%d" % i
        setattr(F, bf, SelectField("booze", choices=sorted_booze_list)) 
        setattr(F, bp, DecimalField("parts", [validators.NumberRange(min=1, max=100)], places=0));
        setattr(F, dbi, HiddenField("id"))
        kwargs[bf] = booze.booze.name
        kwargs[bp] = booze.value
        kwargs[dbi] = booze.id
        fields.append((bf, bp, dbi, show))
    form = F(**kwargs)

    return render_template("admin/drink", fields=fields, drinks=drinks, form=form, title="Enter new drink")

@expose('/admin/drink/edit/<id>')
def edit(request, id):

    saved = int(request.args.get('saved', "0"))
    class F(DrinkForm):
        pass

    boozes = session.query(Booze).order_by(Booze.id).all()
    booze_list = [(b.id, b.name) for b in boozes] 

    sorted_booze_list = sorted(booze_list, key=itemgetter(1))
    drink = Drink.query.filter_by(id=int(id)).first()

    # convert size to fl oz
    drink.sugg_size = drink.sugg_size / constant.ML_PER_FL_OZ

    kwargs = {}
    fields = []
    null_drink_booze = DrinkBooze(Drink("dummy"), boozes[0], 0, 0)
    for i in xrange(MAX_BOOZES_PER_DRINK):
        if i < len(drink.drink_boozes):
            booze = drink.drink_boozes[i]
            show = 1
        else:
            booze = null_drink_booze
            show = 0

        bf = "booze_name_%d" % i
        bp = "booze_parts_%d" % i
        dbi = "drink_booze_id_%d" % i
        setattr(F, bf, SelectField("booze", choices=sorted_booze_list)) 
        setattr(F, bp, DecimalField("parts", [validators.NumberRange(min=1, max=100)], places=0));
        setattr(F, dbi, HiddenField("id"))
        kwargs[bf] = booze.booze.name
        kwargs[bp] = booze.value
        kwargs[dbi] = booze.id
        fields.append((bf, bp, dbi, show))

    form = F(obj=drink, drink_name=drink.name.name, **kwargs)
    for i, booze in enumerate(drink.drink_boozes):
        form["booze_name_%d" % i].data = "%d" % booze_list[booze.booze_id - 1][0]
    drinks = session.query(Drink).join(DrinkName).filter(Drink.name_id == DrinkName.id) \
                                 .order_by(DrinkName.name).all()
    return render_template("admin/drink", drinks=drinks, form=form, fields=fields, 
                           title="Edit drink", saved=saved)


@expose('/admin/drink/save')
def save(request):

    cancel = request.form.get("cancel")
    if cancel: return redirect('/admin/drink')

    form = DrinkForm(request.form)
    if request.method == 'POST' and form.validate():
        id = int(request.form.get("id") or '0')
        if id:
            drink = Drink.query.filter_by(id=int(id)).first()
        else:
            drink = Drink()
            session.add(drink)

        drink.name.name = form.data['drink_name']
        drink.desc = form.data['desc']
        drink.sugg_size = int(form.data['sugg_size'] * constant.ML_PER_FL_OZ);
        drink.popular = form.data['popular']
        drink.available = form.data['available']

        for i in xrange(MAX_BOOZES_PER_DRINK):
            try:
                parts = request.form['booze_parts_%d' % i]
                parts = int(parts)
            except KeyError:
                parts = -1

            try:
                dbi = int(request.form['drink_booze_id_%d' % i] or "-1")
                dbi = int(dbi)
            except KeyError:
                dbi = -1

            try:
                dbn = int(request.form['booze_name_%d' % i] or "-1")
                dbn = int(dbn)
            except KeyError:
                dbn = -1

            if parts == 0:
                if dbi != 0:
                    for i, db in enumerate(drink.drink_boozes):
                        if db.id == dbi:
                            session.delete(drink.drink_boozes[i])
                            break
                continue

            if dbi > 0:
                for db in drink.drink_boozes:
                    if dbi == db.id:
                        db.value = parts
                        newid = dbn
                        if (newid != db.booze_id):
                            db.booze = Booze.query.filter_by(id=newid).first()
                        break

            else:
                booze = Booze.query.filter_by(id=dbn).first()
                DrinkBooze(drink, booze, parts, 0)

        session.commit()
        mc = local.application.mc
        mc.delete("top_drinks")
        mc.delete("other_drinks")
        mc.delete("available_drink_list")
        return redirect('/admin/drink/edit/%d?saved=1' % drink.id)

    drinks = session.query(Drink).join(DrinkName).filter(Drink.name_id == DrinkName.id) \
                                 .order_by(DrinkName.name).all()
    return render_template("admin/drink", drinks=drinks, form=form, title="")
