# -*- coding: utf-8 -*-
from operator import itemgetter
from werkzeug.utils import redirect
from wtforms import Form, TextField, SelectField, DecimalField, validators, HiddenField
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

    class F(DrinkForm):
        pass

    boozes = session.query(Booze).order_by(Booze.id).all()
    booze_list = [(b.id, b.name) for b in boozes] 

    sorted_booze_list = sorted(booze_list, key=itemgetter(1))
    drink = Drink.query.filter_by(id=int(id)).first()
    kwargs = {}
    fields = []
    for i, booze in enumerate(drink.drink_boozes):
        bf = "booze_name_%d" % i
        bp = "booze_parts_%d" % i
        dbi = "drink_booze_id_%d" % i
        setattr(F, bf, SelectField("booze", choices=sorted_booze_list)) 
        setattr(F, bp, DecimalField("parts", [validators.NumberRange(min=1, max=100)], places=0));
        setattr(F, dbi, HiddenField("id"))
        kwargs[bf] = booze.booze.name
        kwargs[bp] = booze.value
        kwargs[dbi] = booze.id
        fields.append((bf, bp, dbi))

    form = F(obj=drink, drink_name=drink.name.name, **kwargs)
    for i, booze in enumerate(drink.drink_boozes):
        form["booze_name_%d" % i].data = "%d" % booze_list[booze.booze_id - 1][0]
    drinks = session.query(Drink).join(DrinkName).filter(Drink.name_id == DrinkName.id) \
                                 .order_by(DrinkName.name).all()
    return render_template("admin/drink", drinks=drinks, form=form, fields=fields, title="Edit drink")

@expose('/admin/drink/save')
def save(request):

    #print "request.form", request.form

    cancel = request.form.get("cancel")
    if cancel: return redirect('/admin/drink')

    form = DrinkForm(request.form)
    if request.method == 'POST' and form.validate():
        id = int(request.form.get("id") or '0')
        if id:
            drink = Drink.query.filter_by(id=int(id)).first()
            drink.name.name = form.data['drink_name']
            drink.desc = form.data['desc']
            for db in drink.drink_boozes:
                for i in xrange(100):
                    try:
                        if int(request.form['drink_booze_id_%d' % i]) == db.id:
                            db.value = int(request.form['booze_parts_%d' % i])
                            newid = int(request.form['booze_name_%d' % i])
                            if (newid != db.booze_id):
                                db.booze = Booze.query.filter_by(id=newid).first()
                    except KeyError:
                        break;
        else:
            drink_boozes = []
            for i in xrange(100):
                try:
                    print form.data
                    booze = Booze.query.filter_by(id=int(request.form.get("booze_name_%d" % i))).first()
                    drink_boozes.append(DrinkBooze(drink, booze, int(request.form.get("booze_parts_%d" % i)), 0))
                except TypeError:
                    break
            print "-------------"
            print drink_boozes
            print "-------------"
            drink = Drink(data=form.data)
            drink.drink_boozes = drink_boozes
            session.add(drink)

        session.commit()
        return redirect('/admin/drink')

    drinks = session.query(Drink).join(DrinkName).filter(Drink.name_id == DrinkName.id) \
                                 .order_by(DrinkName.name).all()
    return render_template("admin/drink", drinks=drinks, form=form, title="")
