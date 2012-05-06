# -*- coding: utf-8 -*-
from sqlalchemy.orm import mapper, relationship
from sqlalchemy import Table, Column, Integer, String, MetaData, UnicodeText, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from bartendro.utils import session, Base

class CustomDrink(Base):
    """
    This class provides details about customizable drinks. 
    """

    __tablename__ = 'custom_drink'
    id = Column(Integer, primary_key=True)
    drink_id = Column(Integer, ForeignKey('drink.id'), nullable=False)
    name = Column(UnicodeText, nullable=False)
 
    query = session.query_property()

    def __init__(self, name = u''):
        self.name = name
        session.add(self)

    def __repr__(self):
        return "<CustomDrink(%d,<Drink>(%d),'%s')>" % (self.id or -1, 
                                                      self.drink_id,
                                                      self.name)
