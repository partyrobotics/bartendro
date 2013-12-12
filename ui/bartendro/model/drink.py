# -*- coding: utf-8 -*-
from bartendro import db
from sqlalchemy.orm import mapper, relationship
from sqlalchemy import Table, Column, Integer, String, MetaData, UnicodeText, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from bartendro.model.drink_name import DrinkName
from operator import attrgetter

DEFAULT_SUGGESTED_DRINK_SIZE = 118 #ml (4 oz)

class Drink(db.Model):
    """
    Defintion of a drink. Pretty bare since name is in drink_name and drink details are in drink_liquid
    """

    __tablename__ = 'drink'
    id = Column(Integer, primary_key=True)
    desc = Column(UnicodeText, nullable=False)
    name_id = Column(Integer, ForeignKey('drink_name.id'), nullable=False)
    sugg_size = Column(Integer)
    popular = Column(Boolean)
    available = Column(Boolean)

    # Not for storing in the DB, but for telling the UI if a drink is lucky
    am_lucky = 0

    query = db.session.query_property()

    def __init__(self, desc = u'', data = None, size = DEFAULT_SUGGESTED_DRINK_SIZE, popular = False, available = True):
        self.name = DrinkName()
        if data: 
            self.update(data)
            return
        self.desc = desc
        self.size = size
        self.popular = popular
        self.available = available
        self.sugg_size = 0
        db.session.add(self)
    
    def set_ingredients_text(self, txt=""):
        self.ingredients = [{ 'name' : txt, 
                              'id' : 0, 
                              'parts' : 1, 
                              'type' : 0 
                           }]

    def process_ingredients(self):
        ing = []

        self.drink_boozes = sorted(self.drink_boozes, key=attrgetter('booze.abv', 'booze.name'), reverse=True)
        for db in self.drink_boozes:
            ing.append({ 'name' : db.booze.name, 
                         'id' : db.booze.id, 
                         'parts' : db.value, 
                         'type' : db.booze.type 
                       })
        self.ingredients = ing

    def set_lucky(self, lucky):
        self.am_lucky = lucky

    def __repr__(self):
        return "<Drink>(%d,%s,%s,%s)>" % (self.id or -1, self.name.name, self.desc, " ".join(["<DrinkBooze>(%d)" % (db.id or -1) for db in self.drink_boozes]))

