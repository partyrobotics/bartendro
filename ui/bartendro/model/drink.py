# -*- coding: utf-8 -*-
from sqlalchemy.orm import mapper, relationship
from sqlalchemy import Table, Column, Integer, String, MetaData, UnicodeText, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from bartendro.utils import session, metadata
from bartendro.model.drink_name import DrinkName

Base = declarative_base(metadata=metadata)
class Drink(Base):
    """
    Defintion of a drink. Pretty bare since name is in drink_name and drink details are in drink_liquid
    """

    __tablename__ = 'drink'
    id = Column(Integer, primary_key=True)
    desc = Column(UnicodeText, nullable=False)
    name_id = Column(Integer, ForeignKey('drink_name.id'), nullable=False)

    query = session.query_property()

    def __init__(self, desc = u'', data = None):
        self.name = DrinkName()
        if data: 
            self.update(data)
            return
        self.desc = desc
        session.add(self)

    def json(self):
        return { 
                 'desc' : self.desc,
               }

    def __repr__(self):
        return "<Drink>(%d,%s,%s,%s)>" % (self.id or -1, self.name.name, self.desc, " ".join(["<DrinkBooze>(%d)" % (db.id or -1) for db in self.drink_boozes]))

