#!/usr/bin/env python
from optparse import OptionParser
parser = OptionParser()
parser.set_defaults(
    port='8000',
    host='127.0.0.1',
    settings='settings',
)

parser.add_option('--port', dest='port')
parser.add_option('--host', dest='host')
parser.add_option('--settings', dest='settings')
parser.add_option('--pythonpath', dest='pythonpath')

options, args = parser.parse_args()

import os
os.environ['DJANGO_SETTINGS_MODULE'] = options.settings

import fapws._evwsgi as evwsgi
#from fapws import base
import mybase
import time
import sys
sys.setcheckinterval=100000 # since we don't use threads, internal checks are no more required

if options.pythonpath:
    sys.path.insert(1, options.pythonpath)

from fapws.contrib import django_handler, views
import django

print 'start on', (options.host, options.port)
evwsgi.start(options.host, options.port)
evwsgi.set_base_module(mybase)

def remove_post_buffer(environ):
    i#we just remove the post buffer created in /tmp
    fid = environ['wsgi.input']
    fid.remove()


def generic(environ, start_response):
    res=django_handler.handler(environ, start_response)
    if environ['REQUEST_METHOD'] == 'POST':
       evwsgi.defer(remove_post_buffer,environ,False)
    return [res]

evwsgi.wsgi_cb(('',generic))
evwsgi.set_debug(0)
evwsgi.run()
