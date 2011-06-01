# -*- coding: utf-8 -*-
from bartendro.utils import session, render_template, render_json, expose, validate_url, url_for
from bartendro.model.drink import Drink
from bartendro.model.booze import Booze
from bartendro.form.booze import BoozeForm

@expose('/admin')
def index(request):
    return render_template("admin/index")

@expose('/admin/booze')
def booze(request):

    print "keys:"
    for k, v in request.form.items():
        print "  %s=%s" % (k, v)
    form = BoozeForm(request.form)
    if request.method == 'POST' and form.validate():
        print "save data!"

    boozes = Booze.query.all()
    return render_template("admin/booze", boozes=boozes, form=form)
