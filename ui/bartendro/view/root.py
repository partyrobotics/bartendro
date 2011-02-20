# -*- coding: utf-8 -*-
from bartendro.utils import session, render_template, render_json, expose, validate_url, url_for
from bartendro.model.drink import Drink

@expose('/')
def index(request):
    drinks = Drink.query.all()
    return render_template("index.html", drinks=drinks)
