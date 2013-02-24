# -*- coding: utf-8 -*-
from bartendro import db
from sqlalchemy.orm import mapper, relationship
from sqlalchemy import Table, Column, Integer, String, MetaData, UnicodeText, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from bartendro.utils import session, Base

class DrinkBooze(db.Model):
    """
    Join between the Drink table and the Booze table for 1:n relationship
    """

    __tablename__ = 'drink_booze'
    id = Column(Integer, primary_key=True)
    drink_id = Column(Integer, ForeignKey('drink.id'), nullable=False)
    booze_id = Column(Integer, ForeignKey('booze.id'), nullable=False)
    value = Column(Integer, default=1)
    unit = Column(Integer, default=1)
 
    query = db.session.query_property()

    def __init__(self, drink, booze, value, unit):
        self.drink = drink
        self.drink_id = drink.id
        self.booze = booze
        self.booze_id = booze.id
        self.value = value
        self.unit = unit
        db.session.add(self)

    def json(self):
        return { 
                 'id' : self.id, 
                 'value' : self.value,
                 'unit' : self.unit,
               }

    def __repr__(self):
        return "<DrinkBooze(%d,<Drink>(%d),<Booze>(%d),%d,%d)>" % (self.id or -1, 
                                                 self.drink.id,
                                                 self.booze.id or -1,
                                                 self.value, 
                                                 self.unit)

