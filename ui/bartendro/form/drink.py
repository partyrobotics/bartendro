#!/usr/bin/env python
from wtforms import Form, TextField, DecimalField, HiddenField, validators, TextAreaField, SubmitField

class DrinkForm(Form):
    id = HiddenField(u"id", default=0)
    drink_name = TextField(u"Name", [validators.Length(min=3, max=255)])
    desc = TextAreaField(u"Description", [validators.Length(min=3, max=1024)])
    save = SubmitField(u"save")
    cancel = SubmitField(u"cancel")

form = DrinkForm()
