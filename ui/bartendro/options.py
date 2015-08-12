# -*- coding: utf-8 -*-
import logging
from bartendro import app, db
from bartendro.model.option import Option
from bartendro.model.shot_log import ShotLog
from sqlalchemy.exc import OperationalError

log = logging.getLogger('bartendro')

bartendro_options = {
    u'use_liquid_level_sensors': False,
    u'must_login_to_dispense'  : False,
    u'login_name'              : u"bartendro",
    u'login_passwd'            : u"boozemeup",
    u'metric'                  : False,
    u'drink_size'              : 150,
    u'taster_size'             : 30,
    u'shot_size'               : 30,
    u'test_dispense_ml'        : 10,
    u'show_strength'           : True,
    u'show_size'               : True,
    u'show_taster'             : False,
    u'strength_steps'          : 2,
    u'use_shotbot_ui'          : False,
    u'show_feeling_lucky'      : False,
    u'turbo_mode'              : False
}

class BadConfigOptionsError(Exception):
    pass

class Options(object):
    '''A simple placeholder for options'''

    def add(self, key, value):
        self.__attr__

def setup_options_table():
    '''Check to make sure the options table is present'''

    if not db.engine.dialect.has_table(db.engine.connect(), "option"):
        log.info("Creating options table")
        option = Option()
        option.__table__.create(db.engine)


    # Try and see if we have a legacy config.py kicking around. If so,
    # import the options and save them in the DB
    try:
        import config
    except ImportError:
        config = None

    # Figure out which, if any options are missing from the options table
    options = db.session.query(Option).all()
    opt_dict = {}
    for o in options:
        opt_dict[o.key] = o.value

    # Now populate missing keys from old config or defaults
    for opt in bartendro_options:
        if not opt in opt_dict:
            log.info("option %s is not in DB." % opt)
            try:
                value = getattr(config, opt)
                log.info("Get option from legacy: %s" % value)
            except AttributeError:
                value = bartendro_options[opt]
                log.info("Get option from defaults: %s" % value)

            log.info("Adding option '%s'" % opt)
            o = Option(opt, value)
            db.session.add(o)

    db.session.commit()

    # This should go someplace else, but not right this second
    if not db.engine.dialect.has_table(db.engine.connect(), "shot_log"):
        log.info("Creating shot_log table")
        shot_log = ShotLog()
        shot_log.__table__.create(db.engine)

def load_options():
    '''Load options from the db and make them into a nice an accessible modules'''

    setup_options_table()

    options = Options()
    for o in db.session.query(Option).all():
        try:
            if isinstance(bartendro_options[o.key], int):
               value = int(o.value)
            elif isinstance(bartendro_options[o.key], unicode):
               value = unicode(o.value)
            elif isinstance(bartendro_options[o.key], boolean):
               value = boolean(o.value)
            else:
                raise BadConfigOptionsError
        except KeyError:
            # Ignore options we don't understand
            pass

        setattr(options, o.key, value)

    if app.driver.count() == 1:
        setattr(options, "i_am_shotbot", True)
        setattr(options, "use_shotbot_ui", True)
    else:
        setattr(options, "i_am_shotbot", False)

    return options
