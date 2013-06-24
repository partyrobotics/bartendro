# -*- coding: utf-8 -*-
from bartendro import db
from sqlalchemy.orm import mapper, relationship
from sqlalchemy import Table, Column, Integer, String, MetaData, Unicode, UnicodeText, UniqueConstraint, Text
from sqlalchemy.ext.declarative import declarative_base

class BlenderLog(db.Model):
    """
    Name of a drink, complete with a sortname
    """

    __tablename__ = 'blender_log'
    id = Column(Integer, primary_key=True)
    blend = Column(UnicodeText, nullable=False)
 
    query = db.session.query_property()

    def __init__(self, blend=""):
        self.blend = blend
        db.session.add(self)

    def __repr__(self):
        return "<BlenderLog(%d,'%s')>" % (self.id, self.blend)
