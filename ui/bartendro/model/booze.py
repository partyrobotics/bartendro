# -*- coding: utf-8 -*-
from bartendro import db
from sqlalchemy.orm import mapper, relationship
from sqlalchemy import Table, Column, Integer, String, MetaData, Unicode, UnicodeText, UniqueConstraint, Text, Index
from sqlalchemy.ext.declarative import declarative_base

BOOZE_TYPE_UNKNOWN = 0
BOOZE_TYPE_ALCOHOL = 1
BOOZE_TYPE_TART = 2
BOOZE_TYPE_SWEET = 3
BOOZE_TYPE_EXTERNAL = 4
booze_types = [
               (0, "Unknown"),
               (1, "Alcohol"),
               (2, "Tart"),
               (3, "Sweet"),
               (4, "External")
              ]

class Booze(db.Model):
    """
    Information about a booze. e.g. water, vodka, grandine, bailies, oj 
    """

    __tablename__ = 'booze'
    id = Column(Integer, primary_key=True)
    name = Column(UnicodeText, nullable=False)
    brand = Column(UnicodeText, nullable=True)
    desc = Column(UnicodeText, nullable=False)
    image = Column(UnicodeText, nullable=True)
    abv = Column(Integer, default=0)
    type = Column(Integer, default=0)

    # add unique constraint for name
    UniqueConstraint('name', name='booze_name_undx')
 
    query = db.session.query_property()
    def __init__(self, name = u'', brand = u'', desc = u'', abv = 0, type = 0, out = 0, data = None):
        if data: 
            self.update(data)
            return
        self.name = name
        self.brand = brand
        self.desc = desc
        self.abv = abv
        self.type = type
        self.out = out

    def update(self, data):
        self.name = data['name']
        self.desc = data['desc']
        self.brand = data['brand']
        self.abv = int(data['abv'])
        self.type = int(data['type'])

    def is_abstract(self):
        return len(self.booze_group)

    def __repr__(self):
        return "<Booze('%s','%s')>" % (self.id, self.name)

Index('booze_name_ndx', Booze.name)
