# -*- coding: utf-8 -*-
import time
from bartendro import app, db
from flask import Flask, request, render_template
from flask.ext.login import login_required
from bartendro.model.version import DatabaseVersion

@app.route('/admin/options')
@login_required
def admin_options():
    ver = DatabaseVersion.query.one()
    return render_template("admin/options", options=app.options, title="Options", schema = ver.schema)
