# -*- coding: utf-8 -*-
from time import sleep
from werkzeug.utils import redirect
from werkzeug.exceptions import BadRequest, ServiceUnavailable
from bartendro.utils import session, local, expose, validate_url, url_for, render_text
from bartendro.model.drink import Drink
from bartendro.model.booze import Booze
from bartendro.form.booze import BoozeForm
from bartendro import constant

@expose('/ws/drink/<int:drink>')
def ws_drink(request, drink):
    mixer = local.application.mixer

    recipe = {}
    for arg in request.args:
        recipe[arg] = float(request.args.get(arg)) * constant.ML_PER_FL_OZ

    if mixer.make_drink(drink, recipe):
        return render_text("ok\n")
    else:
        raise ServiceUnavailable("Error: %s (%d)" % (mixer.get_error(), ret))

@expose('/ws/drink/<int:drink>/available/<int:state>')
def ws_drink_available(request, drink, state):

    if not drink:
        session.query(Drink).update({'available' : state})
    else:
        session.query(Drink).filter(Drink.id==drink).update({'available' : state})
    session.flush()
    session.commit()
    return render_text("ok\n")
