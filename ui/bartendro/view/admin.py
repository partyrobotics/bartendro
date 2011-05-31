# -*- coding: utf-8 -*-
from bartendro.utils import session, render_template, render_json, expose, validate_url, url_for
from bartendro.model.drink import Drink
from bartendro.model.booze import Booze

@expose('/admin')
def index(request):
    return render_template("admin/index")

@expose('/admin/booze')
def booze(request):
    boozes = Booze.query.all()
    return render_template("admin/booze", boozes=boozes)
