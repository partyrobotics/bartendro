# -*- coding: utf-8 -*-
from bartendro.utils import session, render_template, render_json, expose, validate_url, url_for

@expose('/admin')
def index(request):
    return render_template("admin/index")
