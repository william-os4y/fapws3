#!/usr/bin/env python
# -*- coding: utf-8 -*-

import fapws._evwsgi as evwsgi
from fapws import base

def start():
    evwsgi.start("/tmp/hello_unix.sock", "unix")
    evwsgi.set_base_module(base)
    
    def hello(environ, start_response):
        start_response('200 OK', [('Content-Type','text/html')])
        return ["hello world!!"]

    def iteration(environ, start_response):
        start_response('200 OK', [('Content-Type','text/plain')])
        yield "hello"
        yield " "
        yield "world!!"

    
    evwsgi.wsgi_cb(("/hello", hello))
    evwsgi.wsgi_cb(("/iterhello", iteration))

    evwsgi.set_debug(0)    
    evwsgi.run()
    

if __name__=="__main__":
    start()
