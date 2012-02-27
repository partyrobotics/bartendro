# -*- coding: utf-8 -*-
from werkzeug.utils import redirect
from bartendro.utils import session, render_template, render_json, expose, validate_url, url_for
from bartendro.model.drink import Drink
from bartendro.model.booze import Booze
from bartendro.model.drink_name import DrinkName
from bartendro import constant 

@expose('/drink/<id>')
def view(request, id):
    drink = session.query(Drink).join(DrinkName).filter(Drink.id == id).first()
    drink.process_ingredients()
    # convert size to fl oz
    drink.sugg_size = drink.sugg_size / constant.ML_PER_FL_OZ
    return render_template("drink/index", drink=drink, title="Make a %s" % drink.name)
