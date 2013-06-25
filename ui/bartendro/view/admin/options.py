# -*- coding: utf-8 -*-
import time
from bartendro import app, db
from flask import Flask, request, render_template
from flask.ext.login import login_required
from bartendro.model.version import DatabaseVersion
import dropbox

@app.route('/admin/options')
@login_required
def admin_options():
    ver = DatabaseVersion.query.one()
    return render_template("admin/options", options=app.options, title="Options", schema = ver.schema)

@app.route('/admin/options/dropboxsetup')
@login_required
def admin_options_dropbox_setup():
    flow = dropbox.client.DropboxOAuth2FlowNoRedirect(app.options.app_key, app.options.app_secret)
    return render_template("admin/dropboxsetup", options=app.options, title="Dropbox setup", url=flow.start())

@app.route('/admin/options/dropboxfinish')
@login_required
def admin_options_dropbox_setup():
    flow = dropbox.client.DropboxOAuth2FlowNoRedirect(app.options.app_key, app.options.app_secret)
    return render_template("admin/dropboxsetup", options=app.options, title="Dropbox setup", url=flow.start())
