# -*- coding: utf-8 -*-
from sqlalchemy.orm import mapper, relationship
from sqlalchemy import Table, Column, Integer, String, MetaData, UnicodeText, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from bartendro.utils import session, metadata
from bartendro.model.drink_name import DrinkName

DEFAULT_SUGGESTED_DRINK_SIZE = 118 #ml (4 oz)

Base = declarative_base(metadata=metadata)
class Drink(Base):
    """
    Defintion of a drink. Pretty bare since name is in drink_name and drink details are in drink_liquid
    """

    __tablename__ = 'drink'
    id = Column(Integer, primary_key=True)
    desc = Column(UnicodeText, nullable=False)
    name_id = Column(Integer, ForeignKey('drink_name.id'), nullable=False)
    sugg_size = Column(Integer)
    popular = Column(Boolean)

    query = session.query_property()

    def __init__(self, desc = u'', data = None, size = DEFAULT_SUGGESTED_DRINK_SIZE, popular = False):
        self.name = DrinkName()
        if data: 
            self.update(data)
            return
        self.desc = desc
        self.size = size
        self.popular = popular
        session.add(self)

    def json(self):
        return { 
                 'desc' : self.desc,
                 'sugg_size' : self.sugg_size,
               }

    def __repr__(self):
        return "<Drink>(%d,%s,%s,%s)>" % (self.id or -1, self.name.name, self.desc, " ".join(["<DrinkBooze>(%d)" % (db.id or -1) for db in self.drink_boozes]))

