#!/usr/bin/env python
from wtforms import Form, TextField, DecimalField, HiddenField, validators, TextAreaField, SubmitField, BooleanField

MAX_SUGGESTED_DRINK_SIZE = 5000 # in ml

class DrinkForm(Form):
    id = HiddenField(u"id", default=0)
    drink_name = TextField(u"Name", [validators.Length(min=3, max=255)])
    desc = TextAreaField(u"Description", [validators.Length(min=3, max=1024)])
    sugg_size = DecimalField(u"Suggested size (fl oz)", [validators.NumberRange(min=1, max=MAX_SUGGESTED_DRINK_SIZE)])
    popular = BooleanField(u"This drink is popular")
    save = SubmitField(u"save")
    cancel = SubmitField(u"cancel")

form = DrinkForm()
