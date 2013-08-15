# -*- coding: utf-8 -*-
from bartendro import app, db, login_manager
from bartendro.form.login import LoginForm
from flask import Flask, request, render_template, flash, redirect, url_for
from flask.ext.login import login_required, login_user, logout_user

class User(object):
    id = 0
    username = ""

    def __init__(self, username):
        self.username = username

    def is_authenticated(self):
        return self.username != ""

    def is_active(self):
        return True

    def is_anonymous(self):
        return self.username == ""

    def get_id(self):
        return self.username

    def __repr__(self):
        return '<User %d>' % self.username

@login_manager.user_loader
def load_user(userid):
    return User(userid)

@app.route("/admin/login", methods=["GET", "POST"])
def login():
    form = LoginForm(request.form)
    if request.method == 'POST' and form.validate():
        user = request.form.get("user" or '')
        password = request.form.get("password" or '')
        if (user == app.options.login_name and password == app.options.login_passwd):
            login_user(User(user))
            return redirect(request.args.get("next") or url_for("dispenser"))
        return render_template("/admin/login", options=app.options, form=form, fail=1)
    return render_template("/admin/login", options=app.options, form=form, fail=0)

@app.route("/admin/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("index"))
