#!/usr/bin/env python
from wtforms import Form, TextField, PasswordField, SubmitField, SelectField, validators

class LoginForm(Form):
    user = TextField(u"Name", [validators.Length(min=3, max=255)])
    password = PasswordField(u"Password", [validators.Length(min=3, max=255)])

    login = SubmitField(u"login")

form = LoginForm()
