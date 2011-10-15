# -*- coding: utf-8 -*-
from os import path
from sqlalchemy import create_engine
from werkzeug import Request, ClosingIterator
from werkzeug.exceptions import HTTPException
from werkzeug import SharedDataMiddleware

from bartendro.utils import session, metadata, local, local_manager, url_map
from bartendro.views import view_map
from bartendro.master import driver
from bartendro import mixer
import bartendro.models

class BartendroUIServer(object):

    def __init__(self, db_uri):
        local.application = self
        self.database_engine = create_engine(db_uri, convert_unicode=True)
        self.dispatch = SharedDataMiddleware(self.dispatch, {
                    '/static':  bartendro.utils.STATIC_PATH
                    })
        self.driver = driver.MasterDriver("/dev/ttyS1", "/tmp/log");
        self.driver.open()
        self.driver.chain_init();
        self.mixer = mixer.Mixer(self.driver)

    def init_database(self):
        metadata.create_all(self.database_engine)

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
