# -*- coding: utf-8 -*-
from werkzeug.utils import redirect
from bartendro.utils import session, render_template, render_json, expose, validate_url, url_for, local
from bartendro.model.drink import Drink
from bartendro.model.booze import Booze
from bartendro.model.booze_group import BoozeGroup
from bartendro.form.liquidout import LiquidOutTestForm

@expose('/admin/liquidout')
def view(request):
    form = LiquidOutTestForm(request.form)
    return render_template("admin/liquidout", form=form, title="Liquid out test")

@expose('/admin/liquidout/test')
def save(request):

    form = LiquidOutTestForm(request.form)
    #if request.method == 'POST' and form.validate():
    dispenser = int(request.form.get("dispenser") or '1') - 1
    threshold = int(request.form.get("threshold") or '0')
    local.application.mixer.liquid_level_test(dispenser, threshold)

    return render_template("admin/liquidout", form=form, title="Liquid out test")
