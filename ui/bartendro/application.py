# -*- coding: utf-8 -*-
import os 
import memcache
import logging
from sqlalchemy import create_engine
from werkzeug import Request, ClosingIterator
from werkzeug.exceptions import HTTPException
from werkzeug import SharedDataMiddleware

from bartendro.utils import session, metadata, local, local_manager, url_map, log, error
from bartendro.views import view_map
from bartendro.router import driver
from bartendro.router import status_led
from bartendro import mixer
import bartendro.models


class BartendroUIServer(object):

    def __init__(self, db_uri):


        try: 
            self.software_only = int(os.environ['BARTENDRO_SOFTWARE_ONLY'])
            self.num_dispensers = 15
        except KeyError:
            self.software_only = 0

        self.setup_logging()
        local.application = self

        self.database_engine = create_engine(db_uri, convert_unicode=True)
        self.dispatch = SharedDataMiddleware(self.dispatch, {
                    '/static':  bartendro.utils.STATIC_PATH
                    })

        # Create a memcache connection and flush everything
        self.mc = memcache.Client(['127.0.0.1:11211'], debug=0)
        self.mc.flush_all()

        self.status = status_led.StatusLED(self.software_only)
        self.status.set_color(0, 0, 1)

        self.driver = driver.RouterDriver("/dev/ttyAMA0", self.software_only);
        self.driver.open()
        log("Found %d dispensers." % self.driver.count())

        self.mixer = mixer.Mixer(self.driver, self.status)

        self.debug_log_file = "logs/bartendro.log"
        self.access_log_file = "logs/access.log"
        self.drinks_log_file = "logs/drinks.log"
        self.comm_log_file = "logs/comm.log"

        if self.software_only:
            log("Running SOFTWARE ONLY VERSION. No communication between software and hardware chain will happen!")
            return

        log("Bartendro starting")

        local.application = self

    def init_database(self):
        metadata.create_all(self.database_engine)
  
    def setup_logging(self):
        self.log = logging.getLogger('bartendro')
        hdlr = logging.FileHandler('logs/bartendro.log')
        formatter = logging.Formatter('%(asctime)s %(message)s')
        hdlr.setFormatter(formatter)
        self.log.addHandler(hdlr) 
        self.log.setLevel(logging.INFO)

    def __call__(self, environ, start_response):
        return self.dispatch(environ, start_response)

    def dispatch(self, environ, start_response):
        local.application = self
        request = Request(environ)
        local.url_adapter = adapter = url_map.bind_to_environ(environ)
        try:
            endpoint, values = adapter.match()
            endpoint, module = endpoint.split(' ')
            handler = getattr(view_map[module], endpoint)
            response = handler(request, **values)
        except HTTPException, e:
            response = e
        return ClosingIterator(response(environ, start_response),
                               [session.remove, local_manager.cleanup])
