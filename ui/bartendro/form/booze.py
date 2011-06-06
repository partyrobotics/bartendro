#!/usr/bin/env python
from wtforms import Form, TextField, DecimalField, HiddenField, validators, TextAreaField, SubmitField

class BoozeForm(Form):
    id = HiddenField(u"id", default=0)
    name = TextField(u"Name", [validators.Length(min=3, max=255)])
    brand = TextField(u"Brand", [validators.Length(min=3, max=255)])
    desc = TextAreaField(u"Description", [validators.Length(min=3, max=1024)])
    abv = DecimalField(u"ABV", [validators.NumberRange(0, 97)], default=0, places=0)
    save = SubmitField(u"save")
    cancel = SubmitField(u"cancel")

form = BoozeForm()
