# -*- coding: utf-8 -*-
import time
import os
from bartendro import app
from flask import Flask, request, render_template, Response
from werkzeug.exceptions import Unauthorized
from flask.ext.login import login_required
from bartendro.model.version import DatabaseVersion

@app.route('/admin/planner')
@login_required
def admin_planner():
    return render_template("admin/planner", 
                           options=app.options)
