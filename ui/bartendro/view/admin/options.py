# -*- coding: utf-8 -*-
import time
import os
from bartendro import app
from flask import Flask, request, render_template, Response
from flask.ext.login import login_required
from bartendro.model.version import DatabaseVersion

@app.route('/admin/options')
@login_required
def admin_options():
    ver = DatabaseVersion.query.one()
    return render_template("admin/options", 
                           options=app.options,
                           title="Options", 
                           schema = ver.schema)
