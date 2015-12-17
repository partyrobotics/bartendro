# -*- coding: utf-8 -*-
import socket
import fcntl
import struct
import time
import os
from bartendro import app
from flask import Flask, request, render_template, Response
from werkzeug.exceptions import Unauthorized
from flask.ext.login import login_required
from bartendro.model.version import DatabaseVersion

def get_ip_address_from_interface(ifname):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        return socket.inet_ntoa(fcntl.ioctl(s.fileno(), 0x8915,  
                                struct.pack('256s', ifname[:15]))[20:24])
    except IOError:
        return "[none]"

@app.route('/admin/options')
@login_required
def admin_options():
    ver = DatabaseVersion.query.one()
    recover = not request.remote_addr.startswith("10.0.0")

    wlan0 = get_ip_address_from_interface("wlan0")
    eth0 = get_ip_address_from_interface("eth0")

    return render_template("admin/options", 
                           options=app.options,
                           show_passwd_recovery=recover,
                           title="Options", 
                           eth0=eth0,
                           wlan0=wlan0,
                           version = app.version,
                           schema = ver.schema)

@app.route('/admin/lost-passwd')
def admin_lost_passwd():
    if request.remote_addr.startswith("10.0.0"):
        raise Unauthorized

    return render_template("admin/lost-passwd", 
                           options=app.options)

@app.route('/admin/upload')
@login_required
def admin_upload_db():
    return render_template("admin/upload", 
                           title="Upload database",
                           options=app.options)
