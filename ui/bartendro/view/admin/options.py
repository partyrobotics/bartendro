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

@app.route('/admin/options/dropbox-setup')
@login_required
def admin_options_dropbox_setup():
    mc = app.mc
    access_token = mc.get("dropbox_access_token")
    user_id = mc.get("dropbox_user_id")
    if not access_token:
        flow = dropbox.client.DropboxOAuth2FlowNoRedirect(app.options.app_key, app.options.app_secret)
        url = flow.start()
    else:
        url = None

    return render_template("admin/dropboxsetup", options=app.options, 
                                                 title="Dropbox setup", 
                                                 access_token=access_token,
                                                 user_id=user_id,
                                                 url=url)
