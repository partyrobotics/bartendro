# -*- coding: utf-8 -*-
import time
import os
from shutil import copyfile
from bartendro import app, db, SQLALCHEMY_DATABASE_FILE, STATIC_FOLDER
from flask import Flask, request, render_template, Response
from flask.ext.login import login_required
from bartendro.model.version import DatabaseVersion

@app.route('/admin/options')
#@login_required
def admin_options():
    ver = DatabaseVersion.query.one()
#    Response.headers.add('Set-Cookie', 'fileDownload=true; path=/')
#    Response.headers.add('Conent-Type', 'application/x-sqlite')
    return render_template("admin/options", options=app.options, title="Options", schema = ver.schema)
