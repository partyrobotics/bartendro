# -*- coding: utf-8 -*-
from sqlalchemy.orm import mapper, relationship
from sqlalchemy import Table, Column, Integer, String, MetaData, Unicode, UnicodeText, UniqueConstraint, Text, Index
from sqlalchemy.ext.declarative import declarative_base
from bartendro.utils import session, Base

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
    UniqueConstraint('name', name='booze_name_undx')
 
    query = session.query_property()
    def __init__(self, name = u'', brand = u'', desc = u'', abv = 0, data = None):
        if data: 
            self.update(data)
            return
        self.name = name
        self.brand = brand
        self.desc = desc
        self.abv = abv

    def update(self, data):
        self.name = data['name']
        self.desc = data['desc']
        self.brand = data['brand']
        self.abv = int(data['abv'])

    def json(self):
        return { 
                 'id' : self.id, 
                 'name' : self.name,
                 'desc' : self.desc,
                 'brand' : self.brand,
                 'abv' : self.abv,
               }

    def __repr__(self):
        return "<Booze('%s','%s')>" % (self.id, self.name)

Index('booze_name_ndx', Booze.name)
