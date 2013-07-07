#!/usr/bin/env python
from wtforms import Form, TextField, DecimalField, HiddenField, validators, TextAreaField, SubmitField, BooleanField

MAX_SUGGESTED_DRINK_SIZE = 5000 # in ml

class DrinkForm(Form):
    id = HiddenField(u"id", default=0)
    drink_name = TextField(u"Name", [validators.Length(min=3, max=255)])
    desc = TextAreaField(u"Description", [validators.Length(min=3, max=1024)])
    popular = BooleanField(u"List this drink in the <i>the essentials</i> section.")
    available = BooleanField(u"List this drink in the main menu")
    save = SubmitField(u"save")
    cancel = SubmitField(u"cancel")

form = DrinkForm()
