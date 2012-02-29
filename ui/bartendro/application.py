# -*- coding: utf-8 -*-
from os import path
import memcache
import logging
from sqlalchemy import create_engine
from werkzeug import Request, ClosingIterator
from werkzeug.exceptions import HTTPException
from werkzeug import SharedDataMiddleware

from bartendro.utils import session, metadata, local, local_manager, url_map, log, error
from bartendro.views import view_map
from bartendro.master import driver
from bartendro import mixer
import bartendro.models


class BartendroUIServer(object):

    def __init__(self, db_uri):
        local.application = self
        self.setup_logging()
        log("Bartendro starting")

        self.database_engine = create_engine(db_uri, convert_unicode=True)
        self.dispatch = SharedDataMiddleware(self.dispatch, {
                    '/static':  bartendro.utils.STATIC_PATH
                    })

        # Create a memcache connection and flush everything
        self.mc = memcache.Client(['127.0.0.1:11211'], debug=0)
        self.mc.flush_all()

        self.driver = driver.MasterDriver("/dev/ttyS1", "/tmp/log");
        self.driver.open()
        self.driver.chain_init();
        self.mixer = mixer.Mixer(self.driver)

        self.debug_log_file = "logs/bartendro.log"
        self.access_log_file = "logs/access.log"
        self.drinks_log_file = "logs/drinks.log"

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
