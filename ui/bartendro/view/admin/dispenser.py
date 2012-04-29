# -*- coding: utf-8 -*-
from operator import itemgetter
import memcache
from werkzeug.utils import redirect
from bartendro.utils import session, render_template, local, render_json, expose, validate_url, url_for, local
from wtforms import Form, SelectField, IntegerField, validators
from bartendro.model.drink import Drink
from bartendro.model.booze import Booze
from bartendro.model.dispenser import Dispenser
from bartendro.form.dispenser import DispenserForm
from bartendro.mixer import CALIBRATE_ML

@expose('/admin/dispenser')
def view(request):
    driver = local.application.driver
    count = driver.count()

    saved = int(request.args.get('saved', "0"))

    class F(DispenserForm):
        pass

    dispensers = session.query(Dispenser).order_by(Dispenser.id).all()
    boozes = session.query(Booze).order_by(Booze.id).all()
    booze_list = [(b.id, b.name) for b in boozes] 
    sorted_booze_list = sorted(booze_list, key=itemgetter(1))

    kwargs = {}
    fields = []
    for i in xrange(1, 17):
        dis = "dispenser%d" % i
        actual = "actual%d" % i
        setattr(F, dis, SelectField("dispenser %d" % i, choices=sorted_booze_list)) 
        setattr(F, actual, IntegerField(actual, [validators.NumberRange(min=1, max=100)]))
        kwargs[dis] = "1" # string of selected booze
        fields.append((dis, actual))

    form = F(**kwargs)
    for i, dispenser in enumerate(dispensers):
        form["dispenser%d" % (i + 1)].data = "%d" % booze_list[dispenser.booze_id - 1][0]
        form["actual%d" % (i + 1)].data = dispenser.actual

    return render_template("admin/dispenser", calibrate_ml=CALIBRATE_ML, form=form, count=count, fields=fields, saved=saved)

@expose('/admin/dispenser/save')
def save(request):

    cancel = request.form.get("cancel")
    if cancel: return redirect('/admin/dispenser')

    form = DispenserForm(request.form)
    if request.method == 'POST' and form.validate():
        dispensers = session.query(Dispenser).order_by(Dispenser.id).all()
        for dispenser in dispensers:
            try:
                dispenser.booze_id = request.form['dispenser%d' % dispenser.id]
                dispenser.actual = request.form['actual%d' % dispenser.id]
            except KeyError:
                continue
        session.commit()

    mc = local.application.mc
    mc.delete("top_drinks")
    mc.delete("other_drinks")
    mc.delete("available_drink_list")
    return redirect('/admin/dispenser?saved=1')
