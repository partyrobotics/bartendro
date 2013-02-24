#!/usr/bin/env python
from wtforms import Form, DecimalField, SelectField, SubmitField, validators

class LiquidOutTestForm(Form):

    # TODO: Ideally this would get the number of actual dispensers
    #dispenser_choices = [i for i in xrange(app.driver.count())]
    dispenser_choices = [(str(i+1), str(i+1)) for i in xrange(15)]
    threshold = DecimalField(u"Liquid out threshold", [validators.NumberRange(0, 255)], default=13, places=0)
    dispenser = SelectField(u"Dispenser", [validators.NumberRange(0, len(dispenser_choices))], 
                                choices=dispenser_choices,
                                coerce=int)
    go = SubmitField(u"go")

form = LiquidOutTestForm()
