# -*- coding: utf-8 -*-
from bartendro import db
from sqlalchemy.orm import mapper, relationship
from sqlalchemy import Table, Column, Integer
from sqlalchemy.ext.declarative import declarative_base

class DatabaseVersion(db.Model):
    """
    This table stores the version of the Bartendro database
    """

    __tablename__ = 'version'
    schema = Column(Integer, primary_key=True)

    query = db.session.query_property()
    def __init__(self, schema = 1):
        self.schema = schema

    def update(self, schema):
        self.schema = schema

    def __repr__(self):
        return "<Version(schema %d)>" % (self.schema)
