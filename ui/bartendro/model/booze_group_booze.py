# -*- coding: utf-8 -*-
from bartendro import db
from sqlalchemy.orm import mapper, relationship
from sqlalchemy import Table, Column, Integer, String, MetaData, UnicodeText, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from bartendro.utils import session, Base

class BoozeGroupBooze(db.Model):
    """
    Join between the Drink table and the Booze table for 1:n relationship
    """

    __tablename__ = 'booze_group_booze'
    id = Column(Integer, primary_key=True)
    booze_group_id = Column(Integer, ForeignKey('booze_group.id'), nullable=False)
    booze_id = Column(Integer, ForeignKey('booze.id'), nullable=False)
    sequence = Column(Integer, default=0)
 
    query = db.session.query_property()

    def __init__(self, sequence):
        self.sequence = sequence
        db.session.add(self)

    def __repr__(self):
        return "<BoozeGroupBooze(%d,BoozeGroup(%d),<Booze>(%d),%d)>" % (self.id or -1, 
                                                 self.booze_group_id,
                                                 self.booze.id or -1,
                                                 self.sequence)

