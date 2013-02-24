#!/usr/bin/env python

from flask import Flask, request, session, g, redirect, url_for, abort, render_template, flash
from flask.ext.sqlalchemy import SQLAlchemy

SQLALCHEMY_DATABASE_URI = 'sqlite:///../bartendro.db'
DEBUG = True
SECRET_KEY = 'let our bot get you drunk!'
USERNAME = 'admin'
PASSWORD = '!freedrinks'

app = Flask(__name__,
            static_url_path = "/static",
            static_folder = "content/static",
            template_folder = "content/templates")
app.config.from_object(__name__)
db = SQLAlchemy(app)

# Import models
from bartendro.model import booze_group
from bartendro.model import custom_drink
from bartendro.model import drink
from bartendro.model import drink_log
from bartendro.model import booze
from bartendro.model import booze_group_booze
from bartendro.model import dispenser
from bartendro.model import drink_booze
from bartendro.model import drink_name

# Import views
from bartendro.view import root
from bartendro.view.admin import admin, booze as booze_admin, drink as drink_admin, \
                                 dispenser as admin_dispenser, report, liquidout
from bartendro.view.drink import drink
from bartendro.view.ws import booze as ws_booze, dispenser as ws_dispenser, drink as ws_drink, \
                              misc as ws_misc, shotbot as ws_shotbot
