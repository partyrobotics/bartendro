#!/usr/bin/env python
from wtforms import Form, TextField, DecimalField, HiddenField, validators

class BoozeForm(Form):
    id = HiddenField(u"id", default=0)
    name = TextField(u"Name")
    brand = TextField(u"Brand")
    desc = TextField(u"Description")
    abv = DecimalField(u"ABV", default=0)

form = BoozeForm()
