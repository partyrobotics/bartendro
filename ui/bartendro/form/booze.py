#!/usr/bin/env python
from wtforms import Form, TextField, DecimalField, HiddenField, validators

class BoozeForm(Form):
    id = HiddenField(u"id", default=0)
    name = TextField(u"Name", [validators.Length(min=3, max=255)])
    brand = TextField(u"Brand", [validators.Length(min=3, max=255)])
    desc = TextField(u"Description", [validators.Length(min=3, max=1024)])
    abv = DecimalField(u"ABV", [validators.NumberRange(0, 97)], default=0, places=0)

form = BoozeForm()
