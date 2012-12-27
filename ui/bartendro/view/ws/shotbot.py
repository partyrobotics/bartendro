# -*- coding: utf-8 -*-
from werkzeug.utils import redirect
from werkzeug.exceptions import BadRequest, ServiceUnavailable
from bartendro.utils import session, local, expose, validate_url, url_for, render_text
from bartendro.model.drink import Drink
from bartendro.model.booze import Booze
from bartendro.form.booze import BoozeForm

@expose('/ws/shotbot')
def ws_reset(request):
    driver = local.application.driver
    driver.make_shot()
    return render_text("ok\n")
