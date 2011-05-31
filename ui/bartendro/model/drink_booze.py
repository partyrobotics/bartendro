# -*- coding: utf-8 -*-
from sqlalchemy.orm import mapper, relationship
from sqlalchemy import Table, Column, Integer, String, MetaData, UnicodeText, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from bartendro.utils import session, metadata

Base = declarative_base(metadata=metadata)
class DrinkBooze(Base):
    """
    Join between the Drink table and the Booze table for 1:n relationship
    """

    __tablename__ = 'drink_booze'
    id = Column(Integer, primary_key=True)
    drink_id = Column(Integer, ForeignKey('drink.id'), nullable=False)
    booze_id = Column(Integer, ForeignKey('booze.id'), nullable=False)
    value = Column(Integer, default=1)
    unit = Column(Integer, default=1)
 
    query = session.query_property()

    def __init__(self, value, unit):
        self.value = value
        self.unit = unit
        session.add(self)

    def json(self):
        return { 
                 'id' : self.id, 
                 'value' : self.value,
                 'unit' : self.unit,
               }

    def __repr__(self):
        return "<DrinkBooze(%d,%d,%d)>" % (self.id, self.value, self.unit)

