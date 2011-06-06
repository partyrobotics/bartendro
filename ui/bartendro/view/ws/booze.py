# -*- coding: utf-8 -*-
from werkzeug.utils import redirect
from bartendro.utils import session, render_template, render_json, expose, validate_url, url_for
from bartendro.model.drink import Drink
from bartendro.model.booze import Booze
from bartendro.form.booze import BoozeForm

@expose('/ws/booze/match/<str>')
def ws_booze(request, str):
    str = str + "%%"
    boozes = session.query("id", "name").from_statement("SELECT id, name FROM booze WHERE name LIKE :s").params(s=str).all()
    print boozes
    return render_json(boozes)
