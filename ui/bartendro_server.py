#!/usr/bin/env python

import cherrypy
from cherrypy import wsgiserver
from bartendro.application import BartendroUIServer

app = BartendroUIServer('sqlite:///bartendro.db')
server = wsgiserver.CherryPyWSGIServer(("0.0.0.0", 80), app)

cherrypy.log("server starting")
try:
    server.start()
except KeyboardInterrupt:
    server.stop()
