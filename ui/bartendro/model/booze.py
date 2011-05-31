# -*- coding: utf-8 -*-
from sqlalchemy.orm import mapper, relationship
from sqlalchemy import Table, Column, Integer, String, MetaData, Unicode, UnicodeText, UniqueConstraint, Text
from sqlalchemy.ext.declarative import declarative_base
from bartendro.utils import session, metadata

Base = declarative_base(metadata=metadata)
class Booze(Base):
    """
    Information about a booze. e.g. water, vodka, grandine, bailies, oj 
    """

    __tablename__ = 'booze'
    id = Column(Integer, primary_key=True)
    name = Column(UnicodeText, nullable=False)
    brand = Column(UnicodeText, nullable=True)
    desc = Column(UnicodeText, nullable=False)
    abv = Column(Integer, default=0)

    # add unique constraint for name
 
    query = session.query_property()
    def __init__(self, name = u'', brand = u'', desc = u'', abv = 0):
        self.name = name
        self.brand = brand
        self.desc = desc
        self.abv = abv

    def json(self):
        return { 
                 'id' : self.id, 
                 'name' : self.name,
                 'sortname' : self.sortname,
                 'abv' : self.abv,
               }

    def __repr__(self):
        return "<Booze('%s','%s')>" % (self.id, self.name)

