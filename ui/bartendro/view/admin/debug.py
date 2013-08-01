# -*- coding: utf-8 -*-
import time
from bartendro import app, db
from flask import Flask, request, render_template
from flask.ext.login import login_required

LOG_LINES_TO_SHOW = 1000

@app.route('/admin/debug')
@login_required
def debug_index():

    startup_log = app.driver.get_startup_log()
    try:
        b_log = open("logs/bartendro.log", "r")
        lines = b_log.readlines()
        b_log.close()
        lines = lines[-LOG_LINES_TO_SHOW:]
        bartendro_log = "".join(lines)
        print bartendro_log
    except IOError, e:
        print "file open fail"
        bartendro_log = "%s" % e 

    return render_template("admin/debug", options=app.options, 
                                          title="Debug bartendro", 
                                          startup_log=startup_log,
                                          bartendro_log=bartendro_log)
