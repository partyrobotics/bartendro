# -*- coding: utf-8 -*-
from sqlalchemy.orm import mapper, relationship
from sqlalchemy import Table, Column, Integer, String, MetaData, UnicodeText, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from bartendro.utils import session, Base

BOOZE_ATTRIBUTE_NOT_USED = 0
BOOZE_ATTRIBUTE_SWEET    = 1
BOOZE_ATTRIBUTE_TANGY    = 2
BOOZE_ATTRIBUTE_ALCOHOL  = 3

class CustomDrinkBooze(Base):
    """
    This join table ties the custom drink and the boozes that go in into a custom drink.
    """

    __tablename__ = 'custom_drink_booze'
    id = Column(Integer, primary_key=True)
    booze_id = Column(Integer, ForeignKey('booze.id'), nullable=False)
    custom_drink_id = Column(Integer, ForeignKey('custom_drink.id'), nullable=False)
    type = Column(Integer)
 
    query = session.query_property()

    def __init__(self, attr = BOOZE_ATTRIBUTE_NOT_USED):
        self.attr = attr
        session.add(self)

    def __repr__(self):
        return "<CustomDrinkBooze(%d,<Booze>(%d),CustomDrink(%d),%d)>" % (self.id or -1, 
                                                      self.booze_id,
                                                      self.custom_drink_id,
                                                      self.attr)
