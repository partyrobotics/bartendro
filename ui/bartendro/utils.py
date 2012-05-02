# -*- coding: utf-8 -*-
from sqlalchemy import MetaData
from sqlalchemy.orm import create_session, scoped_session
from sqlalchemy.ext.declarative import declarative_base
from werkzeug import Local, LocalManager
from werkzeug.routing import Map, Rule
from os import path
from urlparse import urlparse
from werkzeug import Response
from jinja2 import Environment, FileSystemLoader
from json import dumps

local = Local()
local_manager = LocalManager([local])
application = local('application')

metadata = MetaData()
Base = declarative_base(metadata=metadata)

session = scoped_session(lambda: create_session(application.database_engine,
                         autocommit=False, autoflush=False),
                         local_manager.get_ident)

url_map = Map([Rule('/static/<file>', endpoint='static', build_only=True)])
def expose(rule, **kw):
    def decorate(f):
        kw['endpoint'] = f.__name__ + " " + f.__module__
        url_map.add(Rule(rule, **kw))
        return f
    return decorate

def url_for(endpoint, _external=False, **values):
    return local.url_adapter.build(endpoint, values, force_external=_external)

ALLOWED_SCHEMES = frozenset(['http'])
TEMPLATE_PATH = 'content/templates'
STATIC_PATH = 'content/static'

jinja_env = Environment(loader=FileSystemLoader(TEMPLATE_PATH))
jinja_env.globals['url_for'] = url_for

def render_template(template, **context):
    return Response(jinja_env.get_template(template).render(**context),
                    mimetype='text/html')

def render_template_no_cache(template, **context):
    return Response(jinja_env.get_template(template).render(**context),
                    headers=[["Cache-Control", "no-store"]],
                    mimetype='text/html')

def render_error(code, err):
    return Response(err, mimetype='text/plain')

def render_json(data):
    return Response(dumps(data), 
                    mimetype='application/json')

def render_text(data):
    return Response(data,
                    mimetype='text/plain')

def validate_url(url):
    return urlparse(url)[0] in ALLOWED_SCHEMES

def log(msg):
    print msg
    application.log.info(msg)

def error(msg):
    print msg
    application.log.error(msg)

def warn(msg):
    print msg
    application.log.warn(msg)
