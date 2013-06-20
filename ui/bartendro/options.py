# -*- coding: utf-8 -*-
import logging
from bartendro import app, db
from bartendro.model.option import Option
from sqlalchemy.exc import OperationalError

log = logging.getLogger('bartendro')

bartendro_options = {
    u'use_liquid_level_sensors': u'0',
    u'must_login_to_dispense'  : u'0',
    u'login_name'              : u"bartendro",
    u'login_passwd'            : u"boozemeup",
    u'metric'                  : u'0',
    u'drink_size'              : u'150',
    u'show_strength'           : u'1',
    u'show_size'               : u'1',
    u'show_taster'             : u'0',
    u'strength_steps'          : u'2',
    u'test_dispense_ml'        : u'10'
}

class Options(object):
    '''A simple placeholder for options'''

    def add(self, key, value):
        self.__attr__

def setup_options_table():
    '''Check to make sure the options table is present'''

    if db.engine.dialect.has_table(db.engine.connect(), "option"):
        return

    log.info("Creating options table")
    option = Option()
    option.__table__.create(db.engine)

    # Try and see if we have a legacy config.py kicking around. If so,
    # import the options and save them in the DB
    try:
        import config
    except ImportError:
        pass

    # Figure out which, if any options are missing from the options table
    options = db.session.query(Option).all()
    opt_dict = {}
    for o in options:
        opt_dict[o.key] = value

    # Now populate missing keys from old config or defaults
    for opt in bartendro_options:
        if not opt in opt_dict:
            try:
                value = getattr(config, opt)
            except AttributeError:
                value = bartendro_options[opt]

            log.info("Adding option '%s'" % opt)
            o = Option(opt, value)
            db.session.add(o)

    db.session.commit()

def load_options():
    '''Load options from the db and make them into a nice an accessible modules'''

    setup_options_table()

    options = Options()
    for o in db.session.query(Option).all():
        setattr(options, o.key, o.value)

    return options
