# -*- coding: utf-8 -*-
import time
from bartendro import app, db
from flask import Flask, request, render_template
from flask.ext.login import login_required

@app.route('/admin/debug')
@login_required
def report_index():
    startup_log = app.driver.get_startup_log()
    return render_template("admin/debug", options=app.options, title="Debug bartendro", startup_log=startup_log)
