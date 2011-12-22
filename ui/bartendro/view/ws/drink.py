# -*- coding: utf-8 -*-
from time import sleep
from werkzeug.utils import redirect
from werkzeug.exceptions import BadRequest, ServiceUnavailable
from bartendro.utils import session, local, expose, validate_url, url_for, render_text
from bartendro.model.drink import Drink
from bartendro.model.booze import Booze
from bartendro.form.booze import BoozeForm

@expose('/ws/drink/<int:drink>/<int:size>/<int:strength>')
def ws_drink(request, drink, size, strength):
    driver = local.application.driver

    print "Make drink! drink: %d size: %d strength: %d" % (drink, size, strength)
    sleep(3)
    ret = driver.check()
    if ret == 0:
        return render_text("ok\n")
    else:
        raise ServiceUnavailable("Error: %s (%d)" % (driver.get_error(), ret))
