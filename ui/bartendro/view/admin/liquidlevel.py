# -*- coding: utf-8 -*-
from bartendro import app, db
from flask import Flask, request, render_template
from flask.ext.login import login_required

@app.route('/admin/liquidlevel')
@login_required
def admin_liquidlevel():
    count = app.driver.count()
    return render_template("admin/liquidlevel", options=app.options, count=count, title="Liquid level test")
