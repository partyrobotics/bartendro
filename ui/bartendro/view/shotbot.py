# -*- coding: utf-8 -*-
import memcache
from bartendro.utils import session, render_template, render_json, expose, validate_url, url_for, local
from bartendro.model.drink import Drink
from bartendro.model.drink_name import DrinkName

@expose('/shotbot')
def index(request):
    return render_template("shotbot", title="ShotBot!")
