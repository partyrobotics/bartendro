# -*- coding: utf-8 -*-
from werkzeug.utils import redirect
from werkzeug.exceptions import BadRequest, ServiceUnavailable
from bartendro.utils import session, local, expose, validate_url, url_for, render_text
from bartendro.model.drink import Drink
from bartendro.model.booze import Booze
from bartendro.form.booze import BoozeForm

@expose('/ws/dispenser/<int:disp>/on')
def ws_dispenser_on(request, disp):
    driver = local.application.driver
    driver.start(disp - 1)
    return render_text("ok\n")

@expose('/ws/dispenser/<int:disp>/off')
def ws_dispenser_off(request, disp):
    driver = local.application.driver
    driver.stop(disp - 1)
    return render_text("ok\n")
