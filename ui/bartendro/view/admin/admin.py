# -*- coding: utf-8 -*-
from bartendro import app, db
from flask import Flask, request, render_template

@app.route('/admin')
def admin():
    return render_template("admin/index", title="Admin")
