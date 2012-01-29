#!/usr/bin/env python

import fapws._evwsgi as evwsgi
from fapws import base
import time
import sys
from fapws.contrib import views, zip, log

import trace

base.supported_HTTP_command.append(b"TRACE")
def start():
    evwsgi.start("0.0.0.0", "8080")
    evwsgi.set_base_module(base)
    
    @trace.Trace()
    def hello(environ, start_response):
        start_response('200 OK', [('Content-Type','text/html')])
        return ["hello world!!"]

    evwsgi.wsgi_cb(("/hello", hello))

    evwsgi.set_debug(0)    
    evwsgi.run()
    

if __name__=="__main__":
    start()
