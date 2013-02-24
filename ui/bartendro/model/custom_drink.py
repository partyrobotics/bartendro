# -*- coding: utf-8 -*-
from bartendro import db
from sqlalchemy.orm import mapper, relationship
from sqlalchemy import Table, Column, Integer, String, MetaData, UnicodeText, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from bartendro.utils import session, Base

class CustomDrink(db.Model):
    """
    This class provides details about customizable drinks. 
    """

    __tablename__ = 'custom_drink'
    id = Column(Integer, primary_key=True)
    drink_id = Column(Integer, ForeignKey('drink.id'), nullable=False)
    name = Column(UnicodeText, nullable=False)
 
    query = db.session.query_property()

    def __init__(self, name = u''):
        self.name = name
        db.session.add(self)

    def __repr__(self):
        return "<CustomDrink(%d,<Drink>(%d),'%s')>" % (self.id or -1, 
                                                      self.drink_id,
                                                      self.name)
