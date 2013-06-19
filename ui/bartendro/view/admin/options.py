# -*- coding: utf-8 -*-
import time
import os
from sqlalchemy import asc, func
from shutil import copyfile
from bartendro import app, db, SQLALCHEMY_DATABASE_FILE, STATIC_FOLDER
from flask import Flask, request, render_template, Response
from flask.ext.login import login_required
from bartendro.model.version import DatabaseVersion
from bartendro.model.option import Option

@app.route('/admin/options')
@login_required
def admin_options():

    options = Option.query.order_by(asc(func.lower(Option.key)))
    options_and_type = []
    for option in options:
        if option.value in ['true', 'false']:
            type = 'boolean'
        else:
            type = 'text'
        options_and_type.append({ 'key'   : option.key,
                                  'value' : option.value == 'true',
                                  'type'  : type 
                                })
    ver = DatabaseVersion.query.one()
    return render_template("admin/options", 
             options=app.options, 
             db_options = options_and_type,
             title="Options", 
             schema = ver.schema)
