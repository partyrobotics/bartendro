# -*- coding: utf-8 -*-
from sqlalchemy.orm import mapper, relationship
from sqlalchemy import Table, Column, Integer, String, MetaData, Unicode, UnicodeText, UniqueConstraint, Text
from sqlalchemy.ext.declarative import declarative_base
from bartendro.utils import session, metadata

Base = declarative_base(metadata=metadata)
class Liquid(Base):
    """
    Information about a liquid. e.g. water, vodka, grandine, bailies, oj 
    """

    __tablename__ = 'liquid'
    id = Column(Integer, primary_key=True)
    name = Column(UnicodeText, nullable=False)
    desc = Column(UnicodeText, nullable=False)
    abv = Column(Integer, default=0)
 
    query = session.query_property()
    def __init__(self, name = u'', desc = u'', abv = 0):
        self.name = name
        self.sortname = sortname
        self.abv = abv

    def json(self):
        return { 
                 'id' : self.id, 
                 'name' : self.name,
                 'sortname' : self.sortname,
                 'abv' : self.abv,
               }

    def __repr__(self):
        return "<Liquid('%s','%s')>" % (self.id, self.name)

