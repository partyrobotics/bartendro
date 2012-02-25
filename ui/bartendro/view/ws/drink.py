# -*- coding: utf-8 -*-
from time import sleep
from werkzeug.utils import redirect
from werkzeug.exceptions import BadRequest, ServiceUnavailable
from bartendro.utils import session, local, expose, validate_url, url_for, render_text
from bartendro.model.drink import Drink
from bartendro.model.booze import Booze
from bartendro.form.booze import BoozeForm
from bartendro import constant

@expose('/ws/drink/<int:drink>/<size>/<int:strength>')
def ws_drink(request, drink, size, strength):
    mixer = local.application.mixer

    size = int(float(size) * constant.ML_PER_FL_OZ)
    print "Make drink! drink: %d size: %d strength: %d" % (drink, size, strength)
    ret = mixer.make_drink(drink, size, strength)
    if ret == 0:
        return render_text("ok\n")
    else:
        raise ServiceUnavailable("Error: %s (%d)" % (mixer.get_error(), ret))
