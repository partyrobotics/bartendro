# -*- coding: utf-8 -*-
from bartendro import db
from sqlalchemy.orm import mapper, relationship
from sqlalchemy import Table, Column, Integer, String, MetaData, Unicode, UnicodeText, UniqueConstraint, ForeignKey
from sqlalchemy.ext.declarative import declarative_base

class ShotLog(db.Model):
    """
    Keeps a record of shots we've dispensed. This should be in DrinkLog, but that requires a schema change. :(
    """

    __tablename__ = 'shot_log'
    id = Column(Integer, primary_key=True)
    booze_id = Column(Integer, ForeignKey('booze.id'), nullable=False)
    time = Column(Integer, nullable=False, default=0)
    size = Column(Integer, nullable=False, default=-1)
 
    query = db.session.query_property()

    def __init__(self, booze_id=-1, time=0, size=0):
        self.booze_id = booze_id
        self.time = time
        self.size = size
        db.session.add(self)

    def __repr__(self):
        return "<ShotLog(%d,'%s')>" % (self.id, self.booze_id)

