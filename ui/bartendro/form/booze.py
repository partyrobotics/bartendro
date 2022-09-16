#!/usr/bin/env python
from wtforms import Form, StringField, DecimalField, HiddenField, validators, \
                          TextAreaField, SubmitField, SelectField
#from wtforms import Form, TextField, DecimalField, HiddenField, validators, \
#                          TextAreaField, SubmitField, SelectField
from bartendro.model import booze

class BoozeForm(Form):
    id = HiddenField(u"id", default=0)
    name = StringField(u"Name", [validators.Length(min=3, max=255)])
    brand = StringField(u"Brand") # Currently unused
    desc = TextAreaField(u"Description", [validators.Length(min=3, max=1024)])
    abv = DecimalField(u"ABV", [validators.NumberRange(0, 97)], default=0, places=0)
    type = SelectField(u"Type", [validators.NumberRange(0, len(booze.booze_types))], 
                                choices=booze.booze_types,
                                coerce=int)
    image = StringField(u"image") # 
    save = SubmitField(u"save")
    cancel = SubmitField(u"cancel")

form = BoozeForm()
