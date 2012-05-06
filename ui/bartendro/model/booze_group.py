# -*- coding: utf-8 -*-
from sqlalchemy.orm import mapper, relationship
from sqlalchemy import Table, Column, Integer, String, MetaData, UnicodeText, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from bartendro.utils import session, Base

class BoozeGroup(Base):
    """
    This table groups boozes into a booze class. Titos, Smirnoff and Grey Goose
    are all part of the Vodka booze class.
    """

    __tablename__ = 'booze_group'
    id = Column(Integer, primary_key=True)
    abstract_booze_id = Column(Integer, ForeignKey('booze.id'), nullable=False)
    name = Column(UnicodeText, nullable=False)
 
    query = session.query_property()

    def __init__(self, name = u''):
        self.name = name
        session.add(self)

    def json(self):
        return { 
                 'id' : self.id, 
                 'name' : self.name,
               }

    def __repr__(self):
        return "<BoozeGroup(%d,<Booze>(%d),'%s',%s)>" % (self.id or -1, 
                                                      self.abstract_booze_id,
                                                      self.name,
                                                      " ".join(["<BoozeGroupBooze>(%d)" % (bgb.id or -1) for bgb in self.booze_group_boozes]))
